"""Eight-area foundation shell sharing one authoritative loaded project."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget)
from fonesi_edit.storage.projects import ProjectStore, load_project_file

AREAS = ('Tổng quan', 'Tải nội dung', 'Phụ đề', 'Editor', 'Edit hàng loạt',
         'Ghép theo cảnh', 'Hàng đợi/Lịch sử', 'Preset/Cài đặt')

class MainWindow(QMainWindow):
    def __init__(self, store: ProjectStore):
        super().__init__()
        self.store = store
        self.project = None
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
                open_button = QPushButton('Mở dự án…')
                open_button.clicked.connect(self.choose_project)
                contents.addWidget(open_button)
                contents.addWidget(QLabel('Chưa có tác vụ được chạy. Không có số liệu hiệu suất.'))
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
        self.navigation.setCurrentRow(0)
        self.setCentralWidget(root)
        self.statusBar().showMessage('Bản phát triển — chưa có bộ dựng/xuất video')

    def open_project(self, path: Path):
        # Parse and validate before replacing the current model. Failure preserves it.
        project, _ = load_project_file(path)
        self.project = project
        self.project_label.setText(f'Dự án: {project.name}\nMã: {project.id}')
        return project

    def choose_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Mở dự án', '', 'Dự án (*.json);;Tất cả (*)')
        if not filename:
            return
        try:
            self.open_project(Path(filename))
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, 'Không thể mở dự án', str(exc))
