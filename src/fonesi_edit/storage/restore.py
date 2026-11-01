"""Explicit offline project-backup restore to a NEW owned store, never overwrite."""
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import math
import os
from pathlib import Path
import sqlite3
import time
from fonesi_edit.artifacts.filesystem import Destination,safe_name,_plain,_identity
from .db_ownership import receipt_path,register_database
from .projects import (APPLICATION_ID,SCHEMA_VERSION,PROJECTS_SQL,PROJECTS_V1_SQL,
                       PROJECT_SCHEMA_HASH,PROJECT_V1_HASH,MAX_PROJECT_BYTES,Project,_origin)


class RestoreError(RuntimeError):
    def __init__(self,message,*,destination_created=False,ownership_unknown=False):
        super().__init__(message)
        self.destination_created=destination_created
        self.ownership_unknown=ownership_unknown


class RestoreCanceled(RestoreError):pass


@dataclass(frozen=True)
class RestoreResult:
    destination: Path
    schema_version: int
    project_count: int
    source_sha256: str
    size: int


def _signature(info):
    return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns


def _sidecars_absent(path,*,receipt=False):
    names=[path.with_name(path.name+suffix) for suffix in ('-wal','-shm','-journal')]
    if receipt:names.append(receipt_path(path))
    if any(p.exists() or p.is_symlink() for p in names):
        raise RestoreError('Existing sidecar/receipt prevents isolated backup restoration')


def _header(fd):
    os.lseek(fd,0,os.SEEK_SET);header=os.read(fd,100)
    if (len(header)!=100 or header[:16]!=b'SQLite format 3\x00' or header[18:20]!=b'\x01\x01' or
        int.from_bytes(header[68:72],'big')!=APPLICATION_ID):
        raise RestoreError('Unsupported backup identity or non-rollback journal format')
    version=int.from_bytes(header[60:64],'big')
    if version not in (1,SCHEMA_VERSION):raise RestoreError('Unsupported/newer backup schema; no restore')
    return version


def _hash_fd(fd,size,check):
    os.lseek(fd,0,os.SEEK_SET);digest=sha256();total=0
    while True:
        check();block=os.read(fd,min(1024*1024,size+1-total))
        if not block:break
        total+=len(block)
        if total>size:raise RestoreError('Backup size changed')
        digest.update(block)
    if total!=size:raise RestoreError('Backup size changed')
    return digest.hexdigest()


def _validate_copy(path,version,check,guard):
    db=None
    try:
        check();guard()
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=0)
        db.set_progress_handler(lambda: (check() or 0),1000)
        guard()
        if (db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or
            db.execute('PRAGMA user_version').fetchone()[0]!=version or
            db.execute('PRAGMA journal_mode').fetchone()[0]!='delete'):
            raise RestoreError('Copied database identity changed')
        if db.execute("SELECT 1 FROM sqlite_master WHERE type!='table' AND name NOT LIKE 'sqlite_%'").fetchone():
            raise RestoreError('Backup contains unsupported schema objects')
        tables=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
        if tables!={'projects':PROJECTS_V1_SQL if version==1 else PROJECTS_SQL}:
            raise RestoreError('Backup project schema is not exact known schema')
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RestoreError('Backup integrity check failed')
        origin='NULL' if version==1 else "CASE WHEN origin_base IS NULL THEN NULL WHEN typeof(origin_base)='text' THEN substr(CAST(origin_base AS BLOB),1,131069) ELSE 0 END"
        query=f'''SELECT CASE WHEN typeof(id)='text' THEN substr(CAST(id AS BLOB),1,?) ELSE NULL END,
            CASE WHEN typeof(name)='text' THEN substr(CAST(name AS BLOB),1,801) ELSE NULL END,
            substr(CAST(document AS BLOB),1,?),
            CASE WHEN typeof(version)='integer' THEN version ELSE NULL END,
            CASE WHEN typeof(updated_at) IN ('integer','real') THEN updated_at ELSE NULL END,
            {origin} FROM projects'''
        count=0
        for row in db.execute(query,(MAX_PROJECT_BYTES+1,MAX_PROJECT_BYTES+1)):
            check()
            if type(row[2]) is not bytes or len(row[2])>MAX_PROJECT_BYTES:
                raise RestoreError('Backup project document exceeds bound')
            def text(value,bound):
                if type(value) is not bytes or len(value)>bound:
                    raise RestoreError('Backup metadata exceeds bounded text representation')
                return value.decode('utf-8',errors='strict')
            row_id=text(row[0],MAX_PROJECT_BYTES);row_name=text(row[1],800)
            row_origin=None if row[5] is None else text(row[5],131068)
            project=Project.parse(row[2])
            if (project.id!=row_id or project.name!=row_name or type(row[3]) is not int or row[3]<1 or
                type(row[4]) not in (int,float) or not math.isfinite(row[4]) or row[4]<0):
                raise RestoreError('Backup project row identity/version is inconsistent')
            _origin(row_origin);count+=1
        guard();check();return count
    finally:
        if db is not None:db.close()


