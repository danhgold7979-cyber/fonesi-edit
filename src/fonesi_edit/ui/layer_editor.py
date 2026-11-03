"""Basic layer list and numeric transform editor backed by ProjectSession CAS."""
from copy import deepcopy
from fractions import Fraction
from math import atan2,degrees
from uuid import uuid4

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal, QObject, QEvent
from PySide6.QtGui import QColor, QBrush, QPen, QPainter, QPainterPath
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QSplitter,
    QLabel,QListWidget,QListWidgetItem,QPushButton,QDoubleSpinBox,QComboBox,QCheckBox,QSlider,QLineEdit,
    QGraphicsView,QGraphicsScene,QGraphicsRectItem,QGraphicsLineItem,QGraphicsItem,QAbstractItemView,QMenu)

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.ui.shortcuts import ShortcutRegistry

ANCHORS=('top_left','top_center','top_right','center_left','center','center_right',
         'bottom_left','bottom_center','bottom_right')
LOCKABLE={'x','y','width','height','scale_x','scale_y','rotation','opacity','anchor','flip_x','flip_y'}
TRANSFORM_DEFAULTS={
    'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
    'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
    'anchor':'center','flip_x':False,'flip_y':False,
}
SLIDER_SCALES={'x':100,'y':100,'width':10000,'height':10000,
               'scale_x':1000,'scale_y':1000,'rotation':10,'opacity':1000}

def val(pair): return float(Fraction(pair[0],pair[1]))
def pair(value):
    f=Fraction(str(value)).limit_denominator(100000)
    return [f.numerator,f.denominator]
def locked(layer):
    locks=set(layer.get('locked_fields',()))
    return 'transform' in locks or bool(locks & LOCKABLE)
def offset(anchor,w,h):
    x=0 if anchor.endswith('left') else -w if anchor.endswith('right') else -w/2
    y=0 if anchor.startswith('top') else -h if anchor.startswith('bottom') else -h/2
    return x,y

class LayerBoundsItem(QGraphicsRectItem):
    def __init__(self,layer,width,height,moved,can_move=True,resized=None,rotated=None,show_handles=True):
        t=layer['transform'];w=val(t['width'])*width*val(t['scale_x']);h=val(t['height'])*height*val(t['scale_y'])
        x,y=offset(t['anchor'],w,h)
        super().__init__(QRectF(x,y,w,h))
        self.layer_id=layer['id'];self.moved=moved;self.resized=resized;self.rotated=rotated
        self.anchor=t['anchor'];self.show_handles=show_handles;self.pressed=None
        self.resize_state=None;self.rotate_state=None
        self.setPos(val(t['x'])*width,val(t['y'])*height)
        self.setRotation(val(t['rotation']));self.setOpacity(val(t['opacity']))
        self.setZValue(layer['z']+1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,can_move and not locked(layer))
        self.setData(0,self.layer_id)
        self.setToolTip(f"{layer['type']} · z={layer['z']}")
        if layer['type']=='mask':
            rgba=layer['style']['color'];fill=QColor(*rgba);fill.setAlpha(min(110,rgba[3]));edge=QColor(245,190,80)
        else:fill=QColor(90,170,240,45);edge=QColor(90,190,255)
        self.setBrush(QBrush(fill));self.setPen(QPen(edge,2,Qt.PenStyle.DashLine))

    def boundingRect(self):
        return super().boundingRect().adjusted(-10,-38,10,10)

    def shape(self):
        path=super().shape()
        if self.isSelected() and self.show_handles:
            for point in self._resize_handles().values():
                path.addRect(QRectF(point.x()-7,point.y()-7,14,14))
            handle=self._rotation_handle()
            path.addEllipse(handle,10,10)
        return path

    def _resize_handles(self):
        r=self.rect();cx=r.center().x();cy=r.center().y()
        return {
            'nw':r.topLeft(),'n':QPointF(cx,r.top()),'ne':r.topRight(),
            'e':QPointF(r.right(),cy),'se':r.bottomRight(),
            's':QPointF(cx,r.bottom()),'sw':r.bottomLeft(),'w':QPointF(r.left(),cy),
        }

    def _rotation_handle(self):
        r=self.rect()
        return QPointF(r.center().x(),r.top()-24)

    def paint(self,painter,option,widget=None):
        super().paint(painter,option,widget)
        if not self.isSelected() or not self.show_handles:return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        painter.setPen(QPen(QColor('#17212b'),1))
        painter.setBrush(QBrush(QColor('#f5f7fa')))
        for point in self._resize_handles().values():
            painter.drawRect(QRectF(point.x()-4,point.y()-4,8,8))
        handle=self._rotation_handle()
        painter.setBrush(QBrush(QColor('#f4d35e')))
        painter.drawLine(QPointF(self.rect().center().x(),self.rect().top()),handle)
        painter.drawEllipse(handle,6,6)
        painter.restore()

    def mousePressEvent(self,event):
        if self.isSelected() and self.show_handles:
            point=QPointF(event.pos())
            for name,handle in self._resize_handles().items():
                if (point-handle).manhattanLength()<=12:
                    self.resize_state={'handle':name,'start':point,'rect':QRectF(self.rect())}
                    self.pressed=None;event.accept();return
            rotation_handle=self._rotation_handle()
            if (point-rotation_handle).manhattanLength()<=12:
                anchor_scene=self.mapToScene(QPointF(0,0))
                vector=event.scenePos()-anchor_scene
                self.rotate_state={'start_angle':degrees(atan2(vector.y(),vector.x())),
                                   'start_rotation':self.rotation()}
                self.pressed=None;event.accept();return
        self.pressed=QPointF(self.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if self.resize_state is not None:
            state=self.resize_state;name=state['handle'];original=state['rect']
            delta=QPointF(event.pos())-state['start']
            left,right=original.left(),original.right()
            top,bottom=original.top(),original.bottom()
            if 'w' in name:left=min(right-12,left+delta.x())
            if 'e' in name:right=max(left+12,right+delta.x())
            if 'n' in name:top=min(bottom-12,top+delta.y())
            if 's' in name:bottom=max(top+12,bottom+delta.y())
            self.setRect(QRectF(QPointF(left,top),QPointF(right,bottom)))
            self.update();event.accept();return
        if self.rotate_state is not None:
            anchor_scene=self.mapToScene(QPointF(0,0))
            vector=event.scenePos()-anchor_scene
            angle=degrees(atan2(vector.y(),vector.x()))
            delta=(angle-self.rotate_state['start_angle']+180)%360-180
            self.setRotation(self.rotate_state['start_rotation']+delta)
            self.update();event.accept();return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self,event):
        if self.resize_state is not None:
            rect=QRectF(self.rect());state=self.resize_state;self.resize_state=None
            ox,oy=offset(self.anchor,rect.width(),rect.height())
            anchor_scene=self.mapToScene(QPointF(rect.left()-ox,rect.top()-oy))
            if self.resized is not None:
                QTimer.singleShot(0,lambda:self.resized(self.layer_id,rect.width(),rect.height(),anchor_scene))
            event.accept();return
        if self.rotate_state is not None:
            rotation=self.rotation();self.rotate_state=None
            if self.rotated is not None:
                QTimer.singleShot(0,lambda:self.rotated(self.layer_id,rotation))
            event.accept();return
        super().mouseReleaseEvent(event)
        if self.pressed is not None and self.pos()!=self.pressed:
            layer_id=self.layer_id;position=QPointF(self.pos());origin=QPointF(self.pressed)
            alt=bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            QTimer.singleShot(0,lambda:self.moved(layer_id,position,origin,alt))
        self.pressed=None




