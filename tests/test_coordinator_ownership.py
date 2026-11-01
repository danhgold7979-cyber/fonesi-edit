import os,subprocess,sys,time,sqlite3
from pathlib import Path
from contextlib import contextmanager
import pytest
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership,CoordinatorError,CoordinatorBusy,CoordinatorLost,MARKER

@contextmanager
def _post_exit_owner(repo,child,*,clock=time.monotonic,sleep=time.sleep,wait_seconds=3):
    """Observe documented asynchronous OS unlock; never infer ownership from exit.

    Only this test's confirmed exited child qualifies. BUSY may be observed until
    the bounded admission deadline; SQLite/identity/epoch errors are not retried.
    https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex
    """
    assert child.poll() is not None, 'Owned child must be confirmed exited first'
    deadline=clock()+wait_seconds;last_busy=None
    while True:
        if last_busy is not None and clock()>=deadline:raise last_busy
        candidate=CoordinatorOwnership(repo)
        try:candidate.__enter__()
        except CoordinatorBusy as exc:
            candidate.close();last_busy=exc
            sleep(min(.01,max(0,deadline-clock())))
            continue
        break
    try:yield candidate
    finally:candidate.close()

@pytest.fixture
def repo(tmp_path):
    r=JobRepository(tmp_path/'jobs.db')
    yield r
    r.close()


def test_one_live_owner_and_monotonic_epoch(repo):
    with CoordinatorOwnership(repo) as first:
        assert first.guard()==1
        with pytest.raises(CoordinatorBusy):
            with CoordinatorOwnership(repo):pass
        assert first.guard()==1
        inode=first.path.stat().st_ino
    with pytest.raises(CoordinatorLost):first.guard()
    with CoordinatorOwnership(repo) as second:
        assert second.guard()==2 and second.path.stat().st_ino==inode
        assert second.owner_uuid!=first.owner_uuid
    assert second.path.read_bytes()==MARKER


@pytest.mark.parametrize('data',[b'',b'FOREIGN'])
def test_foreign_lock_never_written(repo,data):
    p=repo.path.with_name(repo.path.name+'.coordinator-lock');p.write_bytes(data)
    with pytest.raises(CoordinatorError):
        with CoordinatorOwnership(repo):pass
    assert p.read_bytes()==data
    assert repo.db.execute('SELECT COUNT(*) FROM coordinator_epochs').fetchone()[0]==0


def test_symlink_lock_refused(repo,tmp_path):
    foreign=tmp_path/'foreign';foreign.write_bytes(b'sentinel');lock=repo.path.with_name(repo.path.name+'.coordinator-lock')
    try:lock.symlink_to(foreign)
    except OSError:pytest.skip('Symlink creation unavailable')
    with pytest.raises(CoordinatorError):
        with CoordinatorOwnership(repo):pass
    assert foreign.read_bytes()==b'sentinel'


def test_unexpected_epoch_revokes_old_instance(repo):
    with CoordinatorOwnership(repo) as owner:
        repo.db.execute("INSERT INTO coordinator_epochs(owner_uuid) VALUES('out-of-band')")
        with pytest.raises(CoordinatorLost,match='epoch'):owner.guard()


def test_changed_lock_name_not_authority(repo):
    with CoordinatorOwnership(repo) as owner:
        try:owner.path.rename(owner.path.with_suffix('.old'))
        except PermissionError:
            assert os.name=='nt';return
        owner.path.write_bytes(MARKER)
        with pytest.raises(CoordinatorLost,match='identity'):owner.guard()


def test_owned_child_death_releases_os_lock_not_epoch(repo,tmp_path):
    marker=tmp_path/'ready'
    code=f'''from pathlib import Path
import time
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership
r=JobRepository({str(repo.path)!r})
with CoordinatorOwnership(r) as owner:
 Path({str(marker)!r}).write_text(str(owner.epoch))
 time.sleep(30)
'''
    child=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if child.poll() is not None:
                out,err=child.communicate();pytest.fail(f'Child exited: {out!r} {err!r}')
            if marker.exists() and marker.read_text()=='1':break
            time.sleep(.01)
        else:pytest.fail('Coordinator child did not acquire lock')
        with pytest.raises(CoordinatorBusy):
            with CoordinatorOwnership(repo):pass
        child.kill();child.wait(timeout=5)
        try:
            with _post_exit_owner(repo,child) as owner:assert owner.guard()==2
        except sqlite3.Error as exc:
            # Diagnostic only: no query/reopen/retry before collecting the failure.
            pytest.fail(f'Post-child-exit coordinator acquisition failed: '
                        f'sqlite={sqlite3.sqlite_version} '
                        f'code={getattr(exc,"sqlite_errorcode",None)} '
                        f'name={getattr(exc,"sqlite_errorname",None)} '
                        f'in_transaction={repo.db.in_transaction} child_exit={child.returncode}; {exc}')
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
        child.stdout.close();child.stderr.close()


