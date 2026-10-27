from copy import deepcopy
from dataclasses import asdict,replace
from pathlib import Path
from uuid import uuid4
import tempfile

from PySide6.QtCore import Qt,QUrl,Signal
from PySide6.QtGui import QUndoCommand,QUndoStack,QColor,QKeySequence,QAction,QFont
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QSplitter,QFormLayout,QLineEdit,QPlainTextEdit,
    QDoubleSpinBox,QSpinBox,QComboBox,QCheckBox,QPushButton,QListWidget,QLabel,QTabWidget,QFileDialog,QColorDialog,QScrollArea,QToolBar,QMenu,QFontComboBox)

from ..domain import Composition,Clip,Layer,identifier
from ..prototypes.media import probe,extract_frame
from .canvas import Canvas
from .timeline import Timeline,clip_positions


class Snapshot(QUndoCommand):
    def __init__(self,editor,before,after,name):
        super().__init__(name);self.editor,self.before,self.after=editor,before,after
    def undo(self): self.editor.set_composition(Composition.from_dict(self.before))
    def redo(self): self.editor.set_composition(Composition.from_dict(self.after))


class Editor(QWidget):
    changed=Signal()
    render_requested=Signal(dict)

    def __init__(self,host):
        super().__init__();self.host=host
        self.composition=Composition();self.selected_id=None;self.frame=None;self._before=None;self._loading=False
        self.undo=QUndoStack(self);self.undo.setUndoLimit(100)
        layout=QVBoxLayout(self);toolbar=QToolBar();layout.addWidget(toolbar)
        actions=[('Thêm video',self.add_video),('Chữ',lambda:self.add_layer('text')),('Logo',lambda:self.add_layer('image')),
                 ('Vùng che',lambda:self.add_layer('mask')),('Nhân bản',self.duplicate),('Xóa layer',self.delete_layer),
                 ('Undo',self.undo.undo),('Redo',self.undo.redo),('Chia clip',self.split),('Render',self.request_render)]
        for label,callback in actions:
            action=toolbar.addAction(label);action.triggered.connect(lambda checked=False,callback=callback:callback())
        toolbar.addAction('Đầu ra',lambda:self.output_dialog());toolbar.addAction('Âm thanh',lambda:self.audio_dialog())
        self.scope=QComboBox();self.scope.addItems(['Clip hiện tại','Các clip đã chọn','Preset cả lô']);toolbar.addWidget(self.scope)
        self.scope.currentIndexChanged.connect(self.change_scope)
        split=QSplitter();layout.addWidget(split,1)
        assets=QWidget();left=QVBoxLayout(assets);self.clips=QListWidget();self.layers=QListWidget()
        self.clips.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left.addWidget(QLabel('Media'));left.addWidget(self.clips);left.addWidget(QLabel('Layers'));left.addWidget(self.layers)
        self.layers.currentRowChanged.connect(self.select_row)
        layer_buttons=QHBoxLayout();left.addLayout(layer_buttons)
        for label,delta in [('Lên',1),('Xuống',-1)]:
            b=QPushButton(label);b.clicked.connect(lambda _,d=delta:self.reorder(d));layer_buttons.addWidget(b)
        split.addWidget(assets)
        center=QWidget();middle=QVBoxLayout(center);self.views=QTabWidget();middle.addWidget(self.views,1)
        self.canvas=Canvas(self);self.canvas.selected.connect(self.select_id);self.views.addTab(self.canvas,'Bố cục')
        self.video=QVideoWidget();self.views.addTab(self.video,'Playback / render tham chiếu')
        self.player=QMediaPlayer(self);self.audio=QAudioOutput(self);self.player.setAudioOutput(self.audio);self.player.setVideoOutput(self.video)
        self.player.errorOccurred.connect(lambda _,error:self.host.message(error))
        controls=QHBoxLayout();middle.addLayout(controls)
        play=QPushButton('Phát / dừng');play.clicked.connect(self.toggle_play);controls.addWidget(play)
        ref=QPushButton('Preview chất lượng xuất');ref.clicked.connect(self.reference);controls.addWidget(ref)
        self.frame_label=QLabel('');controls.addWidget(self.frame_label)
        self.timeline=Timeline(self);self.timeline.seek.connect(lambda t:self.player.setPosition(round(t*1000)));middle.addWidget(self.timeline)
        self.player.positionChanged.connect(lambda milliseconds:self.timeline.position(milliseconds/1000))
        split.addWidget(center)
        self.inspector=QTabWidget();split.addWidget(self.inspector);self.fields={}
        self.build_inspector();split.setSizes([170,740,300])
        self.refresh()

    def build_inspector(self):
        transform=QWidget();form=QFormLayout(transform)
        self.add_field(form,'name','Tên','str')
        for key,label,lo,hi in [('x','X / rộng',0,1),('y','Y / cao',0,1),('width','Rộng / khung',.01,2),('height','Cao / khung',.01,2),
                               ('rotation','Xoay °',-360,360),('opacity','Độ rõ',0,1),('start','Bắt đầu s',0,100000),('end','Kết thúc s (0=cuối)',0,100000)]:
            self.add_field(form,key,label,'number',lo,hi)
        self.add_field(form,'visible','Hiển thị','bool');self.add_field(form,'locked','Khóa chỉnh tự động','bool')
        self.inspector.addTab(transform,'Vị trí')
        style=QWidget();form=QFormLayout(style)
        for key,label,kind in [('text','Nội dung','str'),('style.font_family','Font','font'),('style.color','Màu HEX','str'),
                               ('style.outline_color','Viền HEX','str'),('style.background','Nền HEX','str')]:self.add_field(form,key,label,kind)
        for key,label,lo,hi in [('font_size','Cỡ chữ',8,300),('outline','Viền px',0,20),('line_spacing','Giãn dòng',0,100),
                               ('shadow','Bóng px',0,30),('padding','Padding',0,100)]:self.add_field(form,'style.'+key,label,'number',lo,hi)
        for key,label in [('bold','Đậm'),('italic','Nghiêng'),('underline','Gạch chân')]:self.add_field(form,'style.'+key,label,'bool')
        self.add_field(form,'style.align','Căn chữ','choice',options=['left','center','right'])
        self.add_field(form,'style.mode','Kiểu vùng che','choice',options=['blur','mosaic','color'])
        for key,label,lo,hi in [('radius','Cường độ blur',1,50),('corner_radius','Bo góc vùng che',0,200),('feather','Feather vùng che',0,100),('spacing','Giãn ký tự',0,50)]:self.add_field(form,'style.'+key,label,'number',lo,hi)
        font=QPushButton('Chọn font TTF/OTF');font.clicked.connect(self.choose_font);form.addRow(font)
        color=QPushButton('Bảng màu chữ');color.clicked.connect(self.choose_color);form.addRow(color)
        self.inspector.addTab(style,'Kiểu')
        motion=QWidget();form=QFormLayout(motion)
        self.add_field(form,'motion.preset','Di chuyển','choice',options=['fixed','a-b','left-right','right-left','top-bottom','bottom-top','diagonal','pingpong','bounce','corners','random','zoom'])
        for key,label,lo,hi in [('speed','Tốc độ px/s',0,2000),('duration','Một vòng s',.1,3600),('delay','Trễ s',0,3600),('end_x','Đích X',0,1),('end_y','Đích Y',0,1),('fade_in','Fade vào s',0,30),('fade_out','Fade ra s',0,30)]:
            self.add_field(form,'motion.'+key,label,'number',lo,hi)
        self.add_field(form,'motion.repeat','Lặp','bool');self.add_field(form,'motion.easing','Gia tốc','choice',options=['linear','ease-in','ease-out','ease-in-out'])
        for key,label,lo,hi in [('hold','Nghỉ giữa vòng s',0,600),('repeat_count','Số vòng (0=vô hạn)',0,10000),('zoom_min','Zoom min',.1,5),('zoom_max','Zoom max',.1,5),('rotate_speed','Xoay độ/s',-360,360)]:self.add_field(form,'motion.'+key,label,'number',lo,hi)
        key=QPushButton('Đặt keyframe X/Y tại playhead');key.clicked.connect(self.keyframe);form.addRow(key)
        advanced=QPushButton('Bảng sửa keyframe đầy đủ');advanced.clicked.connect(self.edit_keyframes);form.addRow(advanced)
        self.inspector.addTab(motion,'Chuyển động')
        tabs=[(self.inspector.widget(i),self.inspector.tabText(i)) for i in range(self.inspector.count())]
        self.inspector.clear()
        for widget,name in tabs:
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(widget);self.inspector.addTab(scroll,name)

    def add_field(self,form,key,label,kind,lo=0,hi=1,options=None):
        if kind=='number':
            widget=QDoubleSpinBox();widget.setRange(lo,hi);widget.setDecimals(3);widget.setSingleStep(.01 if hi<=2 else 1)
            widget.valueChanged.connect(lambda _:self.field_changed(key))
        elif kind=='font':widget=QFontComboBox();widget.currentFontChanged.connect(lambda _:self.field_changed(key))
        elif kind=='bool':widget=QCheckBox();widget.toggled.connect(lambda _:self.field_changed(key))
        elif kind=='choice':widget=QComboBox();widget.addItems(options);widget.currentTextChanged.connect(lambda _:self.field_changed(key))
        else:widget=QLineEdit();widget.editingFinished.connect(lambda:self.field_changed(key))
        self.fields[key]=(widget,kind);form.addRow(label,widget)

    def layer(self):return next((x for x in self.composition.layers if x.id==self.selected_id),None)
    def begin(self):self._before=self.composition.to_dict()

    def commit(self,name):
        before=self._before;self._before=None
        try:after=self.composition.to_dict()
        except ValueError as exc:
            if before:self.set_composition(Composition.from_dict(before))
            self.host.message(str(exc));return
        if before and before!=after:self.undo.push(Snapshot(self,before,after,name))
        else:self.refresh()

    def set_composition(self,composition):
        self.composition=composition;self.refresh();self.changed.emit()

    def refresh(self):
        self._loading=True
        self.clips.clear()
        for c in self.composition.clips:self.clips.addItem(Path(c.path).name)
        self.layers.clear()
        for layer in self.composition.layers:self.layers.addItem(('🔒 ' if layer.locked else '')+layer.name)
        selected=next((i for i,x in enumerate(self.composition.layers) if x.id==self.selected_id),-1)
        self.layers.setCurrentRow(selected)
        self.canvas.rebuild();self.timeline.rebuild();self.load_fields();self._loading=False

    def select_row(self,index):
        if self._loading:return
        self.select_id(self.composition.layers[index].id if 0<=index<len(self.composition.layers) else '')

    def select_id(self,layer_id):
        self.selected_id=layer_id;self._loading=True;self.load_fields();self._loading=False
        index=next((i for i,l in enumerate(self.composition.layers) if l.id==layer_id),-1)
        self.layers.blockSignals(True);self.layers.setCurrentRow(index);self.layers.blockSignals(False)

    def load_fields(self):
        layer=self.layer()
        for key,(widget,kind) in self.fields.items():
            widget.setEnabled(layer is not None)
            if not layer:continue
            if '.' in key:
                parent,name=key.split('.');value=getattr(layer,parent).get(name)
                if value is None:value={'font_size':32,'font_family':'Arial','color':'#000000' if layer.kind=='mask' else '#ffffff','outline_color':'#000000','outline':2,'mode':'blur','radius':10,'duration':5,'speed':20,'repeat':True,'zoom_min':.95,'zoom_max':1.05,'easing':'linear','align':'left'}.get(name)
            else:value=getattr(layer,key)
            widget.blockSignals(True)
            if kind=='number':widget.setValue(float(value or (8 if key=='style.font_size' else 0)))
            elif kind=='bool':widget.setChecked(bool(value))
            elif kind=='choice':widget.setCurrentText(str(value or ('fixed' if key=='motion.preset' else 'linear' if key=='motion.easing' else 'left')))
            elif kind=='font':widget.setCurrentFont(QFont(value or 'Arial'))
            else:widget.setText(str(value or ''))
            widget.blockSignals(False)

    def field_changed(self,key):
        layer=self.layer()
        if self._loading or not layer:return
        widget,kind=self.fields[key]
        value=widget.value() if kind=='number' else widget.isChecked() if kind=='bool' else widget.currentText() if kind=='choice' else widget.currentFont().family() if kind=='font' else widget.text()
        if key=='end' and value==0:value=None
        self.begin()
        if '.' in key:parent,name=key.split('.');getattr(layer,parent)[name]=value
        else:setattr(layer,key,value)
        self.commit('Đổi '+key)

    def add_video(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Thêm media',filter='Video (*.mp4 *.mkv *.mov *.webm *.avi);;Tất cả (*)')
        for path in paths:self.open_media(Path(path))

    def open_media(self,path):
        frame=Path(self.host.workspace.name)/(uuid4().hex+'.png')
        def work(progress,cancel):
            info=probe(path);extract_frame(path,frame,min(.1,info.duration/2));return path,info,frame
        def done(data):
            path,info,frame=data;self.begin()
            self.composition.clips.append(Clip(str(path.resolve()),end=info.duration,source_duration=info.duration))
            self.frame=frame;self.commit('Thêm video')
            self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
            self.frame_label.setText(f'{info.width}×{info.height} • {info.duration:.2f}s')
        self.host.background(work,done)

    def add_layer(self,kind):
        path=None
        if kind=='image':
            path,_=QFileDialog.getOpenFileName(self,'Chọn logo',filter='Ảnh (*.png *.jpg *.webp)')
            if not path:return
        self.begin();layer=Layer(kind=kind,name={'text':'Chữ','image':'Logo','mask':'Vùng che'}[kind],path=path)
        if kind=='mask':layer.y=.75;layer.width=.8;layer.height=.12;layer.style={'mode':'blur','radius':10}
        layer.clip_ids=self.scope_ids();self.composition.layers.append(layer);self.selected_id=layer.id;self.commit('Thêm layer')

    def duplicate(self):
        if self.layer():
            self.begin();copy=deepcopy(self.layer());copy.id=identifier();copy.name+=' copy';copy.x=min(.95,copy.x+.02)
            self.composition.layers.append(copy);self.selected_id=copy.id;self.commit('Nhân bản')

    def delete_layer(self):
        if self.layer() and not self.layer().locked:
            self.begin();self.composition.layers=[l for l in self.composition.layers if l.id!=self.selected_id];self.selected_id=None;self.commit('Xóa layer')

    def reorder(self,delta):
        index=next((i for i,l in enumerate(self.composition.layers) if l.id==self.selected_id),-1)
        target=index+delta
        if index>=0 and 0<=target<len(self.composition.layers):
            self.begin();layers=self.composition.layers;layers[index],layers[target]=layers[target],layers[index];self.commit('Đổi thứ tự')

    def split(self):
        t=self.timeline.playhead
        for clip,offset,length in clip_positions(self.composition):
            if offset<t<offset+length:
                self.begin();cut=clip.start+(t-offset)*clip.speed
                right=replace(clip,id=identifier(),start=cut,offset=t);clip.end=cut
                self.composition.clips.insert(self.composition.clips.index(clip)+1,right);self.commit('Chia clip');return

    def choose_font(self):
        if not self.layer():return
        path,_=QFileDialog.getOpenFileName(self,'Font riêng',filter='Font (*.ttf *.otf)')
        if path:self.begin();self.layer().style['font_file']=path;self.commit('Font riêng')

    def choose_color(self):
        if not self.layer():return
        color=QColorDialog.getColor(QColor(self.layer().style.get('color','#ffffff')),self)
        if color.isValid():self.begin();self.layer().style['color']=color.name();self.commit('Màu chữ')

    def keyframe(self):
        if not self.layer() or self.layer().locked:return
        self.begin();layer=self.layer();t=round(self.timeline.playhead,3)
        for key in ('x','y'):
            points=[p for p in layer.keyframes.get(key,[]) if p['time']!=t]
            points.append({'time':t,'value':getattr(layer,key)});layer.keyframes[key]=sorted(points,key=lambda p:p['time'])
        self.commit('Đặt keyframe')

    def toggle_play(self):
        self.views.setCurrentIndex(1)
        self.player.pause() if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState else self.player.play()

    def request_render(self):self.render_requested.emit(self.composition.to_dict())
    def reference(self):self.host.reference(self.composition,self.timeline.playhead)
    def output_dialog(self):
        from .dialogs import OutputDialog
        OutputDialog(self).exec()
    def audio_dialog(self):
        from .dialogs import AudioDialog
        AudioDialog(self).exec()
    def edit_keyframes(self):
        if not self.layer() or self.layer().locked:return
        from .dialogs import KeyframeDialog
        KeyframeDialog(self).exec()
    def scope_ids(self):
        if self.scope.currentIndex()==2 or not self.composition.clips:return []
        indices=sorted({i.row() for i in self.clips.selectedIndexes()}) if self.scope.currentIndex()==1 else [max(0,self.clips.currentRow())]
        return [self.composition.clips[i].id for i in indices if i<len(self.composition.clips)]
    def change_scope(self):
        if not self.layer():return
        self.begin();self.layer().clip_ids=self.scope_ids();self.commit('Đổi phạm vi layer')
