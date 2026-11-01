import uuid
import pytest
from fonesi_edit.jobs.observations import LatestProgress
from fonesi_edit.jobs.progress import JobProgress, Progress
from test_queue_view import queue


def event(job_id=None, *, attempt=1, frame=10):
    return JobProgress(job_id or str(uuid.uuid4()),'b'*64,attempt,Progress(frame,1000,100,False))


def test_latest_only_bound_drain_close_and_numeric_allowlist():
    buffer=LatestProgress('a'*64,capacity=2);first=event();second=event();third=event()
    for i in range(1000):buffer.put(event(first.job_id,frame=i))
    buffer.put(second);batch=buffer.drain()
    assert batch.store_token=='a'*64 and len(batch.events)==2 and batch.events[0].observation.frame==999
    assert buffer.drain().events==()
    buffer.put(first);buffer.put(second);buffer.put(third)
    assert tuple(e.job_id for e in buffer.drain().events)==(second.job_id,third.job_id)
    with pytest.raises(ValueError):buffer.put(event(frame='secret-path'))
    with pytest.raises(ValueError):buffer.put(event(frame=2**64))
    buffer.put(first);buffer.close();buffer.put(second);assert buffer.drain().events==()


def test_older_attempt_cannot_displace_newer_buffer_event():
    buffer=LatestProgress('a'*64);new=event(attempt=2)
    buffer.put(new);buffer.put(event(new.job_id,attempt=1))
    assert buffer.drain().events==(new,)


def test_ui_filters_store_snapshot_attempt_and_final_rows(queue,qt_app):
    from dataclasses import replace
    from fonesi_edit.jobs.ownership import CoordinatorOwnership
    from fonesi_edit.jobs.inbox import CoordinatorInbox
    from fonesi_edit.jobs.view import read_queue
    from fonesi_edit.ui.queue import QueuePage
    repo,jobs=queue;running=repo.claim(jobs[0])
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        page=QueuePage(repo.path,inbox=inbox);snapshot=read_queue(repo.path);page.show_snapshot(snapshot)
        row=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==running.id)
        valid=JobProgress(running.id,running.snapshot_hash,running.attempt,Progress(42,123,200,True))
        original=page.table.item(row,4).text()
        for bad in (replace(valid,attempt=running.attempt+1),replace(valid,snapshot_hash='c'*64)):
            inbox.progress.put(bad);page.poll_progress();assert page.table.item(row,4).text()==original
        page.store_token='d'*64;inbox.progress.put(valid);page.poll_progress();assert page.table.item(row,4).text()==original
        page.show_snapshot(snapshot);inbox.progress.put(valid);page.poll_progress()
        assert '42' in page.table.item(row,4).text() and 'chờ xác nhận' in page.table.item(row,4).text()
        assert repo.get(running.id).state=='running'
        canceled=repo.request_cancel(repo.get(running.id));repo.worker_transition(canceled,canceled.lease_token,'canceled')
        page.show_snapshot(read_queue(repo.path));inbox.progress.put(valid);page.poll_progress()
        assert '42' not in page.table.item(row,4).text()
        page.request_stop();assert not page.progress_timer.isActive();page.close();page.deleteLater();qt_app.processEvents()


def test_real_runner_progress_and_selected_ui_cancel(queue,qt_app):
    import sys
    import threading
    from fonesi_edit.jobs.repository import JobRepository
    from fonesi_edit.jobs.ownership import CoordinatorOwnership
    from fonesi_edit.jobs.inbox import CoordinatorInbox
    from fonesi_edit.jobs.progress import FFmpegProgress
    from fonesi_edit.jobs.process import run_owned,ProcessCanceled
    from fonesi_edit.ui.queue import QueuePage
    from test_queue_view import wait_for
    repo,jobs=queue;ready=threading.Event();shared={};errors=[]
    def runner():
        own=None
        try:
            own=JobRepository(repo.path,existing_only=True)
            with CoordinatorOwnership(own) as owner, CoordinatorInbox(owner) as inbox:
                job=own.claim(own.get(jobs[0].id));shared['inbox']=inbox;ready.set()
                progress=FFmpegProgress(inbox.progress_observer(job))
                def cancel():
                    inbox.drain();return own.get(job.id).cancel_requested
                # Real owned Python producer; tests transport, NOT FFmpeg encoding.
                script='import time;print("frame=42\\nout_time_us=500000\\ntotal_size=100\\nprogress=end",flush=True);time.sleep(10)'
                with pytest.raises(ProcessCanceled):run_owned([sys.executable,'-c',script],cancel=cancel,on_stdout=progress.feed,timeout=8)
                current=own.get(job.id);own.worker_transition(current,current.lease_token,'canceled')
        except BaseException as exc:errors.append(exc);ready.set()
        finally:
            if own is not None:own.close()
    thread=threading.Thread(target=runner);thread.start();page=None
    try:
        assert ready.wait(5) and not errors
        page=QueuePage(repo.path,inbox=shared['inbox']);page.show();page.refresh()
        wait_for(qt_app,lambda:not page.busy)
        row=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==jobs[0].id)
        wait_for(qt_app,lambda:'42' in page.table.item(row,4).text())
        assert repo.get(jobs[0].id).state=='running'
        page.table.selectRow(row);page.action_buttons['cancel'].click()
        wait_for(qt_app,lambda:not page.busy and repo.get(jobs[0].id).state=='canceled')
        thread.join(3);assert not thread.is_alive() and not errors
    finally:
        if page is not None:
            page.request_stop();wait_for(qt_app,lambda:not page.busy);page.close();page.deleteLater();qt_app.processEvents()
        if 'inbox' in shared:shared['inbox'].close()
        thread.join(10)


def test_progress_waits_for_initial_successful_snapshot(queue,qt_app):
    from fonesi_edit.jobs.ownership import CoordinatorOwnership
    from fonesi_edit.jobs.inbox import CoordinatorInbox
    from fonesi_edit.jobs.view import read_queue
    from fonesi_edit.ui.queue import QueuePage
    repo,jobs=queue;job=repo.claim(jobs[0])
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        page=QueuePage(repo.path,inbox=inbox)
        inbox.progress_observer(job)(Progress(17,None,None,False))
        page.poll_progress() # Timer before initial async snapshot must not lose it.
        page.show_snapshot(read_queue(repo.path));page.poll_progress()
        row=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==job.id)
        assert '17' in page.table.item(row,4).text()
        page.show_error('read failed');inbox.progress_observer(job)(Progress(18,None,None,False));page.poll_progress()
        assert '18' not in page.table.item(row,4).text()
        page.request_stop();page.close();page.deleteLater();qt_app.processEvents()
