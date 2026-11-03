"""Layer shortcuts are active only in the layer tree/canvas focus scopes."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Layer shortcuts',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    return store,window


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();store.close()


def test_tree_shortcuts_group_undo_redo_and_delete(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first,second},first)
        before=window.session.revision
        editor.layers.setFocus()
        QTest.keyClick(editor.layers,Qt.Key.Key_G,Qt.KeyboardModifier.ControlModifier)
        assert window.session.revision==before+1
        layers={x['id']:x for x in window.session.project.plan.to_dict()['layers']}
        assert layers[first]['group_id']==layers[second]['group_id']

        QTest.keyClick(editor.layers,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
        assert window.session.revision==before+2
        assert all('group_id' not in x for x in window.session.project.plan.to_dict()['layers'])
        QTest.keyClick(editor.layers,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier)
        assert window.session.revision==before+3
        editor._sync_selection({first},first)
        QTest.keyClick(editor.layers,Qt.Key.Key_Delete)
        assert {x['id'] for x in window.session.project.plan.to_dict()['layers']}==set()
    finally:
        _close(store,window,qt_app)


def test_numeric_inspector_keeps_native_ctrl_z_and_does_not_trigger_layer_undo(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor;editor.add_mask()
        before=window.session.revision
        editor.spins['x'].setValue(0.6);editor.apply_inspector()
        changed=window.session.revision
        assert changed==before+1
        editor.spins['x'].setFocus()
        QTest.keyClick(editor.spins['x'],Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
        assert window.session.revision==changed
        assert window.session.project.plan.to_dict()['layers'][0]['transform']['x']==[3,5]
    finally:
        _close(store,window,qt_app)


def test_canvas_focus_shortcut_moves_selected_layer_forward(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first},first)
        before=window.session.revision
        editor.view.setFocus()
        QTest.keyClick(editor.view.viewport(),Qt.Key.Key_Up,Qt.KeyboardModifier.AltModifier)
        assert window.session.revision==before+1
        ordered=sorted(window.session.project.plan.to_dict()['layers'],key=lambda x:x['z'])
        assert [x['id'] for x in ordered]==[second,first]
    finally:
        _close(store,window,qt_app)