class LayerShortcutRouter(QObject):
    """Route remappable keys only from layer tree/canvas; never from inspector inputs."""
    def __init__(self,editor,registry):
        super().__init__(editor);self.editor=editor;self.registry=registry
        self.ime_preedit_active=False

    def eventFilter(self,watched,event):
        if event.type()==QEvent.Type.InputMethod:
            self.ime_preedit_active=bool(event.preeditString())
            return False
        if event.type() in (QEvent.Type.FocusIn,QEvent.Type.FocusOut):
            # A focus transition ends any preedit owned by the previous focus target.
            self.ime_preedit_active=False
            return False
        if event.type()!=QEvent.Type.KeyPress or self.editor.stopping or self.ime_preedit_active:return False
        bindings=(
            ('layer.undo',self.editor.undo),
            ('layer.redo',self.editor.redo),
            ('layer.delete',self.editor.delete_selected),
            ('layer.group',self.editor.group_selected),
            ('layer.ungroup',self.editor.ungroup_selected),
            ('layer.raise',lambda:self.editor.move_selected(1)),
            ('layer.lower',lambda:self.editor.move_selected(-1)),
        )
        for action_id,callback in bindings:
            if self.registry.matches(action_id,event):
                if event.isAutoRepeat():event.accept();return True
                callback();event.accept();return True
        return False

