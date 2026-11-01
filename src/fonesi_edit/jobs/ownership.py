"""Live single-coordinator OS lock plus monotonically increasing DB epoch.

Cooperating app processes only, in app-owned user data. Never infer authority from a
PID, caller-supplied epoch, persisted lock-file existence or expiring wall clock.
"""
import os
from pathlib import Path
import stat
import uuid

MARKER=b'FONESI-EDIT-COORDINATOR-LOCK-v1\n'

class CoordinatorError(RuntimeError):pass
class CoordinatorBusy(CoordinatorError):pass
class CoordinatorLost(CoordinatorError):pass


def identity(info):return info.st_dev,info.st_ino

def regular(info):
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400 and bool(info.st_ino)


class CoordinatorOwnership:
    def __init__(self,repository):
        self.repository=repository
        self.path=repository.path.with_name(repository.path.name+'.coordinator-lock')
        self._fd=None;self._db_fd=None;self.epoch=None;self.owner_uuid=None
        self._active=False;self._revoked=False

    def __enter__(self):
        if self._revoked:raise CoordinatorLost('Revoked ownership cannot be reacquired by the same instance')
        if self._active or self._fd is not None:raise CoordinatorError('Ownership instance already active')
        flags=os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
        try:
            try:
                self._fd=os.open(self.path,flags|os.O_CREAT|os.O_EXCL,0o600)
                if os.write(self._fd,MARKER)!=len(MARKER):raise CoordinatorError('Incomplete new lock marker; explicit recovery needed')
                os.fsync(self._fd)
            except FileExistsError:
                if not regular(self.path.lstat()):raise CoordinatorError('Foreign lock symlink/reparse/nonregular path')
                self._fd=os.open(self.path,flags)
            self._lock_identity=identity(os.fstat(self._fd))
            self._check_lock(marker=False)
            os.lseek(self._fd,0,os.SEEK_SET)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(self._fd,msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(self._fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except (BlockingIOError,PermissionError) as exc:
                raise CoordinatorBusy('Another coordinator holds the lock, or access is unavailable') from exc
            # Pin database incarnation for this live owner, not only its pathname.
            self._db_fd=self.repository.duplicate_database_anchor()
            self._db_identity=self.repository.database_identity
            self._check_db()
            self.repository._prepare_coordinator_connection()
            self._check_lock();self._check_db()
            db=self.repository.db
            db.execute('BEGIN IMMEDIATE')
            try:
                self._check_lock();self._check_db()
                self.owner_uuid=str(uuid.uuid4())
                cursor=db.execute('INSERT INTO coordinator_epochs(owner_uuid) VALUES(?)',(self.owner_uuid,))
                self.epoch=cursor.lastrowid
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:db.execute('ROLLBACK')
                raise
            self._active=True;self.guard();return self
        except BaseException:
            self.close();raise

    def _check_lock(self,*,marker=True):
        if self._fd is None:raise CoordinatorLost('Coordinator lock is closed')
        opened=os.fstat(self._fd);named=self.path.lstat()
        if not regular(opened) or not regular(named) or identity(opened)!=identity(named) or identity(opened)!=self._lock_identity:
            raise CoordinatorLost('Coordinator lock identity changed')
        if not marker:return # acquire byte lock before reading another owner's locked byte
        os.lseek(self._fd,0,os.SEEK_SET)
        if opened.st_size!=len(MARKER) or os.read(self._fd,len(MARKER)+1)!=MARKER:
            raise CoordinatorLost('Foreign or incomplete lock marker; left untouched')
        os.lseek(self._fd,0,os.SEEK_SET)

    def _check_db(self):
        self.repository.guard_database()
        opened=os.fstat(self._db_fd);named=self.repository.path.lstat()
        if not regular(opened) or not regular(named) or identity(opened)!=self._db_identity or identity(named)!=self._db_identity:
            raise CoordinatorLost('Jobs database physical identity changed')

    def guard(self):
        if not self._active or self._revoked:raise CoordinatorLost('No active coordinator authority')
        try:
            self._check_lock();self._check_db()
            row=self.repository.db.execute('SELECT epoch,owner_uuid FROM coordinator_epochs ORDER BY epoch DESC LIMIT 1').fetchone()
            if row is None or tuple(row)!=(self.epoch,self.owner_uuid):
                raise CoordinatorLost('Coordinator epoch is stale or changed')
            return self.epoch
        except Exception as exc:
            self._revoked=True;self._active=False
            if isinstance(exc,CoordinatorLost):raise
            raise CoordinatorLost('Coordinator continuity lost; instance permanently revoked') from exc

    def close(self):
        self._active=False
        try:
            if self._db_fd is not None:os.close(self._db_fd)
        finally:
            self._db_fd=None
            try:
                if self._fd is not None:os.close(self._fd)
            finally:self._fd=None
        # Never unlink: another process may already have opened the canonical inode.

    def __exit__(self,*args):self.close()
