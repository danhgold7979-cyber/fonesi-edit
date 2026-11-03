"""Explicit local media-library import; no render-ready asset conversion."""
from pathlib import Path
from uuid import uuid4
import os
import stat
import unicodedata

from PySide6.QtCore import QThread, Signal, QTimer, Qt, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QListWidget, QListWidgetItem)

from fonesi_edit.domain.media_library import MediaRecord, MediaPath, validate_observation
from fonesi_edit.media.probe import inspect_media, fingerprint, ProbeCanceled, ProbeError
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.media.frames import observe_frames
from fonesi_edit.media.retirement import ValidationLifecycle
from fonesi_edit.storage.media_commands import add_media
from fonesi_edit.storage.timeline_commands import add_video_clip, TimelineImportError


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


MAX_DROP_QUEUE_FILES=64
MAX_DROP_QUEUE_ROWS=128
MAX_DROP_QUEUE_URLS_PER_DROP=256


def _drop_detail(url):
    if url.isLocalFile():
        return str(Path(url.toLocalFile()))
    # Do not echo credentials, query tokens or fragments from a rejected URL.
    return f'{url.scheme()}://{url.host()}{url.path()}'


class LocalMediaDropQueue(QListWidget):
    """Bounded local-file review queue; dropping never probes or imports."""
    changed=Signal()
    summary=Signal(int,int)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.viewport().installEventFilter(self)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setToolTip('Kéo nhiều tệp cục bộ vào đây. Chỉ chọn tệp; không tự kiểm tra hoặc nhập.')
        self._seen=set()
        self._valid_count=0
        self._refused_count=0
        self._overflow_item=None
        self._overflow_rows=0

    @property
    def valid_count(self):
        return self._valid_count

    @property
    def refused_count(self):
        return self._refused_count

    @staticmethod
    def _candidate(url):
        if not url.isLocalFile():
            raise ValueError('Chỉ nhận tệp cục bộ; URL mạng bị từ chối.')
        raw=url.toLocalFile()
        try:
            encoded=raw.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError('Đường dẫn tệp không hợp lệ.') from exc
        if (not raw or '\x00' in raw or len(raw)>32768 or len(encoded)>131072 or
                raw.startswith(('\\\\','//'))):
            raise ValueError('Đường dẫn rỗng, quá dài hoặc là đường dẫn mạng/UNC.')
        path=Path(raw)
        if not path.is_absolute():
            raise ValueError('Đường dẫn phải tuyệt đối.')
        _regular_original(path)
        return path

    def _append_overflow_summary(self,count):
        if count<=0:return
        if self._overflow_item is None:
            self._overflow_item=QListWidgetItem()
            self._overflow_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.addItem(self._overflow_item)
        self._overflow_rows+=count
        self._overflow_item.setText(
            f'Đã ẩn {self._overflow_rows} mục bổ sung vì giới hạn {MAX_DROP_QUEUE_ROWS} dòng.')
        self._overflow_item.setToolTip(
            'Danh sách được giới hạn để tránh nhận quá nhiều mục kéo thả. Các mục ẩn không được xếp hàng.')

    def _append_item(self,item):
        # Reserve the final visible row for an explicit overflow summary.
        if self.count()<MAX_DROP_QUEUE_ROWS-1:
            self.addItem(item)
            return True
        self._append_overflow_summary(1)
        return False

    def _refusal(self,label,reason,tooltip=None):
        self._refused_count+=1
        item=QListWidgetItem(f'Từ chối · {label} — {reason}')
        item.setData(Qt.ItemDataRole.UserRole,None)
        item.setData(Qt.ItemDataRole.UserRole+1,'REFUSED')
        item.setToolTip(tooltip or reason)
        self._append_item(item)

    def add_urls(self,urls):
        urls=tuple(urls)
        accepted=rejected=0
        bounded_urls=urls[:MAX_DROP_QUEUE_URLS_PER_DROP]
        for index,url in enumerate(bounded_urls):
            remaining=len(bounded_urls)-index
            if self.count()>=MAX_DROP_QUEUE_ROWS-1:
                rejected+=remaining
                self._refused_count+=remaining
                self._append_overflow_summary(remaining)
                break
            if self._valid_count>=MAX_DROP_QUEUE_FILES:
                self._refusal(
                    'Hàng đợi',
                    f'Đã đạt giới hạn {MAX_DROP_QUEUE_FILES} tệp hợp lệ; các mục còn lại không được xếp hàng.')
                rejected+=remaining
                break
            detail=_drop_detail(url)
            try:
                path=self._candidate(url)
            except (OSError,ValueError,ProbeError) as exc:
                label=url.fileName() or ('URL không cục bộ' if not url.isLocalFile() else 'Tệp không hợp lệ')
                self._refusal(label,str(exc),detail)
                rejected+=1
                continue
            key=unicodedata.normalize('NFC',os.path.normcase(os.path.normpath(str(path))))
            if key in self._seen:
                self._refusal(path.name,'Tệp trùng lặp trong hàng đợi',str(path))
                rejected+=1
                continue
            self._seen.add(key)
            self._valid_count+=1
            item=QListWidgetItem(f'Chờ chọn · {path.name}')
            item.setData(Qt.ItemDataRole.UserRole,str(path))
            item.setData(Qt.ItemDataRole.UserRole+1,'PENDING')
            item.setToolTip(str(path))
            self._append_item(item)
            accepted+=1
        omitted=max(0,len(urls)-MAX_DROP_QUEUE_URLS_PER_DROP)
        if omitted:
            rejected+=omitted
            self._refused_count+=omitted
            self._append_overflow_summary(omitted)
        self.changed.emit()
        self.summary.emit(accepted,rejected)
        return accepted,rejected

    def clear_queue(self):
        self.clear()
        self._seen.clear()
        self._valid_count=0
        self._refused_count=0
        self._overflow_item=None
        self._overflow_rows=0
        self.changed.emit()

    def eventFilter(self,watched,event):
        # QAbstractScrollArea delivers native drag/drop to its viewport.
        if watched==self.viewport():
            if event.type()==QEvent.Type.DragEnter:
                self.dragEnterEvent(event);return True
            if event.type()==QEvent.Type.DragMove:
                self.dragMoveEvent(event);return True
            if event.type()==QEvent.Type.Drop:
                self.dropEvent(event);return True
        return super().eventFilter(watched,event)

    def dragEnterEvent(self,event:QDragEnterEvent):
        if self.isEnabled() and event.mimeData().hasUrls():event.acceptProposedAction()
        else:event.ignore()

    def dragMoveEvent(self,event):
        if self.isEnabled() and event.mimeData().hasUrls():event.acceptProposedAction()
        else:event.ignore()

    def dropEvent(self,event:QDropEvent):
        if not self.isEnabled() or not event.mimeData().hasUrls():
            event.ignore()
            return
        # Invalid entries are still consumed and rendered as refusal rows.
        self.add_urls(event.mimeData().urls())
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