class LayerEditorWorkspace(QWidget):
    project_changed=Signal()
    def __init__(self,get_session,parent=None,shortcut_registry=None):
        super().__init__(parent);self.get_session=get_session
        self.shortcut_registry=shortcut_registry or ShortcutRegistry(self)
        self.selected_id=None;self.selected_ids=set();self.undo_stack=[];self.redo_stack=[]
        self.syncing=False;self.committing=False;self.stopping=False
        self.last_session=None;self.last_revision=None;self.original_transform=None
        root=QVBoxLayout(self)
        self.notice=QLabel('Canvas hình học layer; chưa giải mã video hoặc render hiệu ứng. Không phải preview/export.')
        self.notice.setWordWrap(True);root.addWidget(self.notice)
        bar=QHBoxLayout()
        self.add_button=QPushButton('Thêm vùng che');self.delete_button=QPushButton('Xóa layer')
        self.lock_button=QPushButton('Khóa/mở');self.hide_button=QPushButton('Ẩn/hiện')
        self.up_button=QPushButton('Đưa lên');self.down_button=QPushButton('Đưa xuống')
        self.group_button=QPushButton('Nhóm');self.ungroup_button=QPushButton('Bỏ nhóm')
        self.bring_button=QPushButton('Đưa vào khung')
        self.grid_check=QCheckBox('Lưới 5%');self.safe_check=QCheckBox('Safe area 90%')
        self.snap_check=QCheckBox('Snap (Alt bỏ qua)');self.snap_check.setChecked(True)
        self.undo_button=QPushButton('Hoàn tác');self.redo_button=QPushButton('Làm lại')
        for b in (self.add_button,self.delete_button,self.lock_button,self.hide_button,self.up_button,self.down_button,self.group_button,self.ungroup_button,self.bring_button,self.grid_check,self.safe_check,self.snap_check,self.undo_button,self.redo_button):bar.addWidget(b)
        root.addLayout(bar)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('Layer'))
        self.layers=QListWidget();self.layers.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layers.itemSelectionChanged.connect(self.select_rows)
        self.layers.customContextMenuRequested.connect(self.show_layer_context_menu)
        ll.addWidget(self.layers);split.addWidget(left)
        self.scene=QGraphicsScene(self);self.view=QGraphicsView(self.scene);split.addWidget(self.view)
        right=QWidget();form=QFormLayout(right)
        self.inspector_search=QLineEdit()
        self.inspector_search.setPlaceholderText('Tìm thuộc tính…')
        self.inspector_search.setAccessibleName('Tìm thuộc tính')
        self.inspector_search.setToolTip('Tìm theo tên tiếng Việt hoặc mã thuộc tính. Kết quả tìm kiếm bao gồm cả thuộc tính nâng cao.')
        self.inspector_search.textChanged.connect(self._filter_inspector)
        form.addRow('Tìm thuộc tính',self.inspector_search)
        self.inspector_advanced=QCheckBox('Nâng cao')
        self.inspector_advanced.setToolTip('Hiện thêm tỷ lệ, góc xoay, điểm neo và lật.')
        self.inspector_advanced.toggled.connect(self._filter_inspector)
        form.addRow('Chế độ',self.inspector_advanced)
        self.inspector_rows={}
        self.spins={};self.sliders={};self.slider_scales={};self.reset_buttons={}
        fields=(
            ('x','X (tỷ lệ khung)',-10,10),
            ('y','Y (tỷ lệ khung)',-10,10),
            ('width','Rộng (tỷ lệ khung)',.0001,10),
            ('height','Cao (tỷ lệ khung)',.0001,10),
            ('scale_x','Tỷ lệ X (×)',.0001,100),
            ('scale_y','Tỷ lệ Y (×)',.0001,100),
            ('rotation','Xoay (°)',-36000,36000),
            ('opacity','Độ mờ (0–1)',0,1),
        )
        for name,label,lo,hi in fields:
            scale=SLIDER_SCALES[name]
            spin=QDoubleSpinBox();spin.setDecimals(4);spin.setRange(lo,hi);spin.setSingleStep(.01);spin.setFixedWidth(88)
            slider=QSlider(Qt.Orientation.Horizontal);slider.setRange(round(lo*scale),round(hi*scale))
            slider.setSingleStep(max(1,round(.01*scale)));slider.setPageStep(max(1,round(.1*scale)))
            slider.setMinimumWidth(72)
            reset=QPushButton('↺');reset.setFixedWidth(30)
            reset.setAccessibleName(f'Đặt lại {label}')
            reset.setToolTip(f'Đặt lại {label.lower()} về mặc định')
            row=QWidget();row_layout=QHBoxLayout(row);row_layout.setContentsMargins(0,0,0,0);row_layout.setSpacing(4)
            row_layout.addWidget(slider,1);row_layout.addWidget(spin);row_layout.addWidget(reset)
            spin.editingFinished.connect(self.apply_inspector)
            slider.valueChanged.connect(lambda value,key=name:self._slider_value_changed(key,value))
            slider.sliderReleased.connect(self.apply_inspector)
            reset.clicked.connect(lambda _checked=False,key=name:self.reset_inspector_property(key))
            self.spins[name]=spin;self.sliders[name]=slider;self.slider_scales[name]=scale;self.reset_buttons[name]=reset
            field_label=QLabel(label);form.addRow(field_label,row)
            search_terms=f'{name} {label} {label.lower()} {name.replace("_"," ")}'.casefold()
            self.inspector_rows[name]=(row,field_label,search_terms,name not in {'x','y','width','height','opacity'})
        self.anchor=QComboBox();self.anchor.addItems(ANCHORS);self.anchor.activated.connect(self.apply_inspector)
        self.reset_anchor_button=QPushButton('↺');self.reset_anchor_button.setToolTip('Đặt lại điểm neo')
        anchor_row=QWidget();anchor_layout=QHBoxLayout(anchor_row);anchor_layout.setContentsMargins(0,0,0,0)
        anchor_layout.addWidget(self.anchor,1);anchor_layout.addWidget(self.reset_anchor_button)
        self.reset_anchor_button.clicked.connect(lambda:self.reset_inspector_property('anchor'))
        anchor_label=QLabel('Điểm neo');form.addRow(anchor_label,anchor_row)
        self.inspector_rows['anchor']=(anchor_row,anchor_label,'anchor điểm neo căn neo',True)
        self.flip_x=QCheckBox('Lật ngang');self.flip_y=QCheckBox('Lật dọc')
        self.flip_x.toggled.connect(self.apply_inspector);self.flip_y.toggled.connect(self.apply_inspector)
        self.reset_flip_x_button=QPushButton('↺');self.reset_flip_y_button=QPushButton('↺')
        self.reset_flip_x_button.setToolTip('Đặt lại lật ngang');self.reset_flip_y_button.setToolTip('Đặt lại lật dọc')
        flip_x_row=QWidget();flip_x_layout=QHBoxLayout(flip_x_row);flip_x_layout.setContentsMargins(0,0,0,0)
        flip_x_layout.addWidget(self.flip_x,1);flip_x_layout.addWidget(self.reset_flip_x_button)
        flip_y_row=QWidget();flip_y_layout=QHBoxLayout(flip_y_row);flip_y_layout.setContentsMargins(0,0,0,0)
        flip_y_layout.addWidget(self.flip_y,1);flip_y_layout.addWidget(self.reset_flip_y_button)
        self.reset_flip_x_button.clicked.connect(lambda:self.reset_inspector_property('flip_x'))
        self.reset_flip_y_button.clicked.connect(lambda:self.reset_inspector_property('flip_y'))
        form.addRow(flip_x_row);form.addRow(flip_y_row)
        self.inspector_rows['flip_x']=(flip_x_row,None,'flip_x flip x lật ngang',True)
        self.inspector_rows['flip_y']=(flip_y_row,None,'flip_y flip y lật dọc',True)
        self.reset_transform_button=QPushButton('Đặt lại toàn bộ biến đổi')
        self.reset_transform_button.clicked.connect(self.reset_inspector_transform)
        form.addRow(self.reset_transform_button)
        self.inspector_reason=QLabel('Mở hoặc tạo dự án để chỉnh thuộc tính layer.')
        self.inspector_reason.setWordWrap(True);self.inspector_reason.setAccessibleName('Lý do trạng thái thuộc tính')
        form.addRow(self.inspector_reason)
        self.status=QLabel('Chưa chọn layer.');self.status.setWordWrap(True);form.addRow(self.status)
        self._filter_inspector()
        split.addWidget(right);split.setStretchFactor(0,1);split.setStretchFactor(1,4);split.setStretchFactor(2,1)
        root.addWidget(split)
        self.add_button.clicked.connect(self.add_mask);self.delete_button.clicked.connect(self.delete_selected)
        self.lock_button.clicked.connect(self.toggle_lock);self.hide_button.clicked.connect(self.toggle_visibility)
        self.up_button.clicked.connect(lambda:self.move_selected(1));self.down_button.clicked.connect(lambda:self.move_selected(-1))
        self.group_button.clicked.connect(self.group_selected);self.ungroup_button.clicked.connect(self.ungroup_selected)
        self.bring_button.clicked.connect(self.bring_into_frame)
        self.grid_check.toggled.connect(lambda _checked:self.update_project())
        self.safe_check.toggled.connect(lambda _checked:self.update_project())
        self.undo_button.clicked.connect(self.undo);self.redo_button.clicked.connect(self.redo)
        self.scene.selectionChanged.connect(self.scene_selected)
        self._install_shortcuts()
        self.update_project()

    def _install_shortcuts(self):
        self.shortcut_router=LayerShortcutRouter(self,self.shortcut_registry)
        for owner in (self.layers,self.layers.viewport(),self.view,self.view.viewport()):
            owner.installEventFilter(self.shortcut_router)
        help_text='Phím tắt có thể đổi trong Cài đặt → Phím tắt. Chỉ hoạt động khi focus ở danh sách/canvas; ô số giữ phím chỉnh sửa và IME được ưu tiên.'
        self.layers.setToolTip(help_text);self.view.setToolTip(help_text)

    @property
    def busy(self):return False
    def request_stop(self):self.stopping=True;self.update_actions()
    def data(self):
        session=self.get_session()
        return None if session is None else session.project.plan.to_dict()
    def selected(self,data=None):
        data=self.data() if data is None else data
        return None if data is None else next((x for x in data['layers'] if x['id']==self.selected_id),None)

    def selected_layers(self,data=None):
        data=self.data() if data is None else data
        if data is None:return []
        return [x for x in data['layers'] if x['id'] in self.selected_ids]

    @staticmethod
    def expand_group_ids(ids,data):
        layers=data['layers'];selected=set(ids)
        group_ids={x.get('group_id') for x in layers if x['id'] in selected and x.get('group_id')}
        if group_ids:
            selected.update(x['id'] for x in layers if x.get('group_id') in group_ids)
        return selected

    def update_actions(self):
        session=self.get_session();ready=session is not None and not session.reconciliation_required and not self.stopping
        self.add_button.setEnabled(ready);self.undo_button.setEnabled(ready and bool(self.undo_stack))
        self.redo_button.setEnabled(ready and bool(self.redo_stack))
        selected=self.selected_layers()
        single=selected[0] if len(selected)==1 else None
        edit=single is not None and not locked(single) and ready
        reason=self._inspector_disabled_reason()
        self.inspector_reason.setText(reason)
        for name,s in self.spins.items():
            s.setEnabled(edit);s.setToolTip(f'{name}: {reason}')
        for name,slider in self.sliders.items():slider.setToolTip(f'{name}: {reason}')
        for name,button in self.reset_buttons.items():button.setToolTip(f'Đặt lại {name}; {reason}')
        for slider in self.sliders.values():slider.setEnabled(edit)
        for button in self.reset_buttons.values():button.setEnabled(edit)
        self.anchor.setEnabled(edit);self.anchor.setToolTip(f'Điểm neo; {reason}')
        self.flip_x.setEnabled(edit);self.flip_x.setToolTip(f'Lật ngang; {reason}')
        self.flip_y.setEnabled(edit);self.flip_y.setToolTip(f'Lật dọc; {reason}')
        special_resets=(
            (self.reset_anchor_button,'Đặt lại điểm neo'),
            (self.reset_flip_x_button,'Đặt lại lật ngang'),
            (self.reset_flip_y_button,'Đặt lại lật dọc'),
            (self.reset_transform_button,'Đặt lại toàn bộ biến đổi'),
        )
        for button,label in special_resets:
            button.setEnabled(edit);button.setToolTip(f'{label}; {reason}')
        has_selection=bool(selected) and ready
        for b in (self.delete_button,self.lock_button,self.hide_button,self.up_button,self.down_button,self.bring_button):
            b.setEnabled(has_selection)
        group_ids={x.get('group_id') for x in selected if x.get('group_id')}
        already_one_group=bool(group_ids) and all(x.get('group_id') in group_ids for x in selected) and len(group_ids)==1
        self.group_button.setEnabled(ready and len(selected)>=2 and not already_one_group)
        self.ungroup_button.setEnabled(has_selection and bool(group_ids))
        if not selected:self.status.setText('Chưa chọn layer.')
        elif len(selected)>1:self.status.setText(f'Đã chọn {len(selected)} layer · thao tác sẽ áp dụng đồng thời.')
        else:self.status.setText(('Đã khóa biến đổi' if locked(single) else 'Có thể chỉnh sửa')+
                                 (' · đang ẩn' if not single['visible'] else ' · đang hiện'))

    def update_project(self):
        session=self.get_session()
        if session is None:
            self.last_session=None;self.last_revision=None;self.undo_stack.clear();self.redo_stack.clear()
            self.selected_id=None;self.selected_ids.clear();self.layers.clear();self.scene.clear();self.scene.setSceneRect(QRectF(0,0,640,360))
            self.update_actions();return
        if not self.committing and (session is not self.last_session or session.revision!=self.last_revision):
            self.undo_stack.clear();self.redo_stack.clear()
        self.last_session=session;self.last_revision=session.revision
        data=session.project.plan.to_dict();W=data['output']['width'];H=data['output']['height']
        valid_ids={x['id'] for x in data['layers']}
        self.selected_ids.intersection_update(valid_ids)
        if self.selected_id not in valid_ids:self.selected_id=next(iter(self.selected_ids),None)
        self.selected_ids=self.expand_group_ids(self.selected_ids,data)
        if self.selected_id is None and self.selected_ids:self.selected_id=next(iter(self.selected_ids))
        selected_locked=any(locked(x) for x in data['layers'] if x['id'] in self.selected_ids)
        self.syncing=True
        try:
            self.layers.clear()
            for layer in sorted(data['layers'],key=lambda x:(x['z'],x['id'])):
                group=layer.get('group_id')
                group_label=f" · nhóm {group[:6]}" if group else ''
                row=QListWidgetItem(f"{layer['z']} · {layer['type']} · "+
                    ('ẩn' if not layer['visible'] else 'hiện')+' · '+('khóa' if locked(layer) else 'mở')+group_label)
                row.setData(Qt.ItemDataRole.UserRole,layer['id']);self.layers.addItem(row)
                if layer['id'] in self.selected_ids:row.setSelected(True)
            self.scene.clear();self.scene.setSceneRect(QRectF(0,0,W,H))
            bg=QGraphicsRectItem(QRectF(0,0,W,H));bg.setBrush(QBrush(QColor('#202832')))
            bg.setPen(QPen(QColor('#d0d7de'),2));bg.setZValue(-10000)
            bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,False);self.scene.addItem(bg)
            self._draw_canvas_guides(W,H)
            for layer in data['layers']:
                if not layer['visible']:continue
                can_move=not selected_locked if layer['id'] in self.selected_ids else not locked(layer)
                show_handles=len(self.selected_ids)==1 and layer['id'] in self.selected_ids and not locked(layer)
                item=LayerBoundsItem(layer,W,H,self.dragged,can_move,self.resized,self.rotated,show_handles)
                self.scene.addItem(item)
                if layer['id'] in self.selected_ids:item.setSelected(True)
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        finally:self.syncing=False
        self.set_inspector(self.selected(data));self.update_actions()

    def _draw_canvas_guides(self,width,height):
        if self.grid_check.isChecked():
            pen=QPen(QColor(120,145,170,85),1,Qt.PenStyle.DotLine)
            for index in range(1,20):
                x=width*index/20;y=height*index/20
                for x1,y1,x2,y2 in ((x,0,x,height),(0,y,width,y)):
                    line=QGraphicsLineItem(x1,y1,x2,y2)
                    line.setPen(pen);line.setZValue(-9000)
                    line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,False)
                    line.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                    self.scene.addItem(line)
        if self.safe_check.isChecked():
            safe=QGraphicsRectItem(QRectF(width*.05,height*.05,width*.9,height*.9))
            safe.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            safe.setPen(QPen(QColor(235,190,90,180),2,Qt.PenStyle.DashLine))
            safe.setZValue(-8999)
            safe.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,False)
            safe.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(safe)

    def set_inspector(self,layer):
        self.syncing=True
        try:
            if layer is not None:
                t=layer['transform'];self.original_transform=deepcopy(t)
                for name,s in self.spins.items():
                    value=val(t[name]);s.setValue(value)
                    self.sliders[name].setValue(round(value*self.slider_scales[name]))
                self.anchor.setCurrentText(t['anchor'])
                self.flip_x.setChecked(t['flip_x']);self.flip_y.setChecked(t['flip_y'])
            else:
                self.original_transform=None
        finally:self.syncing=False

    def _filter_inspector(self,*_):
        query=self.inspector_search.text().strip().casefold()
        advanced=self.inspector_advanced.isChecked()
        for _name,(row,label,terms,is_advanced) in self.inspector_rows.items():
            visible=(query in terms) if query else (advanced or not is_advanced)
            row.setVisible(visible)
            if label is not None:label.setVisible(visible)

    def _inspector_disabled_reason(self):
        session=self.get_session()
        if session is None:return 'Mở hoặc tạo dự án trước khi chỉnh thuộc tính.'
        if self.stopping:return 'Ứng dụng đang đóng; không thể chỉnh thuộc tính.'
        if session.reconciliation_required:return 'Dự án cần đối soát; thao tác chỉnh sửa đang tạm khóa.'
        selected=self.selected_layers()
        if not selected:return 'Chọn một layer trong danh sách hoặc canvas để chỉnh thuộc tính.'
        if len(selected)>1:return 'Đang chọn nhiều layer; chọn đúng một layer để dùng inspector số.'
        if locked(selected[0]):return 'Layer đang khóa biến đổi; mở khóa layer trước khi chỉnh.'
        return 'Đang chỉnh một layer. X, Y, rộng/cao là tỷ lệ theo khung; scale là hệ số ×; xoay tính bằng độ; opacity từ 0 đến 1.'

    def _slider_value_changed(self,name,value):
        if self.syncing:return
        self.syncing=True
        try:self.spins[name].setValue(value/self.slider_scales[name])
        finally:self.syncing=False
        # Mouse drags are a single gesture; keyboard steps remain single commands.
        if not self.sliders[name].isSliderDown():self.apply_inspector()

    def reset_inspector_property(self,name):
        data=self.data();layer=self.selected(data)
        if layer is None or locked(layer):return
        default=deepcopy(TRANSFORM_DEFAULTS[name])
        if layer['transform'][name]==default:return
        layer['transform'][name]=default
        self.commit(data,f'đặt lại {name}')

    def reset_inspector_transform(self):
        data=self.data();layer=self.selected(data)
        if layer is None or locked(layer):return
        defaults=deepcopy(TRANSFORM_DEFAULTS)
        if all(layer['transform'].get(name)==value for name,value in defaults.items()):return
        layer['transform'].update(defaults)
        self.commit(data,'đặt lại toàn bộ biến đổi layer')

    def _sync_selection(self,ids,primary=None):
        data=self.data()
        if data is None:
            self.selected_ids=set();self.selected_id=None;return
        valid={x['id'] for x in data['layers']}
        ids=self.expand_group_ids(set(ids)&valid,data)
        self.selected_ids=ids
        self.selected_id=primary if primary in ids else (next(iter(sorted(ids)),None))
        self.syncing=True
        try:
            for i in range(self.layers.count()):
                item=self.layers.item(i);item.setSelected(item.data(Qt.ItemDataRole.UserRole) in ids)
            selected_locked=any(locked(x) for x in data['layers'] if x['id'] in ids)
            for item in self.scene.items():
                if isinstance(item,LayerBoundsItem):
                    is_selected=item.layer_id in ids
                    item.setSelected(is_selected)
                    layer=next(x for x in data['layers'] if x['id']==item.layer_id)
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                                 not locked(layer) and (not selected_locked if is_selected else True))
        finally:self.syncing=False
        self.set_inspector(self.selected());self.update_actions()

    def select_rows(self):
        if self.syncing:return
        ids={item.data(Qt.ItemDataRole.UserRole) for item in self.layers.selectedItems()}
        current=self.layers.currentItem()
        primary=None if current is None else current.data(Qt.ItemDataRole.UserRole)
        self._sync_selection(ids,primary)

    def scene_selected(self):
        if self.syncing:return
        items=[x for x in self.scene.selectedItems() if isinstance(x,LayerBoundsItem)]
        ids={x.layer_id for x in items}
        primary=items[-1].layer_id if items else None
        self._sync_selection(ids,primary)

    def resized(self,layer_id,width_px,height_px,anchor_scene):
        data=self.data()
        if data is None:return
        layer=next((x for x in data['layers'] if x['id']==layer_id),None)
        if layer is None or locked(layer):self.update_project();return
        t=layer['transform'];W=data['output']['width'];H=data['output']['height']
        sx=Fraction(t['scale_x'][0],t['scale_x'][1]);sy=Fraction(t['scale_y'][0],t['scale_y'][1])
        if sx<=0 or sy<=0:self.update_project();return
        t['width']=pair(Fraction(str(width_px))/(W*sx))
        t['height']=pair(Fraction(str(height_px))/(H*sy))
        t['x']=pair(Fraction(str(anchor_scene.x()))/W)
        t['y']=pair(Fraction(str(anchor_scene.y()))/H)
        self.selected_id=layer_id;self.selected_ids={layer_id}
        self.commit(data,'đổi kích thước layer trên canvas')

    def rotated(self,layer_id,rotation):
        data=self.data()
        if data is None:return
        layer=next((x for x in data['layers'] if x['id']==layer_id),None)
        if layer is None or locked(layer):self.update_project();return
        layer['transform']['rotation']=pair(rotation)
        self.selected_id=layer_id;self.selected_ids={layer_id}
        self.commit(data,'xoay layer trên canvas')

    def dragged(self,layer_id,position,origin=None,alt=False):
        data=self.data()
        if data is None:return
        layers={x['id']:x for x in data['layers']}
        ids=self.expand_group_ids(self.selected_ids or {layer_id},data)
        if not ids or any(x not in layers or locked(layers[x]) for x in ids):
            self.update_project();return
        width=data['output']['width'];height=data['output']['height']
        if origin is not None:
            dx=Fraction(str(position.x()-origin.x()))/width
            dy=Fraction(str(position.y()-origin.y()))/height
            primary=layers[layer_id]['transform']
            current_x=Fraction(primary['x'][0],primary['x'][1])+dx
            current_y=Fraction(primary['y'][0],primary['y'][1])+dy
            if self.snap_check.isChecked() and not alt:
                step=Fraction(1,20)
                dx=(round(current_x/step)*step)-Fraction(primary['x'][0],primary['x'][1])
                dy=(round(current_y/step)*step)-Fraction(primary['y'][0],primary['y'][1])
            for selected_id in ids:
                transform=layers[selected_id]['transform']
                transform['x']=pair(Fraction(transform['x'][0],transform['x'][1])+dx)
                transform['y']=pair(Fraction(transform['y'][0],transform['y'][1])+dy)
        else:
            layer=layers[layer_id]
            layer['transform']['x']=pair(position.x()/width)
            layer['transform']['y']=pair(position.y()/height)
        self.selected_ids=ids;self.selected_id=layer_id
        self.commit(data,'di chuyển nhóm layer' if len(ids)>1 else 'di chuyển layer')

    def bring_into_frame(self):
        data=self.data()
        if data is None:return
        targets=self._selected_targets(data)
        if not targets:return
        for layer in targets:
            if locked(layer):
                self.status.setText('Nhóm có layer bị khóa; không thay đổi layer nào.')
                return
        changes={}
        for layer in targets:
            t=layer['transform']
            w=Fraction(t['width'][0],t['width'][1])*Fraction(t['scale_x'][0],t['scale_x'][1])
            h=Fraction(t['height'][0],t['height'][1])*Fraction(t['scale_y'][0],t['scale_y'][1])
            if w>1 or h>1:
                self.status.setText('Layer lớn hơn khung đầu ra; không thể đưa toàn bộ vào khung nếu không resize.')
                return
            x=Fraction(t['x'][0],t['x'][1]);y=Fraction(t['y'][0],t['y'][1])
            ox=Fraction(0) if t['anchor'].endswith('left') else (-w if t['anchor'].endswith('right') else -w/2)
            oy=Fraction(0) if t['anchor'].startswith('top') else (-h if t['anchor'].startswith('bottom') else -h/2)
            left=x+ox;top=y+oy
            if left<0:x-=left
            elif left+w>1:x-=left+w-1
            if top<0:y-=top
            elif top+h>1:y-=top+h-1
            changes[layer['id']]=(x,y)
        changed=False
        for layer in targets:
            x,y=changes[layer['id']];t=layer['transform']
            nx,ny=pair(x),pair(y)
            if t['x']!=nx or t['y']!=ny:
                t['x'],t['y']=nx,ny;changed=True
        if changed:self.commit(data,'đưa layer vào khung')

    def select_row(self,row):
        if self.syncing:return
        item=self.layers.item(row) if row>=0 else None
        self._sync_selection(set() if item is None else {item.data(Qt.ItemDataRole.UserRole)},
                             None if item is None else item.data(Qt.ItemDataRole.UserRole))

    def commit(self,data,label):
        session=self.get_session()
        if session is None or session.reconciliation_required or self.stopping:return False
        before=session.project.plan.to_dict();expected=session.revision
        data['revision']=expected+1;data['provenance']['project_revision']=expected+1
        try:
            plan=CompositionPlan.parse(data);self.committing=True
            session.commit(CompletedCommand(session.project.with_plan(plan),expected))
        except Exception:
            self.status.setText(f'Không xác nhận thay đổi ({label}); không tự gửi lại.')
            self.update_project();return False
        finally:self.committing=False
        self.undo_stack.append(before);self.redo_stack.clear()
        self.last_session=session;self.last_revision=session.revision
        self.update_project();self.project_changed.emit()
        self.status.setText(f'Đã lưu {label}; chưa có kết quả render.')
        return True

    def add_mask(self):
        data=self.data()
        if data is None:return
        layer_id=str(uuid4())
        data['layers'].append({'id':layer_id,'type':'mask',
            'z':max((x['z'] for x in data['layers']),default=-1)+1,
            'intervals':[{'start':[0,1],'end':data['output']['duration']}],
            'transform':{'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
                'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
                'anchor':'center','flip_x':False,'flip_y':False},
            'style':{'mode':'color','amount':[0,1],'feather_px':[0,1],'radius_px':[0,1],'color':[0,0,0,180]},
            'content':None,'keyframes':[],'visible':True,'locked_fields':[]})
        self.selected_id=layer_id;self.selected_ids={layer_id};self.commit(data,'thêm vùng che')

    def _selected_targets(self,data):
        ids=self.expand_group_ids(self.selected_ids,data)
        return [x for x in data['layers'] if x['id'] in ids]

    def group_selected(self):
        data=self.data()
        if data is None:return
        targets=self._selected_targets(data)
        if len(targets)<2:return
        group_id=str(uuid4())
        for layer in targets:layer['group_id']=group_id
        self.selected_ids={x['id'] for x in targets};self.selected_id=next(iter(sorted(self.selected_ids)))
        self.commit(data,'nhóm layer')

    def ungroup_selected(self):
        data=self.data()
        if data is None:return
        targets=self._selected_targets(data)
        grouped=[x for x in targets if x.get('group_id')]
        if not grouped:return
        for layer in targets:layer.pop('group_id',None)
        self.selected_ids={x['id'] for x in targets};self.selected_id=next(iter(sorted(self.selected_ids)))
        self.commit(data,'bỏ nhóm layer')

    def show_layer_context_menu(self,position):
        item=self.layers.itemAt(position)
        if item is not None and item not in self.layers.selectedItems():
            self._sync_selection({item.data(Qt.ItemDataRole.UserRole)},item.data(Qt.ItemDataRole.UserRole))
        menu=QMenu(self)
        group_action=menu.addAction('Nhóm các layer đã chọn')
        ungroup_action=menu.addAction('Bỏ nhóm')
        menu.addSeparator()
        lock_action=menu.addAction('Khóa/mở biến đổi')
        visibility_action=menu.addAction('Ẩn/hiện')
        menu.addSeparator()
        raise_action=menu.addAction('Đưa lên trên')
        lower_action=menu.addAction('Đưa xuống dưới')
        bring_action=menu.addAction('Đưa vào khung')
        delete_action=menu.addAction('Xóa layer đã chọn')
        group_action.setEnabled(self.group_button.isEnabled())
        ungroup_action.setEnabled(self.ungroup_button.isEnabled())
        selected=bool(self.selected_ids)
        for action in (lock_action,visibility_action,raise_action,lower_action,bring_action,delete_action):
            action.setEnabled(selected and not self.stopping)
        chosen=menu.exec(self.layers.viewport().mapToGlobal(position))
        if chosen is group_action:self.group_selected()
        elif chosen is ungroup_action:self.ungroup_selected()
        elif chosen is lock_action:self.toggle_lock()
        elif chosen is visibility_action:self.toggle_visibility()
        elif chosen is raise_action:self.move_selected(1)
        elif chosen is lower_action:self.move_selected(-1)
        elif chosen is bring_action:self.bring_into_frame()
        elif chosen is delete_action:self.delete_selected()

    def move_selected(self,direction):
        data=self.data()
        if data is None or not self.selected_ids or direction not in (-1,1):return
        ordered=sorted(data['layers'],key=lambda x:(x['z'],x['id']))
        ids=self.expand_group_ids(self.selected_ids,data)
        indices=[i for i,x in enumerate(ordered) if x['id'] in ids]
        if not indices:return
        changed=False
        if direction>0:
            for index in reversed(indices):
                if index<len(ordered)-1 and ordered[index+1]['id'] not in ids:
                    ordered[index],ordered[index+1]=ordered[index+1],ordered[index]
                    changed=True
        else:
            for index in indices:
                if index>0 and ordered[index-1]['id'] not in ids:
                    ordered[index],ordered[index-1]=ordered[index-1],ordered[index]
                    changed=True
        if not changed:return
        for z,item in enumerate(ordered):item['z']=z
        data['layers']=ordered
        self.selected_ids=ids;self.commit(data,'đổi thứ tự layer')

    def delete_selected(self):
        data=self.data()
        if data is None or not self.selected_ids:return
        ids=self.expand_group_ids(self.selected_ids,data)
        data['layers']=[x for x in data['layers'] if x['id'] not in ids]
        self.selected_ids=set();self.selected_id=None
        self.commit(data,'xóa layer khỏi project')

    def toggle_lock(self):
        data=self.data()
        if data is None:return
        targets=self._selected_targets(data)
        if not targets:return
        all_locked=all(locked(x) for x in targets)
        for layer in targets:
            locks=set(layer['locked_fields'])
            if all_locked:locks.difference_update(LOCKABLE|{'transform'})
            else:locks.add('transform')
            layer['locked_fields']=sorted(locks)
        self.commit(data,'khóa/mở biến đổi layer')

    def toggle_visibility(self):
        data=self.data()
        if data is None:return
        targets=self._selected_targets(data)
        if not targets:return
        make_visible=not all(x['visible'] for x in targets)
        for layer in targets:layer['visible']=make_visible
        self.commit(data,'ẩn/hiện layer')

    def apply_inspector(self):
        if self.syncing:return
        data=self.data();layer=self.selected(data)
        if layer is None or locked(layer):return
        t=layer['transform']
        original=self.original_transform or deepcopy(t)
        changed=False
        for name,s in self.spins.items():
            if abs(s.value()-val(original[name]))>0.000051:
                t[name]=pair(s.value());changed=True
        if self.anchor.currentText()!=original['anchor']:
            t['anchor']=self.anchor.currentText();changed=True
        if self.flip_x.isChecked()!=original['flip_x']:
            t['flip_x']=self.flip_x.isChecked();changed=True
        if self.flip_y.isChecked()!=original['flip_y']:
            t['flip_y']=self.flip_y.isChecked();changed=True
        if changed:self.commit(data,'chỉnh thông số layer')

    def undo(self):self._history(True)
    def redo(self):self._history(False)

    def _history(self,is_undo):
        session=self.get_session()
        source=self.undo_stack if is_undo else self.redo_stack
        target=self.redo_stack if is_undo else self.undo_stack
        if session is None or not source or session.reconciliation_required:return
        current=session.project.plan.to_dict();restored=deepcopy(source[-1])
        restored['revision']=session.revision+1;restored['provenance']['project_revision']=session.revision+1
        try:
            plan=CompositionPlan.parse(restored);self.committing=True
            session.commit(CompletedCommand(session.project.with_plan(plan),session.revision))
        except Exception:
            self.status.setText('Không xác nhận hoàn tác/làm lại; không tự gửi lại.');return
        finally:self.committing=False
        source.pop();target.append(current)
        self.last_session=session;self.last_revision=session.revision
        self.update_project();self.project_changed.emit()
