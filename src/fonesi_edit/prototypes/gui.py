"""Actual Qt/FFmpeg P02 experiment, clearly labelled as a technical prototype."""
from pathlib import Path
from threading import Event
from uuid import uuid4
import os
import tempfile

from PySide6.QtCore import QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QGraphicsItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow,
    QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

from .browser import PLATFORMS, create_profile, list_profiles, open_login
from .media import RenderSpec, extract_frame, probe, render
from .tools import scan_tools


class Worker(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(float)

    def __init__(self, action, parent):
        super().__init__(parent)
        self.action = action
        self.cancel = Event()

    def run(self):
        try:
            self.result.emit(self.action(self.progress.emit, self.cancel))
        except Exception as exc:
            self.error.emit(str(exc))


class MovableTitle(QGraphicsTextItem):
    def __init__(self, moved):
        super().__init__()
        self.moved = moved
        self.setDefaultTextColor(QColor("#ffffff"))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.document().setDocumentMargin(0)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        bounds = self.scene().sceneRect()
        x = min(max(0, self.x()), max(0, bounds.width() - self.boundingRect().width()))
        y = min(max(0, self.y()), max(0, bounds.height() - self.boundingRect().height()))
        self.setPos(x, y)
        self.moved(x / bounds.width(), y / bounds.height())


class Canvas(QGraphicsView):
    def __init__(self, moved):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setMinimumSize(400, 300)
        self.setSceneRect(0, 0, 640, 360)
        self.title_item = MovableTitle(moved)
        self.scene().addItem(self.title_item)

    def image(self, path: Path):
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            raise ValueError("Không đọc được frame preview")
        self.scene().removeItem(self.title_item)
        self.scene().clear()
        self.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.scene().addPixmap(pixmap)
        self.scene().addItem(self.title_item)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fonesi Edit — P02 Technical Preview")
        self.resize(1240, 820)
        self.workspace = tempfile.TemporaryDirectory(prefix="fonesi-ui-")
        self.tasks = []
        self.failures = []
        self.source = None
        self.subtitles = None
        self.logo = None
        self.font_file = None
        self.overrides = {}
        self.rendering = False
        data_root = os.environ.get("FONESI_PROTOTYPE_DATA_DIR")
        self.profile_root = Path(data_root) if data_root else Path.home() / ".fonesi-p02" / "profiles"
        root = QWidget()
        layout = QVBoxLayout(root)
        heading = QLabel("FONESI EDIT   /   P02 • KIỂM CHỨNG KỸ THUẬT")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        note = QLabel("Mẫu chạy thật: render CPU, sub, logo và quét công cụ. Chưa phải editor đầy đủ hoặc bản Windows đã nghiệm thu.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.media_tab(), "Preview & render")
        self.tabs.addTab(self.tools_tab(), "Công cụ cần thiết")
        self.tabs.addTab(self.chrome_tab(), "Chrome & tài khoản")
        layout.addWidget(self.tabs, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        self.status = QLabel("Sẵn sàng kiểm chứng với video cục bộ. Nguồn/quyền truy cập/API được kiểm tra riêng.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.setCentralWidget(root)
        self.refresh_overlay()
        QTimer.singleShot(0, self.rescan)

    def background(self, action, done, failed=None):
        worker = Worker(action, self)
        self.tasks.append(worker)
        worker.result.connect(done, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(failed or self.failed, Qt.ConnectionType.QueuedConnection)
        worker.progress.connect(lambda n: self.progress.setValue(round(n * 100)), Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(lambda: self.tasks.remove(worker))
        worker.start()
        return worker

    def failed(self, message):
        self.failures.append(message)
        self.status.setText("Lỗi: " + message[-1600:])
        self.rendering = False
        self.render_button.setEnabled(self.source is not None)

    def media_tab(self):
        tab = QWidget()
        row = QHBoxLayout(tab)
        split = QSplitter()
        row.addWidget(split)
        preview = QWidget()
        view_layout = QVBoxLayout(preview)
        self.source_label = QLabel("Chưa chọn video")
        self.source_label.setWordWrap(True)
        view_layout.addWidget(self.source_label)
        self.views = QTabWidget()
        self.canvas = Canvas(self.overlay_moved)
        self.views.addTab(self.canvas, "Bố trí chữ • thử UX")
        self.video = QVideoWidget()
        self.views.addTab(self.video, "Playback • nguồn / bản render")
        view_layout.addWidget(self.views, 1)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.errorOccurred.connect(lambda _, text: self.status.setText("Playback: " + text))
        controls = QHBoxLayout()
        play = QPushButton("Phát / dừng")
        play.clicked.connect(self.toggle_play)
        controls.addWidget(play)
        self.seek = QSpinBox()
        self.seek.setSuffix(" ms")
        self.seek.setRange(0, 0)
        self.seek.valueChanged.connect(self.player.setPosition)
        controls.addWidget(self.seek)
        self.player.durationChanged.connect(lambda n: self.seek.setMaximum(n))
        self.player.positionChanged.connect(self.player_position)
        view_layout.addLayout(controls)
        view_layout.addWidget(QLabel("Bố trí là thử nghiệm kéo vị trí; bản render FFmpeg là tham chiếu hình ảnh, chưa chốt parity P07."))
        split.addWidget(preview)
        panel = QWidget()
        form = QFormLayout(panel)
        open_button = QPushButton("Chọn video…")
        open_button.clicked.connect(self.choose_source)
        form.addRow(open_button)
        self.title_input = QLineEdit("Fonesi Edit • Kiểm chứng P02")
        self.title_input.textChanged.connect(self.refresh_overlay)
        form.addRow("Chữ phủ", self.title_input)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 200)
        self.font_size.setValue(28)
        self.font_size.valueChanged.connect(self.refresh_overlay)
        form.addRow("Cỡ chữ (pixel)", self.font_size)
        self.x = QDoubleSpinBox()
        self.y = QDoubleSpinBox()
        for control, value in ((self.x, 0.05), (self.y, 0.08)):
            control.setRange(0, 1)
            control.setDecimals(3)
            control.setSingleStep(0.01)
            control.setValue(value)
            control.valueChanged.connect(self.refresh_overlay)
        form.addRow("X / chiều rộng", self.x)
        form.addRow("Y / chiều cao", self.y)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(-2000, 2000)
        self.speed.setSuffix(" px/s")
        form.addRow("Chạy ngang", self.speed)
        self.mask = QCheckBox("Thêm vùng blur cố định để thử")
        self.mask.setChecked(True)
        form.addRow(self.mask)
        for label, kind in (("Phụ đề SRT…", "subtitles"), ("Logo ảnh…", "logo"), ("Font TTF/OTF…", "font")):
            button = QPushButton(label)
            button.clicked.connect(lambda _, k=kind: self.choose_asset(k))
            form.addRow(button)
        self.assets_label = QLabel("Sub: chưa chọn\nLogo: chưa chọn\nFont: mặc định hệ thống")
        self.assets_label.setWordWrap(True)
        form.addRow(self.assets_label)
        self.render_button = QPushButton("Render tham chiếu…")
        self.render_button.setObjectName("primary")
        self.render_button.setEnabled(False)
        self.render_button.clicked.connect(self.start_render)
        form.addRow(self.render_button)
        cancel = QPushButton("Hủy tác vụ đang chạy")
        cancel.clicked.connect(lambda: [task.cancel.set() for task in self.tasks])
        form.addRow(cancel)
        split.addWidget(panel)
        split.setSizes([820, 330])
        return tab

    def tools_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Kiểm tra khởi chạy/version thật. Tải/cài tự động và tool lease được triển khai ở P03; chưa có trong mẫu này."))
        buttons = QHBoxLayout()
        scan = QPushButton("Quét lại")
        scan.clicked.connect(self.rescan)
        buttons.addWidget(scan)
        choose = QPushButton("Trỏ tệp công cụ đang chọn…")
        choose.clicked.connect(self.choose_tool)
        buttons.addWidget(choose)
        layout.addLayout(buttons)
        self.tool_table = QTableWidget(0, 4)
        self.tool_table.setHorizontalHeaderLabels(["Công cụ", "Trạng thái", "Phiên bản", "Đường dẫn / chi tiết"])
        self.tool_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tool_table.horizontalHeader().setStretchLastSection(True)
        self.tool_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tool_table)
        return tab

    def chrome_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        text = QLabel("Google Chrome chính thức, hồ sơ dữ liệu riêng. Một hồ sơ dùng nhiều nền tảng; nick thứ hai cùng nền tảng dùng hồ sơ khác.\nMẫu chỉ mở login thật; kiểm tra danh tính/session handoff vào downloader chưa được nghiệm thu.")
        text.setWordWrap(True)
        layout.addWidget(text)
        self.profile_combo = QComboBox()
        layout.addWidget(self.profile_combo)
        self.reload_profiles()
        add = QPushButton("Tạo hồ sơ Chrome riêng…")
        add.clicked.connect(self.new_profile)
        layout.addWidget(add)
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(PLATFORMS)
        layout.addWidget(self.platform_combo)
        login = QPushButton("Mở đăng nhập trong Chrome thật")
        login.clicked.connect(self.login)
        layout.addWidget(login)
        layout.addWidget(QLabel("Phiên website: chưa kiểm chứng  •  Connector dùng phiên: chưa kiểm chứng\nKhông đọc cookie, không lưu mật khẩu, không thay Chrome bằng Chromium."))
        layout.addStretch()
        return tab

    def reload_profiles(self):
        self.profiles = list_profiles(self.profile_root)
        self.profile_combo.clear()
        for profile in self.profiles:
            self.profile_combo.addItem(profile.label, profile.id)

    def new_profile(self):
        label, ok = QInputDialog.getText(self, "Hồ sơ Chrome", "Tên hồ sơ")
        if ok and label.strip():
            try:
                profile = create_profile(self.profile_root, label)
                self.reload_profiles()
                self.profile_combo.setCurrentIndex(self.profile_combo.findData(profile.id))
            except (ValueError, OSError) as exc:
                self.failed(str(exc))

    def login(self):
        index = self.profile_combo.currentIndex()
        if index < 0:
            self.failed("Hãy tạo/chọn hồ sơ riêng trước")
            return
        profile = self.profiles[index]
        platform = self.platform_combo.currentText()
        self.background(lambda _, cancel: open_login(profile, platform, self.overrides.get("Google Chrome")),
                        lambda _: self.status.setText("Đã mở Chrome. Người dùng đăng nhập trực tiếp; bridge chưa được kiểm chứng."))

    def rescan(self):
        overrides = self.overrides.copy()
        self.background(lambda _, cancel: scan_tools(overrides), self.tools_loaded)

    def tools_loaded(self, tools):
        self.tool_table.setRowCount(len(tools))
        for row, tool in enumerate(tools):
            for col, value in enumerate((tool.name, tool.status, tool.version, tool.path or tool.detail)):
                item = QTableWidgetItem(value)
                item.setToolTip(value + ("\n" + tool.detail if tool.detail else ""))
                self.tool_table.setItem(row, col, item)

    def choose_tool(self):
        row = self.tool_table.currentRow()
        if row < 0:
            self.status.setText("Chọn một công cụ trong bảng trước")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Chọn executable")
        if path:
            self.overrides[self.tool_table.item(row, 0).text()] = path
            self.rescan()

    def choose_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "Video nguồn", filter="Video (*.mp4 *.mkv *.mov *.webm);;Tất cả (*)")
        if path:
            self.open_source(Path(path))

    def open_source(self, source: Path):
        frame = Path(self.workspace.name) / (uuid4().hex + ".png")
        def action(_, cancel):
            info = probe(source)
            extract_frame(source, frame, min(0.1, info.duration / 2))
            return source, info, frame
        self.background(action, self.source_loaded)

    def source_loaded(self, data):
        self.source, info, frame = data
        self.source_label.setText(f"{self.source.name}  •  {info.width}×{info.height}  •  {info.duration:.2f}s  •  {info.video_codec}")
        self.canvas.image(frame)
        self.refresh_overlay()
        self.player.setSource(QUrl.fromLocalFile(str(self.source.resolve())))
        self.render_button.setEnabled(not self.rendering)

    def choose_asset(self, kind):
        filters = {"subtitles": "SRT (*.srt)", "logo": "Ảnh (*.png *.jpg *.webp)", "font": "Font (*.ttf *.otf)"}
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tài nguyên", filter=filters[kind])
        if path:
            setattr(self, "font_file" if kind == "font" else kind, Path(path))
            self.assets_label.setText(f"Sub: {self.subtitles.name if self.subtitles else 'chưa chọn'}\nLogo: {self.logo.name if self.logo else 'chưa chọn'}\nFont: {self.font_file.name if self.font_file else 'mặc định'}")
            self.refresh_overlay()

    def overlay_moved(self, x, y):
        for control, value in ((self.x, x), (self.y, y)):
            control.blockSignals(True)
            control.setValue(value)
            control.blockSignals(False)

    def refresh_overlay(self):
        if not hasattr(self, "y"):
            return
        family = "DejaVu Sans" if os.name != "nt" else "Arial"
        if self.font_file:
            font_id = QFontDatabase.addApplicationFont(str(self.font_file))
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                family = families[0]
        font = QFont(family)
        font.setPixelSize(self.font_size.value())
        self.canvas.title_item.setFont(font)
        self.canvas.title_item.setPlainText(self.title_input.text())
        bounds = self.canvas.sceneRect()
        self.canvas.title_item.setPos(self.x.value() * bounds.width(), self.y.value() * bounds.height())

    def start_render(self):
        if not self.source or self.rendering:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất video tham chiếu", str(self.source.with_name(self.source.stem + "_p02.mp4")), "MP4 (*.mp4)")
        if not path:
            return
        try:
            spec = RenderSpec(title=self.title_input.text(), font_size=self.font_size.value(), x=self.x.value(),
                y=self.y.value(), speed_px_s=self.speed.value(), mask=self.mask.isChecked(),
                subtitles=self.subtitles, logo=self.logo, font=self.font_file)
        except ValueError as exc:
            self.failed(str(exc))
            return
        source, destination = self.source, Path(path)
        self.rendering = True
        self.render_button.setEnabled(False)
        self.progress.setValue(0)
        self.status.setText("Đang render FFmpeg thật; giữ nguyên video nguồn…")
        self.background(lambda progress, cancel: render(source, destination, spec, progress, cancel), self.rendered)

    def rendered(self, result):
        self.rendering = False
        self.render_button.setEnabled(True)
        self.status.setText(f"Đã kiểm tra decode/tracks/duration: {result['output']} • {result['elapsed_seconds']}s")
        self.player.setSource(QUrl.fromLocalFile(result["output"]))
        self.views.setCurrentIndex(1)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.views.setCurrentIndex(1)
            self.player.play()

    def player_position(self, value):
        self.seek.blockSignals(True)
        self.seek.setValue(value)
        self.seek.blockSignals(False)

    def closeEvent(self, event):
        if self.tasks:
            for task in self.tasks:
                task.cancel.set()
            self.status.setText("Đang đóng worker an toàn…")
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
        self.player.stop()
        self.player.setSource(QUrl())
        self.workspace.cleanup()
        super().closeEvent(event)


def launch(smoke=False, screenshot: Path | None = None, source: Path | None = None):
    app = QApplication.instance() or QApplication([])
    if smoke:
        app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget { background:#101625; color:#e4eaf5; font-size:13px; }
        QLabel#heading { color:#b1a1ff; font-size:21px; font-weight:bold; padding:12px 0; }
        QPushButton { background:#25314b; padding:9px 14px; border:1px solid #384764; border-radius:6px; }
        QPushButton:hover { background:#334563; } QPushButton:disabled { color:#7b8598; }
        QPushButton#primary { background:#6650cf; }
        QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox { background:#1b253a; padding:6px; border:1px solid #384764; border-radius:4px; }
        QTabBar::tab { padding:10px 16px; background:#1b253a; } QTabBar::tab:selected { background:#3d326f; }
        QHeaderView::section { background:#25314b; padding:8px; }
        QProgressBar { border:1px solid #384764; text-align:center; } QProgressBar::chunk { background:#7962dc; }
    """)
    window = Window()
    window.show()
    if source:
        window.open_source(source)
    if smoke or screenshot:
        attempts = [0]
        def finish():
            attempts[0] += 1
            if window.tasks:
                if attempts[0] >= 200:
                    for task in window.tasks:
                        task.cancel.set()
                    if not window.failures:
                        window.failures.append("Smoke worker timeout")
                QTimer.singleShot(100, finish)
                return
            failed = bool(window.failures) or bool(source and window.source is None)
            if screenshot:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not window.grab().save(str(screenshot)):
                    failed = True
            if smoke:
                window.close()
                app.exit(1 if failed else 0)
        QTimer.singleShot(500, finish)
    return app.exec()