class TimelineImportWorker(QThread):
    """Observe an exact frame map for an already imported source; never renders."""
    def __init__(self, record, tool, parent=None):
        super().__init__(parent)
        self.record=record
        self.source=Path(record.path_ref.path)
        self.tool=Path(tool)
        self.scan=None
        self.outcome='UNKNOWN'
        self.retired=False

    def run(self):
        operation=object()
        lifecycle=ValidationLifecycle(operation)
        try:
            with lifecycle.validation_body():
                if (not self.source.is_absolute() or not self.tool.is_absolute() or
                        self.record.observation is None):
                    raise ProbeError('Verified absolute media/tool and typed observation required')
                _regular_original(self.source)
                _regular_original(self.tool)
                videos=[s for s in self.record.observation.streams
                        if s.kind=='video' and not s.attached_picture]
                if len(videos)!=1:
                    raise ProbeError('Exactly one non-attached video stream is supported')
                if self.isInterruptionRequested():
                    raise ProbeCanceled('Canceled before frame observation')
                self.scan=observe_frames(self.source,self.tool,self.record.observation,videos[0].index,
                    cancel=self.isInterruptionRequested,_lifecycle=lifecycle)
            self.outcome='OBSERVED'
        except ProbeCanceled:
            self.outcome='CANCELED'
        except Exception:
            self.outcome='REFUSED'
        finally:
            self.retired=(lifecycle.confirmed_for(operation) and
                          (self.outcome!='OBSERVED' or len(lifecycle.mechanisms)==1))


