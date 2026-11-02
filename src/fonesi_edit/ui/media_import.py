"""Explicit local media-library import; no render-ready asset conversion."""
from pathlib import Path
from uuid import uuid4
import os
import stat

from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem, QAbstractItemView)

from fonesi_edit.domain.media_library import MediaRecord, MediaPath, validate_observation
from fonesi_edit.media.probe import inspect_media, fingerprint, ProbeCanceled, ProbeError
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.media.retirement import ValidationLifecycle
from fonesi_edit.storage.media_commands import add_media


def _source_signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _regular_original(path):
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or
            getattr(info, 'st_file_attributes', 0) & 0x400):
        raise ProbeError('Local source/tool must be a regular non-reparse file')
    return info


class LocalMediaPathEdit(QLineEdit):
    """One local file URL may populate this field; dropping never imports it."""
    dropped = Signal(str)
    rejected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText('Chọn tệp hoặc kéo thả một tệp media cục bộ vào đây')

    @staticmethod
    def _candidate(mime):
        urls = mime.urls()
        if len(urls) != 1:
            raise ValueError('Chỉ nhận một tệp mỗi lần kéo thả.')
        url = urls[0]
        if not url.isLocalFile():
            raise ValueError('Chỉ nhận tệp cục bộ; URL mạng không được nhập tại đây.')
        raw = url.toLocalFile()
        try:
            encoded = raw.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError('Đường dẫn tệp không hợp lệ.') from exc
        if (not raw or '\x00' in raw or len(raw) > 32768 or
                len(encoded) > 131072 or raw.startswith(('\\\\', '//'))):
            raise ValueError('Đường dẫn tệp rỗng, quá dài hoặc không phải đường dẫn cục bộ.')
        path = Path(raw)
        if not path.is_absolute():
            raise ValueError('Đường dẫn tệp phải là đường dẫn tuyệt đối.')
        _regular_original(path)
        return path

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.isEnabled() and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self.isEnabled() and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not self.isEnabled():
            event.ignore()
            return
        try:
            path = self._candidate(event.mimeData())
        except (OSError, ValueError, ProbeError):
            self.rejected.emit('Không nhận được tệp. Chỉ kéo một tệp cục bộ thông thường; thư mục, liên kết và URL mạng bị từ chối.')
            event.ignore()
            return
        self.setText(str(path))
        self.dropped.emit(str(path))
        event.acceptProposedAction()


class MediaImportWorker(QThread):
    """Owns hash/probe operations and their native validator retirement."""
    def __init__(self, source, tool, parent=None):
        super().__init__(parent)
        self.source = Path(source)
        self.tool = Path(tool)
        self.record = None
        self.outcome = 'UNKNOWN'
        self.retired = False

    def run(self):
        operation = object()
        lifecycle = ValidationLifecycle(operation)
        try:
            with lifecycle.validation_body():
                if (not self.source.is_absolute() or not self.tool.is_absolute() or
                        '\x00' in str(self.source) or '\x00' in str(self.tool)):
                    raise ProbeError('Explicit absolute paths required')
                original = _source_signature(_regular_original(self.source))
                _regular_original(self.tool)
                if self.isInterruptionRequested():
                    raise ProbeCanceled('Canceled before external inspection')
                raw = inspect_media(self.source, self.tool,
                                    cancel=self.isInterruptionRequested, _lifecycle=lifecycle)
                observed = validate_observation(normalize_probe(raw))
                digest = fingerprint(self.source, self.isInterruptionRequested)
                if (digest != observed.sha256 or
                        _source_signature(_regular_original(self.source)) != original):
                    raise ProbeError('Media changed during import; no record accepted')
                if self.isInterruptionRequested():
                    raise ProbeCanceled('Canceled before completed observation')
                self.record = MediaRecord(str(uuid4()), digest, original[2],
                    MediaPath('absolute', str(self.source), digest), 'OBSERVED', observed)
            self.outcome = 'OBSERVED'
        except ProbeCanceled:
            self.outcome = 'CANCELED'
        except Exception:
            self.outcome = 'REFUSED'
        finally:
            # Successful observation requires the actual owned process to retire,
            # not just an empty/laundered lifecycle or a normalized JSON object.
            self.retired = (lifecycle.confirmed_for(operation) and
                (self.outcome != 'OBSERVED' or len(lifecycle.mechanisms) == 1))


