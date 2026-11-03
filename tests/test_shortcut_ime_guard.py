"""Layer shortcut router never consumes an active IME preedit sequence."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt,QEvent
from PySide6.QtGui import QInputMethodEvent,QKeyEvent
from fonesi_edit.ui.shortcuts import ShortcutRegistry
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def test_layer_router_preserves_ime_preedit_and_applies_remapped_shortcut_after_commit(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('IME shortcut',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    registry=ShortcutRegistry()
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store,shortcut_registry=registry);window.show();window.open_project(path)
    try:
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first,second},first)
        registry.set_sequence('layer.group','Ctrl+Alt+G')
        router=editor.shortcut_router
        preedit=QInputMethodEvent('拼音',[])
        assert router.eventFilter(editor.layers,preedit) is False
        key=QKeyEvent(QEvent.Type.KeyPress,Qt.Key.Key_G,
                      Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier)
        before=window.session.revision
        assert router.eventFilter(editor.layers,key) is False
        assert window.session.revision==before
        assert all('group_id' not in x for x in window.session.project.plan.to_dict()['layers'])

        committed=QInputMethodEvent('',[])
        assert router.eventFilter(editor.layers,committed) is False
        key=QKeyEvent(QEvent.Type.KeyPress,Qt.Key.Key_G,
                      Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier)
        assert router.eventFilter(editor.layers,key) is True
        layers={x['id']:x for x in window.session.project.plan.to_dict()['layers']}
        assert layers[first]['group_id']==layers[second]['group_id']
    finally:
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater();store.close()
