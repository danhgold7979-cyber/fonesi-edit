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


def test_qt_scene_move_keeps_selected_matrix_row_and_settings_invalidate_preview(tmp_path):
    window=MainWindow(tmp_path/"state")
    try:
        page,groups=setup_page(window,tmp_path/"source")
        page.model.replace(groups,[
            [scene[0] for scene in groups],
            [scene[1] for scene in groups],
        ])
        page.table.selectRow(1)
        selected_before=page.table.currentIndex().row()
        before=page._matrix_revision
        page.scene_list.setCurrentRow(0)
        page.move_scene(1)
        assert page.table.currentIndex().row()==selected_before==1
        assert [a.hash for a in page.model.rows[1]]==[
            "two-1","one-1","three-1"
        ]
        assert page._matrix_revision>before
        before=page._matrix_revision
        page.scene_weights.setText("2,1,3")
        assert page._matrix_revision>before
        before=page._matrix_revision
        page.minimum.setValue(.75)
        assert page._matrix_revision>before
    finally:
        close(window)


def test_qt_explicit_scene_angle_filter_and_pin_are_applied_to_new_rows(tmp_path,monkeypatch):
    from fonesi_edit.matrix import scene_directories
    root=tmp_path/"source"
    full=synthetic_scenes(root)
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _root:full)
    window=MainWindow(tmp_path/"state")
    window.scheduler.paused=True
    try:
        page=window.matrix
        page.folder.setText(str(root))
        page.count.setValue(1)
        page.scan_scene_choices()
        wait_until(lambda:not window.tasks)
        assert page.scene_filter.topLevelItemCount()==3
        excluded=page.scene_filter.topLevelItem(1)
        excluded.setCheckState(0,Qt.CheckState.Unchecked)
        filtered=page.scene_filter.topLevelItem(0)
        filtered.child(0).setCheckState(0,Qt.CheckState.Unchecked)
        pin=page.scene_filter.topLevelItem(2).child(1)
        page.scene_filter.setCurrentItem(pin)
        page.pin_selected_angle()
        assert 'Khóa toàn cảnh' in pin.text(1)
        page.generate()
        wait_until(lambda:not window.tasks)
        assert len(page.scenes)==2
        assert [a.hash for a in page.model.rows[0]]==["one-1","three-1"]
        assert [a.scene for a in page.model.rows[0]]==[1,2]
        assert page._pinned_columns=={2}
        assert page.model.locked=={(0,2)}
        assert scene_directories(page.scenes)==[
            str((root/"C1").resolve()),str((root/"C3").resolve())]
        page.table.selectRow(0)
        page.table.setCurrentIndex(page.model.index(0,2))
        page.lock()
        assert (0,2) in page.model.locked
        assert not page.model.setData(page.model.index(0,2),"G1")
        stored=window.store.setting(page.scene_filter_key())
        assert stored["version"]==1 and len(stored["manifest"])==3
        assert stored["choices"][str((root/"C3").resolve())]["pin"]=="three-1"
        assert not stored["choices"][str((root/"C2").resolve())]["enabled"]
        with pytest.raises(ValueError,match="đủ mọi cảnh"):
            page.rename_preview()
    finally:
        close(window)


def test_qt_selection_persistence_restored_only_for_exact_matching_corpus(tmp_path,monkeypatch):
    from fonesi_edit.matrix import scene_manifest
    root=tmp_path/"sources"
    original=synthetic_scenes(root)
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _folder:original)
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        page.scene_filter.topLevelItem(1).setCheckState(0,Qt.CheckState.Unchecked)
        page.scene_filter.topLevelItem(0).child(0).setCheckState(0,Qt.CheckState.Unchecked)
        page.generate();wait_until(lambda:not window.tasks)
        saved=window.store.setting(page.scene_filter_key())
        assert saved["manifest"]==scene_manifest(original)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        assert page.scene_filter.topLevelItem(1).checkState(0)==Qt.CheckState.Unchecked
        assert page.scene_filter.topLevelItem(0).child(0).checkState(0)==Qt.CheckState.Unchecked
        # An edited source asset invalidates the entire persisted selection;
        # the UI must not silently apply an old angle hash to a new file.
        changed=synthetic_scenes(root)
        changed[0][0]=Angle(1,1,str(root/"C1"/"0.mp4"),"changed-hash")
        monkeypatch.setattr(pages_module,"scan_scenes",lambda _folder:changed)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        assert all(page.scene_filter.topLevelItem(i).checkState(0)==Qt.CheckState.Checked
                   for i in range(3))
        assert page.scene_filter.topLevelItem(0).child(0).checkState(0)==Qt.CheckState.Checked
        assert 'không áp dụng lựa chọn cũ' in window.status.text()
    finally:
        close(window)


def test_qt_global_pin_with_nonzero_w_blocks_new_generation(tmp_path,monkeypatch):
    root=tmp_path/"source"
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _folder:synthetic_scenes(root))
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix
        page.folder.setText(str(root));page.count.setValue(2)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        angle=page.scene_filter.topLevelItem(0).child(0)
        page.scene_filter.setCurrentItem(angle)
        page.pin_selected_angle()
        page.window.setValue(1)
        page.generate()
        wait_until(lambda:not window.tasks)
        assert any('xung đột với W>0' in failure for failure in window.failures)
        assert not page.model.rows
        assert not [job for job in window.store.jobs() if job["kind"]=="render"]
    finally:
        close(window)


