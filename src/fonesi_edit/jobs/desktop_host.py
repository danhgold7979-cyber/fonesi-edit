"""Qt-owned coordinator thread for an already verified jobs database.

This transport only performs selected queue commands. It never admits a render
worker or converts an observation to job success.
"""
from pathlib import Path
import re

from PySide6.QtCore import QThread, Signal

from fonesi_edit.storage.db_ownership import ownership_token
from fonesi_edit.jobs.schema import APPLICATION_ID, KNOWN_LINEAGE_HASHES
from fonesi_edit.jobs.repository import JobRepository, JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership, CoordinatorBusy
from fonesi_edit.jobs.inbox import CoordinatorInbox
from fonesi_edit.jobs.event_store import event_path


class DesktopCoordinatorHost(QThread):
    acquired = Signal(object)
    unavailable = Signal(str)

    def __init__(self, path, expected_token, parent=None, *, poll_ms=20):
        super().__init__(parent)
        self.path = Path(path)
        if not self.path.is_absolute() or self.path.is_symlink():
            raise ValueError('Explicit non-link jobs database path required')
        if type(expected_token) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_token) is None:
            raise ValueError('A previously verified queue ownership token is required')
        if type(poll_ms) is not int or not 5 <= poll_ms <= 100:
            raise ValueError('Bounded owner polling interval required')
        self.expected_token = expected_token
        self.poll_ms = poll_ms

    def run(self):
        repository = None
        try:
            if self.isInterruptionRequested():
                return
            # Read-only identity proof BEFORE opening/migrating or locking anything.
            actual = ownership_token(self.path, APPLICATION_ID, KNOWN_LINEAGE_HASHES)
            if actual != self.expected_token:
                raise JobConflict('Jobs store changed since UI snapshot')
            repository = JobRepository(self.path, existing_only=True)
            if ownership_token(self.path, APPLICATION_ID, KNOWN_LINEAGE_HASHES) != self.expected_token:
                raise JobConflict('Jobs store changed while opening coordinator')
            with CoordinatorOwnership(repository) as owner:
                with CoordinatorInbox(owner, events_path=event_path(self.path)) as inbox:
                    if ownership_token(self.path, APPLICATION_ID, KNOWN_LINEAGE_HASHES) != self.expected_token:
                        raise JobConflict('Jobs store changed before route publication')
                    if self.isInterruptionRequested():
                        return
                    # Only immutable command requests cross into this owner thread.
                    self.acquired.emit(inbox)
                    while not self.isInterruptionRequested():
                        inbox.drain(limit=16)
                        self.msleep(self.poll_ms)
        except CoordinatorBusy:
            self.unavailable.emit('Bộ điều phối khác đang giữ quyền. Chỉ đọc hàng đợi; không gửi lệnh qua đường vòng.')
        except BaseException:
            # No raw exception, path or secret leaves the owner thread.
            self.unavailable.emit('Không xác nhận được bộ điều phối. Giữ trạng thái chỉ đọc; kiểm tra quyền sở hữu dữ liệu.')
        finally:
            # The inbox/owner context must retire on this very thread first.
            if repository is not None:
                repository.close()