class MediaImportPanel(QWidget):
    idle = Signal()
    project_changed = Signal()
    state_changed = Signal()

    def __init__(self, get_session, parent=None):
        super().__init__(parent)
        self.get_session = get_session
        self.worker = None
        self.timeline_worker = None
        self.timeline_cancel_requested = False
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
        layout.addWidget(QLabel('Hàng đợi tệp kéo thả — tối đa 64 tệp hợp lệ; nhập từng tệp có xác nhận'))
        self.drop_queue=LocalMediaDropQueue(self)
        self.drop_queue.setMinimumHeight(96)
        self.drop_queue.changed.connect(self.update_actions)
        self.drop_queue.summary.connect(self._drop_queue_summary)
        self.drop_queue.currentRowChanged.connect(self.update_actions)
        layout.addWidget(self.drop_queue)
        drop_buttons=QHBoxLayout()
        self.use_drop_button=QPushButton('Dùng tệp đã chọn')
        self.clear_drop_button=QPushButton('Xóa hàng đợi')
        self.use_drop_button.clicked.connect(self.use_selected_drop)
        self.clear_drop_button.clicked.connect(self.clear_drop_queue)
        drop_buttons.addWidget(self.use_drop_button);drop_buttons.addWidget(self.clear_drop_button)
        layout.addLayout(drop_buttons)
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
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.update_actions)
        layout.addWidget(self.table)
        self.timeline_button=QPushButton('Đưa media đã chọn vào timeline')
        self.timeline_button.clicked.connect(self.add_selected_to_timeline)
        layout.addWidget(self.timeline_button)
        self.source.textChanged.connect(self.update_actions)
        self.tool.textChanged.connect(lambda _:self.trust.setChecked(False))
        self.tool.textChanged.connect(self.update_actions)
        self.trust.toggled.connect(self.update_actions)
        self.update_project()

    @property
    def busy(self):
        return self.worker is not None or self.timeline_worker is not None

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
                if column==0:cell.setData(Qt.ItemDataRole.UserRole,item.id)
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
        for control in (self.source,self.tool,self.source_button,self.tool_button,self.trust,self.drop_queue):
            control.setEnabled(available)
        self.use_drop_button.setEnabled(available and self._selected_drop_path() is not None)
        self.clear_drop_button.setEnabled(available and self.drop_queue.count()>0)
        self.add_button.setEnabled(available and session is not None and
            not session.reconciliation_required and self.trust.isChecked() and
            bool(self.source.text()) and bool(self.tool.text()))
        self.timeline_button.setEnabled(available and session is not None and
            not session.reconciliation_required and self.trust.isChecked() and
            bool(self.tool.text()) and self._selected_record() is not None)
        active_worker=self.worker if self.worker is not None else self.timeline_worker
        self.cancel_button.setEnabled(active_worker is not None and not self.stopping and
            not active_worker.isInterruptionRequested())

    def _selected_drop_path(self):
        item=self.drop_queue.currentItem()
        return None if item is None else item.data(Qt.ItemDataRole.UserRole)

    def use_selected_drop(self):
        if self.busy or self.stopping or self.revoked:return
        path=self._selected_drop_path()
        if not path:
            self.message.setText('Chọn một tệp hợp lệ trong hàng đợi trước. Không có media nào được nhập.')
            return
        self.source.setText(path)
        self.message.setText('Đã chọn tệp từ hàng đợi. Chưa chạy kiểm tra hoặc nhập; hãy rà soát rồi bấm nút nhập.')
        self.update_actions()

    def clear_drop_queue(self):
        if self.busy or self.stopping or self.revoked:return
        self.drop_queue.clear_queue()
        self.message.setText('Đã xóa hàng đợi tệp kéo thả. Thư viện dự án không thay đổi.')
        self.update_actions()

    def _drop_queue_summary(self,accepted,rejected):
        self.message.setText(f'Đã xếp {accepted} tệp hợp lệ; {rejected} mục bị từ chối hoặc trùng. Chưa chạy kiểm tra hay nhập media.')

    def _selected_record(self):
        session=self.get_session()
        if session is None or session.project.library is None:return None
        rows=self.table.selectionModel().selectedRows()
        if len(rows)!=1:return None
        cell=self.table.item(rows[0].row(),0)
        if cell is None:return None
        media_id=cell.data(Qt.ItemDataRole.UserRole)
        return next((item for item in session.project.library.items if item.id==media_id),None)

    def add_selected_to_timeline(self):
        session=self.get_session();record=self._selected_record()
        if (self.busy or self.stopping or self.revoked or session is None or record is None or
                session.reconciliation_required or not self.trust.isChecked()):
            return
        tool=Path(self.tool.text())
        if not tool.is_absolute():
            self.message.setText('Chọn ffprobe bằng đường dẫn tuyệt đối và xác nhận tin cậy trước.')
            return
        revision=session.revision
        self.timeline_cancel_requested=False
        worker=TimelineImportWorker(record,tool,self)
        self.timeline_worker=worker
        worker.finished.connect(lambda:self._timeline_finished(worker,session,revision,record))
        self.message.setText('Đang quan sát PTS của luồng video đã chọn; chưa tạo clip hoặc render.')
        self.update_actions();self.state_changed.emit();worker.start()

    def _timeline_finished(self,worker,session,revision,record):
        if self.timeline_worker is not worker:return
        if not worker.wait(0):
            QTimer.singleShot(10,lambda:self._timeline_finished(worker,session,revision,record));return
        if not worker.retired:
            self.revoked=True
            self.message.setText('Chưa xác nhận tiến trình quan sát đã dừng an toàn. Không thêm timeline hoặc chạy lại.')
        elif self.stopping or self.timeline_cancel_requested or worker.outcome=='CANCELED':
            self.message.setText('Đã hủy quan sát frame; project không đổi.')
        elif worker.outcome!='OBSERVED' or worker.scan is None:
            self.message.setText('Không xác nhận được frame map; project không đổi.')
        elif self.get_session() is not session or session.revision!=revision:
            self.message.setText('Project/revision đã đổi trong khi quan sát; không ghi kết quả cũ.')
        else:
            try:
                addition=add_video_clip(session.project,record,worker.scan,expected_revision=revision)
                session.commit(addition.command)
            except TimelineImportError as exc:
                self.message.setText(f'Không thể thêm clip: {exc}')
            except Exception:
                self.message.setText('Không xác nhận ghi timeline; kiểm tra project/khôi phục, không tự thử lại.')
            else:
                self.project_changed.emit()
                self.message.setText('Đã thêm clip và các track âm thanh đã quan sát. Chưa phát, dựng hoặc xuất video.')
        self.timeline_worker=None;worker.deleteLater()
        self.update_actions();self.state_changed.emit();self.idle.emit()

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
        if self.timeline_worker is not None:
            self.timeline_cancel_requested = True
            self.timeline_worker.requestInterruption()
            self.message.setText('Đã yêu cầu dừng quan sát frame; chờ tiến trình sở hữu nghỉ an toàn.')
            self.update_actions()

    def request_stop(self):
        self.stopping = True
        self.cancel()
        self.update_actions()