def test_qt_changing_scene_filter_revokes_old_plan_without_touching_queued_job(tmp_path,monkeypatch):
    root=tmp_path/"root"
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _root:synthetic_scenes(root))
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        page.generate();wait_until(lambda:not window.tasks)
        assert len(page.model.rows)==1
        queued=window.store.submit('render',{
            'composition':window.editor.composition.to_dict(),
            'output':str(tmp_path/"future.mp4")})
        snapshot=window.store.job(queued)["payload"]
        page.scene_filter.topLevelItem(1).setCheckState(0,Qt.CheckState.Unchecked)
        assert not page.model.rows and not page.scenes
        assert not page.model.locked
        assert page.scene_list.count()==0
        assert window.store.job(queued)["payload"]==snapshot
        assert not window.store.job(queued)["cancel_requested"]
    finally:
        close(window)


def test_qt_stale_selection_scan_is_discarded_after_source_change(tmp_path,monkeypatch):
    source=tmp_path/"first"
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    started,finish=Event(),Event()
    try:
        page=window.matrix;page.folder.setText(str(source))
        def slow_scan(_folder):
            started.set()
            assert finish.wait(8)
            return synthetic_scenes(source)
        monkeypatch.setattr(pages_module,"scan_scenes",slow_scan)
        page.scan_scene_choices()
        wait_until(started.is_set)
        page.folder.setText(str(tmp_path/"other"))
        finish.set()
        wait_until(lambda:not window.tasks)
        assert page.scene_filter.topLevelItemCount()==0
        assert page._available_scenes==[]
        assert not page.model.rows
        assert 'Bỏ kết quả quét cảnh cũ' in window.status.text()
    finally:
        finish.set()
        close(window)


def test_qt_scene_pin_moves_with_reordered_scene_and_remains_uneditable(tmp_path,monkeypatch):
    root=tmp_path/"source"
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _root:synthetic_scenes(root))
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        pinned=page.scene_filter.topLevelItem(1).child(1)
        page.scene_filter.setCurrentItem(pinned)
        page.pin_selected_angle()
        page.generate();wait_until(lambda:not window.tasks)
        assert page._pinned_columns=={2} and page.model.locked=={(0,2)}
        assert page.model.rows[0][1].hash=="two-1"
        page.scene_list.setCurrentRow(1)
        assert page.move_scene(-1)
        assert page._pinned_columns=={1} and page.model.locked=={(0,1)}
        assert page.model.rows[0][0].hash=="two-1"
        assert page.model.rows[0][0].scene==1
        assert not page.model.setData(page.model.index(0,1),"G1")
        page.table.setCurrentIndex(page.model.index(0,1))
        page.lock()
        assert page.model.locked=={(0,1)}
        page.scene_filter.setCurrentItem(pinned)
        page.unpin_selected_scene()
        assert not page.model.rows and not page._pinned_columns
    finally:
        close(window)


def test_qt_filter_change_discards_inflight_generation(tmp_path,monkeypatch):
    root=tmp_path/"source"
    original=synthetic_scenes(root)
    started,release=Event(),Event()
    real=pages_module.generate
    def gated(*args,**kwargs):
        started.set()
        assert release.wait(8)
        return real(*args,**kwargs)
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _folder:original)
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        monkeypatch.setattr(pages_module,"generate",gated)
        page.generate()
        wait_until(started.is_set)
        page.scene_filter.topLevelItem(1).setCheckState(0,Qt.CheckState.Unchecked)
        release.set()
        wait_until(lambda:not window.tasks)
        assert not page.model.rows and not page.scenes
        assert 'Đã bỏ ma trận sinh nền' in window.status.text()
    finally:
        release.set()
        close(window)


def test_qt_angle_exclusion_blocks_unsafe_physical_rename_and_stale_csv(tmp_path,monkeypatch):
    root=tmp_path/"source"
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _root:synthetic_scenes(root))
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        page.scene_filter.topLevelItem(0).child(0).setCheckState(
            0,Qt.CheckState.Unchecked)
        with pytest.raises(ValueError,match="ma trận hợp lệ"):
            page.csv()
        page.generate();wait_until(lambda:not window.tasks)
        assert page.model.rows
        assert len(page.scenes)==3  # Only one angle, not the whole scene, was removed.
        with pytest.raises(ValueError,match="đủ mọi cảnh/góc"):
            page.rename_preview()
        assert not window.failures,window.failures
    finally:
        close(window)


def test_qt_reorder_after_excluding_one_angle_keeps_old_history_provenance(tmp_path,monkeypatch):
    from fonesi_edit.domain import canonical
    root=tmp_path/"source"
    full=synthetic_scenes(root)
    monkeypatch.setattr(pages_module,"scan_scenes",lambda _root:full)
    window=MainWindow(tmp_path/"state");window.scheduler.paused=True
    try:
        page=window.matrix;page.folder.setText(str(root));page.count.setValue(1)
        with window.store.connect() as conn:
            conn.execute(
                "INSERT INTO matrix_history(scope,combination,state,job_id,created) "
                "VALUES(?,?,'succeeded',NULL,?)",
                (page.scope(),canonical(["one-0","two-0","three-0"]),time.time()))
        page.scan_scene_choices();wait_until(lambda:not window.tasks)
        page.scene_filter.topLevelItem(0).child(0).setCheckState(
            0,Qt.CheckState.Unchecked)
        page.generate();wait_until(lambda:not window.tasks)
        assert len(page.model.rows)==1
        assert page.model.rows[0][0].hash=="one-1"
        assert page.old_history==[["one-0","two-0","three-0"]]
        page.scene_list.setCurrentRow(0)
        assert page.move_scene(1)
        assert page.old_history==[["two-0","one-0","three-0"]]
        assert page.model.rows[0][1].hash=="one-1"
        assert window.store.setting(page.scene_order_key())==scene_directories(page.scenes)
        assert not window.failures,window.failures
    finally:
        close(window)
