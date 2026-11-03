"""Eight-area foundation shell sharing one authoritative loaded project."""
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSettings,QByteArray
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget,QTabWidget)
from fonesi_edit.storage.projects import ProjectStore, StorageError
from fonesi_edit.storage.autosave import prepare_open
from fonesi_edit.ui.queue import QueuePage
from fonesi_edit.jobs.desktop_host import DesktopCoordinatorHost
from fonesi_edit.ui.project_relink import RelinkPanel
from fonesi_edit.ui.project_restore import RestorePanel
from fonesi_edit.ui.media_inspection import InspectionPanel
from fonesi_edit.ui.media_import import MediaImportPanel
from fonesi_edit.ui.layer_editor import LayerEditorWorkspace
from fonesi_edit.ui.timeline import TimelinePanel
from fonesi_edit.ui.tool_inventory import ToolInventoryPanel
from fonesi_edit.ui.tool_pair import PairCheckPanel
from fonesi_edit.ui.account_metadata import AccountMetadataPanel
from fonesi_edit.ui.project_creation import NewProjectDialog
from fonesi_edit.ui.shortcuts import ShortcutRegistry,ShortcutSettingsPanel,ShortcutEventRouter
from fonesi_edit.ui.appearance import AppearanceSettingsPanel

AREAS = ('Tổng quan', 'Tải nội dung', 'Phụ đề', 'Editor', 'Edit hàng loạt',
         'Ghép theo cảnh', 'Hàng đợi/Lịch sử', 'Preset/Cài đặt')

