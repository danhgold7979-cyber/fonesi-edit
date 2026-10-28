from copy import deepcopy
import math
from dataclasses import asdict,replace
from pathlib import Path
from uuid import uuid4
import tempfile

from PySide6.QtCore import Qt,QUrl,Signal
from PySide6.QtGui import QUndoCommand,QUndoStack,QColor,QKeySequence,QAction,QActionGroup,QFont
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QSplitter,QFormLayout,QLineEdit,QPlainTextEdit,
    QDoubleSpinBox,QSpinBox,QComboBox,QCheckBox,QPushButton,QListWidget,QLabel,QTabWidget,QFileDialog,QColorDialog,QScrollArea,QToolBar,QMenu,QFontComboBox)

from ..domain import Composition,Clip,Layer,identifier,canonical
from ..prototypes.media import probe,extract_frame
from ..thumbnails import thumbnail_identity,thumbnail_strip
from ..proxy import proxy_identity,playback_proxy
from .canvas import Canvas
from .timeline import Timeline,clip_positions

def loop_seek_target(milliseconds, start, end, *, enabled, verified):
    """Seek only in a matching rendered composition preview, never raw source time."""
    if not enabled or not verified or start is None or end is None:
        return None
    if (not all(math.isfinite(value) for value in (start, end))
            or start < 0 or end <= start or end-start < .04):
        return None
    return round(start*1000) if milliseconds >= round(end*1000) else None


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
        self.composition=Composition();self.selected_id=None;self.selected_ids=set();self.frame=None;self._before=None;self._loading=False;self.in_point=None;self.out_point=None
        self.preview_fingerprint=None;self._loop_seeking=False
        self.composition_fingerprint=canonical(self.composition.to_dict())
        self.waveforms={};self.thumbnails={};self._thumbnail_pending=set();self._thumbnail_failed=set()
        self.proxy_cache={};self._proxy_pending=set();self._proxy_failed=set()
        self.undo=QUndoStack(self);self.undo.setUndoLimit(100)
        layout=QVBoxLayout(self);toolbar=QToolBar();layout.addWidget(toolbar)
        actions=[('Thêm video',self.add_video),('Chữ',lambda:self.add_layer('text')),('Logo',lambda:self.add_layer('image')),
                 ('Vùng che',lambda:self.add_layer('mask')),('Nhân bản',self.duplicate),('Xóa layer',self.delete_layer),
                 ('Undo',self.undo.undo),('Redo',self.undo.redo),('Chia clip',self.split),('Render',self.request_render)]
        for label,callback in actions:
            action=toolbar.addAction(label);action.triggered.connect(lambda checked=False,callback=callback:callback())
        toolbar.addAction('Đầu ra',lambda:self.output_dialog());toolbar.addAction('Âm thanh',lambda:self.audio_dialog())
        extra=QPushButton('Thao tác thêm ▾');menu=QMenu(extra)
        for name,callback in [('Sửa clip',self.clip_dialog),('Đặt In',self.mark_in),('Đặt Out',self.mark_out),('Áp dụng In/Out',self.trim_in_out),('Xóa clip và dồn sau',self.ripple_delete),('Nhóm layer',self.group),('Bỏ nhóm',self.ungroup),('Căn giữa ngang',lambda:self.align('x')),('Căn giữa dọc',lambda:self.align('y')),('Phân bố ngang',lambda:self.distribute('x')),('Phân bố dọc',lambda:self.distribute('y')),('Copy kiểu',self.copy_style),('Dán kiểu',self.paste_style),('Khóa / mở chọn',self.lock_selected),('Ẩn / hiện chọn',self.hide_selected),('Preview có âm thanh',lambda:self.host.playback_preview(self.composition))]:
            action=menu.addAction(name);action.triggered.connect(lambda checked=False,callback=callback:callback())
        self.grid_action=menu.addAction('Lưới căn chỉnh (5%)')
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(bool(self.composition.adjustments.get('canvas_grid', False)))
        self.grid_action.triggered.connect(self.set_canvas_grid)
        self.loop_action=menu.addAction('Lặp đoạn In–Out (preview đã render)')
        self.loop_action.setCheckable(True)
        self.loop_action.setChecked(False)
        self.loop_action.toggled.connect(self.toggle_loop)
        self.thumbnail_action=menu.addAction('Thumbnail video trên timeline (tạo nền)')
        self.thumbnail_action.setCheckable(True)
        self.thumbnail_action.setChecked(bool(self.composition.adjustments.get('timeline_thumbnails',False)))
        self.thumbnail_action.toggled.connect(self.set_timeline_thumbnails)
        self.proxy_group=QActionGroup(self)
        self.proxy_group.setExclusive(True)
        self.proxy_actions={}
        for label,value in [('Không dùng proxy','off'),('Proxy nhanh (640px)','fast'),
                            ('Proxy cân bằng (1280px)','balanced'),('Proxy cao (1920px)','high')]:
            action=menu.addAction(label)
            action.setData(value);action.setCheckable(True)
            action.setChecked(value==self.composition.adjustments.get('playback_proxy_quality','off'))
            self.proxy_group.addAction(action);self.proxy_actions[value]=action
        self.proxy_group.triggered.connect(lambda action:self.set_proxy_quality(action.data()))
        extra.setMenu(menu);toolbar.addWidget(extra)
        self.scope=QComboBox();self.scope.addItems(['Clip hiện tại','Các clip đã chọn','Preset cả lô']);toolbar.addWidget(self.scope)
        self.scope.currentIndexChanged.connect(self.change_scope)
        split=QSplitter();layout.addWidget(split,1)
        assets=QWidget();left=QVBoxLayout(assets);self.clips=QListWidget();self.layers=QListWidget()
        self.clips.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.clips.currentRowChanged.connect(lambda _:self.load_proxy())
        self.layers.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left.addWidget(QLabel('Media'));left.addWidget(self.clips);left.addWidget(QLabel('Layers'));left.addWidget(self.layers)
        self.layers.itemSelectionChanged.connect(self.list_selection)
        self.clips.itemDoubleClicked.connect(lambda item:self.clip_dialog())
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
        self.player.positionChanged.connect(self.player_position_changed)
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
        self.preview_fingerprint=None
        self.composition=composition
        self.composition_fingerprint=canonical(composition.to_dict())
        self.refresh();self.changed.emit()

    def refresh(self):
        self._loading=True
        clip_ids={self.clips.item(i.row()).data(Qt.ItemDataRole.UserRole) for i in self.clips.selectedIndexes()}
        self.clips.clear()
        for c in self.composition.clips:
            self.clips.addItem(Path(c.path).name);item=self.clips.item(self.clips.count()-1);item.setData(Qt.ItemDataRole.UserRole,c.id);item.setSelected(c.id in clip_ids)
        if self.clips.count() and not self.clips.selectedItems():self.clips.setCurrentRow(0)
        self.layers.clear()
        for layer in self.composition.layers:self.layers.addItem(('🔒 ' if layer.locked else '')+layer.name)
        selected=next((i for i,x in enumerate(self.composition.layers) if x.id==self.selected_id),-1)
        self.selected_ids.intersection_update(l.id for l in self.composition.layers)
        if self.selected_id:self.selected_ids.add(self.selected_id)
        for index,layer in enumerate(self.composition.layers):self.layers.item(index).setSelected(layer.id in self.selected_ids)
        if hasattr(self, 'grid_action'):
            self.grid_action.blockSignals(True)
            self.grid_action.setChecked(bool(self.composition.adjustments.get('canvas_grid', False)))
            self.grid_action.blockSignals(False)
        if hasattr(self, 'thumbnail_action'):
            self.thumbnail_action.blockSignals(True)
            self.thumbnail_action.setChecked(bool(self.composition.adjustments.get('timeline_thumbnails',False)))
            self.thumbnail_action.blockSignals(False)
        if hasattr(self,'proxy_actions'):
            quality=self.composition.adjustments.get('playback_proxy_quality','off')
            action=self.proxy_actions.get(quality,self.proxy_actions['off'])
            action.setChecked(True)
        self.canvas.rebuild();self.timeline.rebuild();self.load_fields();self._loading=False
        self.load_waveforms()
        self.load_thumbnails()
        self.load_proxy()

    def load_waveforms(self):
        if not hasattr(self.host,'background'):return
        from ..waveform import waveform
        paths={c.path for c in self.composition.clips}|{a['path'] for a in self.composition.audio}
        for path in paths:
            if path in self.waveforms or not Path(path).is_file():continue
            self.waveforms[path]={}
            def work(progress,cancel,path=path):
                try:return path,waveform(path,Path(self.host.workspace.name)/'waveforms',cancel)
                except (ValueError,RuntimeError,OSError):return path,{}
            def done(data):self.waveforms[data[0]]=data[1];self.timeline.rebuild()
            self.host.background(work,done)

    def set_timeline_thumbnails(self,enabled):
        if bool(self.composition.adjustments.get('timeline_thumbnails',False))==bool(enabled):
            return
        self._thumbnail_failed.clear()
        self.begin()
        self.composition.adjustments['timeline_thumbnails']=bool(enabled)
        self.commit('Bật/tắt thumbnail trên timeline')

    def thumbnail_assets(self,clip):
        if not self.composition.adjustments.get('timeline_thumbnails',False):
            return []
        entry=self.thumbnails.get(clip.id)
        if not entry:return []
        try:key=thumbnail_identity(clip)
        except (OSError,ValueError):return []
        return entry.get('frames',[]) if entry.get('key')==key else []

    def load_thumbnails(self):
        if (not self.composition.adjustments.get('timeline_thumbnails',False)
                or not hasattr(self.host,'background')
                or not hasattr(self.host,'workspace')):
            return
        for clip in self.timeline.visible_clips(limit=8):
            if len(self._thumbnail_pending)>=8:break
            try:key=thumbnail_identity(clip)
            except (OSError,ValueError):
                continue
            entry=self.thumbnails.get(clip.id)
            if (entry and entry.get('key')==key
                    or key in self._thumbnail_pending
                    or key in self._thumbnail_failed):
                continue
            self._thumbnail_pending.add(key)
            snapshot=deepcopy(clip)
            destination=Path(self.host.workspace.name)/'thumbnails'
            def work(progress,cancel,clip=snapshot,key=key):
                try:return clip.id,key,thumbnail_strip(clip,destination,cancel),None
                except (RuntimeError,ValueError,TimeoutError,OSError) as exc:
                    return clip.id,key,None,str(exc)[:200]
            def done(outcome):
                clip_id,identity,data,error=outcome
                self._thumbnail_pending.discard(identity)
                if error:self._thumbnail_failed.add(identity)
                else:
                    current=next((c for c in self.composition.clips if c.id==clip_id),None)
                    if current:
                        try:matches=thumbnail_identity(current)==identity
                        except (OSError,ValueError):matches=False
                        if matches:self.thumbnails[clip_id]=data
                if self.composition.adjustments.get('timeline_thumbnails',False):
                    self.timeline.rebuild()
                    self.load_thumbnails()
            self.host.background(work,done)

    def set_proxy_quality(self,quality):
        if quality not in {'off','fast','balanced','high'}:
            raise ValueError('Chất lượng proxy không hỗ trợ')
        if self.composition.adjustments.get('playback_proxy_quality','off')==quality:
            return
        self._proxy_failed.clear()
        self.begin()
        self.composition.adjustments['playback_proxy_quality']=quality
        self.commit('Thay chất lượng proxy nguồn')

    def load_proxy(self):
        if self._loading or not hasattr(self,'player') or not hasattr(self,'clips'):
            return
        index=self.clips.currentRow()
        if not 0<=index<len(self.composition.clips):
            return
        clip=self.composition.clips[index]
        if not Path(clip.path).is_file() or self.preview_fingerprint is not None:
            return
        quality=self.composition.adjustments.get('playback_proxy_quality','off')
        if quality not in {'off','fast','balanced','high'}:
            return
        if quality=='off':
            original=QUrl.fromLocalFile(str(Path(clip.path).resolve()))
            if self.player.source()!=original:self.player.setSource(original)
            return
        if not hasattr(self.host,'background') or not hasattr(self.host,'workspace'):
            return
        try:key=proxy_identity(clip.path,quality)
        except (OSError,ValueError):return
        entry=self.proxy_cache.get(key)
        if entry and Path(entry['path']).is_file():
            target=QUrl.fromLocalFile(entry['path'])
            if self.player.source()!=target:self.player.setSource(target)
            return
        if key in self._proxy_pending or key in self._proxy_failed or self._proxy_pending:
            return
        self._proxy_pending.add(key)
        source=clip.path
        cache_root=Path(getattr(self.host,'data',self.host.workspace.name))/'cache'/'proxies'
        def work(progress,cancel):
            try:return key,playback_proxy(source,cache_root,quality,cancel),None
            except (RuntimeError,TimeoutError,ValueError,OSError) as exc:
                return key,None,str(exc)[:200]
        def done(result):
            identity,data,error=result
            self._proxy_pending.discard(identity)
            if error:self._proxy_failed.add(identity)
            elif data:self.proxy_cache[identity]=data
            index=self.clips.currentRow()
            if (data and 0<=index<len(self.composition.clips)
                    and self.composition.clips[index].path==source
                    and self.composition.adjustments.get('playback_proxy_quality')==quality
                    and self.preview_fingerprint is None):
                try:matches=proxy_identity(source,quality)==identity
                except (OSError,ValueError):matches=False
                if matches and Path(data['path']).is_file():
                    self.player.setSource(QUrl.fromLocalFile(data['path']))
                    self.host.message('Đã nạp proxy nguồn local; bản xuất vẫn dùng tệp gốc.')
            if error and self.composition.adjustments.get('playback_proxy_quality')==quality:
                self.host.message('Không tạo được proxy nguồn: '+error)
        self.host.background(work,done)

    def select_row(self,index):
        if self._loading:return
        self.select_id(self.composition.layers[index].id if 0<=index<len(self.composition.layers) else '')

    def select_id(self,layer_id):
        self.select_ids([layer_id] if layer_id else [])

    def list_selection(self):
        if self._loading:return
        self.select_ids([self.composition.layers[i.row()].id for i in self.layers.selectedIndexes()]);self.canvas.rebuild()

    def select_ids(self,layer_ids):
        layer_id=layer_ids[0] if layer_ids else None;self.selected_ids=set(layer_ids)
        self.selected_id=layer_id;self._loading=True;self.load_fields();self._loading=False
        self.layers.blockSignals(True)
        for index,layer in enumerate(self.composition.layers):self.layers.item(index).setSelected(layer.id in self.selected_ids)
        self.layers.blockSignals(False)

    def selected_layers(self):return [l for l in self.composition.layers if l.id in (self.selected_ids|{self.selected_id})]

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
        if '.' in key:
            parent,name=key.split('.');getattr(layer,parent)[name]=value
            if key=='style.font_family':layer.style.pop('font_file',None)
        else:setattr(layer,key,value)
        self.commit('Đổi '+key)

    def set_canvas_grid(self, enabled):
        enabled=bool(enabled)
        if bool(self.composition.adjustments.get('canvas_grid', False))==enabled:
            return
        self.begin()
        self.composition.adjustments['canvas_grid']=enabled
        self.commit('Bật/tắt lưới căn chỉnh')

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
        layer.clip_ids=self.scope_ids();self.composition.layers.append(layer);self.selected_id=layer.id;self.selected_ids={layer.id};self.commit('Thêm layer')

    def duplicate(self):
        if self.layer():
            self.begin();copy=deepcopy(self.layer());copy.id=identifier();copy.name+=' copy';copy.x=min(.95,copy.x+.02)
            self.composition.layers.append(copy);self.selected_id=copy.id;self.selected_ids={copy.id};self.commit('Nhân bản')

    def delete_layer(self):
        ids={l.id for l in self.selected_layers() if not l.locked}
        if ids:
            self.begin();self.composition.layers=[l for l in self.composition.layers if l.id not in ids];self.selected_id=None;self.selected_ids=set();self.commit('Xóa layer')

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
                for layer in self.composition.layers:
                    if clip.id in layer.clip_ids:layer.clip_ids.append(right.id)
                self.composition.clips.insert(self.composition.clips.index(clip)+1,right);self.commit('Chia clip');return

    def group(self):
        layers=[l for l in self.selected_layers() if not l.locked]
        if len(layers)<2:return
        self.begin();key=identifier()
        for layer in layers:layer.group=key
        self.commit('Nhóm layer')
    def ungroup(self):
        self.begin()
        for layer in self.selected_layers():
            if not layer.locked:layer.group=None
        self.commit('Bỏ nhóm')
    def align(self,axis):
        self.begin()
        for layer in self.selected_layers():
            if not layer.locked:setattr(layer,axis,(1-getattr(layer,'width' if axis=='x' else 'height'))/2)
        self.commit('Căn giữa')
    def distribute(self,axis):
        layers=sorted([l for l in self.selected_layers() if not l.locked],key=lambda l:getattr(l,axis))
        if len(layers)<3:return
        self.begin();first,last=getattr(layers[0],axis),getattr(layers[-1],axis)
        for i,layer in enumerate(layers):setattr(layer,axis,first+(last-first)*i/(len(layers)-1))
        self.commit('Phân bố layer')
    def copy_style(self):
        if self.layer():self.style_clipboard=deepcopy(self.layer().style)
    def paste_style(self):
        if not hasattr(self,'style_clipboard'):return
        self.begin()
        for layer in self.selected_layers():
            if not layer.locked:layer.style=deepcopy(self.style_clipboard)
        self.commit('Dán kiểu')
    def lock_selected(self):
        self.begin();layers=self.selected_layers();value=not all(l.locked for l in layers)
        for layer in layers:layer.locked=value
        self.commit('Khóa/mở layer')
    def hide_selected(self):
        self.begin();layers=[l for l in self.selected_layers() if not l.locked];value=not any(l.visible for l in layers)
        for layer in layers:layer.visible=value
        self.commit('Ẩn/hiện layer')
    def mark_in(self):self.in_point=self.timeline.playhead;self.host.message(f'In: {self.in_point:.3f}s')
    def mark_out(self):self.out_point=self.timeline.playhead;self.host.message(f'Out: {self.out_point:.3f}s')
    def trim_in_out(self):
        if self.in_point is None or self.out_point is None or self.out_point<=self.in_point:self.host.message('Đặt In trước Out trong một clip');return
        for clip,offset,length in clip_positions(self.composition):
            if offset<=self.in_point<self.out_point<=offset+length:
                self.begin();start=clip.start;clip.start=start+(self.in_point-offset)*clip.speed;clip.end=start+(self.out_point-offset)*clip.speed;clip.freeze=0;self.composition.duration_target=None;self.commit('Cắt In/Out');return
        self.host.message('In/Out phải nằm trong cùng một clip; chia clip trước khi cắt qua nhiều cảnh')
    def ripple_delete(self):
        indices={i.row() for i in self.clips.selectedIndexes()}
        if not indices:return
        positions=clip_positions(self.composition);ids={self.composition.clips[i].id for i in indices};shift=0;self.begin()
        for clip,offset,length in positions:
            if clip.id in ids:shift+=length-self.composition.transition
            elif clip.offset is not None:clip.offset=max(0,offset-shift)
        self.composition.clips=[c for c in self.composition.clips if c.id not in ids]
        self.composition.layers=[l for l in self.composition.layers if not l.clip_ids or any(cid not in ids for cid in l.clip_ids)]
        for layer in self.composition.layers:layer.clip_ids=[cid for cid in layer.clip_ids if cid not in ids]
        self.composition.duration_target=None;self.commit('Xóa clip và dồn sau')

    def clip_dialog(self):
        if not self.composition.clips:return
        from .dialogs import ClipDialog
        ClipDialog(self,max(0,self.clips.currentRow())).exec()

    def choose_font(self):
        if not self.layer():return
        path,_=QFileDialog.getOpenFileName(self,'Font riêng',filter='Font (*.ttf *.otf *.ttc *.otc)')
        if path:
            from ..fonts import font_faces
            faces=font_faces(path);self.begin();self.layer().style.update({'font_file':path,'font_family':faces[0]['family']});self.commit('Font riêng')

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

    def toggle_loop(self,enabled):
        if not enabled:return
        if (self.in_point is None or self.out_point is None
                or not math.isfinite(self.in_point) or not math.isfinite(self.out_point)
                or self.in_point<0 or self.out_point<=self.in_point
                or self.out_point-self.in_point<.04):
            self.loop_action.blockSignals(True)
            self.loop_action.setChecked(False)
            self.loop_action.blockSignals(False)
            self.host.message('Đặt In và Out hợp lệ (Out sau In ít nhất 40 ms) để lặp preview')
            return
        positions=clip_positions(self.composition)
        duration=max((offset+length for _,offset,length in positions),default=0)
        if self.out_point>duration+.002:
            self.loop_action.blockSignals(True)
            self.loop_action.setChecked(False)
            self.loop_action.blockSignals(False)
            self.host.message('Điểm Out vượt thời lượng composition')
            return
        if self.preview_fingerprint!=self.composition_fingerprint:
            self.host.message('Để lặp đúng thời gian, hãy dựng Preview có âm thanh từ compositor')
            if hasattr(self.host,'playback_preview'):
                self.host.playback_preview(self.composition)

    def player_position_changed(self,milliseconds):
        self.timeline.position(milliseconds/1000)
        if self._loop_seeking:return
        verified=(self._before is None and self.preview_fingerprint==self.composition_fingerprint)
        if self.player.playbackState()!=QMediaPlayer.PlaybackState.PlayingState:return
        target=loop_seek_target(milliseconds,self.in_point,self.out_point,
            enabled=self.loop_action.isChecked(),verified=verified)
        if target is not None and target!=milliseconds:
            self._loop_seeking=True
            try:self.player.setPosition(target)
            finally:self._loop_seeking=False

    def toggle_play(self):
        self.views.setCurrentIndex(1)
        if (self.loop_action.isChecked()
                and self.preview_fingerprint!=self.composition_fingerprint):
            if hasattr(self.host,'playback_preview'):self.host.playback_preview(self.composition)
            else:self.host.message('Lặp đoạn cần render preview composition trước')
            return
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
