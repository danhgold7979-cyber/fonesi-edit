"""Native bounded local CPU batch. No durable queue or preset claims."""

import shutil
from fractions import Fraction
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from fonesi_edit.batch import render_batch, scan
from fonesi_edit.style import STYLE
from fonesi_edit.worker import Worker


class BatchEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.closing = False
        self.source = None
        self.output = None
        self.scan_result = None
        self.ffmpeg = parent.ffmpeg if parent is not None else shutil.which("ffmpeg")
        self.ffprobe = parent.ffprobe if parent is not None else shutil.which("ffprobe")
        self.setWindowTitle("Lô CPU cục bộ · Bản phát triển")
        self.resize(920, 580)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Một nguồn → một MP4 CPU. Không áp preset/trim/sub của Editor.")
        )
        bar = QHBoxLayout()
        self.source_button = QPushButton("Thư mục nguồn…")
        self.output_button = QPushButton("Thư mục đầu ra…")
        self.scan_button = QPushButton("Quét nguồn")
        self.run_button = QPushButton("Xuất các mục đã chọn")
        self.cancel_button = QPushButton("Hủy tác vụ")
        for button in (
            self.source_button,
            self.output_button,
            self.scan_button,
            self.run_button,
            self.cancel_button,
        ):
            bar.addWidget(button)
        layout.addLayout(bar)
        self.paths = QLabel("Chưa chọn thư mục")
        self.paths.setTextFormat(Qt.PlainText)
        self.paths.setWordWrap(True)
        layout.addWidget(self.paths)
        self.items = QListWidget()
        layout.addWidget(self.items)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel(
            "Chọn nguồn và đầu ra, sau đó quét. Nguồn không bị xóa/ghi đè."
        )
        self.status.setTextFormat(Qt.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.source_button.clicked.connect(lambda: self.choose_folder(False))
        self.output_button.clicked.connect(lambda: self.choose_folder(True))
        self.scan_button.clicked.connect(self.scan_sources)
        self.run_button.clicked.connect(self.run_selected)
        self.cancel_button.clicked.connect(self.cancel_work)
        self.items.itemChanged.connect(self.refresh)
        self.refresh()

    def choose_folder(self, output):
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục hiện có")
        if path:
            self.set_folder(Path(path), output=output)

    def set_folder(self, path, *, output):
        if self.worker is not None:
            return False
        if output:
            self.output = path
        else:
            self.source = path
        self.scan_result = None
        self.items.clear()
        self.paths.setText(
            f"Nguồn: {self.source or 'chưa chọn'}\nĐầu ra: {self.output or 'chưa chọn'}"
        )
        self.status.setText("Thư mục đã đổi; cần quét lại trước khi xuất.")
        self.refresh()
        return True

    def selected_items(self):
        if self.scan_result is None:
            return ()
        return tuple(
            value
            for i, value in enumerate(self.scan_result.items)
            if self.items.item(i).checkState() == Qt.Checked
        )

    def refresh(self, *_):
        busy = self.worker is not None
        for button in (self.source_button, self.output_button):
            button.setEnabled(not busy)
        self.scan_button.setEnabled(
            not busy and self.source is not None and self.output is not None
        )
        self.run_button.setEnabled(
            not busy
            and self.source is not None
            and self.output is not None
            and bool(self.ffmpeg and self.ffprobe)
            and self.scan_result is not None
            and self.scan_result.status == "COMPLETE"
            and bool(self.selected_items())
        )
        self.cancel_button.setEnabled(busy)
        self.items.setEnabled(not busy)
        self.progress.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress.setValue(0)

    def start(self, operation, callback):
        if self.worker is not None:
            return False
        self.worker = Worker(operation)
        self.worker.result.connect(callback)
        self.worker.failure.connect(
            lambda code: self.status.setText("Không hoàn tất: " + code)
        )
        self.worker.finished.connect(self.finished_work)
        self.refresh()
        self.worker.start()
        return True

    def finished_work(self):
        old = self.worker
        self.worker = None
        if old:
            old.deleteLater()
        self.refresh()
        if self.closing:
            self.close()

    def cancel_work(self):
        if self.worker:
            self.worker.cancel.set()
            self.status.setText("Đang yêu cầu hủy; chờ dừng an toàn…")

    def scan_sources(self):
        if self.worker or self.source is None or self.output is None:
            return False
        self.scan_result = None
        self.items.clear()
        source, output = self.source, self.output
        self.status.setText("Đang quét; chưa xác nhận nội dung media.")
        return self.start(
            lambda cancel: scan((source,), output, cancel=cancel.is_set), self.scanned
        )

    def scanned(self, result):
        self.items.blockSignals(True)
        self.items.clear()
        self.scan_result = result
        for value in result.items:
            name = (
                value.relative.stem
                + "-"
                + value.relative.suffix.lstrip(".")
                + "-edit.mp4"
            )
            destination = Path(value.root_id) / value.relative.parent / name
            item = QListWidgetItem(f"{value.relative} → {destination}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.items.addItem(item)
        self.items.blockSignals(False)
        self.status.setText(
            f"Quét {result.status}: {len(result.items)} ứng viên; {len(result.warnings)} cảnh báo. "
            "Chỉ quét COMPLETE mới được xuất; tệp sẽ được probe khi chạy."
        )
        self.refresh()

    def run_selected(self):
        if self.worker or not self.run_button.isEnabled():
            return False
        selected, output = self.selected_items(), self.output
        ffmpeg, ffprobe = Path(self.ffmpeg), Path(self.ffprobe)
        self.status.setText(
            f"Đang xuất {len(selected)} mục; chỉ báo số hoàn tất sau validation. Dung sai thử 100ms."
        )
        return self.start(
            lambda cancel: render_batch(
                selected,
                output,
                ffmpeg,
                ffprobe,
                duration_tolerance=Fraction(1, 10),
                cancel=cancel,
            ),
            self.rendered,
        )

    def rendered(self, result):
        self.status.setText(
            f"Lô {result.status}: {len(result.artifacts)} đầu ra đã kiểm tra, "
            f"{len(result.failures)} lỗi. "
            + "; ".join(f"{i + 1}: {code}" for i, code in result.failures[:10])
        )

    def reject(self):
        # Escape follows the same cancellation-and-wait path as window Close.
        self.close()

    def closeEvent(self, event):
        if self.worker:
            self.closing = True
            self.cancel_work()
            event.ignore()
        else:
            self.closing = False
            event.accept()
