"""Bounded queue observations; no snapshot/credential content or state mutation."""
from dataclasses import dataclass
import os
import re
from pathlib import Path
import sqlite3
import stat
import uuid

from fonesi_edit.storage.db_ownership import owns_database,ownership_token,DatabaseOwnershipError
from .schema import APPLICATION_ID,VERSION,KNOWN_LINEAGE_HASHES,matches


class QueueReadError(RuntimeError):pass


@dataclass(frozen=True)
class QueueRow:
    id: str
    state: str
    attempt: int
    cancel_requested: bool
    unresolved_publication: bool
    version: int=1
    snapshot_hash: str|None=None


@dataclass(frozen=True)
class QueueSnapshot:
    rows: tuple[QueueRow,...]
    truncated: bool
    store_exists: bool
    store_token: str|None=None


def read_queue(path,*,limit=500,cancel=lambda:False):
    if type(limit) is not int or not 1<=limit<=1000:raise QueueReadError('Bounded queue page required')
    path=Path(path)
    if not path.is_absolute():raise QueueReadError('Explicit queue path required')
    if cancel():raise QueueReadError('Queue read canceled')
    fd=None;db=None
    try:
        try:info=path.lstat()
        except FileNotFoundError:return QueueSnapshot((),False,False)
        if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise QueueReadError('Queue database identity unavailable')
        fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
        identity=(info.st_dev,info.st_ino)
        def guard():
            current=path.lstat();opened=os.fstat(fd)
            if (not stat.S_ISREG(current.st_mode) or getattr(current,'st_file_attributes',0)&0x400 or
                identity!=(current.st_dev,current.st_ino) or identity!=(opened.st_dev,opened.st_ino)):
                raise QueueReadError('Queue database changed')
        guard()
        if not owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):raise QueueReadError('Queue ownership unverified')
        token=ownership_token(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)
        db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=.5)
        db.set_progress_handler(lambda:int(bool(cancel())),1000)
        guard()
        if (db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or
            db.execute('PRAGMA user_version').fetchone()[0]!=VERSION or not matches(db,VERSION)):
            raise QueueReadError('Unsupported queue schema')
        # No snapshot_json/request_key/source paths are selected or exposed.
        rows=db.execute('''SELECT j.id,j.state,j.attempt,j.cancel_requested,
            EXISTS(SELECT 1 FROM artifact_sets s WHERE s.job_id=j.id AND s.state IN ('prepared','claimed')),j.version,j.snapshot_hash
            FROM jobs j ORDER BY j.rowid DESC LIMIT ?''',(limit+1,)).fetchall()
        guard()
        states={'pending','running','validating','publishing','retry_wait','blocked_configuration','paused','succeeded','succeeded_with_warnings','failed','canceled','skipped'}
        for row in rows:
            if (type(row[0]) is not str or str(uuid.UUID(row[0]))!=row[0] or row[1] not in states or
                type(row[2]) is not int or not 0<=row[2]<=2147483647 or row[3] not in (0,1) or type(row[5]) is not int or row[5]<1 or
                type(row[6]) is not str or not re.fullmatch('[0-9a-f]{64}',row[6])):
                raise QueueReadError('Malformed queue observation')
        if token!=ownership_token(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):raise QueueReadError('Queue ownership changed')
        if cancel():raise QueueReadError('Queue read canceled')
        return QueueSnapshot(tuple(QueueRow(r[0],r[1],r[2],bool(r[3]),bool(r[4]),r[5],r[6]) for r in rows[:limit]),len(rows)>limit,True,token)
    except QueueReadError:raise
    except (OSError,sqlite3.Error,ValueError,DatabaseOwnershipError) as exc:
        raise QueueReadError('Queue unavailable; existing data left unchanged') from exc
    finally:
        if db is not None:db.close()
        if fd is not None:os.close(fd)
