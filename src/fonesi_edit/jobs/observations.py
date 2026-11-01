"""Bounded latest-only progress transport; observations confer no authority."""
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
import re
import uuid
from .progress import JobProgress, Progress


@dataclass(frozen=True)
class ProgressBatch:
    store_token: str
    events: tuple[JobProgress, ...]


class LatestProgress:
    def __init__(self, store_token, *, capacity=64):
        if type(store_token) is not str or not re.fullmatch('[0-9a-f]{64}', store_token):
            raise ValueError('Exact store token required')
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError('Progress capacity must be 1..256')
        self._token = store_token
        self._capacity = capacity
        self._lock = Lock()
        self._events = OrderedDict()
        self._closed = False

    def put(self, event):
        if (type(event) is not JobProgress or type(event.observation) is not Progress
            or type(event.job_id) is not str or str(uuid.UUID(event.job_id)) != event.job_id
            or type(event.snapshot_hash) is not str or not re.fullmatch('[0-9a-f]{64}', event.snapshot_hash)
            or type(event.attempt) is not int or not 1 <= event.attempt <= 2147483647):
            raise ValueError('Bounded typed progress required')
        observation = event.observation
        for value in (observation.frame, observation.out_time_us, observation.total_size):
            if value is not None and (type(value) is not int or abs(value) > 2**63-1):
                raise ValueError('Bounded progress counters required')
        if (type(observation.ended) is not bool or
            any(value is not None and value < 0 for value in (observation.frame, observation.total_size))):
            raise ValueError('Invalid progress counters')
        with self._lock:
            if self._closed:return
            previous = self._events.get(event.job_id)
            if previous is not None and previous.attempt > event.attempt:return
            self._events.pop(event.job_id, None)
            self._events[event.job_id] = event
            if len(self._events) > self._capacity:self._events.popitem(last=False)

    def drain(self):
        with self._lock:
            result = ProgressBatch(self._token, tuple(self._events.values()))
            self._events.clear()
            return result

    def close(self):
        with self._lock:
            self._closed = True
            self._events.clear()
