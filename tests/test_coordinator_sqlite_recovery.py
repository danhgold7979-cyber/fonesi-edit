import sqlite3
import pytest
import fonesi_edit.jobs.repository as module
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership


def error(code):
    exc=sqlite3.OperationalError('controlled I/O failure');exc.sqlite_errorcode=code
    return exc


class ConnectionFault:
    def __init__(self,connection,code=1546,statement='SELECT epoch'):
        self.connection=connection;self.code=code;self.statement=statement;self.closed=False;self.failures=0
    def __getattr__(self,name):return getattr(self.connection,name)
    def execute(self,sql,*args):
        if sql.startswith(self.statement):
            self.failures+=1;raise error(self.code)
        return self.connection.execute(sql,*args)
    def close(self):self.closed=True;self.connection.close()


@pytest.fixture
def repo(tmp_path):
    value=JobRepository(tmp_path/'jobs.db')
    yield value
    value.close()


def test_successful_read_keeps_existing_connection(repo,monkeypatch):
    original=repo.db
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('Healthy connection reopened'))
    repo._prepare_coordinator_connection(windows=True)
    assert repo.db is original


def test_exact_windows_owned_read_fault_reopens_before_any_epoch_mutation(repo):
    failed=ConnectionFault(repo.db);repo.db=failed
    repo._prepare_coordinator_connection(windows=True)
    assert failed.closed and failed.failures==1 and repo.db is not failed
    assert repo.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==0
    assert repo.db.execute('PRAGMA foreign_keys').fetchone()[0]==1
    assert repo.db.execute('PRAGMA synchronous').fetchone()[0]==2
    assert repo.db.execute('PRAGMA busy_timeout').fetchone()[0]==5000
    with CoordinatorOwnership(repo) as owner:assert owner.epoch==1


@pytest.mark.parametrize('windows,code,owned',[(False,1546,True),(True,10,True),(True,1546,False)])
def test_nonmatching_fault_never_closes_or_reopens(repo,monkeypatch,windows,code,owned):
    failed=ConnectionFault(repo.db,code);repo.db=failed
    if not owned:monkeypatch.setattr(module,'owns_database',lambda *a:False)
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('Disallowed reopen'))
    with pytest.raises(sqlite3.OperationalError) as caught:repo._prepare_coordinator_connection(windows=windows)
    assert caught.value.sqlite_errorcode==code and not failed.closed and failed.failures==1


def test_active_transaction_not_read_or_replayed(repo,monkeypatch):
    repo.db.execute('BEGIN IMMEDIATE')
    failed=ConnectionFault(repo.db);repo.db=failed
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('Active connection reopened'))
    with pytest.raises(JobConflict,match='idle'):repo._prepare_coordinator_connection(windows=True)
    assert failed.failures==0 and not failed.closed and repo.db.in_transaction
    repo.db.execute('ROLLBACK')


def test_startup_reopen_failure_propagates_without_epoch_insert(repo,monkeypatch):
    failed=ConnectionFault(repo.db);repo.db=failed
    def exhausted(*a,**k):raise error(1546)
    monkeypatch.setattr(module,'open_versioned',exhausted)
    with pytest.raises(sqlite3.OperationalError):repo._prepare_coordinator_connection(windows=True)
    assert failed.closed and repo.db is None
    with sqlite3.connect(repo.path) as check:assert check.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==0


def test_wrong_reopened_schema_closed_without_configuration_writes(repo,monkeypatch):
    failed=ConnectionFault(repo.db);repo.db=failed
    foreign=sqlite3.connect(':memory:',isolation_level=None);statements=[]
    foreign.set_trace_callback(statements.append)
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:(foreign,2))
    with pytest.raises(JobConflict,match='identity/schema'):repo._prepare_coordinator_connection(windows=True)
    assert statements==['PRAGMA application_id'] and repo.db is None
    with pytest.raises(sqlite3.ProgrammingError):foreign.execute('SELECT 1')


def test_begin_error_is_never_retried_or_reopened(repo,monkeypatch):
    failed=ConnectionFault(repo.db,statement='BEGIN IMMEDIATE');repo.db=failed
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('BEGIN replay/reopen forbidden'))
    with pytest.raises(sqlite3.OperationalError):
        with CoordinatorOwnership(repo):pass
    assert failed.failures==1 and not failed.closed
    assert repo.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==0
