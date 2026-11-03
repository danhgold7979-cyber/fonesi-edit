import sqlite3
import sys
import threading
import time
from concurrent.futures import CancelledError
import pytest
from fonesi_edit.jobs.inbox import CoordinatorInbox
from fonesi_edit.jobs.commands import QueueCommand
from fonesi_edit.jobs.ownership import CoordinatorOwnership, CoordinatorLost
from fonesi_edit.jobs.repository import JobRepository, JobConflict
from fonesi_edit.jobs.process import run_owned, ProcessCanceled
from fonesi_edit.jobs.view import read_queue
from test_queue_view import queue, wait_for


def request(repo, job, action='cancel'):
    return QueueCommand(action, job.id, job.version, read_queue(repo.path).store_token)


def test_bounded_pending_cancel_stale_and_owner_thread(queue):
    repo,jobs=queue
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner,capacity=1) as inbox:
        future=inbox.submit(request(repo,jobs[0],'pause'))
        with pytest.raises(JobConflict,match='full'):inbox.submit(request(repo,jobs[1]))
        assert future.cancel() and inbox.drain()==0 and repo.get(jobs[0].id)==jobs[0]
        future=inbox.submit(request(repo,jobs[0],'pause'));assert inbox.drain()==1
        assert future.result().state=='paused'
        stale=inbox.submit(request(repo,jobs[0]));inbox.drain()
        with pytest.raises(JobConflict,match='refresh'):stale.result()
        errors=[]
        def wrong_thread():
            try:inbox.drain()
            except Exception as exc:errors.append(exc)
        worker=threading.Thread(target=wrong_thread);worker.start();worker.join()
        assert len(errors)==1 and isinstance(errors[0],JobConflict)
        pending=inbox.submit(request(repo,jobs[1]));inbox.close()
        with pytest.raises(JobConflict,match='stopped'):pending.result()
        with pytest.raises(JobConflict,match='retired'):inbox.submit(request(repo,jobs[2]))


def test_owner_loss_retires_all_requests(queue):
    repo,jobs=queue
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        futures=[inbox.submit(request(repo,j)) for j in jobs]
        repo.db.execute('UPDATE coordinator_epochs SET owner_uuid=? WHERE epoch=?',('lost',owner.epoch))
        with pytest.raises(CoordinatorLost):inbox.drain()
        for future in futures:
            with pytest.raises(JobConflict):future.result()
        assert all(repo.get(j.id)==j for j in jobs)


def test_unknown_commit_retires_without_replay(queue):
    repo,jobs=queue
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        future=inbox.submit(request(repo,jobs[0],'pause'));pending=inbox.submit(request(repo,jobs[1]))
        original=repo.db
        class Unknown:
            def __getattr__(self,name):return getattr(original,name)
            def execute(self,sql,*args):
                result=original.execute(sql,*args)
                if sql=='COMMIT':raise sqlite3.OperationalError('unknown commit')
                return result
        repo.db=Unknown()
        try:
            with pytest.raises(sqlite3.OperationalError):inbox.drain()
            with pytest.raises(sqlite3.OperationalError):future.result()
            with pytest.raises(JobConflict):pending.result()
            assert repo.get(jobs[0].id).state=='paused' and repo.get(jobs[1].id)==jobs[1]
        finally:repo.db=original


def test_real_owner_thread_receives_cancel_during_owned_child(queue,tmp_path):
    repo,jobs=queue;ready=threading.Event();finished=threading.Event();shared={};errors=[]
    marker=tmp_path/'descendant.txt'
    release=tmp_path/'release-descendant.txt'
    child=f'import pathlib,time;p=pathlib.Path({str(marker)!r});r=pathlib.Path({str(release)!r});p.write_text("ready");\nwhile not r.exists():time.sleep(.01)\np.write_text("SURVIVED")'
    parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(10)'
    def runner():
        own=None
        try:
            own=JobRepository(repo.path,existing_only=True)
            with CoordinatorOwnership(own) as owner, CoordinatorInbox(owner) as inbox:
                running=own.claim(own.get(jobs[0].id));shared.update(inbox=inbox,command=request(own,running));ready.set()
                def cancel():
                    inbox.drain()
                    return own.get(running.id).cancel_requested
                with pytest.raises(ProcessCanceled):run_owned([sys.executable,'-c',parent],cancel=cancel,timeout=8)
                current=own.get(running.id)
                assert current.state=='running' and current.cancel_requested
                own.worker_transition(current,current.lease_token,'canceled')
        except BaseException as exc:errors.append(exc);ready.set()
        finally:
            if own is not None:own.close()
            finished.set()
    thread=threading.Thread(target=runner);thread.start()
    try:
        assert ready.wait(5) and not errors
        deadline=time.monotonic()+5
        while not marker.exists() and time.monotonic()<deadline:time.sleep(.01)
        assert marker.exists()
        result=shared['inbox'].submit(shared['command']).result(timeout=5)
        assert result.state=='running' and result.cancel_requested
        assert finished.wait(5)
    finally:
        if 'inbox' in shared:shared['inbox'].close()
        thread.join(10)
    assert not thread.is_alive() and not errors
    # Release a surviving descendant only after the owned runner has
    # reported retirement. This handshake avoids a wall-clock race between
    # child startup and cancellation while still detecting any escaped child.
    release.write_text('release')
    deadline=time.monotonic()+2
    while marker.read_text()=='ready' and time.monotonic()<deadline:time.sleep(.01)
    assert marker.read_text()=='ready' and repo.get(jobs[0].id).state=='canceled'


