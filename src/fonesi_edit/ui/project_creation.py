"""Real empty-project creation; output intent is not a renderer readiness claim."""
from fractions import Fraction
from pathlib import Path
from PySide6.QtCore import QThread,Signal,QTimer,Qt
from PySide6.QtWidgets import QWidget,QDialog,QVBoxLayout,QFormLayout,QLineEdit,QSpinBox,QLabel,QPushButton,QHBoxLayout,QFileDialog
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project,create_project_file,CreationCanceled,CreationUnknown
from fonesi_edit.storage.projects import ConflictError


class CreationWorker(QThread):
    def __init__(self,path,project,parent=None):
        super().__init__(parent);self.path=path;self.project=project;self.result=None;self.outcome='UNKNOWN'
    def run(self):
        try:
            self.result=create_project_file(self.path,self.project,cancel=self.isInterruptionRequested)
            self.outcome='CREATED'
        except CreationCanceled:self.outcome='CANCELED_BEFORE_WRITE'
        except ConflictError:self.outcome='CONFLICT'
        except Exception:self.outcome='UNKNOWN'


class NewProjectPanel(QWidget):
    idle=Signal()
    def __init__(self,get_session,activate,parent=None):
        super().__init__(parent);self.get_session=get_session;self.activate=activate
        self.worker=None;self.stopping=False;self.uncertain=False;self.cancel_requested=False
        layout=QVBoxLayout(self);form=QFormLayout()
        self.name=QLineEdit('Dự án mới');self.name.setMaxLength(200);form.addRow('Tên dự án trắng',self.name)
        self.path=QLineEdit();self.path.setMaxLength(32767);self.path.setPlaceholderText('Tệp JSON mới, đường dẫn tuyệt đối; không ghi đè')
        pathrow=QHBoxLayout();pathrow.addWidget(self.path);self.choose=QPushButton('Chọn nơi tạo…');pathrow.addWidget(self.choose)
        self.choose.clicked.connect(self.choose_path);form.addRow('Tệp mới',pathrow)
        self.width=self._number(2,16384,1920,2);self.height=self._number(2,16384,1080,2)
        self.fps_num=self._number(1,1000000,30);self.fps_den=self._number(1,1000000,1)
        self.duration_num=self._number(1,1000000,10);self.duration_den=self._number(1,1000000,1)
        for label,widget in [('Rộng (px)',self.width),('Cao (px)',self.height),('FPS tử số',self.fps_num),('FPS mẫu số',self.fps_den),('Thời lượng giây: tử số',self.duration_num),('Thời lượng: mẫu số',self.duration_den)]:form.addRow(label,widget)
        layout.addLayout(form)
        notice=QLabel('Tạo cấu trúc trống, không có media/timeline/render. Ý định đầu ra ban đầu: MP4/H.264/AAC, yuv420p/BT.709, 48 kHz stereo; CHƯA xác minh codec. Kích thước phải chẵn. Seed 0, không preset.')
        notice.setTextFormat(Qt.PlainText);notice.setWordWrap(True);layout.addWidget(notice)
        row=QHBoxLayout();self.button=QPushButton('Tạo tệp mới và mở dự án');self.cancel_button=QPushButton('Dừng / không mở kết quả')
        row.addWidget(self.button);row.addWidget(self.cancel_button);layout.addLayout(row)
        self.button.clicked.connect(self.start);self.cancel_button.clicked.connect(self.cancel)
        self.message=QLabel('Chưa tạo tệp. Hủy sau khi tệp đã tạo sẽ giữ tệp, không tự xóa.')
        self.message.setWordWrap(True);self.message.setTextFormat(Qt.PlainText);layout.addWidget(self.message)
        self.update_actions()
    def _number(self,low,high,value,step=1):
        widget=QSpinBox();widget.setRange(low,high);widget.setValue(value);widget.setSingleStep(step);return widget
    @property
    def busy(self):return self.worker is not None
    def update_actions(self):
        available=not self.busy and not self.stopping and not self.uncertain
        for widget in (self.name,self.path,self.choose,self.width,self.height,self.fps_num,self.fps_den,self.duration_num,self.duration_den,self.button):widget.setEnabled(available)
        self.cancel_button.setEnabled(self.busy and not self.stopping and not self.worker.isInterruptionRequested())
    def choose_path(self):
        if self.busy or self.stopping or self.uncertain:return
        path,_=QFileDialog.getSaveFileName(self,'Chọn tệp dự án MỚI — không ghi đè','','Dự án (*.json);;Tất cả (*)')
        if path:self.path.setText(path)
    def start(self):
        if self.busy or self.stopping or self.uncertain:return
        try:
            path=Path(self.path.text())
            if not path.is_absolute() or '\0' in str(path):raise ValueError
            project=empty_project(NewProjectIntent(self.name.text(),self.width.value(),self.height.value(),
                Fraction(self.fps_num.value(),self.fps_den.value()),Fraction(self.duration_num.value(),self.duration_den.value())))
        except (ValueError,TypeError):
            self.message.setText('Tên, đường dẫn tuyệt đối, kích thước chẵn và thời gian hữu tỉ dương cần hợp lệ. Chưa ghi tệp.');return
        session=self.get_session();revision=None if session is None else session.revision
        worker=CreationWorker(path,project,self);self.worker=worker;self.cancel_requested=False
        worker.finished.connect(lambda:self._finished(worker,session,revision))
        self.message.setText('Đang tạo tệp mới; nếu hủy sau khi ghi, tệp được giữ lại và không tự mở.')
        self.update_actions();worker.start()
    def _finished(self,worker,session,revision):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,lambda:self._finished(worker,session,revision));return
        if worker.outcome=='UNKNOWN':
            self.uncertain=True;self.message.setText('Chưa xác nhận kết quả tạo; giữ dự án đang mở. Không thử tạo lại. Kiểm tra tệp và dùng Mở dự án để đối chiếu.')
        elif worker.result is not None:
            current=self.get_session()
            if (self.stopping or self.cancel_requested or current is not session or
                (current is not None and current.revision!=revision)):
                self.message.setText('Tệp mới đã tạo, giữ nguyên trên ổ đĩa; không mở vì đã hủy/đóng hoặc dự án hiện tại thay đổi.')
            else:
                try:self.activate(worker.result,session,revision)
                except Exception:self.message.setText('Tệp đã tạo nhưng không mở được trạng thái đã xác nhận; giữ dự án cũ. Mở tệp rõ ràng để đối chiếu, không tạo lại.')
                else:self.message.setText('Đã tạo và mở dự án trắng. Chưa có media, timeline hoặc bộ dựng/xuất.')
        elif worker.outcome=='CONFLICT':self.message.setText('Tên tệp đã có/đang dùng hoặc xung đột; không ghi đè. Chọn tên mới.')
        else:self.message.setText('Đã hủy trước khi vào bộ ghi; không tạo dự án.')
        self.worker=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        if self.worker is not None:
            self.cancel_requested=True;self.worker.requestInterruption();self.message.setText('Đã yêu cầu dừng; chờ bộ ghi xác nhận. Không xóa tệp đã tạo.');self.update_actions()
    def request_stop(self):self.stopping=True;self.cancel();self.update_actions()
    def closeEvent(self,event):
        self.request_stop()
        if self.busy:event.ignore()
        else:super().closeEvent(event)


class NewProjectDialog(QDialog):
    """Modeless editor for creation intent; closing waits, never destroys a writer."""
    def __init__(self,get_session,activate,parent=None):
        super().__init__(parent);self.setWindowTitle('Tạo dự án trắng');self.close_requested=False
        layout=QVBoxLayout(self);self.panel=NewProjectPanel(get_session,activate,self);layout.addWidget(self.panel)
        self.panel.idle.connect(self._idle)
    def open_panel(self):
        if self.panel.stopping:return
        self.close_requested=False;self.show();self.raise_()
    def _idle(self):
        if self.close_requested and not self.panel.busy:self.hide()
    def reject(self):self.close()
    def closeEvent(self,event):
        self.close_requested=True
        if self.panel.busy:self.panel.cancel();event.ignore()
        else:event.accept();self.hide()
