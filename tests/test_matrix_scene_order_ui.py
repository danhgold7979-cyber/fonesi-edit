"""Qt scene order controls and stale worker safety (offscreen, no live accounts)."""
import os
import time
from threading import Event

import pytest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow
from fonesi_edit.matrix import Angle, combination, scene_directories
import fonesi_edit.ui.pages as pages_module

APP=QApplication.instance() or QApplication([])


def wait_until(condition, seconds=12):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        APP.processEvents()
        if condition():
            return
        time.sleep(.02)
    raise AssertionError("Timed out waiting for Matrix UI")


def close(window):
    window.force_close=True
    window.close()
    wait_until(lambda:not window.tasks and not window.scheduler.active)
    APP.processEvents()


def synthetic_scenes(root):
    return [
        [Angle(1,j+1,str(root/"C1"/f"{j}.mp4"),f"one-{j}") for j in range(2)],
        [Angle(2,j+1,str(root/"C2"/f"{j}.mp4"),f"two-{j}") for j in range(2)],
        [Angle(3,j+1,str(root/"C3"/f"{j}.mp4"),f"three-{j}") for j in range(2)],
    ]


def setup_page(window, root):
    page=window.matrix
    page.folder.setText(str(root))
    groups=synthetic_scenes(root)
    page.scenes=groups
    page.model.replace(groups,[[group[0] for group in groups]])
    page.refresh_scene_list()
    return page,groups


def test_qt_move_buttons_keep_source_locks_vectors_formula_and_persist(tmp_path,monkeypatch):
    root=tmp_path/"sources"
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    try:
        page,original=setup_page(window,root)
        page.model.locked.add((0,1))
        page.scene_weights.setText("1,2,3")
        page.scene_durations.setText("0.5,1,1.5")
        first=scene_directories(original)
        before=[group[0].path for group in original]
        page.scene_list.setCurrentRow(0)
        assert page.move_scene(1)
        assert scene_directories(page.scenes)==[first[1],first[0],first[2]]
        assert [angle.path for angle in page.model.rows[0]]==[before[1],before[0],before[2]]
        assert page.model.locked=={(0,2)}
        assert page.scene_weights.text()=="2,1,3"
        assert page.scene_durations.text()=="1,0.5,1.5"
        assert page.model.data(page.model.index(0,4))=="C1G1+C2G1+C3G1"
        assert page.scene_list.item(0).text().startswith("C1 ← C2")
        assert page.scene_list.currentItem().data(Qt.ItemDataRole.UserRole)==first[0]
        assert page.host.store.setting(page.scene_order_key())==[first[1],first[0],first[2]]
        assert 'Đã đổi thứ tự cảnh' in page.summary.text()
        assert page.move_scene(-1)
        assert [angle.path for angle in page.model.rows[0]]==before
        assert page.model.locked=={(0,1)}
        assert page.scene_weights.text()=="1,2,3"

        # Next scan restores only a matching saved folder set and regenerates
        # new matrix rows, while source files themselves are not renamed.
        with monkeypatch.context() as patch:
            patch.setattr(pages_module,'scan_scenes',lambda _folder:original)
            page.count.setValue(2)
            page.generate()
            wait_until(lambda:not window.tasks)
        assert scene_directories(page.scenes)==first
        assert len(page.model.rows)==2
        assert not window.failures,window.failures
    finally:
        close(window)


def test_qt_drag_handler_reorders_scene_list_and_remaps_lock(tmp_path):
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    try:
        page,original=setup_page(window,tmp_path/"media")
        page.model.locked.add((0,3))
        # Simulate the model's post-drop order and run the same callback
        # connected to QListWidget.model().rowsMoved for a real drag.
        moving=page.scene_list.takeItem(2)
        page.scene_list.insertItem(0,moving)
        page.scene_list.setCurrentItem(moving)
        page.scene_list_reordered()
        assert [angle.hash for angle in page.model.rows[0]]==[
            "three-0","one-0","two-0"
        ]
        assert page.model.locked=={(0,1)}
        assert page.scene_list.item(0).text().startswith("C1 ← C3")
        assert page.host.store.setting(page.scene_order_key())==scene_directories(page.scenes)
    finally:
        close(window)


