"""Separate owned bounded diagnostic store; never job/publication authority."""
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import sqlite3
import uuid
from fonesi_edit.storage.db_ownership import owns_database, register_database, receipt_path
from fonesi_edit.storage.sqlite_open import open_versioned
from .ownership import identity, regular
from .events import Event,EventCode,EventStage

APPLICATION_ID=0x4645444C
VERSION=1
SQL='''CREATE TABLE events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    store_token TEXT NOT NULL CHECK(length(store_token)=64),
    job_id TEXT NOT NULL CHECK(length(job_id)=36),
    attempt INTEGER NOT NULL CHECK(attempt>=0),
    job_version INTEGER NOT NULL CHECK(job_version>0),
    observed_ms INTEGER NOT NULL CHECK(observed_ms>=0),
    payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB))<=256))'''
SCHEMA_HASH=sha256(SQL.encode()).hexdigest()

class EventStoreError(RuntimeError):pass


@dataclass(frozen=True)
class EventRecord:
    store_token: str
    job_id: str
    attempt: int
    job_version: int
    observed_ms: int
    event: Event

    def __post_init__(self):
        if type(self.store_token) is not str or not re.fullmatch('[0-9a-f]{64}',self.store_token):
            raise ValueError('Exact diagnostic store token required')
        if type(self.job_id) is not str or len(self.job_id)!=36 or str(uuid.UUID(self.job_id))!=self.job_id:
            raise ValueError('Canonical diagnostic job UUID required')
        for value,lower in ((self.attempt,0),(self.job_version,1),(self.observed_ms,0)):
            if type(value) is not int or not lower<=value<2**63:raise ValueError('Bounded diagnostic integer required')
        if type(self.event) is not Event:raise ValueError('Typed diagnostic required')


def _matches(db,version):
    if db.execute("SELECT 1 FROM sqlite_master WHERE type!='table' AND name NOT LIKE 'sqlite_%'").fetchone():return False
    actual=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    return actual==({'events':SQL} if version==VERSION else {})


def event_path(jobs_path):
    path=Path(jobs_path)
    if not path.is_absolute():raise EventStoreError('Explicit jobs path required')
    return path.with_name(path.name+'.events.sqlite3')


