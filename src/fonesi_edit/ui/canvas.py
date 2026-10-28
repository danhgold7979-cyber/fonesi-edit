from __future__ import annotations
from dataclasses import replace
import math
from PIL import Image
from PySide6.QtCore import Qt,QRectF,QPointF,Signal
from PySide6.QtGui import QPainter,QColor,QPen,QImage
from PySide6.QtWidgets import QWidget,QInputDialog
from ..core.model import Project,CommandHistory
from ..services.composition import paint_frame


def qt_image(image:Image.Image):
    rgba=image.convert('RGBA');data=rgba.tobytes()
    return QImage(data,rgba.width,rgba.height,rgba.width*4,QImage.Format.Format_RGBA8888).copy()


class Canvas(QWidget):
    changed=Signal();selected=Signal(str);error=Signal(str)
    def __init__(self,project:Project,history:CommandHistory,parent=None):
        super().__init__(parent);self.project=project;self.history=history;self.selection=set();self.time=0
        self.base=None;self.zoom=1.;self.grid=True;self.snap=True;self.drag=None;self.reference=None
        self.setMinimumSize(440,270);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setMouseTracking(True)
        self.setToolTip('Kéo: di chuyển • góc phải dưới: kích thước • tay nắm trên: xoay • Alt: bỏ snap • Esc: hủy')

    def viewport(self):
        scale=min((self.width()-40)/self.project.width,(self.height()-40)/self.project.height)*self.zoom
        w,h=self.project.width*scale,self.project.height*scale
        return QRectF((self.width()-w)/2,(self.height()-h)/2,w,h),scale

    def point(self,pos):
        rect,scale=self.viewport();return QPointF((pos.x()-rect.x())/scale,(pos.y()-rect.y())/scale)

    def bounds(self,layer):
        values=layer.at(self.time)
        return QRectF(values['x']*self.project.width,values['y']*self.project.height,values['width']*self.project.width,values['height']*self.project.height)

    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect(),QColor('#0b1220'));rect,scale=self.viewport()
        base=self.base or Image.new('RGB',(self.project.width,self.project.height),'#172338')
        try:image=self.reference if self.reference is not None else paint_frame(base,self.project,self.time)
        except Exception as exc:
            image=base;painter.setPen(QColor('#f59e0b'));painter.drawText(12,18,str(exc)[:120])
        painter.drawImage(rect,qt_image(image));painter.setPen(QPen(QColor('#53647b'),1));painter.drawRect(rect)
        if self.grid:
            painter.setPen(QPen(QColor(160,180,200,70),1,Qt.PenStyle.DashLine))
            for f in (1/3,2/3):
                painter.drawLine(QPointF(rect.x()+rect.width()*f,rect.y()),QPointF(rect.x()+rect.width()*f,rect.bottom()))
                painter.drawLine(QPointF(rect.x(),rect.y()+rect.height()*f),QPointF(rect.right(),rect.y()+rect.height()*f))
            painter.drawRect(rect.adjusted(rect.width()*.05,rect.height()*.05,-rect.width()*.05,-rect.height()*.05))
        for layer in self.project.layers:
            if layer.id not in self.selection:continue
            b=self.bounds(layer);b=QRectF(rect.x()+b.x()*scale,rect.y()+b.y()*scale,b.width()*scale,b.height()*scale)
            painter.setPen(QPen(QColor('#2dd4bf' if not layer.locked else '#f59e0b'),2));painter.setBrush(Qt.BrushStyle.NoBrush);painter.drawRect(b)
            painter.setBrush(QColor('#2dd4bf'));painter.drawRect(QRectF(b.right()-5,b.bottom()-5,10,10))
            painter.drawLine(QPointF(b.center().x(),b.top()),QPointF(b.center().x(),b.top()-20));painter.drawEllipse(QPointF(b.center().x(),b.top()-20),5,5)
        painter.end()

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:return
        self.setFocus();self.reference=None;p=self.point(event.position());rect,scale=self.viewport();hit=None;mode='move'
        for layer in reversed(sorted(self.project.layers,key=lambda l:l.z)):
            if not layer.visible or layer.locked or not layer.start<=self.time<layer.end:continue
            b=self.bounds(layer)
            if layer.id in self.selection and math.hypot(p.x()-b.right(),p.y()-b.bottom())<12/scale:hit=layer;mode='resize';break
            if layer.id in self.selection and math.hypot(p.x()-b.center().x(),p.y()-(b.top()-20/scale))<12/scale:hit=layer;mode='rotate';break
            if b.contains(p):hit=layer;break
        if not hit:self.selection.clear();self.update();return
        if event.modifiers()&Qt.KeyboardModifier.ShiftModifier:self.selection.symmetric_difference_update({hit.id})
        elif hit.id not in self.selection:self.selection={hit.id}
        self.selected.emit(hit.id);self.history.begin()
        originals={l.id:(l.x,l.y,l.width,l.height,l.rotation) for l in self.project.layers if l.id in self.selection and not l.locked}
        self.drag={'start':p,'mode':mode,'id':hit.id,'originals':originals};self.update()

    def mouseMoveEvent(self,event):
        if not self.drag:return
        p=self.point(event.position());dx=(p.x()-self.drag['start'].x())/self.project.width;dy=(p.y()-self.drag['start'].y())/self.project.height
        for l in self.project.layers:
            if l.id not in self.drag['originals']:continue
            x,y,w,h,r=self.drag['originals'][l.id]
            if self.drag['mode']=='move':
                l.x=x+dx;l.y=y+dy
                if self.snap and not event.modifiers()&Qt.KeyboardModifier.AltModifier:
                    for edge in (0,.5,1):
                        for offset in (0,w/2,w):
                            if abs(l.x+offset-edge)<.01:l.x=edge-offset
                        for offset in (0,h/2,h):
                            if abs(l.y+offset-edge)<.01:l.y=edge-offset
            elif self.drag['mode']=='resize':l.width=max(.01,w+dx);l.height=max(.01,h+dy)
            else:
                cx=(x+w/2)*self.project.width;cy=(y+h/2)*self.project.height
                l.rotation=math.degrees(math.atan2(p.y()-cy,p.x()-cx))+90
        self.update();self.changed.emit()

    def mouseReleaseEvent(self,event):
        if self.drag:
            self.history.commit(self.drag['mode']);self.drag=None;self.changed.emit();self.update()

    def mouseDoubleClickEvent(self,event):
        if len(self.selection)!=1:return
        layer=next((l for l in self.project.layers if l.id in self.selection),None)
        if layer and layer.kind=='text' and not layer.locked:
            value,ok=QInputDialog.getMultiLineText(self,'Sửa chữ','Nội dung',layer.text)
            if ok:self.history.begin();layer.text=value;self.history.commit('text');self.changed.emit();self.update()

    def keyPressEvent(self,event):
        key=event.key()
        if key==Qt.Key.Key_Escape:
            if self.drag:self.history.cancel();self.drag=None;self.changed.emit()
            else:self.selection.clear()
            self.update();return
        if key==Qt.Key.Key_Delete:
            self.history.begin();self.project.layers[:]=[l for l in self.project.layers if l.id not in self.selection or l.locked];self.history.commit('remove objects');self.selection.intersection_update({l.id for l in self.project.layers});self.changed.emit();self.update();return
        delta={Qt.Key.Key_Left:(-1,0),Qt.Key.Key_Right:(1,0),Qt.Key.Key_Up:(0,-1),Qt.Key.Key_Down:(0,1)}.get(key)
        if delta and self.selection:
            step=10 if event.modifiers()&Qt.KeyboardModifier.ShiftModifier else 1
            self.history.begin()
            for l in self.project.layers:
                if l.id in self.selection and not l.locked:l.x+=delta[0]*step/self.project.width;l.y+=delta[1]*step/self.project.height
            self.history.commit('nudge');self.changed.emit();self.update();return
        super().keyPressEvent(event)
