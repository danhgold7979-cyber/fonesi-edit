"""Session-only media tool selection; no installation or PATH mutation."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from fonesi_edit.media_tools import MediaTools, inspect_tools
from fonesi_edit.style import STYLE
from fonesi_edit.worker import Worker


class ToolDialog(QDialog):
    def __init__(self, ffmpeg, ffprobe, apply_tools, has_jobs, parent=None):
        super().__init__(parent)
        self.worker = None
        self.closing = False
        self.verified = None
        self.revision = 0
        self.verified_revision = None
        self.verified_draft = None
        self.apply_tools = apply_tools
        self.has_jobs = has_jobs
        self.setWindowTitle("FFmpeg / ffprobe · Chỉ phiên hiện tại")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(850, 320)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Chỉ chọn công cụ đã cài từ nguồn tin cậy. Không tải/cài hoặc sửa PATH.\nKiểm tra CLI không xác minh nhà phát hành; lựa chọn chỉ dùng trong phiên này."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.fields, self.choose_buttons = [], []
        for label, initial in (("FFmpeg", ffmpeg), ("ffprobe", ffprobe)):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            field = QLineEdit(initial or "")
            field.setMaxLength(4096)
            button = QPushButton("Chọn file…")
            button.clicked.connect(
                lambda checked=False, target=field: self.choose(target)
            )
            field.textChanged.connect(self.changed)
            row.addWidget(field, 1)
            row.addWidget(button)
            layout.addLayout(row)
            self.fields.append(field)
            self.choose_buttons.append(button)
        buttons = QHBoxLayout()
        self.check_button = QPushButton("Kiểm tra CLI / encoder")
        self.apply_button = QPushButton("Dùng trong phiên này")
        self.cancel_button = QPushButton("Hủy kiểm tra")
        self.check_button.clicked.connect(self.check_tools)
        self.apply_button.clicked.connect(self.apply_selection)
        self.cancel_button.clicked.connect(self.cancel_work)
        for button in (self.check_button, self.apply_button, self.cancel_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.status = QLabel("Cần kiểm tra cả hai công cụ trước khi áp dụng.")
        self.status.setTextFormat(Qt.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.refresh()

    def draft(self):
        return tuple(field.text() for field in self.fields)

    def changed(self):
        self.revision += 1
        self.verified_revision = None
        self.verified = self.verified_draft = None
        self.status.setText(
            "Đường dẫn đã đổi; kết quả kiểm tra trước không còn hiệu lực."
        )
        self.refresh()

    def choose(self, field):
        if self.worker:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn executable đã cài từ nguồn tin cậy"
        )
        if path and len(path) > 4096:
            self.status.setText("Đường dẫn quá dài; chưa đổi lựa chọn.")
        elif path:
            field.setText(path)

    def refresh(self):
        busy = self.worker is not None
        for widget in (*self.fields, *self.choose_buttons):
            widget.setEnabled(not busy)
        self.check_button.setEnabled(not busy and not self.has_jobs())
        self.apply_button.setEnabled(
            not busy
            and not self.has_jobs()
            and self.verified is not None
            and self.draft() == self.verified_draft
            and self.revision == self.verified_revision
        )
        self.cancel_button.setEnabled(busy)

    def check_tools(self):
        if self.worker or self.has_jobs():
            self.status.setText("Đợi import/export/batch hiện tại hoàn tất trước.")
            return False
        requested = self.draft()
        self.revision += 1
        revision = self.revision
        self.verified = self.verified_draft = None
        self.worker = Worker(
            lambda cancel: inspect_tools(*(Path(p) for p in requested), cancel=cancel)
        )
        self.worker.result.connect(
            lambda result: self.checked(requested, result, revision)
        )
        self.worker.failure.connect(
            lambda code: self.status.setText("Kiểm tra không đạt: " + code)
        )
        self.worker.finished.connect(self.finished_work)
        self.status.setText("Đang kiểm tra CLI; không cài hay sửa công cụ…")
        self.refresh()
        self.worker.start()
        return True

    def checked(self, requested, result, revision):
        if revision != self.revision:
            self.status.setText("Kết quả thuộc lần sửa đường dẫn cũ; cần kiểm tra lại.")
            return
        if self.worker is not None and self.worker.cancel.is_set():
            self.status.setText("Đã hủy; không giữ kết quả kiểm tra.")
            return
        if not isinstance(result, MediaTools):
            self.status.setText("Kết quả công cụ không hợp lệ.")
            return
        if self.draft() != requested:
            self.status.setText(
                "Đường dẫn đã đổi trong lúc kiểm tra; không áp dụng kết quả cũ."
            )
            return
        self.verified, self.verified_draft = result, requested
        self.verified_revision = revision
        self.status.setText(
            f"FFmpeg {result.ffmpeg_version}; ffprobe {result.ffprobe_version}; libx264/aac được khai báo. Chưa thay kiểm chứng media thật."
        )
        self.refresh()

    def finished_work(self):
        old, self.worker = self.worker, None
        old.deleteLater()
        self.refresh()
        if self.closing:
            self.close()

    def apply_selection(self):
        if (
            self.worker
            or self.has_jobs()
            or self.verified is None
            or self.draft() != self.verified_draft
            or self.revision != self.verified_revision
        ):
            self.status.setText(
                "Không áp dụng: công việc đang chạy hoặc kết quả không còn hợp lệ."
            )
            return False
        if not self.apply_tools(self.verified):
            self.status.setText("Công việc đã bắt đầu; giữ nguyên công cụ đang dùng.")
            return False
        self.accept()
        return True

    def cancel_work(self):
        if self.worker:
            self.worker.cancel.set()
            self.status.setText("Đang yêu cầu dừng kiểm tra…")

    def reject(self):
        self.close()

    def closeEvent(self, event):
        if self.worker:
            self.closing = True
            self.cancel_work()
            event.ignore()
        else:
            self.closing = False
            event.accept()
