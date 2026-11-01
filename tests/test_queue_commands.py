import sqlite3
import pytest
from fonesi_edit.jobs.commands import QueueCommand,apply_queue_command
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership,CoordinatorBusy
from fonesi_edit.jobs.view import read_queue
from fonesi_edit.domain.composition import CompositionPlan
from test_queue_view import queue,wait_for


def command(repo,job,action):return QueueCommand(action,job.id,job.version,read_queue(repo.path).store_token)


def test_selected_pending_pause_resume_cancel_and_stale_version(queue):
    repo,jobs=queue;original=jobs[0]
    pause=command(repo,original,'pause');result=apply_queue_command(repo.path,pause)
    assert result.state=='paused' and not hasattr(result,'snapshot_json')
    with pytest.raises(JobConflict):apply_queue_command(repo.path,pause)
    paused=repo.get(original.id)
    assert apply_queue_command(repo.path,command(repo,paused,'resume')).state=='pending'
    current=repo.get(original.id)
    assert apply_queue_command(repo.path,command(repo,current,'cancel')).state=='canceled'
    assert repo.get(jobs[1].id)==jobs[1] and repo.get(jobs[2].id)==jobs[2]


def test_running_cancel_is_request_not_process_stopped(queue):
    repo,jobs=queue;running=repo.claim(jobs[0])
    result=apply_queue_command(repo.path,command(repo,running,'cancel'))
    assert result.state=='running' and result.cancel_requested
    assert repo.get(running.id).lease_token==running.lease_token


def test_resume_does_not_release_configuration_or_publication_hold(queue):
    repo,jobs=queue;running=repo.claim(jobs[0]);blocked=repo.worker_transition(running,running.lease_token,'blocked_configuration')
    with pytest.raises(JobConflict):apply_queue_command(repo.path,command(repo,blocked,'resume'))
    assert repo.get(blocked.id)==blocked


def test_busy_coordinator_never_bypassed(queue):
    repo,jobs=queue;request=command(repo,jobs[0],'pause')
    with CoordinatorOwnership(repo):
        with pytest.raises(CoordinatorBusy):apply_queue_command(repo.path,request)
    assert repo.get(jobs[0].id)==jobs[0]


def test_existing_only_never_creates_missing_store_or_migrates_foreign(tmp_path):
    absent=tmp_path/'absent'/'jobs.db'
    with pytest.raises(OSError):JobRepository(absent,existing_only=True)
    assert not absent.parent.exists()
    foreign=tmp_path/'foreign.db'
    with sqlite3.connect(foreign) as db:db.execute('CREATE TABLE unrelated(x)')
    before=foreign.read_bytes()
    with pytest.raises(JobConflict):JobRepository(foreign,existing_only=True)
    assert foreign.read_bytes()==before and not list(tmp_path.glob('*.backup-*'))


def test_store_identity_token_blocks_same_job_in_other_owned_database(queue,tmp_path,empty_plan):
    repo,jobs=queue;request=command(repo,jobs[0],'pause')
    other=JobRepository(tmp_path/'other.db')
    try:
        copy=other.submit('copy',CompositionPlan.parse(empty_plan),0)
        other.db.execute('UPDATE jobs SET id=? WHERE id=?',(jobs[0].id,copy.id))
        with pytest.raises(JobConflict,match='store changed'):apply_queue_command(other.path,request)
        assert other.get(jobs[0].id).state=='pending'
        assert other.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0]==0
    finally:other.close()


def test_cancel_before_admission_does_not_change_job(queue):
    repo,jobs=queue;request=command(repo,jobs[0],'pause')
    with pytest.raises(JobConflict):apply_queue_command(repo.path,request,cancel=lambda:True)
    assert repo.get(jobs[0].id)==jobs[0]


def test_unknown_job_commit_outcome_not_replayed(queue,monkeypatch):
    import fonesi_edit.jobs.commands as module
    repo,jobs=queue;request=command(repo,jobs[0],'pause');real=module.JobRepository;commits=[]
    class AfterSecondCommit:
        def __init__(self,db):self.db=db
        def __getattr__(self,name):return getattr(self.db,name)
        def execute(self,sql,*args):
            result=self.db.execute(sql,*args)
            if sql=='COMMIT':
                commits.append(sql)
                if len(commits)==2:raise sqlite3.OperationalError('unknown outcome')
            return result
    def injected(*args,**kwargs):
        opened=real(*args,**kwargs);opened.db=AfterSecondCommit(opened.db);return opened
    monkeypatch.setattr(module,'JobRepository',injected)
    with pytest.raises(sqlite3.OperationalError):apply_queue_command(repo.path,request)
    current=repo.get(jobs[0].id)
    assert current.state=='paused' and current.version==jobs[0].version+1 and len(commits)==2


def test_actual_desktop_selected_pause_then_refresh(queue,tmp_path,qt_app):
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.storage.projects import ProjectStore
    from fonesi_edit.ui.shell import MainWindow
    app=qt_app;repo,jobs=queue
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show();window.navigation.setCurrentRow(6)
        wait_for(app,lambda:not window.queue_page.busy)
        window.queue_page.table.selectRow(0)
        selected=window.queue_page._selected()
        assert window.queue_page.action_buttons['pause'].isEnabled()
        window.queue_page.action_buttons['pause'].click()
        window.queue_page.table.selectRow(1) # late selection cannot retarget captured command
        wait_for(app,lambda:not window.queue_page.busy)
        assert repo.get(selected.id).state=='paused'
        assert 'paused' in [window.queue_page.table.item(r,1).text() for r in range(3)]
        window.close();app.processEvents()


