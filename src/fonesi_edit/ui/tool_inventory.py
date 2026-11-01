"""Visible metadata-only executable inventory; never a trust/activation resolver."""
from datetime import datetime, timezone
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QFormLayout,QLineEdit,QLabel,
    QCheckBox,QPushButton,QHBoxLayout,QTableWidget,QTableWidgetItem,QPlainTextEdit,
    QAbstractItemView)
from fonesi_edit.dependencies.discovery import discover_tools,system_search_dirs,TOOL_NAMES

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
    def __init__(self,parent=None):
        super().__init__(parent);self.worker=None;self.stopping=False;self.revision=0
        layout=QVBoxLayout(self)
        notice=QLabel('Danh sách 5 công cụ thực thi — chỉ đọc tên/tệp, KHÔNG chạy/cài/cập nhật. '
            'Đường dẫn thử trong phiên này chưa lưu thành cấu hình. Font/runtime/model và registry kích hoạt còn chưa tích hợp.')
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
        self.candidates=QPlainTextEdit();self.candidates.setReadOnly(True)
        self.candidates.document().setMaximumBlockCount(1024);self.candidates.setMaximumHeight(110)
        layout.addWidget(self.candidates);self.clear_rows();self.update_actions()
    @property
    def busy(self):return self.worker is not None
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
    def update_actions(self):
        available=not self.busy and not self.stopping
        for field in (*self.paths.values(),self.extra,self.system,self.scan_button):field.setEnabled(available)
        self.cancel_button.setEnabled(self.busy and not self.stopping and not self.worker.isInterruptionRequested())
    def start(self):
        if self.busy or self.stopping:return
        configured={tool:field.text() for tool,field in self.paths.items() if field.text()}
        extra=self.extra.text()
        if extra and not Path(extra).is_absolute():
            self.message.setText('Thư mục bổ sung phải tuyệt đối; không dùng thư mục hiện hành.');return
        worker=InventoryWorker(configured,extra,self.system.isChecked(),self)
        revision=self.revision;self.worker=worker;self.clear_rows()
        worker.finished.connect(lambda:self._finished(worker,revision))
        self.message.setText('Đang đọc metadata, tối đa 256 kiểm tra/3 giây giữa thao tác; I/O hệ điều hành có thể chậm hơn.')
        self.update_actions();worker.start()
    def _finished(self,worker,revision):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,lambda:self._finished(worker,revision));return
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
        self.worker=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        if self.worker is not None:
            self.worker.requestInterruption();self.message.setText('Đã yêu cầu dừng; chờ thao tác đọc đang chạy kết thúc.');self.update_actions()
    def request_stop(self):self.stopping=True;self.cancel();self.update_actions()
    def closeEvent(self,event):
        self.request_stop()
        if self.busy:event.ignore()
        else:super().closeEvent(event)
