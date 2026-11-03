"""Appearance preferences and window-layout persistence."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from PySide6.QtCore import QSettings,QByteArray,QSize
from PySide6.QtGui import QPalette

from fonesi_edit.ui.appearance import (
    AppearancePreferences,AppearanceSettingsPanel,AppearanceSettingsStore,
)
from fonesi_edit.ui.shell import MainWindow
from fonesi_edit.storage.projects import ProjectStore
from test_queue_view import wait_for


def _settings(path):
    settings=QSettings(str(path),QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


def test_appearance_store_allowlists_and_persists_user_preferences(tmp_path):
    path=tmp_path/'appearance.ini'
    settings=_settings(path)
    store=AppearanceSettingsStore(settings)
    assert store.load()==AppearancePreferences()

    chosen=AppearancePreferences('dark',14,125)
    assert store.save(chosen)==chosen
    settings.sync()
    reopened=AppearanceSettingsStore(QSettings(str(path),QSettings.Format.IniFormat))
    assert reopened.load()==chosen

    settings.setValue('appearance/theme','neon')
    settings.setValue('appearance/font_size_pt',999)
    settings.setValue('appearance/zoom_percent',999)
    assert store.load()==AppearancePreferences()


def test_appearance_panel_applies_live_and_resets_only_appearance(qt_app,tmp_path):
    settings=_settings(tmp_path/'appearance-panel.ini')
    settings.setValue('shortcuts/layer.undo','Ctrl+Alt+Z')
    settings.setValue('window/navigation_index',4)
    panel=AppearanceSettingsPanel(settings)

    panel.theme_combo.setCurrentIndex(panel.theme_combo.findData('dark'))
    panel.font_size_combo.setCurrentIndex(panel.font_size_combo.findData(14))
    panel.zoom_combo.setCurrentIndex(panel.zoom_combo.findData(125))

    assert settings.value('appearance/theme')=='dark'
    assert int(settings.value('appearance/font_size_pt'))==14
    assert int(settings.value('appearance/zoom_percent'))==125
    assert qt_app.palette().color(QPalette.ColorRole.Window).name().lower()=='#252930'
    assert qt_app.font().pointSizeF()==17.5
    assert 'padding: 5px' in qt_app.styleSheet()

    panel.reset_button.click()
    assert panel.preferences==AppearancePreferences()
    assert settings.value('appearance/theme') is None
    assert settings.value('appearance/font_size_pt') is None
    assert settings.value('appearance/zoom_percent') is None
    assert settings.value('shortcuts/layer.undo')=='Ctrl+Alt+Z'
    assert int(settings.value('window/navigation_index'))==4
    assert qt_app.styleSheet()==''

    panel.deleteLater()
    qt_app.processEvents()


def test_main_window_restores_geometry_navigation_and_tab_selection(qt_app,tmp_path):
    settings=_settings(tmp_path/'window-layout.ini')
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        first=MainWindow(store,ui_settings=settings)
        first.resize(1350,850)
        first.show()
        first.navigation.setCurrentRow(3)
        first.editor_tabs.setCurrentIndex(2)
        first.settings_tabs.setCurrentIndex(3)
        first.close()
        wait_for(qt_app,lambda:not first.background_busy and not first.isVisible())
        settings.sync()

        assert int(settings.value('window/navigation_index'))==3
        assert int(settings.value('window/editor_tab'))==2
        assert int(settings.value('window/settings_tab'))==3
        assert isinstance(settings.value('window/geometry'),QByteArray)
        assert isinstance(settings.value('window/state'),QByteArray)
        first.deleteLater()
        qt_app.processEvents()

        second=MainWindow(store,ui_settings=settings)
        second.show()
        assert second.navigation.currentRow()==3
        assert second.editor_tabs.currentIndex()==2
        assert second.settings_tabs.currentIndex()==3
        assert second.width()>=1300 and second.height()>=800
        second.close()
        wait_for(qt_app,lambda:not second.background_busy and not second.isVisible())
        second.deleteLater()
        qt_app.processEvents()


def test_pending_close_does_not_persist_unaccepted_window_layout(qt_app,tmp_path):
    class RunningHost:
        def __init__(self):self.running=True
        def isRunning(self):return self.running
        def requestInterruption(self):pass

    settings=_settings(tmp_path/'pending-close.ini')
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store,ui_settings=settings)
        window.resize(1420,900)
        window.show()
        host=RunningHost()
        window.coordinator_host=host
        window.close()
        assert window.isVisible()
        assert settings.value('window/geometry') is None
        host.running=False
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        assert isinstance(settings.value('window/geometry'),QByteArray)
        window.deleteLater()
        qt_app.processEvents()


def test_corrupt_window_geometry_and_state_fall_back_to_default(qt_app,tmp_path):
    settings=_settings(tmp_path/'corrupt-layout.ini')
    settings.setValue('window/geometry',QByteArray(b'not-a-qt-geometry'))
    settings.setValue('window/state',QByteArray(b'not-a-qt-state'))
    settings.setValue('window/navigation_index',999)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store,ui_settings=settings)
        assert window.size()==QSize(1200,760)
        assert window.navigation.currentRow()==0
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater()
        qt_app.processEvents()


def test_oversized_window_geometry_is_ignored_without_touching_other_preferences(qt_app,tmp_path):
    settings=_settings(tmp_path/'oversized-layout.ini')
    settings.setValue('window/geometry',QByteArray(b'x'*65537))
    settings.setValue('appearance/theme','dark')
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store,ui_settings=settings)
        assert window.size()==QSize(1200,760)
        assert window.appearance_settings.preferences.theme=='dark'
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater()
        qt_app.processEvents()
