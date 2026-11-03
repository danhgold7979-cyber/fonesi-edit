"""Basic layer list and numeric transform editor backed by ProjectSession CAS."""
from copy import deepcopy
from fractions import Fraction
from uuid import uuid4

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QSplitter,
    QLabel,QListWidget,QListWidgetItem,QPushButton,QDoubleSpinBox,QComboBox,QCheckBox,
    QGraphicsView,QGraphicsScene,QGraphicsRectItem,QGraphicsItem,QAbstractItemView,QMenu)

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand

ANCHORS=('top_left','top_center','top_right','center_left','center','center_right',
         'bottom_left','bottom_center','bottom_right')
LOCKABLE={'x','y','width','height','scale_x','scale_y','rotation','opacity','anchor','flip_x','flip_y'}

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
    def __init__(self,layer,width,height,moved,can_move=True):
        t=layer['transform'];w=val(t['width'])*width*val(t['scale_x']);h=val(t['height'])*height*val(t['scale_y'])
        x,y=offset(t['anchor'],w,h)
        super().__init__(QRectF(x,y,w,h))
        self.layer_id=layer['id'];self.moved=moved;self.pressed=None
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

    def mousePressEvent(self,event):
        self.pressed=QPointF(self.pos())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        if self.pressed is not None and self.pos()!=self.pressed:
            layer_id=self.layer_id;position=QPointF(self.pos());origin=QPointF(self.pressed)
            QTimer.singleShot(0,lambda:self.moved(layer_id,position,origin))
        self.pressed=None


class LayerEditorWorkspace(QWidget):
    project_changed=Signal()
    def __init__(self,get_session,parent=None):
        super().__init__(parent);self.get_session=get_session
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
        self.undo_button=QPushButton('Hoàn tác');self.redo_button=QPushButton('Làm lại')
        for b in (self.add_button,self.delete_button,self.lock_button,self.hide_button,self.up_button,self.down_button,self.group_button,self.ungroup_button,self.undo_button,self.redo_button):bar.addWidget(b)
        root.addLayout(bar)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('Layer'))
        self.layers=QListWidget();self.layers.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layers.itemSelectionChanged.connect(self.select_rows)
        self.layers.customContextMenuRequested.connect(self.show_layer_context_menu)
        ll.addWidget(self.layers);split.addWidget(left)
        self.scene=QGraphicsScene(self);self.view=QGraphicsView(self.scene);split.addWidget(self.view)
        right=QWidget();form=QFormLayout(right);self.spins={}
        for name,label,lo,hi in (('x','X',-10,10),('y','Y',-10,10),('width','Rộng',.0001,10),
            ('height','Cao',.0001,10),('scale_x','Tỷ lệ X',.0001,100),('scale_y','Tỷ lệ Y',.0001,100),
            ('rotation','Xoay',-36000,36000),('opacity','Độ mờ',0,1)):
            s=QDoubleSpinBox();s.setDecimals(4);s.setRange(lo,hi);s.setSingleStep(.01)
            s.editingFinished.connect(self.apply_inspector);self.spins[name]=s;form.addRow(label,s)
        self.anchor=QComboBox();self.anchor.addItems(ANCHORS);self.anchor.activated.connect(self.apply_inspector)
        form.addRow('Điểm neo',self.anchor)
        self.flip_x=QCheckBox('Lật ngang');self.flip_y=QCheckBox('Lật dọc')
        self.flip_x.toggled.connect(self.apply_inspector);self.flip_y.toggled.connect(self.apply_inspector)
        form.addRow(self.flip_x);form.addRow(self.flip_y)
        self.status=QLabel('Chưa chọn layer.');self.status.setWordWrap(True);form.addRow(self.status)
        split.addWidget(right);split.setStretchFactor(0,1);split.setStretchFactor(1,4);split.setStretchFactor(2,1)
        root.addWidget(split)
        self.add_button.clicked.connect(self.add_mask);self.delete_button.clicked.connect(self.delete_selected)
        self.lock_button.clicked.connect(self.toggle_lock);self.hide_button.clicked.connect(self.toggle_visibility)
        self.up_button.clicked.connect(lambda:self.move_selected(1));self.down_button.clicked.connect(lambda:self.move_selected(-1))
        self.group_button.clicked.connect(self.group_selected);self.ungroup_button.clicked.connect(self.ungroup_selected)
        self.undo_button.clicked.connect(self.undo);self.redo_button.clicked.connect(self.redo)
        self.scene.selectionChanged.connect(self.scene_selected)
        self.update_project()

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
        for s in self.spins.values():s.setEnabled(edit)
        self.anchor.setEnabled(edit);self.flip_x.setEnabled(edit);self.flip_y.setEnabled(edit)
        has_selection=bool(selected) and ready
        for b in (self.delete_button,self.lock_button,self.hide_button,self.up_button,self.down_button):
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
            for layer in data['layers']:
                if not layer['visible']:continue
                can_move=not selected_locked if layer['id'] in self.selected_ids else not locked(layer)
                item=LayerBoundsItem(layer,W,H,self.dragged,can_move)
                self.scene.addItem(item)
                if layer['id'] in self.selected_ids:item.setSelected(True)
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        finally:self.syncing=False
        self.set_inspector(self.selected(data));self.update_actions()

    def set_inspector(self,layer):
        self.syncing=True
        try:
            if layer is not None:
                t=layer['transform'];self.original_transform=deepcopy(t)
                for name,s in self.spins.items():s.setValue(val(t[name]))
                self.anchor.setCurrentText(t['anchor'])
                self.flip_x.setChecked(t['flip_x']);self.flip_y.setChecked(t['flip_y'])
            else:
                self.original_transform=None
        finally:self.syncing=False

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

    def dragged(self,layer_id,position,origin=None):
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
        delete_action=menu.addAction('Xóa layer đã chọn')
        group_action.setEnabled(self.group_button.isEnabled())
        ungroup_action.setEnabled(self.ungroup_button.isEnabled())
        selected=bool(self.selected_ids)
        for action in (lock_action,visibility_action,raise_action,lower_action,delete_action):
            action.setEnabled(selected and not self.stopping)
        chosen=menu.exec(self.layers.viewport().mapToGlobal(position))
        if chosen is group_action:self.group_selected()
        elif chosen is ungroup_action:self.ungroup_selected()
        elif chosen is lock_action:self.toggle_lock()
        elif chosen is visibility_action:self.toggle_visibility()
        elif chosen is raise_action:self.move_selected(1)
        elif chosen is lower_action:self.move_selected(-1)
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
