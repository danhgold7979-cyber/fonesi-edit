"""Visible metadata-only executable inventory; never a trust/activation resolver."""
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QFormLayout,QLineEdit,QLabel,
    QCheckBox,QPushButton,QHBoxLayout,QTableWidget,QTableWidgetItem,QPlainTextEdit,
    QAbstractItemView)
from fonesi_edit.dependencies.discovery import discover_tools,system_search_dirs,TOOL_NAMES

from fonesi_edit.dependencies.preferences import ToolPreferences
from .tool_preferences import PreferenceWorker,reconciles
from .shortcuts import ShortcutRegistry,ShortcutEventRouter

ROLES = {'ffmpeg':'Dựng/chuyển đổi media','ffprobe':'Đọc thông tin media',
         'yt-dlp':'Tải theo connector hỗ trợ','gallery-dl':'Tải theo connector hỗ trợ',
         'chrome':'Phiên trình duyệt nếu workflow cần'}
REASONS = {'MISSING':'Chưa thấy trong phạm vi quét',
           'NOT_EXAMINED':'Chưa kiểm tra hết / chưa quét',
           'INVALID_EXPLICIT_PATH':'Đường dẫn chỉ định không hợp lệ; KHÔNG thay thế',
           'NEEDS_CHECK':'Có tệp; CHƯA xác minh phiên bản/chức năng/tin cậy'}


class InventoryWorker(QThread):
    def __init__(self,configured,extra,include_system,parent=None):
        super().__init__(parent);self.configured=dict(configured);self.extra=extra
        self.include_system=include_system;self.result=None;self.failed=False;self.observed_at=None
    def run(self):
        try:
            roots=system_search_dirs() if self.include_system else ()
            self.result=discover_tools(configured=self.configured,system_dirs=roots,
                extra_dirs=(Path(self.extra),) if self.extra else (),
                cancel=self.isInterruptionRequested,max_checks=256,timeout=3)
            self.observed_at=datetime.now(timezone.utc).isoformat(timespec='seconds')
        except Exception:self.failed=True  # no raw OS paths/messages in status diagnostics


