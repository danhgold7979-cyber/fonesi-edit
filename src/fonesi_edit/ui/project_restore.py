"""Explicit new-store backup import; never switches the active GUI store."""
from pathlib import Path
import time
from PySide6.QtCore import QThread,Signal,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFileDialog
from fonesi_edit.storage.restore import restore_project_backup,RestoreError


class RestoreWorker(QThread):
    copied=Signal(object)
    def __init__(self,source,destination,parent=None):
        super().__init__(parent);self.source=Path(source);self.destination=Path(destination)
        self.result=None;self.outcome='UNKNOWN';self.ownership_unknown=False;self.destination_created=False
    def run(self):
        last=0.
        def progress(done,total):
            nonlocal last
            now=time.monotonic()
            if now-last>=.1 or done==total:
                last=now;self.copied.emit((done,total))
        try:
            self.result=restore_project_backup(self.source,self.destination,
                        cancel=self.isInterruptionRequested,progress=progress)
        except RestoreError as exc:
            self.destination_created=exc.destination_created;self.ownership_unknown=exc.ownership_unknown
            self.outcome='REFUSED'
        except Exception:
            # A non-domain failure still cannot authorize retry/removal.
            self.outcome='UNKNOWN'
        else:self.outcome='CONFIRMED'


class RestorePanel(QWidget):
    idle=Signal()
    def __init__(self,parent=None):
        super().__init__(parent);self.worker=None;self.stopping=False
        layout=QVBoxLayout(self)
        self.button=QPushButton('Khôi phục bản sao vào kho mới…');self.button.clicked.connect(self.choose)
        self.cancel_button=QPushButton('Yêu cầu dừng khôi phục');self.cancel_button.clicked.connect(self.cancel)
        self.message=QLabel('Không ghi đè hoặc chuyển kho đang mở. Chỉ nhập bản sao offline vào tệp mới.')
        self.message.setTextFormat(Qt.PlainText);self.message.setWordWrap(True)
        layout.addWidget(self.button);layout.addWidget(self.cancel_button);layout.addWidget(self.message)
        self.update_actions()
    @property
    def busy(self):return self.worker is not None
    def update_actions(self):
        self.button.setEnabled(not self.busy and not self.stopping)
        self.cancel_button.setEnabled(self.busy and not self.stopping and not self.worker.isInterruptionRequested())
    def choose(self):
        if self.busy or self.stopping:return
        source,_=QFileDialog.getOpenFileName(self,'Chọn bản sao dự án offline','','Bản sao SQLite (*);;Tất cả (*)')
        if not source:return
        directory=QFileDialog.getExistingDirectory(self,'Chọn thư mục chứa kho MỚI projects.sqlite3 — không ghi đè')
        if directory:self.start(source,Path(directory)/'projects.sqlite3')
    def start(self,source,destination):
        if self.busy or self.stopping:return
        self.worker=RestoreWorker(source,destination,self)
        worker=self.worker
        worker.copied.connect(lambda value:self._copied(worker,value));worker.finished.connect(lambda:self._finished(worker))
        self.message.setText('Đang sao chép và xác minh bản sao; chưa xác nhận kho mới.')
        self.update_actions();self.worker.start()
    def _copied(self,worker,value):
        if self.worker is not worker or self.stopping or self.worker.isInterruptionRequested():return
        done,total=value
        self.message.setText(f'Đã sao chép {done}/{total} byte; còn xác minh dữ liệu và quyền sở hữu, chưa hoàn tất.')
    def _finished(self,worker):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,lambda:self._finished(worker));return
        if worker.outcome=='CONFIRMED' and worker.result is not None:
            self.message.setText(f'Đã xác nhận kho mới với {worker.result.project_count} dự án. '
                'Kho đang mở không thay đổi. Khởi động riêng với --data-dir trỏ tới thư mục chứa projects.sqlite3 để sử dụng bản phục hồi.')
        elif worker.outcome=='REFUSED' and not worker.destination_created:
            self.message.setText('Không tạo kho mới. Kiểm tra bản sao offline và đường dẫn đích chưa tồn tại; kho đang mở không thay đổi.')
        else:
            self.message.setText('Chưa xác nhận khôi phục. Tệp đích/bằng chứng quyền sở hữu có thể còn lại; '
                'không tự thử lại hoặc xóa. Kho đang mở không thay đổi.')
        self.worker=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        if self.worker is not None:
            self.worker.requestInterruption()
            self.message.setText('Đã yêu cầu dừng; chờ kết quả thực tế. Tệp mới có thể đã được tạo, không tự xóa/thử lại.')
            self.update_actions()
    def request_stop(self):
        self.stopping=True;self.cancel();self.update_actions()