class MediaImportPanel(QWidget):
    idle = Signal()
    project_changed = Signal()
    state_changed = Signal()

    def __init__(self, get_session, parent=None):
        super().__init__(parent)
        self.get_session = get_session
        self.worker = None
        self.stopping = False
        self.revoked = False
        self.cancel_requested = False
        layout = QVBoxLayout(self)
        title = QLabel('Thư viện nguồn dự án — chưa phải timeline hoặc video sẵn sàng xuất')
        title.setTextFormat(Qt.PlainText)
        title.setWordWrap(True)
        layout.addWidget(title)
        self.source = LocalMediaPathEdit()
        self.source.dropped.connect(self._source_dropped)
        self.source.rejected.connect(self._drop_rejected)
        self.tool = QLineEdit()
        self.tool.setPlaceholderText('ffprobe tuyệt đối, do bạn lựa chọn và tin cậy')
        self.source_button = QPushButton('Chọn tệp…')
        self.tool_button = QPushButton('Chọn ffprobe…')
        self.source_button.clicked.connect(self.choose_source)
        self.tool_button.clicked.connect(self.choose_tool)
        for field, button in ((self.source, self.source_button),(self.tool,self.tool_button)):
            row = QHBoxLayout()
            row.addWidget(field)
            row.addWidget(button)
            layout.addLayout(row)
        self.trust = QCheckBox('Tôi cho phép chạy chính tệp ffprobe đã chọn, không tự thay công cụ')
        layout.addWidget(self.trust)
        self.add_button = QPushButton('Kiểm tra và thêm vào thư viện dự án')
        self.cancel_button = QPushButton('Hủy kiểm tra')
        self.add_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.cancel)
        row = QHBoxLayout()
        row.addWidget(self.add_button)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        self.message = QLabel('Chưa mở hoặc chưa chọn media. Nguồn luôn được giữ nguyên.')
        self.message.setTextFormat(Qt.PlainText)
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Tên tệp', 'ID thư viện', 'Dung lượng B', 'Trạng thái'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        self.source.textChanged.connect(self.update_actions)
        self.tool.textChanged.connect(lambda _:self.trust.setChecked(False))
        self.tool.textChanged.connect(self.update_actions)
        self.trust.toggled.connect(self.update_actions)
        self.update_project()

    @property
    def busy(self):
        return self.worker is not None

    def update_project(self):
        session = self.get_session()
        library = None if session is None else session.project.library
        items = () if library is None else library.items
        # A bounded display, not an implicit read or import of all files.
        self.table.setRowCount(min(len(items), 200))
        for index, item in enumerate(items[:200]):
            for column, value in enumerate((Path(item.path_ref.path).name, item.id,
                                            str(item.size_bytes), item.observation_state)):
                cell = QTableWidgetItem(value)
                cell.setToolTip(value)
                self.table.setItem(index, column, cell)
        if session is None:
            self.message.setText('Mở một dự án trước khi nhập media. Chưa thay đổi tệp.')
        elif len(items) > 200:
            self.message.setText(f'Thư viện có {len(items)} mục, chỉ hiển thị 200 đầu; không kết luận render-ready.')
        elif not self.busy:
            self.message.setText(f'Thư viện có {len(items)} mục; chưa đưa vào timeline hoặc xác minh codec xuất.')
        self.update_actions()

    def update_actions(self, *_):
        session = self.get_session()
        available = not self.busy and not self.stopping and not self.revoked
        for control in (self.source, self.tool, self.source_button, self.tool_button, self.trust):
            control.setEnabled(available)
        self.add_button.setEnabled(available and session is not None and
            not session.reconciliation_required and self.trust.isChecked() and
            bool(self.source.text()) and bool(self.tool.text()))
        self.cancel_button.setEnabled(self.busy and not self.stopping and
            not self.worker.isInterruptionRequested())

    def _source_dropped(self, path):
        self.message.setText('Đã chọn đường dẫn nguồn. Chưa chạy kiểm tra hoặc thêm media; hãy rà soát rồi bấm nút nhập.')

    def _drop_rejected(self, message):
        self.message.setText(message)

    def choose_source(self):
        if self.busy or self.stopping or self.revoked:
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Chọn media nguồn')
        if path:
            self.source.setText(path)

    def choose_tool(self):
        if self.busy or self.stopping or self.revoked:
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Chọn chính ffprobe bạn tin cậy để chạy')
        if path:
            self.tool.setText(path)

    def start(self):
        session = self.get_session()
        if (self.busy or self.stopping or self.revoked or session is None or
                session.reconciliation_required or not self.trust.isChecked()):
            return
        source = Path(self.source.text())
        tool = Path(self.tool.text())
        if not source.is_absolute() or not tool.is_absolute():
            self.message.setText('Đường dẫn tuyệt đối mới hợp lệ. Chưa ghi dữ liệu.')
            return
        captured_revision = session.revision
        self.cancel_requested = False
        worker = MediaImportWorker(source, tool, self)
        self.worker = worker
        worker.finished.connect(lambda:self._finished(worker, session, captured_revision))
        self.message.setText('Đang băm và kiểm tra media trên luồng nền; không ghi nguồn.')
        self.update_actions()
        self.state_changed.emit()
        worker.start()

    def _finished(self, worker, session, revision):
        if self.worker is not worker:
            return
        if not worker.wait(0):
            QTimer.singleShot(10, lambda:self._finished(worker, session, revision))
            return
        if not worker.retired:
            self.revoked = True
            self.message.setText('Chưa chứng minh tiến trình kiểm tra đã dừng an toàn. Không nhập hoặc chạy lại.')
        elif self.stopping or self.cancel_requested or worker.outcome == 'CANCELED':
            self.message.setText('Đã hủy; không ghi thêm media vào dự án.')
        elif worker.outcome != 'OBSERVED' or worker.record is None:
            self.message.setText('Không xác nhận được nguồn/công cụ/metadata; dự án không đổi.')
        elif self.get_session() is not session or session.revision != revision:
            self.message.setText('Dự án hoặc phiên bản thay đổi trong lúc kiểm tra; không ghi kết quả cũ.')
        else:
            try:
                result = add_media(session.project, worker.record)
                if result.command is not None:
                    session.commit(result.command)
            except Exception:
                # Unknown post-COMMIT is a blocked session; no automatic replay.
                self.message.setText('Không xác nhận ghi thư viện; kiểm tra bản khôi phục, không tự thử lại.')
            else:
                self.project_changed.emit()
                self.message.setText('Đã ghi thư viện' if result.command is not None else
                                     'Nội dung đã có trong thư viện; không tạo bản sao.')
        self.worker = None
        worker.deleteLater()
        self.update_actions()
        self.state_changed.emit()
        self.idle.emit()

    def cancel(self):
        if self.worker is not None:
            self.cancel_requested = True
            self.worker.requestInterruption()
            self.message.setText('Đã yêu cầu dừng; chờ kiểm tra quyền sở hữu tiến trình.')
            self.update_actions()

    def request_stop(self):
        self.stopping = True
        self.cancel()
        self.update_actions()