def restore_project_backup(source,destination,*,cancel=lambda:False,timeout=300,
                           progress=lambda copied,total:None,fault=lambda stage:None):
    """Copy/validate before ownership publication; failed new files are retained.

    Source is never opened by SQLite, recovered, modified or deleted. Caller must
    keep the new destination namespace private/cooperating until this returns.
    Cancellation/deadline are checked between operations, not a preemptive OS-I/O limit.
    """
    source=Path(source);destination=Path(destination)
    if not source.is_absolute() or not destination.is_absolute():raise RestoreError('Explicit absolute restore paths required')
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=3600:
        raise RestoreError('Restore timeout must be finite and positive and at most3600seconds')
    deadline=time.monotonic()+timeout;created=False;registration_attempted=False
    def check():
        if cancel():raise RestoreCanceled('Restore canceled; any new destination is retained')
        if time.monotonic()>deadline:raise RestoreError('Restore deadline reached; any new destination is retained')
    try:
        check();safe_name(destination.name)
        if destination.name.lower().endswith(('-wal','-shm','-journal','.fonesi-owner')):
            raise RestoreError('A SQLite sidecar/ownership name cannot be a restored database')
        _sidecars_absent(source);_sidecars_absent(destination,receipt=True)
        with ExitStack() as stack:
            parent=stack.enter_context(Destination(destination.parent))
            named=source.lstat();_plain(named)
            source_fd=os.open(source,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
            stack.callback(os.close,source_fd)
            opened=os.fstat(source_fd);_plain(opened)
            if _identity(opened)!=_identity(named) or opened.st_size!=named.st_size:raise RestoreError('Source identity changed')
            version=_header(source_fd)
            def source_guard():
                current=source.lstat();held=os.fstat(source_fd);_plain(current);_plain(held)
                if _signature(named)!=_signature(current) or _signature(opened)!=_signature(held) or _identity(current)!=_identity(held):
                    raise RestoreError('Backup changed during restoration')
                _sidecars_absent(source)
            source_guard();check();parent._check();_sidecars_absent(destination,receipt=True)
            target_fd=parent._open(destination.name,os.O_RDWR|os.O_CREAT|os.O_EXCL)
            created=True;stack.callback(os.close,target_fd);target_identity=_plain(os.fstat(target_fd))
            def target_guard():
                parent._check();named_target=parent._stat(destination.name);held=os.fstat(target_fd)
                if _plain(named_target)!=target_identity or _plain(held)!=target_identity:
                    raise RestoreError('New destination identity changed')
            fault('after_create');os.lseek(source_fd,0,os.SEEK_SET);digest=sha256();total=0
            while True:
                check();block=os.read(source_fd,min(1024*1024,opened.st_size+1-total))
                if not block:break
                total+=len(block)
                if total>opened.st_size:raise RestoreError('Backup grew during copying')
                digest.update(block);remaining=memoryview(block)
                while remaining:
                    check();written=os.write(target_fd,remaining)
                    if written<=0:raise RestoreError('Incomplete restore write')
                    remaining=remaining[written:]
                progress(total,opened.st_size)
            if total!=opened.st_size:raise RestoreError('Backup changed size')
            os.fsync(target_fd);source_guard();target_guard();fault('after_copy');check()
            expected=digest.hexdigest()
            if _hash_fd(source_fd,opened.st_size,check)!=expected:raise RestoreError('Backup content changed')
            source_guard();_sidecars_absent(destination,receipt=True)
            if _header(target_fd)!=version:raise RestoreError('Copied header differs')
            if _hash_fd(target_fd,opened.st_size,check)!=expected:raise RestoreError('Copied bytes differ')
            count=_validate_copy(destination,version,check,target_guard);fault('after_validate')
            source_guard();target_guard();_sidecars_absent(destination,receipt=True)
            if _header(target_fd)!=version or _hash_fd(target_fd,opened.st_size,check)!=expected:
                raise RestoreError('Validated target changed')
            check();fault('before_register');source_guard();target_guard()
            if (_hash_fd(source_fd,opened.st_size,check)!=expected or
                _hash_fd(target_fd,opened.st_size,check)!=expected):
                raise RestoreError('Source or target changed before ownership registration')
            source_guard();target_guard();_sidecars_absent(destination,receipt=True)
            registration_attempted=True
            register_database(destination,APPLICATION_ID,PROJECT_V1_HASH if version==1 else PROJECT_SCHEMA_HASH)
            fault('after_register');target_guard()
            if _hash_fd(target_fd,opened.st_size,check)!=expected:raise RestoreError('Registered target changed')
            result=RestoreResult(destination,version,count,expected,total)
        return result
    except Exception as exc:
        cls=RestoreCanceled if isinstance(exc,RestoreCanceled) else RestoreError
        raise cls('Restoration not confirmed; any new destination is retained, never auto-retried',
                  destination_created=created,ownership_unknown=registration_attempted) from exc
