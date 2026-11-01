"""Explicit read-only observations, not a timeline or trusted tool registry."""
from pathlib import Path
from PySide6.QtCore import QThread,Signal,QTimer,Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,
    QPushButton,QCheckBox,QSpinBox,QPlainTextEdit,QFileDialog)
from fonesi_edit.media.probe import inspect_media,ProbeCanceled
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.media.frames import observe_frames
from fonesi_edit.media.retirement import ValidationLifecycle


class InspectionWorker(QThread):
    def __init__(self,source,tool,frame_stream,parent=None):
        super().__init__(parent);self.source=Path(source);self.tool=Path(tool);self.frame_stream=frame_stream
        self.observation=None;self.frames=None;self.outcome='UNKNOWN';self.retired=False
    def run(self):
        operation=object();lifecycle=ValidationLifecycle(operation)
        try:
            with lifecycle.validation_body():
                raw=inspect_media(self.source,self.tool,cancel=self.isInterruptionRequested,_lifecycle=lifecycle)
                self.observation=normalize_probe(raw)
                if self.frame_stream is not None:
                    self.frames=observe_frames(self.source,self.tool,self.observation,self.frame_stream,
                                              cancel=self.isInterruptionRequested,_lifecycle=lifecycle)
            self.outcome='OBSERVED'
        except ProbeCanceled:self.outcome='CANCELED'
        except Exception:self.outcome='REFUSED'
        finally:
            self.retired=(lifecycle.confirmed_for(operation) and
                (self.outcome!='OBSERVED' or len(lifecycle.mechanisms)==(2 if self.frame_stream is not None else 1)))


def describe(observation,frames):
    lines=['Quan sát thông tin — KHÔNG xác nhận media hợp lệ hoặc đủ điều kiện dựng/xuất.',
           f'SHA256: {observation.sha256}',f'Thời lượng container: {observation.container_duration}',
           'Chẩn đoán container: '+', '.join(observation.diagnostics)]
    for s in observation.streams:
        lines += [f'Luồng {s.index}: {s.kind}, codec={s.codec}; ảnh bìa={s.attached_picture}',
                  f'  time_base={s.time_base}; start={s.start} ({s.start_basis}); duration={s.duration} ({s.duration_basis})',
                  f'  {s.width}x{s.height}; SAR={s.sar}; xoay={s.rotation_degrees} ({s.rotation_basis}); matrix={s.display_matrix}',
                  f'  âm thanh: rate={s.sample_rate}; channels={s.channels}; layout={s.channel_layout}',
                  '  '+', '.join(s.diagnostics)]
    if frames is not None:
        lines += [f'Frame: {frames.status}; {len(frames.frames)} record giữ lại; chỉ hiển thị tối đa64.',
                  'EOF chỉ là kết thúc lệnh/JSON, không chứng minh đầy đủ frame hợp lệ.',
                  ', '.join(frames.diagnostics)]
        for index,f in enumerate(frames.frames[:64]):
            lines.append(f'  #{index}: pts={f.pts}; best_effort={f.best_effort_timestamp}; duration={f.duration}; pkt_duration={f.packet_duration}; '+','.join(f.diagnostics))
    lines.append('None = chưa biết/chưa quan sát; không tự thay bằng0, stereo hoặc CFR.')
    return '\n'.join(lines)


