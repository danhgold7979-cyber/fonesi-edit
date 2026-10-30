"""P09-06 Qt offscreen Matrix enqueue cancellation and immutable-commit messaging."""
import os
import time
from threading import Event

import pytest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow
from fonesi_edit.matrix import Angle, MatrixEnqueueCancelled
import fonesi_edit.ui.pages as pages_module

APP=QApplication.instance() or QApplication([])


def _wait(predicate,seconds=12):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        APP.processEvents()
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Matrix worker UI timed out")


def _open(tmp_path):
    window=MainWindow(tmp_path/"data")
    window.scheduler.paused=True
    page=window.matrix
    root=tmp_path/"source"
    page.folder.setText(str(root))
    scenes=[
        [Angle(i+1,j+1,str(root/f"C{i+1}"/f"G{j+1}.mp4"),f"{i}-{j}")
         for j in range(2)]
        for i in range(2)
    ]
    page.scenes=scenes
    page.model.replace(scenes,[[scene[0] for scene in scenes]])
    page.refresh_scene_list()
    page.output.setText(str(tmp_path/"out"))
    return window,page


def _close(window):
    window.force_close=True
    window.close()
    _wait(lambda:not window.tasks and not window.scheduler.active)
    APP.processEvents()


@pytest.mark.parametrize("action",["seed","cell","scene-order","filter","editor"])
def test_qt_matrix_edit_revokes_prepublication_enqueue_without_queue_navigation(
        tmp_path,monkeypatch,action):
    window,page=_open(tmp_path)
    started=Event();revoked=Event()
    def blocked(*args,**kwargs):
        cancel=kwargs["cancel"]
        started.set()
        while not cancel.is_set():
            time.sleep(.008)
        revoked.set()
        raise MatrixEnqueueCancelled("revoked before SQLite commit")
    monkeypatch.setattr(pages_module,"enqueue_rows",blocked)
    before=len(window.failures)
    try:
        page.enqueue()
        _wait(started.is_set)
        with pytest.raises(ValueError,match="đang chuẩn bị"):
            page.enqueue()
        if action=="seed":
            page.seed.setValue(13)
        elif action=="cell":
            assert page.model.setData(page.model.index(0,1),"G2")
        elif action=="scene-order":
            page.scene_list.setCurrentRow(0)
            assert page.move_scene(1)
        elif action=="filter":
            page.scene_filters_changed()
        else:
            window.editor.changed.emit()
        _wait(lambda:revoked.is_set() and not window.tasks)
        assert len(window.failures)==before
        assert not window.store.jobs()
        assert window.nav.currentWidget() is not window.queue
        assert "Đã hủy chuẩn bị" in window.status.text()
    finally:
        _close(window)


def test_qt_global_cancel_button_reaches_matrix_preflight_worker(tmp_path,monkeypatch):
    window,page=_open(tmp_path)
    started=Event();cancelled=Event()
    def blocked(*args,**kwargs):
        event=kwargs["cancel"]
        started.set()
        while not event.is_set():
            time.sleep(.008)
        cancelled.set()
        raise MatrixEnqueueCancelled("user canceled")
    monkeypatch.setattr(pages_module,"enqueue_rows",blocked)
    try:
        page.enqueue()
        _wait(started.is_set)
        window.cancel_preparation.click()
        _wait(lambda:cancelled.is_set() and not window.tasks)
        assert window.nav.currentWidget() is not window.queue
        assert not window.failures
        assert "Đã hủy chuẩn bị" in window.status.text()
    finally:
        _close(window)


def test_qt_late_option_edit_does_not_misreport_committed_jobs_as_cancelled(
        tmp_path,monkeypatch):
    window,page=_open(tmp_path)
    committed=Event()
    def completed(*args,**kwargs):
        assert not kwargs["cancel"].is_set()
        committed.set()
        return ["already-committed-job"]
    monkeypatch.setattr(pages_module,"enqueue_rows",completed)
    try:
        page.enqueue()
        # Worker has returned but its QueuedConnection callback remains
        # unprocessed on this Qt thread. An edit must not erase the commit.
        assert committed.wait(5)
        page.seed.setValue(99)
        _wait(lambda:not window.tasks and
              window.nav.currentWidget() is window.queue)
        assert "snapshot cũ" in window.status.text()
        assert "không hủy job" in window.status.text()
        assert not window.failures
    finally:
        _close(window)