class ToolInventoryPanel(QWidget):
    idle=Signal()
    def __init__(self,parent=None,*,preferences_path=None,shortcut_registry=None):
        super().__init__(parent);self.worker=None;self.worker_revision=None;self.stopping=False;self.revision=0
        self.shortcut_registry=shortcut_registry or ShortcutRegistry(self)
        self.preferences_path=preferences_path;self.preference_worker=None;self.preference_revision=None
        self.saved_snapshot=None;self.saved_revision=None;self.uncertain_save=None
        self.first_open_attempted=False;self.navigation_generation=0
        layout=QVBoxLayout(self)
        notice=QLabel('Danh sách 5 công cụ thực thi — chỉ đọc tên/tệp, KHÔNG chạy/cài/cập nhật. '
            'Chỉ Lưu rõ ràng mới ghi đường dẫn; đọc lại không quét/chạy hay cấp tin cậy. Font/runtime/model và registry kích hoạt còn chưa tích hợp.')
        notice.setWordWrap(True);notice.setTextFormat(Qt.PlainText);layout.addWidget(notice)
        form=QFormLayout();self.paths={}
        for tool in TOOL_NAMES:
            field=QLineEdit();field.setMaxLength(32767)
            field.setPlaceholderText('Đường dẫn tuyệt đối tùy chọn; để trống mới tìm trong thư mục quét')
            self.paths[tool]=field;form.addRow(tool,field)
            field.textChanged.connect(self.invalidate)
        self.extra=QLineEdit();self.extra.setMaxLength(32767)
        self.extra.setPlaceholderText('Một thư mục bổ sung tuyệt đối, không quét đệ quy')
        self.extra.textChanged.connect(self.invalidate);form.addRow('Thư mục bổ sung',self.extra)
        layout.addLayout(form)
        self.system=QCheckBox('Đọc PATH hiện tại và thư mục Chrome phổ biến; không thay đổi PATH')
        self.system.setChecked(True);self.system.toggled.connect(self.invalidate);layout.addWidget(self.system)
        row=QHBoxLayout();self.scan_button=QPushButton('Quét tên tệp (không chạy công cụ)')
        self.cancel_button=QPushButton('Dừng quét');row.addWidget(self.scan_button);row.addWidget(self.cancel_button)
        self.scan_button.clicked.connect(self.start);self.cancel_button.clicked.connect(self.cancel);layout.addLayout(row)
        self.message=QLabel('Chưa quét. Thiếu công cụ không ngăn mở Cài đặt.')
        self.message.setWordWrap(True);self.message.setTextFormat(Qt.PlainText);layout.addWidget(self.message)
        self.table=QTableWidget(len(TOOL_NAMES),8)
        self.table.setHorizontalHeaderLabels(['Công cụ','Vai trò','Đường dẫn được đề xuất','Nguồn tìm',
            'Phiên bản','Kiến trúc','Trạng thái / lý do','Thời điểm quan sát UTC'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(180);layout.addWidget(self.table)
        self.scan_shortcut_router=ShortcutEventRouter(
            self.shortcut_registry,(('tools.rescan',self.start),),self,
        )
        for owner in (self.table,self.table.viewport()):
            owner.installEventFilter(self.scan_shortcut_router)
        self.table.setToolTip('F5 quét lại tên tệp trong bảng công cụ; không chạy hoặc cấp tin cậy cho executable.')
        self.candidates=QPlainTextEdit();self.candidates.setReadOnly(True)
        self.candidates.document().setMaximumBlockCount(1024);self.candidates.setMaximumHeight(110)
        layout.addWidget(self.candidates)
        preferences=QHBoxLayout();self.load_button=QPushButton('Đọc cấu hình đã lưu')
        self.save_button=QPushButton('Lưu đường dẫn / phạm vi quét')
        self.load_button.clicked.connect(self.load_saved);self.save_button.clicked.connect(self.save_current)
        preferences.addWidget(self.load_button);preferences.addWidget(self.save_button);layout.addLayout(preferences)
        self.preference_message=QLabel('Chưa đọc cấu hình; đường dẫn đang sửa chỉ thuộc phiên này.')
        self.preference_message.setWordWrap(True);self.preference_message.setTextFormat(Qt.PlainText)
        layout.addWidget(self.preference_message);self.clear_rows();self.update_actions()
    @property
    def busy(self):return self.worker is not None or self.preference_worker is not None
    def clear_rows(self):
        for row,tool in enumerate(TOOL_NAMES):
            self._row(row,[tool,ROLES[tool],'—','—','Chưa biết','Chưa biết',REASONS['NOT_EXAMINED'],'—'])
        self.candidates.clear()
    def _row(self,row,values):
        for col,value in enumerate(values):
            item=QTableWidgetItem(value);item.setToolTip(value);self.table.setItem(row,col,item)
    def invalidate(self,*_):
        self.revision+=1
        if hasattr(self,'table'):
            self.clear_rows();self.message.setText('Đầu vào thay đổi; kết quả trước không áp dụng. Quét lại khi sẵn sàng.')
        if hasattr(self,'preference_message'):
            self.preference_message.setText('Đường dẫn đã sửa; chưa lưu. Không đổi snapshot của tác vụ đã xếp hàng.')
            self.update_actions()
    def update_actions(self):
        available=not self.busy and not self.stopping
        for field in (*self.paths.values(),self.extra,self.system,self.scan_button):field.setEnabled(available)
        active=self.worker or self.preference_worker
        self.cancel_button.setEnabled(bool(active) and not self.stopping and not active.isInterruptionRequested())
        self.load_button.setEnabled(available and self.preferences_path is not None)
        self.save_button.setEnabled(available and self.preferences_path is not None and self.saved_snapshot is not None and self.uncertain_save is None)
    def start(self):
        self.navigation_generation+=1
        if self.busy or self.stopping:return
        configured={tool:field.text() for tool,field in self.paths.items() if field.text()}
        extra=self.extra.text()
        if extra and not Path(extra).is_absolute():
            self.message.setText('Thư mục bổ sung phải tuyệt đối; không dùng thư mục hiện hành.');return
        worker=InventoryWorker(configured,extra,self.system.isChecked(),self)
        revision=self.revision;self.worker=worker;self.worker_revision=revision;self.clear_rows()
        worker.finished.connect(self._inventory_worker_finished,Qt.ConnectionType.QueuedConnection)
        self.message.setText('Đang đọc metadata, tối đa 256 kiểm tra/3 giây giữa thao tác; I/O hệ điều hành có thể chậm hơn.')
        self.update_actions();worker.start()
    def _inventory_worker_finished(self):
        # A bound QObject slot plus QueuedConnection guarantees UI mutation on
        # the panel's GUI thread, never on the QThread that emitted finished.
        worker=self.worker
        if worker is not None:self._finished(worker,self.worker_revision)
    def _finished(self,worker,revision):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,self,lambda:self._finished(worker,revision));return
        if revision!=self.revision:
            self.clear_rows();self.message.setText('Đầu vào thay đổi khi đang quét; bỏ kết quả cũ, không tự quét lại.')
        elif worker.failed or worker.result is None:
            self.clear_rows();self.message.setText('Không hoàn tất quét. Kiểm tra phạm vi/đường dẫn; không tự thay thế hoặc thử lại.')
        else:
            result=worker.result
            for row,selection in enumerate(result.selections):
                candidate=selection.candidate
                reason=REASONS.get(selection.state,'Trạng thái chưa xác định')
                if candidate and candidate.link_or_reparse:reason+='; liên kết/reparse chưa xác minh'
                self._row(row,[selection.tool,ROLES[selection.tool],candidate.path if candidate else '—',
                    candidate.source if candidate else '—','Chưa biết','Chưa biết',reason,worker.observed_at])
            lines=['Tối đa 64 ứng viên, đường dẫn dài rút gọn; bảng trên giữ đường dẫn đề xuất đầy đủ.']
            lines.extend(f'{x.tool} | {x.source} | {x.path[:512]}'+('…' if len(x.path)>512 else '')+
                f' | {x.size} bytes | {x.readiness}' for x in result.candidates[:64])
            self.candidates.setPlainText('\n'.join(lines))
            self.message.setText(f'{result.status}: đã xem {result.examined} tên tệp. '
                'Không có công cụ nào được xác nhận READY; nguồn tìm không chứng minh sở hữu/tin cậy. '+', '.join(result.diagnostics))
        self.worker=None;self.worker_revision=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        self.navigation_generation+=1
        active=self.worker or self.preference_worker
        if active is not None:
            active.requestInterruption();self.message.setText('Đã yêu cầu dừng; chờ thao tác đọc đang chạy kết thúc.');self.update_actions()
    def first_open(self):
        # One attempt per panel, before dispatch: error/cancel never silently rearms.
        if self.first_open_attempted:return
        self.first_open_attempted=True;self.navigation_generation+=1
        if self.busy or self.stopping or self.preferences_path is None or self.uncertain_save is not None:return
        generation=self.navigation_generation
        self._preferences_start(PreferenceWorker(self.preferences_path,parent=self),auto_generation=generation)
    def _first_scan(self,generation,revision,expected):
        if (self.busy or self.stopping or self.uncertain_save is not None or
            generation!=self.navigation_generation or revision!=self.revision):return
        current=(tuple(self.paths[t].text() for t in TOOL_NAMES),self.extra.text(),self.system.isChecked())
        if current!=(expected.paths,expected.extra,expected.include_system):return
        self.start() # metadata only; never enters selected-pair execution/trust path
    def load_saved(self):
        self.navigation_generation+=1
        if self.busy or self.stopping or self.preferences_path is None:return
        self._preferences_start(PreferenceWorker(self.preferences_path,parent=self))
    def save_current(self):
        self.navigation_generation+=1
        if self.busy or self.stopping or self.saved_snapshot is None or self.uncertain_save is not None:return
        try:value=ToolPreferences(tuple(self.paths[t].text() for t in TOOL_NAMES),self.extra.text(),self.system.isChecked())
        except ValueError:
            self.preference_message.setText('Chỉ lưu đường dẫn tuyệt đối hoặc rỗng, không NUL, tối đa 32768 byte mỗi mục.');return
        self._preferences_start(PreferenceWorker(self.preferences_path,value=value,expected=self.saved_snapshot,parent=self))
    def _preferences_start(self,worker,auto_generation=None):
        revision=self.revision;worker.auto_generation=auto_generation;self.preference_worker=worker;self.preference_revision=revision
        worker.finished.connect(self._preferences_worker_finished,Qt.ConnectionType.QueuedConnection)
        self.preference_message.setText('Đang đọc/lưu cấu hình trên worker; không chạy công cụ. I/O có thể cần chờ.')
        self.update_actions();worker.start()
    def _preferences_worker_finished(self):
        # Keep all QWidget and Project/UI state updates on the GUI thread.
        worker=self.preference_worker
        if worker is not None:self._preferences_finished(worker,self.preference_revision)
    def _preferences_finished(self,worker,revision):
        if self.preference_worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,self,lambda:self._preferences_finished(worker,revision));return
        auto_generation=worker.auto_generation
        auto_eligible=(auto_generation is not None and auto_generation==self.navigation_generation and
            revision==self.revision and not self.stopping and not worker.isInterruptionRequested() and
            self.uncertain_save is None and worker.value is None and not worker.failed and worker.result is not None)
        # Safety state survives stale input revisions and close/cancel requests.
        if worker.unknown:self.uncertain_save=(worker.expected,worker.value)
        if worker.failed or worker.result is None:
            self.preference_message.setText('Chưa xác nhận lưu; KHÔNG thử ghi lại. Đọc lại để đối chiếu.' if self.uncertain_save else
                'Không đọc/lưu được cấu hình; không thay thế tệp. Đọc lại trước khi lưu; quét thủ công vẫn dùng được.')
            self.saved_snapshot=None
        else:
            result=worker.result
            if self.uncertain_save is not None:
                if worker.value is None and reconciles(result,*self.uncertain_save):self.uncertain_save=None
            if self.uncertain_save is not None:
                self.saved_snapshot=None
                self.preference_message.setText('Chưa đối chiếu được lần ghi không rõ kết quả với cùng store; giữ khóa ghi, không tự nhận store khác.')
            elif revision!=self.revision:
                self.saved_snapshot=result
                self.preference_message.setText('Đọc/lưu xong bản đã chụp; giữ nguyên các sửa mới chưa lưu, không thay trường đang hiển thị.')
            elif worker.value is None:
                self.saved_snapshot=result
                for key,value in zip(TOOL_NAMES,result.value.paths):self.paths[key].setText(value)
                self.extra.setText(result.value.extra);self.system.setChecked(result.value.include_system)
                self.saved_revision=self.revision
                self.preference_message.setText(f'Đã đọc phiên bản {result.version}; chưa quét/xác minh/tin cậy. Lưu mới thay đổi cấu hình.')
            else:
                self.saved_snapshot=result;self.saved_revision=revision
                self.preference_message.setText(f'Đã lưu phiên bản {result.version}. Không thực thi/READY/kích hoạt, không đổi tác vụ cũ.')
        applied=worker.result
        self.preference_worker=None;self.preference_revision=None;worker.deleteLater();self.update_actions();self.idle.emit()
        if auto_eligible and self.saved_snapshot==applied:
            applied_revision=self.revision;expected=applied.value
            QTimer.singleShot(0,self,lambda:self._first_scan(auto_generation,applied_revision,expected))
    def request_stop(self):self.stopping=True;self.cancel();self.update_actions()
    def closeEvent(self,event):
        self.request_stop()
        if self.busy:event.ignore()
        else:super().closeEvent(event)