def test_qt_invalid_scene_vector_refuses_move_without_partial_change(tmp_path):
    window=MainWindow(tmp_path/"state")
    try:
        page,original=setup_page(window,tmp_path/"source")
        original_rows=[combination(row) for row in page.model.rows]
        page.scene_weights.setText("1,not-a-number,3")
        page.scene_list.setCurrentRow(0)
        with pytest.raises(ValueError,match="không hợp lệ"):
            page.move_scene(1)
        assert scene_directories(page.scenes)==scene_directories(original)
        assert [combination(row) for row in page.model.rows]==original_rows
        assert window.store.setting(page.scene_order_key()) is None
        page.scene_weights.clear()
        page.scene_durations.setText("1,2")
        with pytest.raises(ValueError,match="mỗi cảnh"):
            page.move_scene(1)
        assert not page.model.locked
        assert scene_directories(page.scenes)==scene_directories(original)
    finally:
        close(window)


def test_qt_scene_move_invalidates_old_async_matrix_generation(tmp_path,monkeypatch):
    started,finish=Event(),Event()
    root=tmp_path/"root"
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    try:
        page,original=setup_page(window,root)
        page.count.setValue(2)
        def delayed(_folder):
            started.set()
            assert finish.wait(8)
            return original
        monkeypatch.setattr(pages_module,"scan_scenes",delayed)
        page.generate()
        wait_until(started.is_set)
        page.scene_list.setCurrentRow(0)
        page.move_scene(1)
        moved=scene_directories(page.scenes)
        assert moved[0].endswith("C2")
        finish.set()
        wait_until(lambda:not window.tasks)
        APP.processEvents()
        assert scene_directories(page.scenes)==moved
        assert len(page.model.rows)==1  # The obsolete 2-row result was discarded.
        assert 'Đã bỏ ma trận sinh nền' in window.status.text()
        assert not window.failures,window.failures
    finally:
        finish.set()
        close(window)


def test_qt_source_root_change_clears_old_matrix_but_not_history(tmp_path):
    window=MainWindow(tmp_path/"state")
    try:
        page,_=setup_page(window,tmp_path/"old")
        page.model.locked.add((0,1))
        assert page.model.rows
        page.folder.setText(str(tmp_path/"new"))
        assert not page.model.rows and not page.scenes
        assert not page.model.locked
        assert page.scene_list.count()==0
        assert 'quét/sinh lại' in page.summary.text()
    finally:
        close(window)


def test_qt_corrupted_persisted_scene_order_is_ignored_without_loss(tmp_path,monkeypatch):
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    try:
        root=tmp_path/"source"
        page,original=setup_page(window,root)
        page.count.setValue(1)
        # A legacy or damaged preference is untrusted; do not crash on
        # an unhashable JSON object or treat it as a valid permutation.
        page.host.store.set_setting(page.scene_order_key(),[{},[],None])
        monkeypatch.setattr(pages_module,"scan_scenes",lambda _folder:original)
        page.generate()
        wait_until(lambda:not window.tasks)
        assert scene_directories(page.scenes)==scene_directories(original)
        assert len(page.model.rows)==1
        assert not window.failures,window.failures
    finally:
        close(window)


def test_qt_second_generate_supersedes_identical_inflight_request(tmp_path,monkeypatch):
    root=tmp_path/"source"
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    old_started,release=Event(),Event()
    try:
        page,original=setup_page(window,root)
        page.count.setValue(1)
        first=[True]
        def slow_scan(_root):
            if first[0]:
                first[0]=False
                old_started.set()
                assert release.wait(8)
            return original
        monkeypatch.setattr(pages_module,"scan_scenes",slow_scan)
        page.generate()
        wait_until(old_started.is_set)
        page.generate()  # Same options, but a newer request wins.
        wait_until(lambda:len(page.model.rows)==1 and
                   page._matrix_revision>=3 and
                   "tối đa lý thuyết" in page.summary.text())
        expected=scene_directories(page.scenes)
        release.set()
        wait_until(lambda:not window.tasks)
        assert scene_directories(page.scenes)==expected
        assert "Đã bỏ ma trận sinh nền" in window.status.text()
        assert not window.failures,window.failures
    finally:
        release.set()
        close(window)
