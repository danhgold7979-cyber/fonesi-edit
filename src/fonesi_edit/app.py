"""Real but deliberately limited native desktop rebuild slice."""

import shutil
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from fonesi_edit.media import probe
from fonesi_edit.prepared_input import capture_source, stage_verified_input
from fonesi_edit.process import run_bounded
from fonesi_edit.project import Project, ProjectMedia, load_project, save_new
from fonesi_edit.render import render_cpu
from fonesi_edit.style import STYLE
from fonesi_edit.timing import ClipMap, Interval
from fonesi_edit.worker import Worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.selected = None
        self.media = []
        self.closing = False
        self.edits = {}
        self._loading_controls = False
        self.media_ids = []
        self.source_refs = {}
        self.source_hashes = {}
        self.exact_edits = {}
        self.project_id = str(uuid4())
        self.project_title = "Dự án mới"
        self.ffmpeg = shutil.which("ffmpeg")
        self.ffprobe = shutil.which("ffprobe")
        self.setWindowTitle("Fonesi Edit · Bản xây lại đang phát triển")
        self.resize(1280, 800)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        head = QHBoxLayout()
        title = QLabel("FONESI EDIT")
        title.setObjectName("brand")
        head.addWidget(title)
        head.addStretch()
        head.addWidget(QLabel("Bản phát triển · Chưa nghiệm thu toàn bộ"))
        layout.addLayout(head)
        tabs = QTabBar()
        tabs.setExpanding(False)
        for name in [
            "Tổng quan",
            "Tải nội dung",
            "Phụ đề",
            "Editor",
            "Edit hàng loạt",
            "Ghép theo cảnh",
            "Hàng đợi",
            "Cài đặt",
        ]:
            tabs.addTab(name)
        for i in range(tabs.count()):
            if i != 3:
                tabs.setTabEnabled(i, False)
                tabs.setTabToolTip(i, "Chưa nối chức năng trong lát cắt rebuild này")
        tabs.setCurrentIndex(3)
        layout.addWidget(tabs)
        controls = QHBoxLayout()
        self.add = QPushButton("Thêm media…")
        self.export = QPushButton("Xuất thử MP4 CPU…")
        self.cancel_button = QPushButton("Hủy tác vụ")
        self.add.clicked.connect(self.choose_source)
        self.export.clicked.connect(self.choose_output)
        self.cancel_button.clicked.connect(self.cancel_work)
        self.subtitle_button = QPushButton("Sửa SRT…")
        self.subtitle_button.clicked.connect(self.open_subtitles)
        self.subtitle_window = None
        self.batch_window = None
        self.batch_button = QPushButton("Lô CPU cục bộ…")
        self.batch_button.clicked.connect(self.open_batch)
        self.open_button = QPushButton("Mở project…")
        self.save_button = QPushButton("Lưu thành project mới…")
        self.inspect_button = QPushButton("Kiểm tra media chọn")
        self.open_button.clicked.connect(self.choose_project)
        self.save_button.clicked.connect(self.choose_save)
        self.inspect_button.clicked.connect(self.inspect_selected)
        controls.addWidget(self.open_button)
        controls.addWidget(self.save_button)
        controls.addWidget(self.add)
        controls.addWidget(self.inspect_button)
        controls.addWidget(self.export)
        controls.addWidget(self.subtitle_button)
        controls.addWidget(self.batch_button)
        controls.addStretch()
        controls.addWidget(self.cancel_button)
        layout.addLayout(controls)
        panes = QSplitter()
        layout.addWidget(panes, 1)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.addWidget(QLabel("MEDIA CỤC BỘ"))
        self.list = QListWidget()
        ll.addWidget(self.list)
        panes.addWidget(left)
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.addWidget(QLabel("KHUNG HÌNH NGUỒN · chưa áp hiệu ứng"))
        self.preview = QLabel(
            "Thêm một video để kiểm tra nội dung.\nNguồn gốc luôn được giữ nguyên."
        )
        self.preview.setObjectName("preview")
        self.preview.setTextFormat(Qt.PlainText)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(480, 320)
        cl.addWidget(self.preview, 1)
        cl.addWidget(
            QLabel(
                "Hiện có: probe thật, khung đầu và xuất CPU.\nTimeline, phụ đề, layer và chuyển động chưa được nối."
            )
        )
        panes.addWidget(center)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.addWidget(QLabel("THUỘC TÍNH NGUỒN"))
        self.details = QLabel("Chưa chọn media")
        self.details.setTextFormat(Qt.PlainText)
        self.details.setWordWrap(True)
        rl.addWidget(self.details)
        form = QFormLayout()
        self.start_time = QDoubleSpinBox()
        self.end_time = QDoubleSpinBox()
        self.speed = QDoubleSpinBox()
        for control in (self.start_time, self.end_time):
            control.setDecimals(6)
            control.setRange(0, 31536000)
            control.setSuffix(" s")
        self.speed.setDecimals(3)
        self.speed.setRange(0.5, 2)
        self.speed.setValue(1)
        self.speed.setSingleStep(0.1)
        self.speed.setSuffix(" ×")
        form.addRow("Bắt đầu", self.start_time)
        form.addRow("Kết thúc", self.end_time)
        form.addRow("Tốc độ", self.speed)
        rl.addLayout(form)
        for control in (self.start_time, self.end_time, self.speed):
            control.valueChanged.connect(self.changed_edit)
        rl.addStretch()
        rl.addWidget(
            QLabel(
                "Trim/tốc độ áp dụng khi xuất.\nKhung nguồn không phải preview hiệu ứng.\nKhông ghi đè tệp đã có."
            )
        )
        panes.addWidget(right)
        panes.setSizes([220, 760, 260])
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel("Sẵn sàng · Chọn media cục bộ.")
        self.status.setTextFormat(Qt.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.list.currentRowChanged.connect(self.select_row)
        self.setStyleSheet(STYLE)
        self.refresh()
        if not self.ffmpeg or not self.ffprobe:
            self.status.setText(
                "Thiếu FFmpeg/ffprobe. Cài công cụ đáng tin cậy rồi mở lại; không tự cài hoặc đổi PATH."
            )

    def refresh(self):
        busy = self.worker is not None
        self.open_button.setEnabled(not busy)
        self.save_button.setEnabled(not busy and bool(self.media))
        row = self.list.currentRow()
        self.inspect_button.setEnabled(
            not busy
            and 0 <= row < len(self.media)
            and bool(self.ffmpeg and self.ffprobe)
        )
        self.add.setEnabled(not busy and bool(self.ffmpeg and self.ffprobe))
        self.export.setEnabled(
            not busy
            and self.selected is not None
            and self.list.currentRow() in self.source_hashes
            and "video" in self.selected[1].stream_types
        )
        for control in (self.start_time, self.end_time, self.speed):
            control.setEnabled(not busy and self.selected is not None)
        if self.selected is not None and (
            self.start_time.value() >= self.end_time.value()
            or Fraction(str(self.end_time.value())) > self.selected[1].duration
        ):
            self.export.setEnabled(False)
        self.cancel_button.setEnabled(busy)
        self.list.setEnabled(not busy)
        self.progress.setRange(0, 0 if busy else 1)
        if not busy:
            self.progress.setValue(0)

    def start(self, operation, on_result):
        if self.worker is not None:
            return False
        worker = Worker(operation)
        self.worker = worker
        worker.result.connect(on_result)
        worker.failure.connect(
            lambda code: self.status.setText(
                "Tác vụ không hoàn tất: " + code + ". Nguồn vẫn giữ nguyên."
            )
        )
        worker.finished.connect(self.finished_work)
        self.refresh()
        worker.start()
        return True

    def finished_work(self):
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.refresh()
        if self.closing:
            self.close()

    def cancel_work(self):
        if self.worker:
            self.worker.cancel.set()
            self.status.setText("Đang yêu cầu hủy; chờ tiến trình dừng an toàn…")

    def open_batch(self):
        from fonesi_edit.batch_editor import BatchEditor

        if self.batch_window is None:
            self.batch_window = BatchEditor(self)
        self.batch_window.show()
        self.batch_window.raise_()
        self.batch_window.activateWindow()

    def open_subtitles(self):
        from fonesi_edit.subtitle_editor import SubtitleEditor

        if self.subtitle_window is None:
            self.subtitle_window = SubtitleEditor(self)
        self.subtitle_window.show()
        self.subtitle_window.raise_()
        self.subtitle_window.activateWindow()

    def choose_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn media nguồn",
            "",
            "Media (*.mp4 *.mkv *.mov *.avi *.webm *.wav *.mp3);;Tất cả (*)",
        )
        if path:
            self.load_source(Path(path))

    def load_source(self, path, replace_row=None):
        if not self.ffmpeg or not self.ffprobe:
            return False

        def work(cancel):
            native = path.absolute()
            with capture_source(
                native,
                Path(tempfile.gettempdir()).absolute(),
                max_bytes=max(1, native.stat().st_size),
                timeout=60,
                cancel=cancel,
            ) as captured:
                info = probe(captured.path, Path(self.ffprobe), cancel=cancel)
                thumbnail = b""
                if "video" in info.stream_types:
                    result = run_bounded(
                        [
                            self.ffmpeg,
                            "-nostdin",
                            "-v",
                            "error",
                            "-protocol_whitelist",
                            "file,pipe",
                            "-i",
                            str(captured.path),
                            "-frames:v",
                            "1",
                            "-vf",
                            "scale=640:-2",
                            "-f",
                            "image2pipe",
                            "-vcodec",
                            "png",
                            "-",
                        ],
                        limit=1048576,
                        cancel=cancel,
                    )
                    if result.status != "OK":
                        raise ValueError("PREVIEW_" + result.status)
                    thumbnail = result.stdout
                if cancel.is_set():
                    raise ValueError("CANCELED")
                return (path, info, thumbnail), captured.sha256

        self.status.setText("Đang kiểm tra media và đọc khung hình…")
        return self.start(
            work,
            lambda result: self.loaded(result[0], replace_row, source_sha=result[1]),
        )

    def loaded(self, result, replace_row=None, *, source_sha=None):
        if replace_row is None:
            self.media.append(result)
            self.media_ids.append(str(uuid4()))
            self.list.addItem(result[0].name)
            row = len(self.media) - 1
            self.source_refs[row] = str(result[0].absolute())
        else:
            row = replace_row
            self.media[row] = result
        if source_sha is not None:
            self.source_hashes[row] = source_sha
        else:
            self.source_hashes.pop(row, None)
        self.list.setCurrentRow(row)
        self.status.setText("Đã đọc nguồn. Đây là khung nguồn, chưa có hiệu ứng.")
        self.select_row(row)

    def select_row(self, row):
        if not 0 <= row < len(self.media):
            self.selected = None
            self.preview.setText("Chưa chọn media.")
            self.details.setText("Chưa chọn media")
            self.refresh()
            return
        path, info, data = self.media[row]
        if info is None:
            self.selected = None
            self.details.setText(
                path.name + "\nChưa kiểm tra nguồn; bấm Kiểm tra media chọn."
            )
            self.preview.setText(
                "Tham chiếu media được giữ nguyên.\nKhông tự mở tệp khi nạp project."
            )
            self.refresh()
            return
        self.selected = self.media[row]
        self._loading_controls = True
        values = self.edits.get(
            row,
            (
                0,
                (info.duration.numerator * 1000000 // info.duration.denominator)
                / 1000000,
                1,
            ),
        )
        for control, value in zip((self.start_time, self.end_time, self.speed), values):
            control.setValue(value)
        self._loading_controls = False
        self.details.setText(
            f"{path.name}\n\nThời lượng: {float(info.duration):.3f} s\nTrack: {', '.join(info.stream_types)}"
        )
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.preview.setPixmap(
                pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.preview.setText("Tệp âm thanh · chưa có phát nghe trong lát cắt này")
        self.refresh()

    def changed_edit(self):
        if self._loading_controls or self.selected is None:
            return
        self.exact_edits.pop(self.list.currentRow(), None)
        self.edits[self.list.currentRow()] = (
            self.start_time.value(),
            self.end_time.value(),
            self.speed.value(),
        )
        self.status.setText(
            "Thiết lập xuất đã đổi. Khung đang xem vẫn là nguồn, chưa áp trim/tốc độ."
        )
        self.refresh()

    def inspect_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.media):
            reference = self.source_refs.get(row, str(self.media[row][0]))
            if not Path(reference).is_absolute():
                self.status.setText(
                    "Đường dẫn thuộc hệ khác hoặc chưa tuyệt đối. Cần chọn lại media, không tự đoán ổ đĩa."
                )
                return False
            return self.load_source(self.media[row][0], replace_row=row)
        return False

    def current_project(self):
        entries = []
        for row, (path, info, data) in enumerate(self.media):
            edit = self.exact_edits.get(row)
            if edit is None and row in self.edits:
                start, end, speed = self.edits[row]
                edit = ClipMap(
                    Interval(Fraction(str(start)), Fraction(str(end))),
                    Fraction(str(speed)),
                )
            entries.append(
                ProjectMedia(
                    self.media_ids[row],
                    self.source_refs.get(row, str(path.absolute())),
                    edit,
                )
            )
        return Project(self.project_id, self.project_title, tuple(entries))

    def choose_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu thành project mới", "project.fonesi", "Fonesi project (*.fonesi)"
        )
        if path:
            self.save_project_to(Path(path))

    def save_project_to(self, path):
        if self.worker:
            return False
        try:
            project = self.current_project()
        except ValueError:
            self.status.setText("Không thể lưu: sửa khoảng trim chưa hợp lệ trước.")
            return False
        self.status.setText("Đang lưu project mới; không ghi đè tệp đã có…")
        return self.start(
            lambda cancel: save_new(project, path),
            lambda result: self.status.setText(
                "Đã lưu project mới. Media nguồn không bị sao chép hoặc thay đổi."
            ),
        )

    def choose_project(self):
        if (
            self.media
            and QMessageBox.question(
                self,
                "Thay project đang mở?",
                "Các thay đổi chưa lưu sẽ rời khỏi cửa sổ. Bạn đã lưu project cần giữ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Mở project", "", "Fonesi project (*.fonesi)"
        )
        if path:
            self.open_project_path(Path(path), replace=True)

    def open_project_path(self, path, *, replace=False):
        if self.worker or (self.media and not replace):
            return False
        self.status.setText("Đang kiểm tra cấu trúc project; không tự mở media…")
        return self.start(lambda cancel: load_project(path), self.project_loaded)

    def project_loaded(self, project):
        self.project_id = project.id
        self.project_title = project.title
        self.selected = None
        self.media = []
        self.media_ids = []
        self.source_refs = {}
        self.source_hashes = {}
        self.edits = {}
        self.exact_edits = {}
        self.list.blockSignals(True)
        self.list.clear()
        for row, entry in enumerate(project.media):
            self.media.append((Path(entry.source), None, b""))
            self.media_ids.append(entry.id)
            self.source_refs[row] = entry.source
            self.list.addItem(Path(entry.source).name)
            if entry.edit is not None:
                self.exact_edits[row] = entry.edit
                self.edits[row] = (
                    float(entry.edit.source.start),
                    float(entry.edit.source.end),
                    float(entry.edit.speed),
                )
        self.list.blockSignals(False)
        if self.media:
            self.list.setCurrentRow(0)
            self.select_row(0)
        else:
            self.preview.setText("Project không có media.")
            self.details.setText("Chưa chọn media")
        self.status.setText(
            "Đã mở project. Chọn media và bấm kiểm tra; tham chiếu thiếu vẫn được giữ."
        )

    def choose_output(self):
        if not self.selected:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Chọn tên đầu ra mới",
            self.selected[0].stem + "-edit.mp4",
            "MP4 (*.mp4)",
        )
        if path:
            self.export_to(Path(path))

    def export_to(self, destination):
        if not self.selected or self.worker:
            return False
        source = self.selected[0].absolute()
        source_sha = self.source_hashes.get(self.list.currentRow())
        if source_sha is None:
            self.status.setText("Cần kiểm tra nguồn trước khi xuất.")
            return False
        mapping = self.exact_edits.get(self.list.currentRow())
        if mapping is None and self.list.currentRow() in self.edits:
            try:
                mapping = ClipMap(
                    Interval(
                        Fraction(str(self.start_time.value())),
                        Fraction(str(self.end_time.value())),
                    ),
                    Fraction(str(self.speed.value())),
                )
            except ValueError:
                self.status.setText(
                    "Khoảng trim không hợp lệ: kết thúc phải lớn hơn bắt đầu."
                )
                return False
        self.status.setText(
            "Đang xuất thử CPU và giải mã kiểm tra; chưa biết % chính xác…"
        )
        ffmpeg, ffprobe = Path(self.ffmpeg), Path(self.ffprobe)

        def work(cancel):
            with stage_verified_input(
                source,
                source_sha,
                destination.absolute().parent,
                max_bytes=max(1, source.stat().st_size),
                timeout=60,
                cancel=cancel,
            ) as captured:
                return render_cpu(
                    captured.path,
                    destination,
                    ffmpeg,
                    ffprobe,
                    duration_tolerance=Fraction(1, 10),
                    cancel=cancel,
                    clip_map=mapping,
                )

        # Provisional developer proof tolerance, not a general editor acceptance gate.
        return self.start(
            work,
            lambda artifact: self.status.setText(
                f"Đã kiểm tra đầu ra: {artifact.path.name} · {artifact.size:,} bytes."
            ),
        )

    def closeEvent(self, event):
        if self.batch_window is not None and self.batch_window.worker:
            self.batch_window.cancel_work()
            self.status.setText("Đợi lô CPU dừng an toàn trước khi đóng ứng dụng.")
            event.ignore()
            return
        if self.subtitle_window is not None and self.subtitle_window.worker:
            self.status.setText(
                "Đợi thao tác tệp phụ đề hoàn tất trước khi đóng ứng dụng."
            )
            event.ignore()
            return
        if self.worker:
            self.closing = True
            self.cancel_work()
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