class EventStore:
    def __init__(self,path,*,global_limit=5000,per_job_limit=500):
        if (type(global_limit) is not int or type(per_job_limit) is not int or
            not 1<=per_job_limit<=global_limit<=100000):raise ValueError('Bounded event retention required')
        self.path=Path(path)
        if not self.path.is_absolute():raise EventStoreError('Explicit event path required')
        self.db=None;self.fd=None;self._revoked=False
        self.global_limit=global_limit;self.per_job_limit=per_job_limit
        self.path.parent.mkdir(parents=True,exist_ok=True)
        created=False;flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
        try:
            try:self.fd=os.open(self.path,flags|os.O_CREAT|os.O_EXCL,0o600);created=True
            except FileExistsError:
                if not regular(self.path.lstat()):raise EventStoreError('Event store must be regular/non-reparse')
                self.fd=os.open(self.path,flags)
            self._identity=identity(os.fstat(self.fd));self.guard()
            if (not created or receipt_path(self.path).exists() or receipt_path(self.path).is_symlink()) and not owns_database(self.path,APPLICATION_ID,SCHEMA_HASH):
                raise EventStoreError('Preexisting unmarked/foreign event store refused')
            connect=lambda path,**kwargs:sqlite3.connect(Path(path).as_uri()+'?mode=rw',uri=True,**kwargs)
            self.db,version=open_versioned(self.path,connect=connect,recovery_seconds=0,owned=lambda:owns_database(self.path,APPLICATION_ID,SCHEMA_HASH))
            self.guard();appid=self.db.execute('PRAGMA application_id').fetchone()[0]
            if (version not in (0,VERSION) or appid not in ((0,APPLICATION_ID) if version==0 else (APPLICATION_ID,)) or
                not _matches(self.db,version)):
                raise EventStoreError('Foreign/newer/corrupt event schema; no migration')
            marker=receipt_path(self.path)
            if marker.exists() or marker.is_symlink():
                if not owns_database(self.path,APPLICATION_ID,SCHEMA_HASH):raise EventStoreError('Invalid event receipt')
            elif version:raise EventStoreError('Existing event store lacks receipt')
            if version==0:
                self.db.execute('BEGIN IMMEDIATE')
                try:
                    self.guard()
                    if (self.db.execute('PRAGMA user_version').fetchone()[0]!=0 or
                        self.db.execute('PRAGMA application_id').fetchone()[0] not in (0,APPLICATION_ID) or not _matches(self.db,0)):
                        raise EventStoreError('Concurrent event initialization; not replayed')
                    self.db.execute(SQL);self.db.execute(f'PRAGMA application_id={APPLICATION_ID}')
                    self.db.execute(f'PRAGMA user_version={VERSION}');self.db.execute('COMMIT')
                except BaseException:
                    if self.db.in_transaction:self.db.execute('ROLLBACK')
                    raise
            self.guard();self.db.execute('PRAGMA journal_mode=DELETE')
            self.db.execute('PRAGMA synchronous=FULL');self.db.execute('PRAGMA busy_timeout=0')
            self.guard();register_database(self.path,APPLICATION_ID,SCHEMA_HASH)
        except BaseException:self.close();raise

    def guard(self):
        if self.fd is None or self._revoked:raise EventStoreError('Event store closed or continuity revoked')
        try:
            named=self.path.lstat();opened=os.fstat(self.fd)
            if not regular(named) or not regular(opened) or identity(named)!=self._identity or identity(opened)!=self._identity:
                raise EventStoreError('Event store identity changed')
        except BaseException:
            self._revoked=True;raise

    def append(self,record):
        if type(record) is not EventRecord:raise ValueError('Typed event record required')
        self.guard();self.db.execute('BEGIN IMMEDIATE')
        try:
            self.guard()
            self.db.execute('INSERT INTO events(store_token,job_id,attempt,job_version,observed_ms,payload) VALUES(?,?,?,?,?,?)',
                (record.store_token,record.job_id,record.attempt,record.job_version,record.observed_ms,record.event.canonical()))
            self.db.execute('DELETE FROM events WHERE store_token=? AND job_id=? AND sequence NOT IN (SELECT sequence FROM events WHERE store_token=? AND job_id=? ORDER BY sequence DESC LIMIT ?)',
                (record.store_token,record.job_id,record.store_token,record.job_id,self.per_job_limit))
            self.db.execute('DELETE FROM events WHERE sequence NOT IN (SELECT sequence FROM events ORDER BY sequence DESC LIMIT ?)',(self.global_limit,))
            self.guard();self.db.execute('COMMIT')
        except BaseException:
            self._revoked=True
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise # Unknown append is never replayed.

    def close(self):
        self._revoked=True
        try:
            if self.db is not None:self.db.close()
        finally:
            self.db=None
            fd,self.fd=self.fd,None
            if fd is not None:os.close(fd)
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def read_events(path,store_token,job_id,*,limit=100,cancel=lambda:False):
    # Validate selection without accepting caller text in any record.
    EventRecord(store_token,job_id,0,1,0,Event(EventCode.QUEUE_PAUSED,EventStage.QUEUE))
    if type(limit) is not int or not 1<=limit<=500:raise ValueError('Bounded event page required')
    path=Path(path)
    if not path.is_absolute():raise EventStoreError('Explicit event path required')
    fd=None;db=None
    try:
        if cancel():raise EventStoreError('Diagnostic read canceled')
        try:named=path.lstat()
        except FileNotFoundError:return ()
        if not regular(named):raise EventStoreError('Event path must be regular/non-reparse')
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0));expected=identity(os.fstat(fd))
        def guard():
            opened=os.fstat(fd);current=path.lstat()
            if not regular(current) or not regular(opened) or identity(current)!=expected or identity(opened)!=expected or identity(named)!=expected:
                raise EventStoreError('Event read identity changed')
        def header_guard():
            # SQLite file-format header offsets18/19: 1=rollback, 2=WAL.
            # Check using the retained original FD BEFORE SQLite can create SHM.
            os.lseek(fd,0,os.SEEK_SET);header=os.read(fd,100)
            if (len(header)!=100 or header[:16]!=b'SQLite format 3\x00' or header[18:20]!=b'\x01\x01' or
                int.from_bytes(header[60:64],'big')!=VERSION or int.from_bytes(header[68:72],'big')!=APPLICATION_ID):
                raise EventStoreError('Unsupported diagnostic header/journal mode; SQLite not opened')
        guard()
        if not owns_database(path,APPLICATION_ID,SCHEMA_HASH):raise EventStoreError('Event ownership unavailable')
        header_guard();guard()
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=.5)
        db.set_progress_handler(lambda:int(bool(cancel())),1000);guard()
        if (db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or
            db.execute('PRAGMA user_version').fetchone()[0]!=VERSION or not _matches(db,VERSION) or
            db.execute('PRAGMA journal_mode').fetchone()[0]!='delete'):
            raise EventStoreError('Unsupported event schema')
        rows=db.execute('SELECT store_token,job_id,attempt,job_version,observed_ms,substr(payload,1,257) FROM events WHERE store_token=? AND job_id=? ORDER BY sequence DESC LIMIT ?',
                        (store_token,job_id,limit)).fetchall()
        result=tuple(EventRecord(*row[:5],Event.parse(row[5])) for row in rows)
        guard();header_guard()
        if not owns_database(path,APPLICATION_ID,SCHEMA_HASH) or cancel():raise EventStoreError('Event read no longer admitted')
        return result
    except (OSError,sqlite3.Error,ValueError,TypeError) as exc:
        raise EventStoreError('Diagnostic records unavailable; no data changed') from exc
    finally:
        try:
            if db is not None:db.close()
        finally:
            if fd is not None:os.close(fd)
