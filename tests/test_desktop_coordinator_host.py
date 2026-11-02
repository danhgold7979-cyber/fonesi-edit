"""Desktop coordinator transport: real Qt thread, actual SQLite ownership, no fake jobs."""
import os
import time
import uuid

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

from fonesi_edit.jobs.desktop_host import DesktopCoordinatorHost
from fonesi_edit.jobs.repository import JobRepository, JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.commands import QueueCommand
from fonesi_edit.jobs.view import read_queue
from fonesi_edit.storage.projects import ProjectStore
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import queue, wait_for


def _host_from(repo):
    return DesktopCoordinatorHost(repo.path, read_queue(repo.path).store_token)


def _settled(qt_app, host):
    wait_for(qt_app, lambda: not host.isRunning(), timeout=5)
    assert host.wait(0)
    qt_app.processEvents()


def test_existing_verified_store_opens_on_owner_thread_and_refuses_cross_thread_drain(queue, qt_app):
    repo, jobs = queue
    host = _host_from(repo)
    acquired = []
    errors = []
    host.acquired.connect(acquired.append)
    host.unavailable.connect(errors.append)
    host.start()
    try:
        wait_for(qt_app, lambda: bool(acquired) or bool(errors))
        assert not errors
        inbox = acquired[0]
        with pytest.raises(JobConflict, match='coordinator thread'):
            inbox.drain()
        row = read_queue(repo.path).rows[0]
        command = QueueCommand('pause', row.id, row.version, read_queue(repo.path).store_token)
        assert inbox.submit(command).result(timeout=4).state == 'paused'
        assert repo.get(row.id).state == 'paused'
        assert all(repo.get(job.id).state == 'pending' for job in jobs if job.id != row.id)
    finally:
        host.requestInterruption()
        _settled(qt_app, host)
        host.deleteLater()
    assert acquired[0].state()[1]


def test_missing_and_wrong_token_do_not_create_or_modify_store(tmp_path, queue, qt_app):
    absent = tmp_path / 'never' / 'jobs.sqlite3'
    missing = DesktopCoordinatorHost(absent, 'a' * 64)
    refused = []
    missing.unavailable.connect(refused.append)
    missing.start()
    _settled(qt_app, missing)
    assert refused and not absent.parent.exists()
    missing.deleteLater()

    repo, jobs = queue
    before = tuple(repo.get(j.id) for j in jobs)
    host = DesktopCoordinatorHost(repo.path, 'b' * 64)
    denied = []
    host.unavailable.connect(denied.append)
    host.start()
    _settled(qt_app, host)
    assert denied and tuple(repo.get(j.id) for j in jobs) == before
    assert repo.db.execute('SELECT count(*) FROM coordinator_epochs').fetchone()[0] == 0
    host.deleteLater()


def test_cooperating_owner_contention_keeps_store_unchanged(queue, qt_app):
    repo, jobs = queue
    before = tuple(repo.get(j.id) for j in jobs)
    with CoordinatorOwnership(repo):
        host = _host_from(repo)
        denied = []
        acquired = []
        host.unavailable.connect(denied.append)
        host.acquired.connect(acquired.append)
        host.start()
        _settled(qt_app, host)
        assert denied and not acquired
        assert tuple(repo.get(j.id) for j in jobs) == before
        host.deleteLater()


def test_ui_explicit_selected_command_uses_actual_host_no_standalone_owner(queue, tmp_path, qt_app):
    repo, jobs = queue
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window = MainWindow(store)
        window.show()
        window.navigation.setCurrentRow(6)
        page = window.queue_page
        try:
            wait_for(qt_app, lambda: not page.busy and page.store_token is not None)
            assert page.coordinator_button.isEnabled()
            page.coordinator_button.click()
            wait_for(qt_app, lambda: page.inbox is not None)
            assert window.coordinator_host is not None and window.coordinator_host.isRunning()
            assert page.coordinator_button.isEnabled() is False
            page.table.selectRow(0)
            selected = page._selected()
            page.action_buttons['pause'].click()
            wait_for(qt_app, lambda: repo.get(selected.id).state == 'paused' and not page.busy)
            assert not page.inbox.state()[1]
            assert repo.get(selected.id).version == selected.version + 1
            assert all(repo.get(job.id).state == 'pending' for job in jobs if job.id != selected.id)
        finally:
            window.close()
            wait_for(qt_app, lambda: not window.background_busy and not window.isVisible())
            assert window.coordinator_host is None
            window.deleteLater()
            qt_app.processEvents()


def test_ui_missing_store_does_not_start_owner_or_create_jobs_db(tmp_path, qt_app):
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window = MainWindow(store)
        window.show()
        window.navigation.setCurrentRow(6)
        wait_for(qt_app, lambda: not window.queue_page.busy)
        assert window.queue_page.coordinator_button.isEnabled() is False
        assert window.coordinator_host is None
        assert not (tmp_path/'jobs.sqlite3').exists()
        window.close()
        window.deleteLater()
        qt_app.processEvents()


def test_ui_contended_owner_reports_read_only_without_mutation(queue, tmp_path, qt_app):
    repo, jobs = queue
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window = MainWindow(store)
        window.show()
        window.navigation.setCurrentRow(6)
        page = window.queue_page
        try:
            wait_for(qt_app, lambda: not page.busy and page.store_token is not None)
            with CoordinatorOwnership(repo):
                page.coordinator_button.click()
                wait_for(qt_app, lambda: window.coordinator_host is None)
                assert page.inbox is None
                assert 'chỉ đọc' in page.command_notice.text().lower()
                page.table.selectRow(0)
                assert not page.action_buttons['pause'].isEnabled()
            assert all(repo.get(job.id) == job for job in jobs)
        finally:
            window.close()
            wait_for(qt_app, lambda: not window.background_busy and not window.isVisible())
            window.deleteLater()
            qt_app.processEvents()


def test_refusal_keeps_retry_disabled_until_exact_qthread_retirement(queue,tmp_path,qt_app,monkeypatch):
    from PySide6.QtCore import QThread,Signal
    import fonesi_edit.ui.shell as shell
    repo,jobs=queue

    class DelayedRefusal(QThread):
        acquired=Signal(object)
        unavailable=Signal(str)
        def __init__(self,path,expected_token,parent=None):
            super().__init__(parent)
        def run(self):
            self.unavailable.emit('Đang có bộ điều phối khác; chỉ đọc.')
            self.msleep(250)

    monkeypatch.setattr(shell,'DesktopCoordinatorHost',DelayedRefusal)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store)
        window.show()
        window.navigation.setCurrentRow(6)
        page=window.queue_page
        try:
            wait_for(qt_app,lambda:not page.busy and page.store_token is not None)
            page.coordinator_button.click()
            wait_for(qt_app,lambda:window._coordinator_error is not None)
            assert window.coordinator_host is not None and window.coordinator_host.isRunning()
            assert page._host_pending and not page.coordinator_button.isEnabled()
            wait_for(qt_app,lambda:window.coordinator_host is None)
            assert page.inbox is None and not page._host_pending
            assert 'chỉ đọc' in page.command_notice.text().lower()
            assert page.coordinator_button.isEnabled()
            assert all(repo.get(job.id)==job for job in jobs)
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()
