"""Eight-area foundation shell sharing one authoritative loaded project."""
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget,QTabWidget)
from fonesi_edit.storage.projects import ProjectStore, StorageError
from fonesi_edit.storage.autosave import prepare_open
from fonesi_edit.ui.queue import QueuePage
from fonesi_edit.ui.project_relink import RelinkPanel
from fonesi_edit.ui.project_restore import RestorePanel
from fonesi_edit.ui.media_inspection import InspectionPanel
from fonesi_edit.ui.tool_inventory import ToolInventoryPanel
from fonesi_edit.ui.tool_pair import PairCheckPanel

AREAS = ('Tổng quan', 'Tải nội dung', 'Phụ đề', 'Editor', 'Edit hàng loạt',
         'Ghép theo cảnh', 'Hàng đợi/Lịch sử', 'Preset/Cài đặt')

class MainWindow(QMainWindow):
    def __init__(self, store: ProjectStore):
        super().__init__()
        self.store = store
        self.project = None
        self.session = None
        self._close_requested=False
        self.queue_page=QueuePage(store.path.parent/'jobs.sqlite3')
        self.queue_page.idle.connect(self._queue_idle)
        self.relink_panel=RelinkPanel(lambda:self.session,self)
        self.relink_panel.idle.connect(self._queue_idle)
        self.relink_panel.state_changed.connect(self._project_actions)
        self.relink_panel.project_changed.connect(self._project_changed)
        self.restore_panel=RestorePanel(self)
        self.restore_panel.idle.connect(self._queue_idle)
        self.inspection_panel=InspectionPanel(self)
        self.inspection_panel.idle.connect(self._queue_idle)
        self.tool_inventory=ToolInventoryPanel(self)
        self.tool_inventory.idle.connect(self._queue_idle)
        self.tool_pair=PairCheckPanel(store.path.parent,self)
        self.tool_pair.idle.connect(self._queue_idle)
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
            heading.setStyleSheet('font-size: 22px; font-weight: bold;')
            contents.addWidget(heading)
            if index == 0:
                contents.addWidget(self.project_label)
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
                contents.addWidget(self.inspection_panel)
                contents.addWidget(QLabel('Chưa có timeline, bộ dựng hoặc xuất video.'))
            elif index == 6:
                contents.addWidget(self.queue_page)
            elif index == 7:
                tabs=QTabWidget();tabs.addTab(self.tool_inventory,'Danh sách — chỉ metadata')
                tabs.addTab(self.tool_pair,'Self-test cặp — chạy công cụ đã chọn');contents.addWidget(tabs)
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
        self.navigation.setCurrentRow(0)
        self.setCentralWidget(root)
        self.statusBar().showMessage('Bản phát triển — chưa có bộ dựng/xuất video')

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
        if self.relink_panel.busy:raise StorageError('Relink verification still active; cancel and wait first')
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
        if self.session is None or self.relink_panel.busy:
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
        self._project_actions()

    def _project_actions(self):
        self.open_button.setEnabled(not self.relink_panel.busy and not self._close_requested)
        self.save_button.setEnabled(self.session is not None and not self.session.reconciliation_required
                                    and not self.relink_panel.busy and not self._close_requested)
        self.relink_panel.update_actions()

    @property
    def background_busy(self):return self.queue_page.busy or self.relink_panel.busy or self.restore_panel.busy or self.inspection_panel.busy or self.tool_inventory.busy or self.tool_pair.busy

    def request_stop(self):
        self._close_requested=True
        self.queue_page.request_stop();self.relink_panel.request_stop();self.restore_panel.request_stop();self.inspection_panel.request_stop();self.tool_inventory.request_stop();self.tool_pair.request_stop()
        self._project_actions()

    def closeEvent(self,event):
        self._close_requested=True
        self.request_stop()
        if self.background_busy:
            event.ignore()
            self.statusBar().showMessage('Đang chờ tác vụ nền dừng an toàn; không buộc hủy luồng.')
        else:super().closeEvent(event)

    def _queue_idle(self):
        if self._close_requested and not self.background_busy:QTimer.singleShot(0,self.close)
