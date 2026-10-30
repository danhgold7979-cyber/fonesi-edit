"""Real but deliberately limited native desktop rebuild slice."""
from fractions import Fraction
from pathlib import Path
import shutil
import sys
import threading
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QPushButton,QLabel,QListWidget,QSplitter,QFileDialog,QProgressBar,QTabBar,QDoubleSpinBox,QFormLayout)
from fonesi_edit.media import probe
from fonesi_edit.process import run_bounded
from fonesi_edit.render import render_cpu
from fonesi_edit.timing import ClipMap, Interval


class Worker(QThread):
    result=Signal(object)
    failure=Signal(str)
    def __init__(self, operation):
        super().__init__();self.operation=operation;self.cancel=threading.Event()
    def run(self):
        try:self.result.emit(self.operation(self.cancel))
        except Exception as exc:
            # No raw exception/path/provider data in the diagnostic status.
            code=str(exc) if isinstance(exc,ValueError) and str(exc).replace('_','').isalnum() else type(exc).__name__
            self.failure.emit(code[:100])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.worker=None;self.selected=None;self.media=[];self.closing=False;self.edits={};self._loading_controls=False
        self.ffmpeg=shutil.which('ffmpeg');self.ffprobe=shutil.which('ffprobe')
        self.setWindowTitle('Fonesi Edit · Bản xây lại đang phát triển');self.resize(1280,800)
        root=QWidget();self.setCentralWidget(root);layout=QVBoxLayout(root);layout.setContentsMargins(20,16,20,16);layout.setSpacing(14)
        head=QHBoxLayout();title=QLabel('FONESI EDIT');title.setObjectName('brand');head.addWidget(title);head.addStretch()
        head.addWidget(QLabel('Bản phát triển · Chưa nghiệm thu toàn bộ'));layout.addLayout(head)
        tabs=QTabBar();tabs.setExpanding(False)
        for name in ['Tổng quan','Tải nội dung','Phụ đề','Editor','Edit hàng loạt','Ghép theo cảnh','Hàng đợi','Cài đặt']:
            tabs.addTab(name)
        for i in range(tabs.count()):
            if i!=3: tabs.setTabEnabled(i,False);tabs.setTabToolTip(i,'Chưa nối chức năng trong lát cắt rebuild này')
        tabs.setCurrentIndex(3);layout.addWidget(tabs)
        controls=QHBoxLayout();self.add=QPushButton('Thêm media…');self.export=QPushButton('Xuất thử MP4 CPU…');self.cancel_button=QPushButton('Hủy tác vụ')
        self.add.clicked.connect(self.choose_source);self.export.clicked.connect(self.choose_output);self.cancel_button.clicked.connect(self.cancel_work)
        controls.addWidget(self.add);controls.addWidget(self.export);controls.addStretch();controls.addWidget(self.cancel_button);layout.addLayout(controls)
        panes=QSplitter();layout.addWidget(panes,1)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('MEDIA CỤC BỘ'));self.list=QListWidget();ll.addWidget(self.list);panes.addWidget(left)
        center=QWidget();cl=QVBoxLayout(center);cl.addWidget(QLabel('KHUNG HÌNH NGUỒN · chưa áp hiệu ứng'))
        self.preview=QLabel('Thêm một video để kiểm tra nội dung.\nNguồn gốc luôn được giữ nguyên.');self.preview.setObjectName('preview');self.preview.setAlignment(Qt.AlignCenter);self.preview.setMinimumSize(480,320);cl.addWidget(self.preview,1)
        cl.addWidget(QLabel('Hiện có: probe thật, khung đầu và xuất CPU.\nTimeline, phụ đề, layer và chuyển động chưa được nối.'));panes.addWidget(center)
        right=QWidget();rl=QVBoxLayout(right);rl.addWidget(QLabel('THUỘC TÍNH NGUỒN'));self.details=QLabel('Chưa chọn media');self.details.setWordWrap(True);rl.addWidget(self.details)
        form=QFormLayout();self.start_time=QDoubleSpinBox();self.end_time=QDoubleSpinBox();self.speed=QDoubleSpinBox()
        for control in (self.start_time,self.end_time):control.setDecimals(6);control.setRange(0,31536000);control.setSuffix(' s')
        self.speed.setDecimals(3);self.speed.setRange(.5,2);self.speed.setValue(1);self.speed.setSingleStep(.1);self.speed.setSuffix(' ×')
        form.addRow('Bắt đầu',self.start_time);form.addRow('Kết thúc',self.end_time);form.addRow('Tốc độ',self.speed);rl.addLayout(form)
        for control in (self.start_time,self.end_time,self.speed):control.valueChanged.connect(self.changed_edit)
        rl.addStretch()
        rl.addWidget(QLabel('Trim/tốc độ áp dụng khi xuất.\nKhung nguồn không phải preview hiệu ứng.\nKhông ghi đè tệp đã có.'));panes.addWidget(right);panes.setSizes([220,760,260])
        self.progress=QProgressBar();self.progress.setTextVisible(False);layout.addWidget(self.progress)
        self.status=QLabel('Sẵn sàng · Chọn media cục bộ.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.list.currentRowChanged.connect(self.select_row)
        self.setStyleSheet('''QWidget{background:#111827;color:#f1f5f9;font-size:13px;} QLabel#brand{font-size:24px;color:#c4b5fd;font-weight:600;}
QPushButton{background:#28364d;border:1px solid #52617c;padding:9px 14px;border-radius:5px;} QPushButton:hover{background:#3c4764;} QPushButton:focus{border:2px solid #c4b5fd;} QPushButton:disabled{color:#8b97aa;background:#1f2937;}
QListWidget,QLabel#preview{background:#0b1220;border:1px solid #38445b;} QListWidget::item{padding:10px;} QListWidget::item:selected{background:#554582;} QTabBar::tab{padding:10px 14px;background:#1f2937;} QTabBar::tab:selected{background:#554582;} QTabBar::tab:disabled{color:#8b97aa;} QProgressBar{background:#1f2937;border:0;height:5px;} QProgressBar::chunk{background:#a78bfa;}''')
        self.refresh()
        if not self.ffmpeg or not self.ffprobe:self.status.setText('Thiếu FFmpeg/ffprobe. Cài công cụ đáng tin cậy rồi mở lại; không tự cài hoặc đổi PATH.')

    def refresh(self):
        busy=self.worker is not None
        self.add.setEnabled(not busy and bool(self.ffmpeg and self.ffprobe));self.export.setEnabled(not busy and self.selected is not None and 'video' in self.selected[1].stream_types)
        for control in (self.start_time,self.end_time,self.speed):control.setEnabled(not busy and self.selected is not None)
        if self.selected is not None and (self.start_time.value()>=self.end_time.value() or Fraction(str(self.end_time.value()))>self.selected[1].duration):self.export.setEnabled(False)
        self.cancel_button.setEnabled(busy);self.list.setEnabled(not busy);self.progress.setRange(0,0 if busy else 1)
        if not busy:self.progress.setValue(0)
    def start(self, operation, on_result):
        if self.worker is not None:return False
        worker=Worker(operation);self.worker=worker
        worker.result.connect(on_result);worker.failure.connect(lambda code:self.status.setText('Tác vụ không hoàn tất: '+code+'. Nguồn vẫn giữ nguyên.'))
        worker.finished.connect(self.finished_work);self.refresh();worker.start();return True
    def finished_work(self):
        worker=self.worker;self.worker=None
        if worker:worker.deleteLater()
        self.refresh()
        if self.closing:self.close()
    def cancel_work(self):
        if self.worker:self.worker.cancel.set();self.status.setText('Đang yêu cầu hủy; chờ tiến trình dừng an toàn…')
    def choose_source(self):
        path,_=QFileDialog.getOpenFileName(self,'Chọn media nguồn','','Media (*.mp4 *.mkv *.mov *.avi *.webm *.wav *.mp3);;Tất cả (*)')
        if path:self.load_source(Path(path))
    def load_source(self,path):
        if not self.ffmpeg or not self.ffprobe:return False
        def work(cancel):
            info=probe(path,Path(self.ffprobe),cancel=cancel);thumbnail=b''
            if 'video' in info.stream_types:
                result=run_bounded([self.ffmpeg,'-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(path.resolve()),'-frames:v','1','-vf','scale=640:-2','-f','image2pipe','-vcodec','png','-'],limit=1048576,cancel=cancel)
                if result.status!='OK':raise ValueError('PREVIEW_'+result.status)
                thumbnail=result.stdout
            if cancel.is_set():raise ValueError('CANCELED')
            return path,info,thumbnail
        self.status.setText('Đang kiểm tra media và đọc khung hình…')
        return self.start(work,self.loaded)
    def loaded(self,result):
        self.media.append(result);self.list.addItem(result[0].name);self.list.setCurrentRow(len(self.media)-1)
        self.status.setText('Đã đọc nguồn. Đây là khung nguồn, chưa có hiệu ứng.');self.select_row(len(self.media)-1)
    def select_row(self,row):
        if not 0<=row<len(self.media):return
        self.selected=self.media[row];path,info,data=self.selected
        self._loading_controls=True
        values=self.edits.get(row,(0,(info.duration.numerator*1000000//info.duration.denominator)/1000000,1))
        for control,value in zip((self.start_time,self.end_time,self.speed),values):control.setValue(value)
        self._loading_controls=False
        self.details.setText(f'{path.name}\n\nThời lượng: {float(info.duration):.3f} s\nTrack: {", ".join(info.stream_types)}')
        if data:
            pixmap=QPixmap();pixmap.loadFromData(data);self.preview.setPixmap(pixmap.scaled(640,480,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        else:self.preview.setText('Tệp âm thanh · chưa có phát nghe trong lát cắt này')
        self.refresh()
    def changed_edit(self):
        if self._loading_controls or self.selected is None:return
        self.edits[self.list.currentRow()]=(self.start_time.value(),self.end_time.value(),self.speed.value())
        self.status.setText('Thiết lập xuất đã đổi. Khung đang xem vẫn là nguồn, chưa áp trim/tốc độ.')
        self.refresh()
    def choose_output(self):
        if not self.selected:return
        path,_=QFileDialog.getSaveFileName(self,'Chọn tên đầu ra mới',self.selected[0].stem+'-edit.mp4','MP4 (*.mp4)')
        if path:self.export_to(Path(path))
    def export_to(self,destination):
        if not self.selected or self.worker:return False
        source=self.selected[0]
        mapping=None
        if self.list.currentRow() in self.edits:
            try:mapping=ClipMap(Interval(Fraction(str(self.start_time.value())),Fraction(str(self.end_time.value()))),Fraction(str(self.speed.value())))
            except ValueError:self.status.setText('Khoảng trim không hợp lệ: kết thúc phải lớn hơn bắt đầu.');return False
        self.status.setText('Đang xuất thử CPU và giải mã kiểm tra; chưa biết % chính xác…')
        # Provisional developer proof tolerance, not a general editor acceptance gate.
        return self.start(lambda cancel:render_cpu(source,destination,Path(self.ffmpeg),Path(self.ffprobe),duration_tolerance=Fraction(1,10),cancel=cancel,clip_map=mapping),
            lambda artifact:self.status.setText(f'Đã kiểm tra đầu ra: {artifact.path.name} · {artifact.size:,} bytes.'))
    def closeEvent(self,event):
        if self.worker:
            self.closing=True;self.cancel_work();event.ignore()
        else:event.accept()


def main():
    app=QApplication.instance() or QApplication(sys.argv);window=MainWindow();window.show();return app.exec()

if __name__=='__main__':raise SystemExit(main())