def test_existing_only_refuses_known_old_schema_without_backup_or_receipt_change(tmp_path):
    from test_jobs_migration import legacy
    from fonesi_edit.storage.db_ownership import receipt_path
    path=tmp_path/'old.db';legacy(path)
    before=path.read_bytes();receipt=receipt_path(path).read_bytes()
    with pytest.raises(JobConflict,match='no migration'):JobRepository(path,existing_only=True)
    assert path.read_bytes()==before and receipt_path(path).read_bytes()==receipt
    assert not list(tmp_path.glob('*.backup-*'))


def test_visibly_deselected_row_cannot_start_command(queue,tmp_path,qt_app):
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.ui.queue import QueuePage
    app=qt_app;repo,jobs=queue
    page=QueuePage(repo.path);page.show_snapshot(read_queue(repo.path));page.table.selectRow(0)
    page.table.clearSelection()
    assert page._selected() is None and not page.action_buttons['pause'].isEnabled()
    page.command('pause')
    assert page.commander is None and tuple(repo.get(j.id) for j in jobs)==tuple(jobs)
    page.close()


def test_snapshot_refresh_does_not_retarget_old_row_selection(queue,qt_app):
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.ui.queue import QueuePage
    from fonesi_edit.jobs.view import QueueSnapshot
    app=qt_app;repo,jobs=queue
    page=QueuePage(repo.path);snapshot=read_queue(repo.path);page.show_snapshot(snapshot);page.table.selectRow(0)
    page.show_snapshot(QueueSnapshot(tuple(reversed(snapshot.rows)),False,True,snapshot.store_token))
    assert page._selected() is None and not page.action_buttons['pause'].isEnabled()
    page.close()


@pytest.mark.parametrize('busy',[False,True])
def test_command_notice_survives_actual_auto_refresh(queue,tmp_path,busy,qt_app):
    from contextlib import nullcontext
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.ui.queue import QueuePage
    app=qt_app;repo,jobs=queue
    if not busy:repo.claim(jobs[-1])
    page=QueuePage(repo.path);page.show_snapshot(read_queue(repo.path));page.table.selectRow(0)
    with CoordinatorOwnership(repo) if busy else nullcontext():
        page.command('pause' if busy else 'cancel')
        wait_for(app,lambda:not page.busy)
        assert ('không tự gửi lại' if busy else 'chưa xác nhận tiến trình đã dừng') in page.command_notice.text()
    if not busy:assert repo.get(jobs[-1].id).state=='running' and repo.get(jobs[-1].id).cancel_requested
    page.close()


def test_finished_signal_does_not_retire_thread_before_wait_succeeds(tmp_path,qt_app):
    from fonesi_edit.ui.queue import QueuePage
    page=QueuePage(tmp_path/'missing.db');events=[]
    class FinishingThread:
        def __init__(self):self.joined=False
        def wait(self,timeout):assert timeout==0;return self.joined
        def deleteLater(self):events.append('deleted')
    worker=FinishingThread();page.reader=worker
    page._finished()
    assert page.busy and events==[]
    worker.joined=True
    wait_for(qt_app,lambda:not page.busy)
    assert events==['deleted']
    page.close()


def test_real_qt_command_process_exits_cleanly(tmp_path,empty_plan):
    import json,os,subprocess,sys
    from pathlib import Path
    (tmp_path/'plan.json').write_text(json.dumps(empty_plan))
    script=r'''
import json,sys,time
from pathlib import Path
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.storage.projects import ProjectStore
from fonesi_edit.ui.shell import MainWindow
base=Path(sys.argv[1]);app=QApplication([])
repo=JobRepository(base/'jobs.sqlite3');store=ProjectStore(base/'projects.sqlite3')
plan=CompositionPlan.parse(json.loads((base/'plan.json').read_text()))
def settled(window):
 deadline=time.monotonic()+5
 while window.queue_page.busy and time.monotonic()<deadline:app.processEvents();time.sleep(.005)
 assert not window.queue_page.busy
for n in range(3):
 job=repo.submit('exit-'+str(n),plan,n)
 window=MainWindow(store);window.show();window.navigation.setCurrentRow(6);settled(window)
 window.queue_page.table.selectRow(0);window.queue_page.command('pause');settled(window)
 assert repo.get(job.id).state=='paused'
 window.close();settled(window);app.processEvents();window.deleteLater()
 QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
store.close();repo.close()
'''
    env=dict(os.environ);env['QT_QPA_PLATFORM']='offscreen';env['PYTHONFAULTHANDLER']='1'
    env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src')
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path)],env=env,capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr.decode(errors='replace')


def test_actual_gui_entrypoint_disposes_widgets_before_application(tmp_path):
    import os,subprocess,sys
    from pathlib import Path
    script=r'''
import sys
from PySide6.QtCore import QTimer
import fonesi_edit.ui.shell as shell
Original=shell.MainWindow
class AutoClose(Original):
 def __init__(self,store):
  super().__init__(store)
  QTimer.singleShot(0,lambda:self.navigation.setCurrentRow(6))
  QTimer.singleShot(1,self.close)
shell.MainWindow=AutoClose
from fonesi_edit.__main__ import main
raise SystemExit(main(['--data-dir',sys.argv[1]]))
'''
    env=dict(os.environ);env['QT_QPA_PLATFORM']='offscreen';env['PYTHONFAULTHANDLER']='1'
    env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src')
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path/'user')],env=env,capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr.decode(errors='replace')
    assert not (tmp_path/'user'/'jobs.sqlite3').exists()
