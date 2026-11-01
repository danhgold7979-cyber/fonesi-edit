"""Explicit selected-pair self-test observations, never installation/activation."""
from pathlib import Path
from datetime import datetime,timezone
import stat
from PySide6.QtCore import QThread,Signal,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QLineEdit,QCheckBox,QPushButton,QLabel,QPlainTextEdit
from fonesi_edit.dependencies.checks import ToolPin,check_pair,ToolCheckCanceled
from fonesi_edit.dependencies.retirement import PairRetirement
from fonesi_edit.dependencies.fixture import materialize_fixture,SHA256,EXPECTED
from fonesi_edit.media.probe import fingerprint,ProbeCanceled


class PairWorker(QThread):
    def __init__(self,ffmpeg,ffprobe,root,parent=None):
        super().__init__(parent);self.ffmpeg=Path(ffmpeg);self.ffprobe=Path(ffprobe);self.root=Path(root)
        self.result=None;self.retired=False;self.outcome='UNKNOWN';self.fixture=None;self.observed_at=None;self.mechanisms=()
    def run(self):
        operation=object();receipt=PairRetirement(operation);entered=False
        try:
            pins=[]
            for name,path in (('ffmpeg',self.ffmpeg),('ffprobe',self.ffprobe)):
                info=path.lstat()
                if not path.is_absolute() or not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400 or not 0<info.st_size<=1024**3:
                    raise ValueError('Bounded regular explicit tool required')
                pins.append(ToolPin(name,path,fingerprint(path,self.isInterruptionRequested)))
            if self.isInterruptionRequested():raise ToolCheckCanceled('Canceled before fixture')
            self.fixture=materialize_fixture(self.root)
            entered=True  # Register delegate boundary before check_pair can launch.
            self.result=check_pair(*pins,self.fixture,SHA256,EXPECTED,cancel=self.isInterruptionRequested,_retirement=receipt)
            self.observed_at=datetime.now(timezone.utc).isoformat(timespec='seconds')
            self.outcome='OBSERVED'
        except (ToolCheckCanceled,ProbeCanceled):self.outcome='CANCELED'
        except BaseException:self.outcome='REFUSED'
        finally:
            self.retired=(not entered or receipt.confirmed_for(operation))
            if self.outcome=='OBSERVED':self.retired=self.retired and receipt.complete_for(operation)
            self.mechanisms=receipt.mechanisms


