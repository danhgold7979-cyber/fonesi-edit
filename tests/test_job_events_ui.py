import pytest
from fonesi_edit.ui.queue import QueuePage
from fonesi_edit.jobs.event_store import event_path
from test_queue_view import queue,wait_for


def test_actual_selected_command_then_readonly_diagnostics(queue,qt_app):
    repo,jobs=queue;page=QueuePage(repo.path);page.show();page.refresh()
    wait_for(qt_app,lambda:not page.busy)
    page.table.selectRow(0);selected=page._selected();page.action_buttons['pause'].click()
    wait_for(qt_app,lambda:not page.busy)
    index=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==selected.id)
    page.table.selectRow(index);page.events_button.click();wait_for(qt_app,lambda:not page.busy)
    text=page.events_view.toPlainText()
    assert selected.id in text and 'Đã tạm dừng tác vụ chờ' in text and 'secret-sentinel' not in text
    assert repo.get(selected.id).state=='paused'
    page.table.clearSelection();assert not page.events_button.isEnabled() and page.events_view.toPlainText()==''
    page.request_stop();page.close();page.deleteLater();qt_app.processEvents()


def test_view_missing_logs_creates_no_event_store_and_close_waits(queue,qt_app):
    repo,jobs=queue;path=event_path(repo.path);page=QueuePage(repo.path);page.refresh()
    wait_for(qt_app,lambda:not page.busy);page.table.selectRow(0);page.events_button.click()
    page.request_stop();wait_for(qt_app,lambda:not page.busy)
    assert not path.exists() and all(repo.get(j.id)==j for j in jobs)
    page.close();page.deleteLater();qt_app.processEvents()


def test_logging_failure_warning_preserves_known_command_result(queue,qt_app):
    repo,jobs=queue;path=event_path(repo.path);path.write_bytes(b'FOREIGN')
    page=QueuePage(repo.path);page.refresh();wait_for(qt_app,lambda:not page.busy)
    page.table.selectRow(0);job=page._selected();page.action_buttons['pause'].click()
    wait_for(qt_app,lambda:not page.busy)
    assert repo.get(job.id).state=='paused' and 'không gửi lại lệnh' in page.command_notice.text()
    assert path.read_bytes()==b'FOREIGN'
    page.request_stop();page.close();page.deleteLater();qt_app.processEvents()


def test_actual_worker_error_shows_fixed_diagnostic_not_private_output(queue,qt_app):
    import sys
    import threading
    from fonesi_edit.jobs.repository import JobRepository
    from fonesi_edit.jobs.ownership import CoordinatorOwnership
    from fonesi_edit.jobs.process import run_owned
    from fonesi_edit.jobs.events import Event,EventCode,EventStage
    from fonesi_edit.jobs.diagnostics import record_job_event,DiagnosticStatus
    repo,jobs=queue;errors=[];done=threading.Event();page=QueuePage(repo.path);page.show()
    def worker():
        own=None
        try:
            own=JobRepository(repo.path,existing_only=True)
            with CoordinatorOwnership(own) as owner:
                job=own.claim(own.get(jobs[0].id))
                result=run_owned([sys.executable,'-c','import sys;sys.stderr.write("TOKEN_SECRET https://private/?key=SECRET");raise SystemExit(7)'])
                assert record_job_event(own,owner,job,Event(EventCode.PROCESS_EXIT,EventStage.DECODE,result.returncode),event_path(own.path)) is DiagnosticStatus.RECORDED
        except BaseException as exc:errors.append(exc)
        finally:
            if own is not None:own.close()
            done.set()
    thread=threading.Thread(target=worker);thread.start()
    try:
        wait_for(qt_app,done.is_set);thread.join();assert not errors
        page.refresh();wait_for(qt_app,lambda:not page.busy)
        index=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==jobs[0].id)
        page.table.selectRow(index);page.events_button.click();wait_for(qt_app,lambda:not page.busy)
        text=page.events_view.toPlainText()
        assert 'process_failure' in text and '(7)' in text and 'DECODE' in text
        assert 'SECRET' not in text and 'private' not in text
        assert repo.get(jobs[0].id).state=='running' # Log is not completion/retry authority.
    finally:
        page.request_stop();wait_for(qt_app,lambda:not page.busy);page.close();page.deleteLater();qt_app.processEvents();thread.join(5)
