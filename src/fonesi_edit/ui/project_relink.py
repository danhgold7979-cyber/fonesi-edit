"""Owned background root verification; commits remain on the GUI/store owner thread."""
from PySide6.QtCore import QThread,Signal,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFileDialog,QInputDialog
from fonesi_edit.storage.relink import relink_root
from fonesi_edit.media.probe import ProbeCanceled


class RelinkWorker(QThread):
    verified=Signal(object)
    refused=Signal(str)
    progress=Signal(int,int)
    def __init__(self,project,base,old_root,new_root,parent=None):
        super().__init__(parent);self.project=project;self.base=base;self.old_root=old_root;self.new_root=new_root
    def run(self):
        try:
            command=relink_root(self.project,self.old_root,self.new_root,project_base=self.base,
                                cancel=self.isInterruptionRequested,progress=self.progress.emit)
            self.verified.emit(command)
        except ProbeCanceled:self.refused.emit('Đã hủy kiểm tra; chưa đổi dự án.')
        except Exception:self.refused.emit('Không thể khớp đầy đủ nội dung. Không đổi dự án hay tệp nguồn.')


class RelinkPanel(QWidget):
    idle=Signal()
    state_changed=Signal()
    project_changed=Signal()
    def __init__(self,get_session,parent=None):
        super().__init__(parent);self.get_session=get_session;self.worker=None;self.target=None;self.stopping=False;self.canceled=False;self.commit_attempted=False
        layout=QVBoxLayout(self)
        self.button=QPushButton('Liên kết lại media theo thư mục gốc…');self.button.clicked.connect(self.choose)
        self.cancel_button=QPushButton('Hủy kiểm tra liên kết');self.cancel_button.clicked.connect(self.cancel)
        self.message=QLabel('Chỉ liên kết tệp có nội dung khớp; không thay thế nguồn khác nội dung.')
        self.message.setTextFormat(Qt.PlainText);self.message.setWordWrap(True)
        layout.addWidget(self.button);layout.addWidget(self.cancel_button);layout.addWidget(self.message)
        self.update_actions()
    @property
    def busy(self):return self.worker is not None
    def update_actions(self):
        session=self.get_session()
        self.button.setEnabled(session is not None and not session.reconciliation_required and not self.busy and not self.stopping)
        self.cancel_button.setEnabled(self.busy and not self.stopping)
    def choose(self):
        session=self.get_session()
        if session is None or self.busy or self.stopping:return
        old,ok=QInputDialog.getText(self,'Thư mục gốc cũ','Đường dẫn tuyệt đối của gốc media cũ (có thể đã di chuyển):',text=str(session.project_base))
        if not ok:return
        new=QFileDialog.getExistingDirectory(self,'Chọn thư mục gốc mới')
        if not new:return
        if self.get_session() is not session:
            self.message.setText('Dự án đã đổi trong lúc chọn thư mục; chọn lại cho dự án hiện tại.');return
        self.start(old,new)
    def start(self,old_root,new_root):
        session=self.get_session()
        if session is None or session.reconciliation_required or self.busy or self.stopping:return
        self.target=session;self.canceled=False;self.commit_attempted=False
        self.worker=RelinkWorker(session.project,session.project_base,old_root,new_root,self)
        self.worker.verified.connect(self._verified);self.worker.refused.connect(self.message.setText)
        self.worker.progress.connect(self._progress);self.worker.finished.connect(self._finished)
        self.message.setText('Đang xác minh nội dung; chưa thay đổi dự án…')
        self.update_actions();self.state_changed.emit();self.worker.start()
    def _progress(self,done,total):
        if not self.stopping and not self.canceled:self.message.setText(f'Đã xác minh {done}/{total} tệp tham chiếu; chưa áp dụng dự án.')
    def _verified(self,command):
        if self.worker is None or self.stopping or self.canceled or self.worker.isInterruptionRequested():return
        if self.get_session() is not self.target:
            self.message.setText('Dự án đang mở đã đổi; bỏ kết quả cũ.');return
        self.commit_attempted=True
        try:self.target.commit(command)
        except Exception:
            self.message.setText('Chưa xác nhận áp dụng liên kết. Giữ mô hình hiện tại; kiểm tra bản tự lưu trước khi thử lại.')
        else:
            self.message.setText('Đã áp dụng và tự lưu liên kết. Bấm Lưu dự án để cập nhật tệp dự án.')
            self.project_changed.emit()
        self.state_changed.emit()
    def _finished(self):
        if self.worker is not None and not self.worker.wait(0):
            QTimer.singleShot(10,self._finished);return
        old=self.worker;self.worker=None;self.target=None
        if self.canceled and not self.commit_attempted:self.message.setText('Đã hủy kiểm tra; chưa đổi dự án.')
        if old is not None:old.deleteLater()
        self.update_actions();self.state_changed.emit();self.idle.emit()
    def cancel(self):
        if self.worker is not None:
            self.canceled=True;self.worker.requestInterruption()
    def request_stop(self):
        self.stopping=True;self.cancel();self.update_actions()
