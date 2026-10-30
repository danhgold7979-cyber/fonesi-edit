"""Local SRT editor: real editing and immutable snapshots, no translation."""

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from fonesi_edit.style import STYLE
from fonesi_edit.subtitles import (
    Cue,
    SubtitleDocument,
    export_srt,
    parse_srt,
    parse_time,
    replace_text,
    rounded_millis,
    timestamp,
)
from fonesi_edit.timing import Interval


class SubtitleModel(QAbstractTableModel):
    changed = Signal()
    rejected = Signal(str)

    def __init__(self, document=None):
        super().__init__()
        self.document = document or SubtitleDocument(())
        self.undo_stack = []
        self.redo_stack = []

    def rowCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self.document.cues)

    def columnCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else 5

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return (
                ["Câu", "Bắt đầu", "Kết thúc", "Nội dung", "Khóa tay"][section]
                if orientation == Qt.Horizontal
                else str(section + 1)
            )

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.document.cues):
            return None
        cue = self.document.cues[index.row()]
        column = index.column()
        if column == 4 and role == Qt.CheckStateRole:
            return Qt.Checked if cue.locked else Qt.Unchecked
        if role in (Qt.DisplayRole, Qt.EditRole):
            return [
                str(index.row() + 1),
                timestamp(rounded_millis(cue.interval.start)),
                timestamp(rounded_millis(cue.interval.end)),
                cue.text,
                "",
            ][column]

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in (1, 2, 3):
            flags |= Qt.ItemIsEditable
        if index.column() == 4:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def replace(self, document, *, remember=True):
        if remember:
            self.undo_stack.append(self.document)
            self.undo_stack = self.undo_stack[-100:]
            self.redo_stack = []
        self.beginResetModel()
        self.document = document
        self.endResetModel()
        self.changed.emit()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or not 0 <= index.row() < len(self.document.cues):
            return False
        old = self.document.cues[index.row()]
        start, end, text, locked = (
            old.interval.start,
            old.interval.end,
            old.text,
            old.locked,
        )
        try:
            if index.column() == 1 and role == Qt.EditRole:
                start = parse_time(str(value))
            elif index.column() == 2 and role == Qt.EditRole:
                end = parse_time(str(value))
            elif index.column() == 3 and role == Qt.EditRole:
                text = str(value)
            elif index.column() == 4 and role == Qt.CheckStateRole:
                if value not in (
                    Qt.Checked,
                    Qt.Unchecked,
                    Qt.Checked.value,
                    Qt.Unchecked.value,
                ):
                    raise ValueError("INVALID_CHECK_STATE")
                locked = value in (Qt.Checked, Qt.Checked.value)
            else:
                return False
            cue = Cue(old.id, Interval(start, end), text, locked)
            if cue == old:
                return True
            cues = list(self.document.cues)
            cues[index.row()] = cue
            self.replace(SubtitleDocument(tuple(cues)))
            return True
        except ValueError:
            self.rejected.emit("Giá trị không hợp lệ; câu gốc được giữ nguyên.")
            return False

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.document)
        self.replace(self.undo_stack.pop(), remember=False)

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.document)
        self.replace(self.redo_stack.pop(), remember=False)


def write_new_srt(document, path):
    data = export_srt(document)
    path = path.absolute()
    with tempfile.TemporaryDirectory(prefix=".fonesi-srt-", dir=path.parent) as folder:
        staged = Path(folder) / "subtitles.srt"
        with staged.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        parsed = parse_srt(staged.read_bytes())
        if [c.text for c in parsed.cues] != [c.text for c in document.cues]:
            raise ValueError("SRT_READBACK_FAILED")
        os.link(staged, path)


class FileWorker(QThread):
    result = Signal(object)
    failure = Signal(str)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            self.result.emit(self.operation())
        except Exception as exc:  # noqa: BLE001 - Qt worker boundary reports sanitized failure, never success.
            self.failure.emit(type(exc).__name__)


class SubtitleEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.closing = False
        self.setWindowTitle("Fonesi Edit · Phụ đề SRT cục bộ")
        self.resize(1050, 650)
        self.setStyleSheet(STYLE)
        self.model = SubtitleModel()
        layout = QVBoxLayout(self)
        buttons = QHBoxLayout()
        self.open_button = QPushButton("Mở SRT…")
        self.save_button = QPushButton("Lưu thành SRT mới…")
        self.undo_button = QPushButton("Hoàn tác")
        self.redo_button = QPushButton("Làm lại")
        for button in (
            self.open_button,
            self.save_button,
            self.undo_button,
            self.redo_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        search_row = QHBoxLayout()
        self.search_text = QLineEdit()
        self.search_text.setMaxLength(256)
        self.search_text.setPlaceholderText("Tìm literal · phân biệt hoa/thường")
        self.replacement_text = QLineEdit()
        self.replacement_text.setMaxLength(1024)
        self.replacement_text.setPlaceholderText("Thay bằng…")
        self.find_button = QPushButton("Tìm tiếp")
        self.replace_button = QPushButton("Thay tất cả · bỏ qua câu khóa")
        for widget in (
            self.search_text,
            self.replacement_text,
            self.find_button,
            self.replace_button,
        ):
            search_row.addWidget(widget)
        layout.addLayout(search_row)
        self.find_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_all)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 140)
        layout.addWidget(self.table, 1)
        self.status = QLabel(
            "SRT UTF-8 · Chưa có dịch hoặc chèn phụ đề trong công cụ này."
        )
        self.status.setTextFormat(Qt.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.open_button.clicked.connect(self.choose_open)
        self.save_button.clicked.connect(self.choose_save)
        self.undo_button.clicked.connect(self.model.undo)
        self.redo_button.clicked.connect(self.model.redo)
        self.model.changed.connect(self.refresh)
        self.model.rejected.connect(self.status.setText)
        self.refresh()

    def refresh(self):
        busy = self.worker is not None
        self.table.setEnabled(not busy)
        for widget in (
            self.search_text,
            self.replacement_text,
            self.find_button,
            self.replace_button,
        ):
            widget.setEnabled(not busy)
        self.open_button.setEnabled(not busy)
        self.save_button.setEnabled(not busy and bool(self.model.document.cues))
        self.undo_button.setEnabled(not busy and bool(self.model.undo_stack))
        self.redo_button.setEnabled(not busy and bool(self.model.redo_stack))

    def start(self, operation, complete):
        if self.worker:
            return False
        self.worker = FileWorker(operation)
        self.worker.result.connect(complete)
        self.worker.failure.connect(
            lambda code: self.status.setText(
                "Không hoàn tất: " + code + ". Không ghi đè nguồn."
            )
        )
        self.worker.finished.connect(self.operation_finished)
        self.refresh()
        self.worker.start()
        return True

    def operation_finished(self):
        old = self.worker
        self.worker = None
        old.deleteLater()
        self.refresh()
        if self.closing:
            self.close()

    def find_next(self):
        if self.worker:
            return False
        query = self.search_text.text()
        cues = self.model.document.cues
        if not query or not cues:
            self.status.setText("Nhập nội dung tìm và mở tài liệu trước.")
            return False
        start = self.table.currentIndex().row()
        for offset in range(1, len(cues) + 1):
            row = (start + offset) % len(cues)
            if query in cues[row].text:
                self.table.selectRow(row)
                self.table.setCurrentIndex(self.model.index(row, 3))
                self.table.scrollTo(self.model.index(row, 3))
                self.status.setText(f"Tìm thấy ở câu {row + 1}; tìm tiếp quay vòng.")
                return True
        self.status.setText("Không tìm thấy; phân biệt hoa/thường, không dùng regex.")
        return False

    def replace_all(self):
        if self.worker:
            return False
        try:
            result = replace_text(
                self.model.document,
                self.search_text.text(),
                self.replacement_text.text(),
            )
        except ValueError:
            self.status.setText(
                "Không thể thay: nội dung/timing hoặc kích thước kết quả không hợp lệ. Chưa đổi tài liệu."
            )
            return False
        if result.changed_cues:
            self.model.replace(result.document)
        self.status.setText(
            f"Đã thay {result.occurrences} vị trí trong {result.changed_cues} câu; bỏ qua {result.skipped_locked} câu khóa. Có thể hoàn tác."
        )
        return bool(result.changed_cues)

    def choose_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở phụ đề", "", "SRT (*.srt)")
        if path:
            self.load_path(Path(path))

    def load_path(self, path):
        def operation():
            with path.open("rb") as stream:
                data = stream.read(4194305)
            return parse_srt(data)

        def complete(document):
            self.model.replace(document)
            self.status.setText(
                f"Đã đọc {len(document.cues)} câu; {len(document.diagnostics())} cảnh báo chồng/thứ tự. Mở file mới có thể hoàn tác."
            )

        return self.start(operation, complete)

    def choose_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu phụ đề mới", "subtitles-edited.srt", "SRT (*.srt)"
        )
        if path:
            self.save_path(Path(path))

    def save_path(self, path):
        document = self.model.document
        return self.start(
            lambda: write_new_srt(document, path),
            lambda _: self.status.setText(
                "Đã lưu tệp SRT mới. Khóa tay là trạng thái editor, SRT không lưu metadata khóa."
            ),
        )

    def reject(self):
        self.close()

    def closeEvent(self, event):
        if self.worker:
            self.closing = True
            self.status.setText("Chờ hoàn tất thao tác tệp an toàn trước khi đóng…")
            event.ignore()
        else:
            self.closing = False
            event.accept()
