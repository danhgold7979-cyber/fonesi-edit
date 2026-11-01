from pathlib import Path
import sqlite3
import pytest
from fonesi_edit.storage.sqlite_open import open_versioned

class Connection:
    def __init__(self,error=None):self.error=error;self.closed=False
    def execute(self,sql):
        assert sql=='PRAGMA user_version'
        if self.error:raise self.error
        return self
    def fetchone(self):return (1,)
    def close(self):self.closed=True

def error(code):
    result=sqlite3.OperationalError('fixture I/O');result.sqlite_errorcode=code
    return result

def test_only_known_windows_error_reopens_and_closes_failed_connections():
    connections=[Connection(error(1546)),Connection(error(1546)),Connection()];pending=iter(connections)
    times=[0.0]
    result,version=open_versioned(Path('fixture'),windows=True,owned=lambda:True,connect=lambda *a,**k:next(pending),clock=lambda:times[0],sleep=lambda n:times.__setitem__(0,times[0]+n))
    assert result is connections[-1] and version==1
    assert all(c.closed for c in connections[:-1]) and not result.closed

@pytest.mark.parametrize('windows,code',[(False,1546),(True,10),(True,4618)])
def test_other_errors_never_retried(windows,code):
    connection=Connection(error(code));calls=[]
    def connect(*args,**kwargs):calls.append(1);return connection
    with pytest.raises(sqlite3.OperationalError):open_versioned(Path('fixture'),windows=windows,connect=connect)
    assert calls==[1] and connection.closed

def test_deadline_exhaustion_stays_failure_and_closes_every_connection():
    created=[];times=[0.0]
    def connect(*args,**kwargs):
        connection=Connection(error(1546));created.append(connection);return connection
    with pytest.raises(sqlite3.OperationalError):
        open_versioned(Path('fixture'),windows=True,owned=lambda:True,connect=connect,clock=lambda:times[0],sleep=lambda n:times.__setitem__(0,times[0]+n),recovery_seconds=.1)
    assert len(created)==2 and all(c.closed for c in created)


def test_no_ownership_never_retries_even_known_error():
    connection=Connection(error(1546));calls=[]
    def connect(*args,**kwargs):calls.append(1);return connection
    with pytest.raises(sqlite3.OperationalError):open_versioned(Path('fixture'),windows=True,owned=lambda:False,connect=connect)
    assert calls==[1] and connection.closed
