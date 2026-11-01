"""Selected-job queue requests, serialized by existing coordinator lock and CAS."""
from dataclasses import dataclass
from contextlib import closing
import uuid
import re
from pathlib import Path
from fonesi_edit.storage.db_ownership import ownership_token
from .schema import APPLICATION_ID,KNOWN_LINEAGE_HASHES
from .repository import JobRepository,JobConflict
from .ownership import CoordinatorOwnership


@dataclass(frozen=True)
class QueueCommand:
    action: str
    job_id: str
    expected_version: int
    store_token: str
    def __post_init__(self):
        if type(self.action) is not str or self.action not in {'pause','resume','cancel'}:raise JobConflict('Unknown queue command')
        try:
            if type(self.job_id) is not str or str(uuid.UUID(self.job_id))!=self.job_id:raise ValueError
        except (ValueError,TypeError,AttributeError):raise JobConflict('Canonical job ID required') from None
        if type(self.store_token) is not str or not re.fullmatch('[0-9a-f]{64}',self.store_token):raise JobConflict('Queue ownership token required')
        if type(self.expected_version) is not int or self.expected_version<1:raise JobConflict('Expected job version required')


@dataclass(frozen=True)
class QueueCommandResult:
    job_id: str
    state: str
    version: int
    cancel_requested: bool


def apply_queue_command(path,command,*,cancel=lambda:False):
    if type(command) is not QueueCommand:raise JobConflict('Typed queue command required')
    if cancel():raise JobConflict('Queue command canceled before admission')
    path=Path(path)
    if not path.is_absolute() or path.is_symlink():raise JobConflict('Original explicit queue path required')
    if ownership_token(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)!=command.store_token:raise JobConflict('Queue store changed; refresh required')
    with closing(JobRepository(path,existing_only=True)) as repo:
        if ownership_token(repo.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)!=command.store_token:raise JobConflict('Queue store changed; refresh required')
        return _apply(repo,command,cancel)


def _apply(repo,command,cancel):
    with CoordinatorOwnership(repo) as owner:
        return _apply_owned(repo,owner,command,cancel)


def _apply_owned(repo,owner,command,cancel=lambda:False):
    if type(command) is not QueueCommand or owner.repository is not repo:
        raise JobConflict("Exact command and repository owner required")
    owner.guard()
    if cancel():raise JobConflict('Queue command canceled before transaction')
    db=repo.db;db.execute('BEGIN IMMEDIATE')
    try:
        owner.guard()
        if ownership_token(repo.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)!=command.store_token:raise JobConflict('Queue ownership changed')
        current=repo.get(command.job_id)
        if current.version!=command.expected_version:raise JobConflict('Queue changed; refresh before issuing a new request')
        if cancel():raise JobConflict('Queue command canceled before mutation')
        if command.action=='pause':result=repo.pause(current)
        elif command.action=='resume':
            if current.state!='paused':raise JobConflict('Only explicitly paused pending jobs can resume here')
            result=repo.resume(current)
        else:result=repo.request_cancel(current)
        owner.guard()
        db.execute('COMMIT')
    except BaseException:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    # No automatic retry after any SQLite error/unknown commit outcome.
    return QueueCommandResult(result.id,result.state,result.version,result.cancel_requested)
