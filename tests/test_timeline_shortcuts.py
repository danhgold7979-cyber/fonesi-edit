"""Timeline keyboard navigation is frame-accurate and focus-scoped."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for
from test_timeline_import_ui import _record,_scan


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Timeline shortcuts',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    window.navigation.setCurrentRow(3)
    record,_payload=_record(tmp_path/'clip.mp4')
    addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
    window.session.commit(addition.command);window._project_changed()
    timeline=window.timeline_panel
    timeline.clip_list.setCurrentRow(0)
    return store,window,timeline


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();store.close()


def test_timeline_shortcuts_move_one_or_ten_frames_and_home_end(tmp_path,qt_app):
    store,window,timeline=_open(tmp_path)
    try:
        revision=window.session.revision
        timeline.clip_list.setFocus()
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_Right)
        assert timeline.playhead_slider.value()==1
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_Right,Qt.KeyboardModifier.ShiftModifier)
        assert timeline.playhead_slider.value()==11
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_Left,Qt.KeyboardModifier.ShiftModifier)
        assert timeline.playhead_slider.value()==1
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_Home)
        assert timeline.playhead_slider.value()==0
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_End)
        assert timeline.playhead_slider.value()==timeline.playhead_slider.maximum()
        assert window.session.revision==revision
    finally:
        _close(store,window,qt_app)


def test_timeline_crop_numeric_field_keeps_native_arrow_keys(tmp_path,qt_app):
    store,window,timeline=_open(tmp_path)
    try:
        timeline.crop_spins['left'].setValue(.25)
        timeline.crop_spins['left'].setFocus()
        before=timeline.playhead_slider.value()
        QTest.keyClick(timeline.crop_spins['left'],Qt.Key.Key_Right)
        assert timeline.playhead_slider.value()==before
        assert timeline.crop_spins['left'].value()>.25
    finally:
        _close(store,window,qt_app)
