import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sqlite3
import time
from dataclasses import FrozenInstanceError,fields
import pytest
from PySide6.QtWidgets import QApplication
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.view import read_queue,QueueReadError
from fonesi_edit.storage.projects import ProjectStore
from fonesi_edit.ui.shell import MainWindow


@pytest.fixture
def queue(tmp_path,empty_plan):
    repo=JobRepository(tmp_path/'jobs.sqlite3')
    plan=CompositionPlan.parse(empty_plan)
    jobs=[repo.submit('secret-sentinel-'+str(i),plan,i) for i in range(3)]
    yield repo,jobs
    repo.close()


def test_actual_queue_rows_bounded_immutable_no_snapshot_or_request_key(queue):
    repo,jobs=queue
    result=read_queue(repo.path,limit=2)
    assert result.truncated and result.store_exists
    assert tuple(r.id for r in result.rows)==tuple(job.id for job in reversed(jobs[-2:]))
    assert all(r.state=='pending' for r in result.rows)
    assert 'secret-sentinel' not in repr(result) and 'snapshot_json' not in repr(result)
    assert {field.name for field in fields(result.rows[0])}=={
        'id','state','attempt','cancel_requested','unresolved_publication','version','snapshot_hash'}
    assert all(row.snapshot_hash==repo.get(row.id).snapshot_hash for row in result.rows)
    assert all(repo.get(row.id).snapshot_json not in repr(result) for row in result.rows)
    with pytest.raises(FrozenInstanceError):result.rows[0].state='succeeded'
    running=repo.claim(jobs[0]);result=read_queue(repo.path)
    assert next(r for r in result.rows if r.id==running.id).state=='running'
    assert repo.get(running.id)==running


def test_missing_store_does_not_create_directory_or_database(tmp_path):
    path=tmp_path/'missing'/'jobs.sqlite3'
    result=read_queue(path)
    assert not result.store_exists and result.rows==() and not path.parent.exists()


def test_foreign_database_and_bad_rows_refused_without_rewriting(tmp_path,queue):
    path=tmp_path/'foreign.db'
    with sqlite3.connect(path) as db:db.execute('CREATE TABLE secrets(value)')
    before=path.read_bytes()
    with pytest.raises(QueueReadError):read_queue(path)
    assert path.read_bytes()==before
    repo,jobs=queue;repo.db.execute("UPDATE jobs SET state='secret-sentinel-untrusted'")
    with pytest.raises(QueueReadError):read_queue(repo.path)


def test_cancel_never_mutates_jobs(queue):
    repo,jobs=queue
    with pytest.raises(QueueReadError):read_queue(repo.path,cancel=lambda:True)
    assert tuple(repo.get(j.id) for j in jobs)==tuple(jobs)


def wait_for(app,predicate,timeout=5):
    deadline=time.monotonic()+timeout
    while not predicate() and time.monotonic()<deadline:app.processEvents();time.sleep(.005)
    assert predicate()


def test_real_queue_page_async_refresh_and_truthful_empty_progress(queue,tmp_path,qt_app):
    app=qt_app
    repo,jobs=queue
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show();window.navigation.setCurrentRow(6)
        wait_for(app,lambda:not window.queue_page.busy)
        assert window.queue_page.table.rowCount()==3
        displayed=' '.join(window.queue_page.table.item(r,c).text() for r in range(3) for c in range(5))
        assert 'pending' in displayed and 'secret-sentinel' not in displayed
        assert 'Chưa có dữ liệu tiến độ' in displayed
        window.close();app.processEvents()


def test_close_requests_cooperative_read_stop_not_thread_termination(tmp_path,monkeypatch,qt_app):
    app=qt_app
    import fonesi_edit.ui.queue as ui
    entered=[];stopped=[]
    def wait_until_canceled(path,*,cancel):
        entered.append(True)
        deadline=time.monotonic()+5
        while not cancel() and time.monotonic()<deadline:time.sleep(.005)
        stopped.append(cancel());raise QueueReadError('canceled')
    monkeypatch.setattr(ui,'read_queue',wait_until_canceled)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show();window.navigation.setCurrentRow(6)
        wait_for(app,lambda:bool(entered))
        window.close()
        wait_for(app,lambda:not window.queue_page.busy)
        app.processEvents()
        assert stopped==[True] and not window.isVisible()


def test_failed_refresh_marks_previous_rows_stale(tmp_path,qt_app):
    app=qt_app
    from fonesi_edit.ui.queue import QueuePage
    from fonesi_edit.jobs.view import QueueRow,QueueSnapshot
    page=QueuePage(tmp_path/'missing.db')
    page.show_snapshot(QueueSnapshot((QueueRow('known-id','pending',0,False,False),),False,True))
    page.show_error('Read refused.')
    assert page.table.rowCount()==1 and 'không phải trạng thái mới nhất' in page.message.text()
    page.close()