class InspectionPanel(QWidget):
    idle=Signal()
    def __init__(self,parent=None):
        super().__init__(parent);self.worker=None;self.stopping=False;self.revoked=False
        layout=QVBoxLayout(self)
        self.source=QLineEdit();self.source.setPlaceholderText('Tệp media tuyệt đối — chỉ đọc')
        self.tool=QLineEdit();self.tool.setPlaceholderText('ffprobe tuyệt đối do bạn tin cậy — không tự tìm/thay thế')
        self.source_button=QPushButton('Chọn media…');self.source_button.clicked.connect(self.choose_source)
        self.tool_button=QPushButton('Chọn ffprobe…');self.tool_button.clicked.connect(self.choose_tool)
        for field,button in ((self.source,self.source_button),(self.tool,self.tool_button)):
            row=QHBoxLayout();row.addWidget(field);row.addWidget(button);layout.addLayout(row)
        self.trust=QCheckBox('Tôi tin cậy tệp công cụ đã chọn; kiểm tra sẽ chạy chương trình này.')
        self.with_frames=QCheckBox('Quan sát frame của luồng video có chỉ số toàn cục:')
        self.stream=QSpinBox();self.stream.setRange(0,2147483647)
        row=QHBoxLayout();row.addWidget(self.with_frames);row.addWidget(self.stream)
        layout.addWidget(self.trust);layout.addLayout(row)
        self.button=QPushButton('Kiểm tra bằng ffprobe đã chọn');self.button.clicked.connect(self.start)
        self.cancel_button=QPushButton('Yêu cầu dừng kiểm tra');self.cancel_button.clicked.connect(self.cancel)
        layout.addWidget(self.button);layout.addWidget(self.cancel_button)
        self.message=QLabel('Chỉ quan sát nguồn. Chưa thêm vào dự án/timeline; chưa dựng hoặc xuất.')
        self.message.setTextFormat(Qt.PlainText);self.message.setWordWrap(True);layout.addWidget(self.message)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.document().setMaximumBlockCount(2000);layout.addWidget(self.output)
        self.tool.textChanged.connect(lambda _:self.trust.setChecked(False))
        for signal in (self.source.textChanged,self.tool.textChanged,self.trust.toggled,self.with_frames.toggled):signal.connect(self.update_actions)
        self.update_actions()
    @property
    def busy(self):return self.worker is not None
    def update_actions(self,*_):
        available=not self.busy and not self.stopping and not self.revoked
        for widget in (self.source,self.tool,self.source_button,self.tool_button,self.trust,self.with_frames):widget.setEnabled(available)
        self.stream.setEnabled(available and self.with_frames.isChecked())
        self.button.setEnabled(available and self.trust.isChecked() and bool(self.source.text()) and bool(self.tool.text()))
        self.cancel_button.setEnabled(self.busy and not self.stopping and not self.worker.isInterruptionRequested())
    def choose_source(self):
        if self.busy or self.stopping or self.revoked:return
        path,_=QFileDialog.getOpenFileName(self,'Chọn media chỉ đọc')
        if path:self.source.setText(path)
    def choose_tool(self):
        if self.busy or self.stopping or self.revoked:return
        path,_=QFileDialog.getOpenFileName(self,'Chọn ffprobe mà bạn tin cậy; chương trình này sẽ được chạy')
        if path:self.tool.setText(path)
    def start(self):
        if self.busy or self.stopping or self.revoked or not self.trust.isChecked():return
        source=Path(self.source.text());tool=Path(self.tool.text())
        if not source.is_absolute() or not tool.is_absolute():
            self.message.setText('Cần đường dẫn tuyệt đối; không dùng thư mục hiện hành hoặc công cụ thay thế.');return
        worker=InspectionWorker(source,tool,self.stream.value() if self.with_frames.isChecked() else None,self)
        self.worker=worker;self.output.clear()
        worker.finished.connect(lambda:self._finished(worker))
        self.message.setText('Đang đọc/hash/probe nguồn; tổng thời gian chưa biết, không tạo phần trăm giả.')
        self.update_actions();worker.start()
    def _finished(self,worker):
        if self.worker is not worker:return
        if not worker.wait(0):QTimer.singleShot(10,lambda:self._finished(worker));return
        if not worker.retired:
            self.revoked=True;self.output.clear()
            self.message.setText('Chưa xác nhận toàn bộ tiến trình đã dừng. Khóa kiểm tra tiếp; không tự thử lại/dọn tệp.')
        elif worker.outcome=='OBSERVED' and worker.observation is not None:
            self.output.setPlainText(describe(worker.observation,worker.frames))
            self.message.setText('Đã nhận quan sát, KHÔNG xác nhận đủ điều kiện dựng/xuất. Dự án không thay đổi.')
        elif worker.outcome=='CANCELED':self.message.setText('Đã dừng kiểm tra và xác nhận tiến trình do ứng dụng tạo đã dừng; dự án không thay đổi.')
        else:self.message.setText('Chưa nhận quan sát hợp lệ; kiểm tra nguồn/công cụ đã chọn. Không tự thử lại hoặc thay công cụ.')
        self.worker=None;worker.deleteLater();self.update_actions();self.idle.emit()
    def cancel(self):
        if self.worker is not None:
            self.worker.requestInterruption();self.message.setText('Đã yêu cầu dừng; chờ luồng và tiến trình sở hữu nghỉ an toàn.');self.update_actions()
    def request_stop(self):self.stopping=True;self.cancel();self.update_actions()
