"""Basic layer list and numeric transform editor backed by ProjectSession CAS."""
from copy import deepcopy
from fractions import Fraction
from uuid import uuid4

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QFormLayout,QSplitter,
    QLabel,QListWidget,QListWidgetItem,QPushButton,QDoubleSpinBox,QComboBox,QCheckBox,
    QGraphicsView,QGraphicsScene,QGraphicsRectItem,QGraphicsItem)

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

class LayerEditorWorkspace(QWidget):
    project_changed=Signal()
    def __init__(self,get_session,parent=None):
        super().__init__(parent);self.get_session=get_session
        self.selected_id=None;self.undo_stack=[];self.redo_stack=[]
        self.syncing=False;self.committing=False;self.stopping=False
        self.last_session=None;self.last_revision=None;self.original_transform=None
        root=QVBoxLayout(self)
        self.notice=QLabel('Canvas hình học layer; chưa giải mã video hoặc render hiệu ứng. Không phải preview/export.')
        self.notice.setWordWrap(True);root.addWidget(self.notice)
        bar=QHBoxLayout()
        self.add_button=QPushButton('Thêm vùng che');self.delete_button=QPushButton('Xóa layer')
        self.lock_button=QPushButton('Khóa/mở');self.hide_button=QPushButton('Ẩn/hiện')
        self.undo_button=QPushButton('Hoàn tác');self.redo_button=QPushButton('Làm lại')
        for b in (self.add_button,self.delete_button,self.lock_button,self.hide_button,self.undo_button,self.redo_button):bar.addWidget(b)
        root.addLayout(bar)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('Layer'))
        self.layers=QListWidget();ll.addWidget(self.layers);split.addWidget(left)
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
        self.undo_button.clicked.connect(self.undo);self.redo_button.clicked.connect(self.redo)
        self.layers.currentRowChanged.connect(self.select_row);self.update_project()

    @property
    def busy(self):return False
    def request_stop(self):self.stopping=True;self.update_actions()
    def data(self):
        session=self.get_session()
        return None if session is None else session.project.plan.to_dict()
    def selected(self,data=None):
        data=self.data() if data is None else data
        return None if data is None else next((x for x in data['layers'] if x['id']==self.selected_id),None)

    def update_actions(self):
        session=self.get_session();ready=session is not None and not session.reconciliation_required and not self.stopping
        self.add_button.setEnabled(ready);self.undo_button.setEnabled(ready and bool(self.undo_stack))
        self.redo_button.setEnabled(ready and bool(self.redo_stack))
        layer=self.selected();edit=layer is not None and not locked(layer) and not self.stopping
        for s in self.spins.values():s.setEnabled(edit)
        self.anchor.setEnabled(edit);self.flip_x.setEnabled(edit);self.flip_y.setEnabled(edit)
        for b in (self.delete_button,self.lock_button,self.hide_button):b.setEnabled(layer is not None and not self.stopping)
        if layer is None:self.status.setText('Chưa chọn layer.')
        else:self.status.setText(('Đã khóa biến đổi' if locked(layer) else 'Có thể chỉnh sửa')+
                                 (' · đang ẩn' if not layer['visible'] else ' · đang hiện'))

    def update_project(self):
        session=self.get_session()
        if session is None:
            self.last_session=None;self.last_revision=None;self.undo_stack.clear();self.redo_stack.clear()
            self.selected_id=None;self.layers.clear();self.scene.clear();self.scene.setSceneRect(QRectF(0,0,640,360))
            self.update_actions();return
        if not self.committing and (session is not self.last_session or session.revision!=self.last_revision):
            self.undo_stack.clear();self.redo_stack.clear()
        self.last_session=session;self.last_revision=session.revision
        data=session.project.plan.to_dict();W=data['output']['width'];H=data['output']['height']
        self.syncing=True
        try:
            self.layers.clear()
            for layer in sorted(data['layers'],key=lambda x:(x['z'],x['id'])):
                row=QListWidgetItem(f"{layer['z']} · {layer['type']} · "+
                    ('ẩn' if not layer['visible'] else 'hiện')+' · '+('khóa' if locked(layer) else 'mở'))
                row.setData(Qt.ItemDataRole.UserRole,layer['id']);self.layers.addItem(row)
                if layer['id']==self.selected_id:self.layers.setCurrentItem(row)
            if self.selected_id not in {x['id'] for x in data['layers']}:self.selected_id=None
            self.scene.clear();self.scene.setSceneRect(QRectF(0,0,W,H))
            bg=QGraphicsRectItem(QRectF(0,0,W,H));bg.setBrush(QBrush(QColor('#202832')))
            bg.setPen(QPen(QColor('#d0d7de'),2));bg.setZValue(-10000)
            bg.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,False);self.scene.addItem(bg)
            for layer in data['layers']:
                if not layer['visible']:continue
                t=layer['transform'];w=val(t['width'])*W*val(t['scale_x']);h=val(t['height'])*H*val(t['scale_y'])
                x,y=offset(t['anchor'],w,h);item=QGraphicsRectItem(QRectF(x,y,w,h))
                item.setPos(val(t['x'])*W,val(t['y'])*H);item.setRotation(val(t['rotation']))
                item.setOpacity(val(t['opacity']));item.setZValue(layer['z']+1)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,True)
                item.setData(0,layer['id']);item.setToolTip(f"{layer['type']} · z={layer['z']}")
                if layer['type']=='mask':
                    rgba=layer['style']['color'];fill=QColor(*rgba);fill.setAlpha(min(110,rgba[3]));edge=QColor(245,190,80)
                else:fill=QColor(90,170,240,45);edge=QColor(90,190,255)
                item.setBrush(QBrush(fill));item.setPen(QPen(edge,2,Qt.PenStyle.DashLine));self.scene.addItem(item)
            self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        finally:self.syncing=False
        self.set_inspector(self.selected(data));self.update_actions()

    def set_inspector(self,layer):
        self.syncing=True
        try:
            if layer is not None:
                t=layer['transform'];self.original_transform=deepcopy(t)
                for name,s in self.spins.items():s.setValue(val(t[name]))
            else:self.original_transform=None
                self.anchor.setCurrentText(t['anchor']);self.flip_x.setChecked(t['flip_x']);self.flip_y.setChecked(t['flip_y'])
        finally:self.syncing=False

    def select_row(self,row):
        if self.syncing:return
        item=self.layers.item(row) if row>=0 else None
        self.selected_id=None if item is None else item.data(Qt.ItemDataRole.UserRole)
        self.update_project()

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
        self.selected_id=layer_id;self.commit(data,'thêm vùng che')

    def delete_selected(self):
        data=self.data()
        if data is None or self.selected_id is None:return
        data['layers']=[x for x in data['layers'] if x['id']!=self.selected_id]
        self.selected_id=None;self.commit(data,'xóa layer khỏi project')

    def toggle_lock(self):
        data=self.data();layer=self.selected(data)
        if layer is None:return
        locks=set(layer['locked_fields'])
        if 'transform' in locks:locks.remove('transform')
        else:locks.add('transform')
        layer['locked_fields']=sorted(locks);self.commit(data,'khóa biến đổi')

    def toggle_visibility(self):
        data=self.data();layer=self.selected(data)
        if layer is None:return
        layer['visible']=not layer['visible'];self.commit(data,'ẩn/hiện layer')

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
