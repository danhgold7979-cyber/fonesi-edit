from pathlib import Path
import copy
from PIL import Image
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QListWidget,QFormLayout,QDoubleSpinBox,QPushButton,QLineEdit,QComboBox,QCheckBox,QFileDialog,QLabel,QSlider,QScrollArea
from ..core.model import Layer,Keyframe,US,uid,Project
from .canvas import Canvas
from .timeline import Timeline

class Editor(QWidget):
    changed=Signal();preview_requested=Signal(object);position_requested=Signal(object);play_requested=Signal();proxy_requested=Signal();audio_requested=Signal();clip_settings_requested=Signal();preset_requested=Signal()
    def __init__(self,project,history,parent=None):
        super().__init__(parent);self.project=project;self.history=history;self.busy=False
        layout=QVBoxLayout(self);toolbar=QHBoxLayout();layout.addLayout(toolbar)
        self.play_button=QPushButton('▶ Phát / dừng');self.play_button.clicked.connect(self.play_requested.emit);toolbar.addWidget(self.play_button)
        proxy_button=QPushButton('Tạo lại proxy');proxy_button.clicked.connect(self.proxy_requested.emit);toolbar.addWidget(proxy_button)
        for label,callback in [('＋ Chữ',self.add_text),('＋ Logo',self.add_logo),('＋ Vùng che',self.add_mask),('＋ Audio',self.audio_requested.emit),('Clip / Audio',self.clip_settings_requested.emit),('Nhân bản',self.duplicate),('Undo',self.undo),('Redo',self.redo),('Frame xuất chuẩn',lambda:self.preview_requested.emit(self.canvas.time))]:
            b=QPushButton(label);b.clicked.connect(callback);toolbar.addWidget(b)
        split=QSplitter();layout.addWidget(split,1);self.layers=QListWidget();self.layers.setMaximumWidth(200);split.addWidget(self.layers)
        self.canvas=Canvas(project,history);split.addWidget(self.canvas);panel=QWidget();form=QFormLayout(panel);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(panel);scroll.setMinimumWidth(250);scroll.setMaximumWidth(330);split.addWidget(scroll)
        self.fields={}
        for key,title,low,high,step in [('x','X (% khung)',-200,200,1),('y','Y (% khung)',-200,200,1),('width','Rộng (%)',1,400,1),('height','Cao (%)',1,400,1),('rotation','Góc (°)',-3600,3600,1),('opacity','Opacity (%)',0,100,1)]:
            field=QDoubleSpinBox();field.setRange(low,high);field.setDecimals(2);field.setSingleStep(step);form.addRow(title,field);self.fields[key]=field;field.editingFinished.connect(lambda k=key:self.numeric_changed(k))
        self.text=QLineEdit();form.addRow('Nội dung',self.text);self.text.editingFinished.connect(self.text_changed)
        self.font_size=QDoubleSpinBox();self.font_size.setRange(6,400);form.addRow('Cỡ chữ (px)',self.font_size);self.font_size.editingFinished.connect(self.font_changed)
        self.lock=QCheckBox('Khóa đối tượng');form.addRow(self.lock);self.lock.clicked.connect(self.lock_changed)
        self.visible=QCheckBox('Hiện đối tượng');form.addRow(self.visible);self.visible.clicked.connect(self.visible_changed)
        self.record=QCheckBox('Ghi keyframe tại playhead');form.addRow(self.record)
        self.snap=QCheckBox('Snap / vùng an toàn');self.snap.setChecked(True);form.addRow(self.snap);self.snap.clicked.connect(self.snap_changed)
        self.zoom=QComboBox();self.zoom.addItems(['Fit','25%','50%','100%','200%']);form.addRow('Zoom preview',self.zoom);self.zoom.currentIndexChanged.connect(self.zoom_changed)
        for label,callback in [('Đưa vào khung',self.keep_inside),('Lên layer',lambda:self.reorder(1)),('Xuống layer',lambda:self.reorder(-1)),('Chọn font TTF/OTF',self.choose_font)]:
            b=QPushButton(label);b.clicked.connect(callback);form.addRow(b)
        notice=QLabel('Preview kéo thả dùng CPU. “Frame xuất chuẩn” chạy cùng đường render, có thể hủy khi đổi dự án. Thuộc tính chưa hỗ trợ không được bỏ qua khi xuất.');notice.setWordWrap(True);form.addRow(notice)

        from ..services.motion import PRESETS
        self.motion_preset=QComboBox();self.motion_preset.addItems(PRESETS);form.addRow('Chuyển động',self.motion_preset)
        self.motion_duration=QDoubleSpinBox();self.motion_duration.setRange(.01,10000);self.motion_duration.setValue(2);form.addRow('Một vòng (s)',self.motion_duration)
        self.motion_repeat=QDoubleSpinBox();self.motion_repeat.setRange(1,100);self.motion_repeat.setDecimals(0);self.motion_repeat.setValue(1);form.addRow('Số vòng',self.motion_repeat)
        self.motion_easing=QComboBox();self.motion_easing.addItems(['linear','ease-in','ease-out','ease-in-out']);form.addRow('Easing',self.motion_easing)
        b=QPushButton('Áp chuyển động (seed project)');b.clicked.connect(self.apply_motion);form.addRow(b)
        b=QPushButton('Preset: nhập/xuất/copy nhóm');b.clicked.connect(self.preset_requested.emit);form.addRow(b)
        self.timeline=Timeline(project,history);layout.addWidget(self.timeline)
        self.scrub=QSlider(Qt.Orientation.Horizontal);layout.addWidget(self.scrub);self.scrub.valueChanged.connect(lambda ms:self.seek(ms*1000))
        self.canvas.changed.connect(self.refresh);self.canvas.selected.connect(self.select_id);self.layers.currentRowChanged.connect(self.select_row)
        self.timeline.changed.connect(self.refresh);self.timeline.seek.connect(self.seek);self.refresh()

    def current(self):return next((l for l in self.project.layers if l.id in self.canvas.selection),None)
    def mutate(self,label,callback):
        self.history.begin();callback();self.history.commit(label);self.canvas.reference=None;self.refresh()
    def add_text(self):self.mutate('add text',lambda:self.project.layers.append(Layer(end=max(US,self.project.duration),z=len(self.project.layers),text='Nội dung',height=.2,style={'font_size':max(16,self.project.height//20),'overflow':'shrink','fill':'#ffffff','stroke':'#000000','stroke_width':2})))
    def add_logo(self):
        path,_=QFileDialog.getOpenFileName(self,'Chọn logo','','Images (*.png *.jpg *.jpeg *.webp)')
        if path:self.mutate('add logo',lambda:self.project.layers.append(Layer(kind='logo',name=Path(path).name,asset_path=path,end=max(US,self.project.duration),width=.2,height=.2,z=len(self.project.layers),style={})))
    def add_mask(self):self.mutate('add mask',lambda:self.project.layers.append(Layer(kind='mask',name='Vùng che',end=max(US,self.project.duration),z=-1,style={'mask_mode':'blur','blur_radius':12})))
    def duplicate(self):
        l=self.current()
        if l:
            new=copy.deepcopy(l);new.id=uid();new.x+=.03;new.y+=.03;new.locked=False;self.mutate('duplicate',lambda:self.project.layers.append(new))
    def apply_motion(self):
        layer=self.current()
        if not layer or layer.locked:return
        from ..services.motion import motion
        try:
            keys=motion(layer,self.motion_preset.currentText(),duration=round(self.motion_duration.value()*US),repeat=int(self.motion_repeat.value()),easing=self.motion_easing.currentText(),seed=self.project.seed)
            self.mutate('motion preset',lambda:setattr(layer,'keyframes',keys))
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self,'Chuyển động',str(exc))
    def undo(self):self.history.undo();self.refresh()
    def redo(self):self.history.redo();self.refresh()
    def select_id(self,identity):
        self.refresh()  # Canvas already applied Shift multi-selection; never collapse it here.
    def select_row(self,index):
        if self.busy or index<0 or index>=len(self.project.layers):return
        self.canvas.selection={self.project.layers[index].id};self.refresh()
    def numeric_changed(self,key):
        l=self.current()
        if self.busy or l is None or l.locked:return
        value=self.fields[key].value()/(1 if key=='rotation' else 100)
        def set_value():
            if self.record.isChecked():
                keys=l.keyframes.setdefault(key,[]);t=max(0,self.canvas.time-l.start);keys[:]=[k for k in keys if k.time!=t];keys.append(Keyframe(t,value))
            else:setattr(l,key,value)
        self.mutate('property '+key,set_value)
    def text_changed(self):
        l=self.current()
        if not self.busy and l and not l.locked:self.mutate('text',lambda:setattr(l,'text',self.text.text()))
    def font_changed(self):
        l=self.current()
        if not self.busy and l and not l.locked:self.mutate('font size',lambda:l.style.update(font_size=int(self.font_size.value())))
    def lock_changed(self):
        l=self.current()
        if l:self.mutate('lock',lambda:setattr(l,'locked',self.lock.isChecked()))
    def visible_changed(self):
        l=self.current()
        if l:self.mutate('visibility',lambda:setattr(l,'visible',self.visible.isChecked()))
    def snap_changed(self):self.canvas.snap=self.snap.isChecked();self.canvas.grid=self.snap.isChecked();self.canvas.update()
    def zoom_changed(self,index):self.canvas.zoom=[1,.25,.5,1,2][index];self.canvas.update()
    def keep_inside(self):
        l=self.current()
        if l and not l.locked:self.mutate('keep inside',lambda:(setattr(l,'x',max(0,min(1-l.width,l.x))),setattr(l,'y',max(0,min(1-l.height,l.y)))))
    def reorder(self,delta):
        l=self.current()
        if l:self.mutate('order',lambda:setattr(l,'z',l.z+delta))
    def choose_font(self):
        l=self.current()
        if not l or l.locked:return
        path,_=QFileDialog.getOpenFileName(self,'Chọn font','','Font (*.ttf *.otf)')
        if path:self.mutate('font',lambda:l.style.update(font_path=path))
    def seek(self,value):
        self.display_time(value);self.position_requested.emit(int(value))
    def display_time(self,value):
        self.canvas.time=int(value);self.timeline.time=int(value);self.canvas.reference=None;self.canvas.update();self.timeline.update();self.scrub.blockSignals(True);self.scrub.setValue(round(value/1000));self.scrub.blockSignals(False)
    def refresh(self):
        self.busy=True;self.layers.clear();self.layers.addItems([('🔒 ' if l.locked else '')+l.name for l in self.project.layers]);l=self.current()
        if l:
            for key,field in self.fields.items():field.setValue(getattr(l,key)*(1 if key=='rotation' else 100));field.setEnabled(not l.locked)
            self.text.setText(l.text);self.font_size.setValue(l.style.get('font_size',40));self.lock.setChecked(l.locked);self.visible.setChecked(l.visible)
        self.scrub.setRange(0,max(1,round(self.project.duration/1000)));self.canvas.update();self.timeline.update();self.busy=False;self.changed.emit()