def test_qt_commander_routes_without_second_lock(queue,qt_app):
    from fonesi_edit.ui.queue import QueueCommander
    repo,jobs=queue;observed=[];refused=[]
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        worker=QueueCommander(repo.path,request(repo,jobs[0],'pause'),inbox=inbox)
        worker.applied.connect(observed.append);worker.refused.connect(refused.append);worker.start()
        deadline=time.monotonic()+5
        while worker.isRunning() and time.monotonic()<deadline:
            inbox.drain();qt_app.processEvents();time.sleep(.005)
        assert worker.wait(1000);qt_app.processEvents()
        assert not refused and len(observed)==1 and observed[0].state=='paused'
        worker.deleteLater();qt_app.processEvents()


def test_qt_finished_timeout_error_is_not_infinite_wait(queue,qt_app):
    from concurrent.futures import Future
    from fonesi_edit.ui.queue import QueueCommander
    repo,jobs=queue;refused=[]
    class FailedInbox:
        def submit(self,command):
            future=Future();future.set_exception(TimeoutError('operation failed'));return future
    worker=QueueCommander(repo.path,request(repo,jobs[0]),inbox=FailedInbox())
    worker.refused.connect(refused.append);worker.start()
    assert worker.wait(1000);qt_app.processEvents()
    assert len(refused)==1 and repo.get(jobs[0].id)==jobs[0]
    worker.deleteLater();qt_app.processEvents()


def test_qt_interruption_cancels_only_pending_request(queue,qt_app):
    from fonesi_edit.ui.queue import QueueCommander
    repo,jobs=queue;submitted=threading.Event();shared={};refused=[]
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        class ObservedInbox:
            def submit(self,command):
                future=inbox.submit(command);shared['future']=future;submitted.set();return future
        worker=QueueCommander(repo.path,request(repo,jobs[0]),inbox=ObservedInbox())
        worker.refused.connect(refused.append);worker.start()
        assert submitted.wait(2);worker.requestInterruption();assert worker.wait(1000)
        qt_app.processEvents();assert len(refused)==1 and shared['future'].cancelled()
        assert inbox.drain()==0 and repo.get(jobs[0].id)==jobs[0]
        worker.deleteLater();qt_app.processEvents()


def test_close_linearizes_with_running_admission(queue,monkeypatch):
    repo,jobs=queue;started=threading.Event();closed=threading.Event()
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        future=inbox.submit(request(repo,jobs[0],'pause'))
        pending=inbox.submit(request(repo,jobs[1],'pause'))
        original=future.set_running_or_notify_cancel
        def closer():
            started.set();inbox.close();closed.set()
        thread=threading.Thread(target=closer)
        def admission():
            thread.start();assert started.wait(1)
            # close cannot pass a dequeued-but-not-admitted request.
            assert not closed.wait(.05)
            return original()
        monkeypatch.setattr(future,'set_running_or_notify_cancel',admission)
        try:assert inbox.drain(limit=1)==1
        finally:thread.join(2)
        assert closed.is_set() and future.result().state=='paused'
        with pytest.raises(JobConflict):pending.result()
        assert repo.get(jobs[1].id)==jobs[1]
    # Opposite ordering: close wins; no later drain may mutate the job.
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        future=inbox.submit(request(repo,jobs[2],'pause'));inbox.close()
        assert inbox.drain()==0
        with pytest.raises(JobConflict):future.result()
        assert repo.get(jobs[2].id)==jobs[2]