class PairCheckPanel(QWidget):
    idle=Signal()
    def __init__(self,fixture_root,parent=None):
        super().__init__(parent);self.fixture_root=Path(fixture_root)
        self.worker=None;self.revision=0;self.stopping=False;self.revoked=False
        layout=QVBoxLayout(self);form=QFormLayout()
        self.ffmpeg=QLineEdit();self.ffprobe=QLineEdit()
        for name,field in (('FFmpeg',self.ffmpeg),('ffprobe',self.ffprobe)):
            field.setMaxLength(32767);field.setPlaceholderText('Đường dẫn tuyệt đối do bạn chọn và tin cậy')
            form.addRow(name,field);field.textChanged.connect(self.invalidate)
        layout.addLayout(form)
        self.trust=QCheckBox('Tôi tin cậy CẢ HAI chương trình và DLL/phụ thuộc cùng thư mục; cho phép chạy self-test.')
        layout.addWidget(self.trust)
        self.start_button=QPushButton('Chạy kiểm tra cặp đã chọn với media tổng hợp')
        self.cancel_button=QPushButton('Dừng self-test')
        self.start_button.clicked.connect(self.start);self.cancel_button.clicked.connect(self.cancel)
        self.trust.toggled.connect(self.update_actions);layout.addWidget(self.start_button);layout.addWidget(self.cancel_button)
        self.message=QLabel('Không tự dùng ứng viên từ danh sách. Không cài, tải, đổi PATH hoặc kích hoạt registry. '
            'Self-test giữ lại tệp tổng hợp riêng 2478 byte; chưa tự dọn. EXE hash không xác minh toàn bộ DLL.')
        self.message.setWordWrap(True);self.message.setTextFormat(Qt.PlainText);layout.addWidget(self.message)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setMaximumHeight(150)
        self.output.document().setMaximumBlockCount(40);layout.addWidget(self.output);self.update_actions()
    @property
    def busy(self):return self.worker is not None
    def invalidate(self,*_):
        self.revision+=1
        if hasattr(self,'trust'):self.trust.setChecked(False)
        if hasattr(self,'output'):
            self.output.clear();self.message.setText('Đường dẫn thay đổi; kết quả trước không áp dụng. Cần xác nhận tin cậy lại.')
        if hasattr(self,'start_button'):self.update_actions()
    def update_actions(self,*_):
        available=not self.busy and not self.stopping and not self.revoked
        for field in (self.ffmpeg,self.ffprobe,self.trust):field.setEnabled(available)
        self.start_button.setEnabled(available and self.trust.isChecked() and bool(self.ffmpeg.text()) and bool(self.ffprobe.text()))
        self.cancel_button.setEnabled(self.busy and not self.stopping and not self.worker.isInterruptionRequested())
    def start(self):
        if self.busy or self.stopping or self.revoked or not self.trust.isChecked():return
        left=Path(self.ffmpeg.text());right=Path(self.ffprobe.text())
        if not left.is_absolute() or not right.is_absolute():
            self.message.setText('Cần hai đường dẫn tuyệt đối; không tìm/thay thế công cụ khác.');return
        worker=PairWorker(left,right,self.fixture_root,self);revision=self.revision
        self.worker=worker;self.output.clear();worker.finished.connect(lambda:self._finished(worker,revision))
        self.message.setText('Đang hash cả hai công cụ rồi kiểm tra phiên bản/media tổng hợp; không tạo phần trăm giả.')
        self.update_actions();worker.start()
    def _finished(self,worker,revision):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,lambda:self._finished(worker,revision));return
        # Safety state is never discarded merely because the displayed inputs changed.
        if not worker.retired:
            self.revoked=True;self.output.clear()
            self.message.setText('Chưa chứng minh mọi tiến trình đã dừng. Khóa chạy lại; không tự thử lại/dọn tệp.')
        elif revision!=self.revision:
            self.output.clear();self.message.setText('Đầu vào đã đổi; không áp dụng kết quả cũ. Không tự chạy lại.')
        elif worker.outcome=='OBSERVED' and worker.result is not None:
            result=worker.result
            lines=[f'Quan sát lúc {worker.observed_at}; KHÔNG cấp lease/READY cho mọi workflow.',
                   f'FFmpeg: {result.ffmpeg.path}',f'SHA256: {result.ffmpeg.sha256}',
                   f'ffprobe: {result.ffprobe.path}',f'SHA256: {result.ffprobe.sha256}',
                   f'Phiên bản cặp: {result.ffmpeg_version.version}',
                   'Chỉ fixture MPEG4 48×32/5fps/1s và frame đen RGB16; chưa kiểm tra GPU/codec khác.',
                   f'Fixture SHA256: {result.fixture_sha256}',f'Phạm vi: {result.scope}',
                   f'Đã nghỉ: {", ".join(worker.mechanisms)}']
            self.output.setPlainText('\n'.join(lines))
            self.message.setText('Self-test cặp cụ thể đạt; EXE/DLL có thể đổi sau thời điểm này. Chưa kích hoạt/cấp lease.')
        elif worker.outcome=='CANCELED':self.message.setText('Đã dừng self-test và xác nhận các tiến trình đã khởi chạy đều nghỉ; không có kết quả READY.')
        else:self.message.setText('Cặp chưa đạt kiểm tra; không tự thay thế, kích hoạt hoặc thử lại. Tệp tổng hợp nếu đã tạo được giữ lại.')
        self.worker=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        if self.worker is not None:self.worker.requestInterruption();self.update_actions()
    def request_stop(self):self.stopping=True;self.cancel();self.update_actions()
    def closeEvent(self,event):
        self.request_stop()
        if self.busy:event.ignore()
        else:super().closeEvent(event)
