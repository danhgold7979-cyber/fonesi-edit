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
        window.navigation.setCurrentRow(3)
        target=window.timeline_panel.clip_list
        target.setFocus()
        QTest.keyClick(target,Qt.Key.Key_Comma,Qt.KeyboardModifier.ControlModifier)
        assert window.navigation.currentRow()==7
        assert window.pages.currentIndex()==7
        assert window.pages.count()==page_count
        assert window.session.project==project
        assert window.navigation.item(7).text()=='Preset/Cài đặt'
    finally:
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater();store.close()