class MainWindow(QMainWindow):
    def __init__(self, store: ProjectStore, shortcut_registry=None, ui_settings=None):
        super().__init__()
        self.store = store
        self.ui_settings=ui_settings if ui_settings is not None else QSettings('Fonesi','Fonesi Edit')
        self.appearance_settings=AppearanceSettingsPanel(self.ui_settings,self)
        self.editor_tabs=None;self.settings_tabs=None
        self.shortcut_registry=shortcut_registry or ShortcutRegistry(self)
        self.shortcut_settings=ShortcutSettingsPanel(self.shortcut_registry,self)
        self.project = None
        self.session = None
        self._close_requested=False
        self.coordinator_host=None
        self._coordinator_error=None
        self.new_project_dialog=NewProjectDialog(lambda:self.session,self.activate_created_project,self)
        self.new_project_panel=self.new_project_dialog.panel
        self.new_project_panel.idle.connect(self._queue_idle)
        self.queue_page=QueuePage(store.path.parent/'jobs.sqlite3')
        self.queue_page.coordinator_requested.connect(self.start_coordinator)
        self.queue_page.idle.connect(self._queue_idle)
        self.relink_panel=RelinkPanel(lambda:self.session,self)
        self.relink_panel.idle.connect(self._queue_idle)
        self.relink_panel.state_changed.connect(self._project_actions)
        self.relink_panel.project_changed.connect(self._project_changed)
        self.restore_panel=RestorePanel(self)
        self.restore_panel.idle.connect(self._queue_idle)
        self.inspection_panel=InspectionPanel(self)
        self.inspection_panel.idle.connect(self._queue_idle)
        self.media_import=MediaImportPanel(lambda:self.session,self)
        self.media_import.idle.connect(self._queue_idle)
        self.media_import.project_changed.connect(self._project_changed)
        self.media_import.state_changed.connect(self._project_actions)
        self.layer_editor=LayerEditorWorkspace(lambda:self.session,self,self.shortcut_registry)
        self.layer_editor.project_changed.connect(self._project_changed)
        self.timeline_panel=TimelinePanel(lambda:self.session,self,self.shortcut_registry)
        self.timeline_panel.project_changed.connect(self._project_changed)
        self.timeline_panel.idle.connect(self._queue_idle)
        self.tool_inventory=ToolInventoryPanel(self,preferences_path=store.path.parent/'tool-preferences.sqlite3',
            shortcut_registry=self.shortcut_registry)
        self.tool_inventory.idle.connect(self._queue_idle)
        self.tool_pair=PairCheckPanel(store.path.parent,self)
        self.tool_pair.idle.connect(self._queue_idle)
        self.account_metadata=AccountMetadataPanel(store.path.parent/'accounts.sqlite3',self)
        self.account_metadata.idle.connect(self._queue_idle)
        self.setWindowTitle('Fonesi Edit — bản phát triển')
        self.resize(1200, 760)
        root = QWidget()
        layout = QHBoxLayout(root)
        self.navigation = QListWidget()
        self.navigation.addItems(AREAS)
        self.navigation.setAccessibleName('Khu vực làm việc')
        self.navigation.setMaximumWidth(240)
        self.pages = QStackedWidget()
        self.project_label = QLabel('Chưa mở dự án.')
        self.project_label.setTextFormat(Qt.PlainText)
        for index, title in enumerate(AREAS):
            page = QWidget()
            contents = QVBoxLayout(page)
            heading = QLabel(title)
            heading_font=heading.font();heading_font.setBold(True)
            heading_font.setPointSizeF(heading_font.pointSizeF()*1.4);heading.setFont(heading_font)
            contents.addWidget(heading)
            if index == 0:
                contents.addWidget(self.project_label)
                self.new_button=QPushButton('Tạo dự án trắng…')
                self.new_button.clicked.connect(self.new_project_dialog.open_panel)
                contents.addWidget(self.new_button)
                self.open_button = QPushButton('Mở dự án…')
                self.open_button.clicked.connect(self.choose_project)
                contents.addWidget(self.open_button)
                self.save_button = QPushButton('Lưu dự án')
                self.save_button.setEnabled(False)
                self.save_button.clicked.connect(self.save_current_project)
                contents.addWidget(self.save_button)
                contents.addWidget(self.relink_panel)
                contents.addWidget(self.restore_panel)
                contents.addWidget(QLabel('Chưa có tác vụ được chạy. Không có số liệu hiệu suất.'))
            elif index == 3:
                tabs=QTabWidget();self.editor_tabs=tabs
                tabs.addTab(self.layer_editor,'Canvas / Layer')
                tabs.addTab(self.timeline_panel,'Timeline')
                tabs.addTab(self.media_import,'Thư viện media')
                tabs.addTab(self.inspection_panel,'Quan sát media')
                contents.addWidget(tabs)
                contents.addWidget(QLabel('Chưa có timeline, bộ dựng hoặc xuất video.'))
            elif index == 6:
                contents.addWidget(self.queue_page)
            elif index == 7:
                tabs=QTabWidget();self.settings_tabs=tabs
                tabs.addTab(self.appearance_settings,'Giao diện')
                tabs.addTab(self.tool_inventory,'Danh sách — chỉ metadata')
                tabs.addTab(self.tool_pair,'Self-test cặp — chạy công cụ đã chọn')
                tabs.addTab(self.shortcut_settings,'Phím tắt')
                tabs.addTab(self.account_metadata,'Hồ sơ / Tài khoản — metadata');contents.addWidget(tabs)
            else:
                message = QLabel('Chức năng này đang được xây dựng, chưa khả dụng.\n'
                                 'Đây là khung ứng dụng, không phải bản hoàn thiện.')
                message.setWordWrap(True)
                contents.addWidget(message)
            contents.addStretch()
            self.pages.addWidget(page)
        layout.addWidget(self.navigation)
        layout.addWidget(self.pages, 1)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.currentRowChanged.connect(lambda index:self.queue_page.refresh() if index==6 else None)
        self.navigation.currentRowChanged.connect(lambda index:self.tool_inventory.first_open() if index==7 else None)
        self.navigation.currentRowChanged.connect(lambda index:self.account_metadata.first_open() if index==7 else None)
        self.navigation.setToolTip('Ctrl+, mở khu vực Preset/Cài đặt')
        self.setCentralWidget(root)
        self.settings_shortcut_router=ShortcutEventRouter(
            self.shortcut_registry,
            (('app.settings',lambda:self.navigation.setCurrentRow(7)),),
            self,ignore_text_entry=True,
        )
        for widget in (self,*self.findChildren(QWidget)):
            widget.installEventFilter(self.settings_shortcut_router)
        self._restore_window_settings()
        self.statusBar().showMessage('Bản phát triển — chưa có bộ dựng/xuất video')

    def _setting_index(self,key,count):
        try:index=int(self.ui_settings.value(key,0))
        except (TypeError,ValueError,OverflowError):return 0
        return index if 0<=index<count else 0

    def _restore_window_settings(self):
        geometry=self.ui_settings.value('window/geometry',None)
        if isinstance(geometry,(QByteArray,bytes,bytearray)) and 0<len(geometry)<=65536:
            try:self.restoreGeometry(geometry)
            except (TypeError,ValueError,RuntimeError):pass
        state=self.ui_settings.value('window/state',None)
        if isinstance(state,(QByteArray,bytes,bytearray)) and 0<len(state)<=65536:
            try:self.restoreState(state,1)
            except (TypeError,ValueError,RuntimeError):pass
        self.navigation.setCurrentRow(self._setting_index('window/navigation_index',len(AREAS)))
        if self.editor_tabs is not None:
            self.editor_tabs.setCurrentIndex(self._setting_index('window/editor_tab',self.editor_tabs.count()))
        if self.settings_tabs is not None:
            self.settings_tabs.setCurrentIndex(self._setting_index('window/settings_tab',self.settings_tabs.count()))

    def _save_window_settings(self):
        self.ui_settings.setValue('window/geometry',self.saveGeometry())
        self.ui_settings.setValue('window/state',self.saveState(1))
        self.ui_settings.setValue('window/navigation_index',max(0,self.navigation.currentRow()))
        if self.editor_tabs is not None:
            self.ui_settings.setValue('window/editor_tab',self.editor_tabs.currentIndex())
        if self.settings_tabs is not None:
            self.ui_settings.setValue('window/settings_tab',self.settings_tabs.currentIndex())
        self.ui_settings.sync()
        if self.ui_settings.status()!=QSettings.Status.NoError:
            self.statusBar().showMessage('Không lưu được bố cục cửa sổ; cài đặt dự án không bị ảnh hưởng.')

    def start_coordinator(self,store_token):
        if self._close_requested or self.coordinator_host is not None:return
        try:
            host=DesktopCoordinatorHost(self.queue_page.path,store_token,self)
        except ValueError:
            self.queue_page.coordinator_unavailable('Không thể xác minh đường dẫn bộ điều phối; chỉ đọc.')
            return
        self.coordinator_host=host
        self._coordinator_error=None
        host.acquired.connect(lambda inbox:self._coordinator_acquired(host,inbox))
        host.unavailable.connect(lambda message:self._coordinator_unavailable(host,message))
        host.finished.connect(lambda:self._coordinator_finished(host))
        host.start()

    def _coordinator_acquired(self,host,inbox):
        if (self.coordinator_host is not host or self._close_requested or
                not host.isRunning() or not self.queue_page.attach_coordinator(inbox)):
            host.requestInterruption()

    def _coordinator_unavailable(self,host,message):
        if self.coordinator_host is host and not self._close_requested:
            # Keep retry disabled until exact QThread/SQLite owner teardown.
            self._coordinator_error=message

    def _coordinator_finished(self,host):
        if self.coordinator_host is not host:return
        if not host.wait(0):
            QTimer.singleShot(10,lambda:self._coordinator_finished(host))
            return
        self.coordinator_host=None
        self.queue_page.coordinator_stopped()
        if self._coordinator_error is not None and not self._close_requested:
            self.queue_page.coordinator_unavailable(self._coordinator_error)
        self._coordinator_error=None
        host.deleteLater()
        self._queue_idle()

    def activate_created_project(self,created,expected_session,expected_revision):
        if (self._close_requested or self.media_import.busy or self.session is not expected_session or
            (self.session is not None and self.session.revision!=expected_revision)):
            raise StorageError('Active project changed during creation')
        offer=prepare_open(self.store,created.path)
        if (offer.local is not None or offer.file_digest!=created.digest or
            offer.file_project.to_json()!=created.project.to_json()):
            raise StorageError('New project identity/content no longer matches creation')
        session=offer.choose(self.store,'file')
        self.session=session;self._project_changed()

    def _choose_recovery(self):
        box = QMessageBox(self)
        box.setWindowTitle('Dữ liệu dự án khác nhau')
        box.setText('Tệp đã chọn khác bản lưu cục bộ. Không tự xác định bản nào mới hơn.')
        file_button = box.addButton('Dùng tệp đã chọn', QMessageBox.AcceptRole)
        local_button = box.addButton('Khôi phục bản cục bộ', QMessageBox.ActionRole)
        cancel_button = box.addButton(QMessageBox.Cancel)
        box.setDefaultButton(cancel_button)
        box.setEscapeButton(cancel_button)
        box.exec()
        clicked = box.clickedButton()
        return 'file' if clicked is file_button else 'recovery' if clicked is local_button else 'cancel'

    def open_project(self, path: Path, *, recovery_choice=None):
        # Resolve and revalidate a choice before replacing any shared UI model.
        if self.relink_panel.busy or self.media_import.busy:raise StorageError('A media/relink verification is active; cancel and wait first')
        offer = prepare_open(self.store, path)
        choice = recovery_choice
        if choice is None:
            choice = self._choose_recovery() if offer.differs else 'file'
        session = offer.choose(self.store, choice)
        if session is None:
            return None
        self.session = session
        self.project = session.project
        self._project_changed()
        self.statusBar().showMessage('Đã mở dự án; chưa chạy dựng/xuất video.')
        return self.project

    def save_current_project(self):
        if self.session is None or self.relink_panel.busy or self.media_import.busy:
            return
        try:
            self.session.save()
        except (OSError, ValueError, RuntimeError):
            self._project_actions()
            QMessageBox.warning(self, 'Chưa xác nhận lưu dự án',
                'Không tự thử lưu lại. Kiểm tra tệp và bản cục bộ, rồi mở lại dự án nếu cần. '
                'Mô hình đang mở được giữ nguyên.')
        else:
            self.statusBar().showMessage('Đã lưu dự án; bản trước được giữ theo cơ chế sao lưu.')

    def choose_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Mở dự án', '', 'Dự án (*.json);;Tất cả (*)')
        if not filename:
            return
        try:
            self.open_project(Path(filename))
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, 'Không thể mở dự án', str(exc))

    def _project_changed(self):
        if self.session is not None:
            self.project=self.session.project
            self.project_label.setText(f'Dự án: {self.project.name}\nMã: {self.project.id}')
        self.media_import.update_project()
        self.layer_editor.update_project()
        self.timeline_panel.update_project()
        self._project_actions()

    def _project_actions(self):
        self.new_button.setEnabled(not self._close_requested and not self.media_import.busy)
        self.open_button.setEnabled(not self.relink_panel.busy and not self.media_import.busy and not self._close_requested)
        self.save_button.setEnabled(self.session is not None and not self.session.reconciliation_required
                                    and not self.relink_panel.busy and not self.media_import.busy and not self._close_requested)
        self.relink_panel.update_actions()
        self.media_import.update_actions()
        self.layer_editor.update_actions()

    @property
    def background_busy(self):return (bool(self.coordinator_host is not None and self.coordinator_host.isRunning()) or
        self.new_project_panel.busy or self.queue_page.busy or self.relink_panel.busy or self.restore_panel.busy or self.inspection_panel.busy or self.media_import.busy or self.timeline_panel.busy or self.tool_inventory.busy or self.tool_pair.busy or self.account_metadata.busy)

    def request_stop(self):
        self._close_requested=True
        if self.coordinator_host is not None:self.coordinator_host.requestInterruption()
        self.new_project_panel.request_stop();self.queue_page.request_stop();self.relink_panel.request_stop();self.restore_panel.request_stop();self.inspection_panel.request_stop();self.media_import.request_stop();self.layer_editor.request_stop();self.timeline_panel.request_stop();self.tool_inventory.request_stop();self.tool_pair.request_stop();self.account_metadata.request_stop()
        self._project_actions()

    def closeEvent(self,event):
        self._close_requested=True
        self.request_stop()
        if self.background_busy:
            event.ignore()
            self.statusBar().showMessage('Đang chờ tác vụ nền dừng an toàn; không buộc hủy luồng.')
        else:
            super().closeEvent(event)
            if event.isAccepted():self._save_window_settings()

    def _queue_idle(self):
        if self._close_requested and not self.background_busy:QTimer.singleShot(0,self.close)
