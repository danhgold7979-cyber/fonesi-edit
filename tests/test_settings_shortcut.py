"""Ctrl+, opens the shared Settings area without creating a second window."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def test_ctrl_comma_opens_existing_settings_page_and_preserves_project(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Settings shortcut',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    try:
        assert window.navigation.currentRow()==0
        page_count=window.pages.count()
        window.navigation.setFocus()
        QTest.keyClick(window.navigation,Qt.Key.Key_Comma,Qt.KeyboardModifier.ControlModifier)
        assert window.navigation.currentRow()==7
        assert window.pages.currentIndex()==7
        assert window.pages.count()==page_count
        assert window.session.project==project
        assert window.navigation.item(7).text()=='Preset/Cài đặt'

        # Ctrl+, is application-scoped and remains available from numeric inspector.
        window.navigation.setCurrentRow(3)
        editor=window.layer_editor
        editor.add_mask()
        numeric=editor.spins['x']
        numeric.setFocus()
        revision=window.session.revision
        QTest.keyClick(numeric,Qt.Key.Key_Comma,Qt.KeyboardModifier.ControlModifier)
        assert window.navigation.currentRow()==7
        assert window.pages.currentIndex()==7
        assert window.session.revision==revision

        # Text entry owns its keys; a propagated Ctrl+, must not navigate away.
        window.navigation.setCurrentRow(3)
        timeline=window.timeline_panel
        timeline.parentWidget().setCurrentIndex(1)
        timeline.preview_path.setFocus()
        QTest.keyClick(timeline.preview_path,Qt.Key.Key_Comma,Qt.KeyboardModifier.ControlModifier)
        assert window.navigation.currentRow()==3
        assert window.pages.currentIndex()==3
    finally:
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater();store.close()
