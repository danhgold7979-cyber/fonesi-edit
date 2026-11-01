"""Bounded UI-to-owner routing; SQLite and authority stay on the runner thread."""
from collections import deque
from concurrent.futures import Future
from threading import Lock, get_ident
from .commands import QueueCommand, _apply_owned
from .repository import JobConflict
from .ownership import CoordinatorLost
from .observations import LatestProgress
from .progress import JobProgressObserver
from .schema import APPLICATION_ID, KNOWN_LINEAGE_HASHES
from fonesi_edit.storage.db_ownership import ownership_token


class CoordinatorInbox:
    def __init__(self, owner, *, capacity=64):
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError('Inbox capacity must be 1..256')
        owner.guard()
        self._owner = owner
        self._thread = get_ident()
        self._capacity = capacity
        self._pending = deque()
        self._lock = Lock()
        self._closed = False
        self._revision = 0
        self._running = 0
        self.progress = LatestProgress(ownership_token(owner.repository.path, APPLICATION_ID, KNOWN_LINEAGE_HASHES))

    def state(self):
        """Coalesced read-refresh hint, never a durable job-state payload."""
        with self._lock:
            return self._revision, self._closed and self._running == 0

    def notify_changed(self):
        if get_ident() != self._thread:
            raise JobConflict('State notifications belong to the coordinator thread')
        self._owner.guard()
        with self._lock:
            if self._closed:raise JobConflict('Coordinator inbox retired')
            self._revision += 1

    def progress_observer(self, job):
        if get_ident() != self._thread:
            raise JobConflict('Progress observer belongs to the coordinator thread')
        with self._lock:
            if self._closed:raise JobConflict('Coordinator inbox retired')
        self._owner.guard()
        return JobProgressObserver(self._owner.repository, job,
                                   guard=self._owner.guard, emit=self.progress.put)

    def submit(self, command):
        if type(command) is not QueueCommand:
            raise JobConflict('Typed queue command required')
        future = Future()
        with self._lock:
            if self._closed:
                raise JobConflict('Coordinator inbox retired')
            if len(self._pending) >= self._capacity:
                raise JobConflict('Coordinator inbox full; no command admitted')
            self._pending.append((command, future))
        return future

    def close(self):
        """Refuse queued work; an already executing transaction is not undone."""
        with self._lock:
            if not self._closed:self._revision += 1
            self._closed = True
            pending = list(self._pending)
            self._pending.clear()
        self.progress.close()
        for _, future in pending:
            if future.set_running_or_notify_cancel():
                future.set_exception(JobConflict('Coordinator stopped before command admission'))

    def drain(self, *, limit=16):
        if get_ident() != self._thread:
            raise JobConflict('Commands must execute on the coordinator thread')
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError('Drain limit must be 1..256')
        processed = 0
        try:
            self._owner.guard()
            for _ in range(limit):
                with self._lock:
                    if self._closed or not self._pending:
                        break
                    command, future = self._pending.popleft()
                    # Admission and close linearize under one lock. Future's
                    # transition invokes no done callbacks (completion is outside).
                    if not future.set_running_or_notify_cancel():
                        continue
                    self._running += 1
                try:
                    result = _apply_owned(self._owner.repository, self._owner, command)
                except BaseException as exc:
                    future.set_exception(exc)
                    # Ordinary stale/invalid requests are refusals. Unknown SQLite
                    # outcome/authority loss retires the route, never replays it.
                    if isinstance(exc, CoordinatorLost) or not isinstance(exc, JobConflict):
                        raise
                else:
                    future.set_result(result)
                finally:
                    with self._lock:
                        self._running -= 1
                        self._revision += 1
                processed += 1
            return processed
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
