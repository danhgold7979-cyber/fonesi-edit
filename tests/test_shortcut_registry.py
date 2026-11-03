"""Shortcut preferences persist outside projects, reject conflicts and rebind live widgets."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

import pytest
from PySide6.QtCore import Qt,QSettings
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest

from fonesi_edit.ui.shortcuts import (
    ShortcutRegistry,ShortcutSettingsPanel,ShortcutConflictError,ShortcutError,
)
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for
from test_timeline_import_ui import _record,_scan


def _settings(path):
    return QSettings(str(path),QSettings.Format.IniFormat)


def test_shortcut_registry_persists_preferences_and_rejects_scope_conflicts(tmp_path):
    path=tmp_path/'shortcuts.ini'
    first=ShortcutRegistry(settings=_settings(path))
    assert first.sequence('layer.undo')=='Ctrl+Z'
    first.set_sequence('layer.undo','Ctrl+Alt+Z')
    second=ShortcutRegistry(settings=_settings(path))
    assert second.sequence('layer.undo')=='Ctrl+Alt+Z'
    with pytest.raises(ShortcutConflictError):
        second.set_sequence('layer.redo','Ctrl+Alt+Z')
    assert second.sequence('layer.redo')=='Ctrl+Shift+Z'
    with pytest.raises(ShortcutConflictError):
        second.set_sequence('app.settings','Left')
    with pytest.raises(ShortcutError):
        second.set_sequence('layer.group','')
    with pytest.raises(ShortcutError,match='one key chord'):
        second.set_sequence('layer.group','Ctrl+K, Ctrl+C')
    second.reset('layer.undo')
    assert second.sequence('layer.undo')=='Ctrl+Z'


def test_shortcut_settings_panel_search_remap_conflict_and_reset(tmp_path,qt_app):
    registry=ShortcutRegistry(settings=_settings(tmp_path/'panel.ini'))
    panel=ShortcutSettingsPanel(registry);panel.show()
    try:
        panel.search.setText('undo')
        assert panel.items.count()==1
        assert panel.items.currentItem().data(Qt.ItemDataRole.UserRole)=='layer.undo'
        panel.sequence_edit.setKeySequence(QKeySequence('Ctrl+Alt+Z'))
        panel.save_selected()
        assert registry.sequence('layer.undo')=='Ctrl+Alt+Z'
        assert 'đã lưu' in panel.status.text().lower()

        panel.sequence_edit.setKeySequence(QKeySequence('Ctrl+G'))
        panel.save_selected()
        assert registry.sequence('layer.undo')=='Ctrl+Alt+Z'
        assert 'xung đột' in panel.status.text().lower()

        panel.reset_selected()
        assert registry.sequence('layer.undo')=='Ctrl+Z'
        panel.reset_all()
        assert registry.sequence('timeline.next_frame')=='Right'
    finally:
        panel.close();panel.deleteLater()


def test_layer_and_timeline_shortcuts_rebind_live_without_reopening_project(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Shortcut remap',1920,1080,Fraction(30),Fraction(10)))
    project_path=tmp_path/'project.json';save_project_file(project_path,project)
    registry=ShortcutRegistry(settings=_settings(tmp_path/'live.ini'))
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store,shortcut_registry=registry);window.show();window.open_project(project_path)
    try:
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first,second},first)
        registry.set_sequence('layer.group','Ctrl+Alt+G')
        editor.layers.setFocus()
        QTest.keyClick(editor.layers,Qt.Key.Key_G,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier)
        layers={x['id']:x for x in window.session.project.plan.to_dict()['layers']}
        assert layers[first]['group_id']==layers[second]['group_id']

        timeline=window.timeline_panel
        timeline.parentWidget().setCurrentIndex(1)
        record,_payload=_record(tmp_path/'clip.mp4')
        addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
        window.session.commit(addition.command);window._project_changed()
        timeline.clip_list.setCurrentRow(0)
        registry.set_sequence('timeline.next_frame','Alt+Right')
        before=window.session.revision
        timeline.clip_list.setFocus()
        QTest.keyClick(timeline.clip_list,Qt.Key.Key_Right,Qt.KeyboardModifier.AltModifier)
        assert timeline.playhead_slider.value()==1
        assert window.session.revision==before
        assert registry.sequence('timeline.next_frame')=='Alt+Right'
    finally:
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater();store.close()
