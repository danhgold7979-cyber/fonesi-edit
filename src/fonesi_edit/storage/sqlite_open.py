"""Bounded recovery of the evidenced Windows SQLite shared-memory retirement gap."""
import os
from pathlib import Path
import sqlite3
import time


def open_versioned(path: Path, *, windows=None, connect=sqlite3.connect,
                   clock=time.monotonic, sleep=time.sleep, recovery_seconds=3.0, owned=lambda:False):
    """Return owned connection and user_version; never remove/modify WAL or SHM.

    Hosted Python3.13/SQLite3.50.4 reproduced SQLITE_IOERR_TRUNCATE(1546)
    immediately after process termination. SQLite upstream identifies a transient
    still-mapped Windows SHM view; only that exact error gets bounded reopen.
    All other errors, and an exhausted retry window, propagate unchanged.
    SQLite busy waits use remaining budget; OS filesystem calls are not preempted.
    """
    if not 0<=recovery_seconds<=3:
        raise ValueError('Recovery deadline must be between0and3seconds')
    windows=os.name=='nt' if windows is None else windows
    deadline=clock()+recovery_seconds
    last_error=None
    while True:
        remaining=max(0,deadline-clock())
        if last_error is not None and remaining<=0:raise last_error
        connection=connect(path,timeout=min(5,remaining),isolation_level=None)
        try:
            version=connection.execute('PRAGMA user_version').fetchone()[0]
            return connection,version
        except BaseException as exc:
            connection.close()
            if (not windows or not isinstance(exc,sqlite3.OperationalError) or
                    getattr(exc,'sqlite_errorcode',None)!=1546 or not owned() or clock()>=deadline):
                raise
            last_error=exc
            sleep(min(.05,max(0,deadline-clock())))