def test_database_replaced_after_repository_open_cannot_gain_epoch(repo,tmp_path):
    import shutil
    original=tmp_path/'original.db'
    try:repo.path.rename(original)
    except PermissionError:
        assert os.name=='nt' # original database anchor prevents replacement
        assert repo.db.execute('SELECT COUNT(*) FROM coordinator_epochs').fetchone()[0]==0
        return
    shutil.copyfile(original,repo.path)
    assert repo.path.stat().st_ino!=original.stat().st_ino
    from fonesi_edit.jobs.repository import JobConflict
    with pytest.raises((CoordinatorError,JobConflict),match='identity'):
        with CoordinatorOwnership(repo):pass
    assert repo.db.execute('SELECT COUNT(*) FROM coordinator_epochs').fetchone()[0]==0


def test_epoch_loss_permanently_revokes_even_after_restoration(repo):
    with CoordinatorOwnership(repo) as owner:
        cursor=repo.db.execute("INSERT INTO coordinator_epochs(owner_uuid) VALUES('temporary-drift')")
        with pytest.raises(CoordinatorLost):owner.guard()
        repo.db.execute('DELETE FROM coordinator_epochs WHERE epoch=?',(cursor.lastrowid,))
        with pytest.raises(CoordinatorLost):owner.guard()
    with pytest.raises(CoordinatorLost,match='Revoked'):
        with owner:pass
    with CoordinatorOwnership(repo) as fresh:assert fresh.guard()>owner.epoch


class _ExitedChild:
    def poll(self):return 1


def test_post_exit_wait_requires_actual_lock_after_busy(repo,monkeypatch):
    factory=CoordinatorOwnership;attempts=[];now=[0.]
    class Busy:
        def __enter__(self):raise CoordinatorBusy('still retiring')
        def close(self):pass
    def delayed(value):
        attempts.append(value)
        return Busy() if len(attempts)<3 else factory(value)
    monkeypatch.setattr(sys.modules[__name__],'CoordinatorOwnership',delayed)
    def sleep(delay):now[0]+=delay
    with _post_exit_owner(repo,_ExitedChild(),clock=lambda:now[0],sleep=sleep) as owner:
        assert owner.guard()==1
    assert len(attempts)==3 and repo.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==1


def test_post_exit_busy_deadline_fails_without_epoch(repo,monkeypatch):
    now=[0.];attempts=[]
    class Busy:
        def __enter__(self):raise CoordinatorBusy('still locked')
        def close(self):pass
    def factory(value):attempts.append(value);return Busy()
    monkeypatch.setattr(sys.modules[__name__],'CoordinatorOwnership',factory)
    def sleep(delay):now[0]+=delay
    with pytest.raises(CoordinatorBusy):
        with _post_exit_owner(repo,_ExitedChild(),clock=lambda:now[0],sleep=sleep,wait_seconds=.02):pass
    assert len(attempts)==2 and repo.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==0


def test_post_exit_sqlite_error_is_not_retried(repo,monkeypatch):
    attempts=[]
    class Failed:
        def __enter__(self):
            attempts.append(1);raise sqlite3.OperationalError('not a busy lock')
    monkeypatch.setattr(sys.modules[__name__],'CoordinatorOwnership',lambda repo:Failed())
    with pytest.raises(sqlite3.OperationalError):
        with _post_exit_owner(repo,_ExitedChild()):pass
    assert len(attempts)==1


def test_post_exit_live_child_never_attempts_acquisition(repo,monkeypatch):
    class Live:
        def poll(self):return None
    monkeypatch.setattr(sys.modules[__name__],'CoordinatorOwnership',lambda repo:pytest.fail('Live child is not retirement proof'))
    with pytest.raises(AssertionError,match='confirmed exited'):
        with _post_exit_owner(repo,Live()):pass
