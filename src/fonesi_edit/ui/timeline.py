from PySide6.QtCore import Qt,QRectF,Signal
from PySide6.QtGui import QPainter,QColor,QPen
from PySide6.QtWidgets import QWidget
from ..core.model import US,Clip,uid

class Timeline(QWidget):
    seek=Signal(object);changed=Signal()
    def __init__(self,project,history,parent=None):
        super().__init__(parent);self.project=project;self.history=history;self.time=0;self.drag=None;self.zoom=1.;self.waveform=[];self.setMinimumHeight(205);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    def scale(self):return (self.width()-100)/max(US,self.project.duration)*self.zoom
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#111c2e'));s=self.scale()
        for row,title in enumerate(['Video','Layer','Phụ đề']):
            y=30+row*40;p.setPen(QColor('#9cabc2'));p.drawText(8,y+20,title);p.setPen(QColor('#28364b'));p.drawLine(90,y+35,self.width(),y+35)
        p.setPen(QColor('#9cabc2'))
        duration=max(US,self.project.duration)
        for i in range(11):
            t=duration*i/10;x=90+t*s;p.drawText(int(x),16,f'{t/US:.1f}');p.drawLine(int(x),20,int(x),25)
        for row,objects in enumerate([self.project.clips,self.project.layers,self.project.cues]):
            for x in objects:
                a=x.offset if row==0 else x.start;b=a+x.time_map.duration if row==0 else x.end
                r=QRectF(90+a*s,30+row*40,max(3,(b-a)*s),28)
                p.setBrush(QColor(['#2563a5','#167e80','#7c4d9e'][row]));p.setPen(QColor('#68b9c3'));p.drawRoundedRect(r,4,4)
                p.setPen(QColor('#ffffff'));p.drawText(r.adjusted(5,0,-3,0),Qt.AlignmentFlag.AlignVCenter,str(getattr(x,'name',getattr(x,'text','Clip')))[:25])
        if self.waveform:
            p.setPen(QPen(QColor('#58b6ae'),1));usable=self.width()-100
            for index,point in enumerate(self.waveform):
                x=90+index/len(self.waveform)*usable;p.drawLine(int(x),int(185-point['max']*15),int(x),int(185-point['min']*15))
        p.setPen(QPen(QColor('#f4b942'),2));x=90+self.time*s;p.drawLine(int(x),20,int(x),self.height());p.end()
    def mousePressEvent(self,event):
        self.setFocus();s=self.scale();t=max(0,round((event.position().x()-90)/s));row=int((event.position().y()-30)//40)
        if row in (1,2):
            items=self.project.layers if row==1 else self.project.cues
            for item in reversed(items):
                if item.start<=t<=item.end and not item.locked:
                    mode='left' if abs(t-item.start)*s<8 else 'right' if abs(t-item.end)*s<8 else 'move'
                    self.history.begin();self.drag=(item.id,row,t,item.start,item.end,mode);return
        self.time=min(t,self.project.duration);self.seek.emit(self.time);self.update()
    def mouseMoveEvent(self,event):
        if not self.drag:return
        identity,row,t,a,b,mode=self.drag;now=max(0,round((event.position().x()-90)/self.scale()));delta=now-t
        obj=next(x for x in (self.project.layers if row==1 else self.project.cues) if x.id==identity)
        if mode=='move':obj.start=max(0,min(self.project.duration-(b-a),a+delta));obj.end=obj.start+(b-a)
        elif mode=='left':obj.start=max(0,min(b-1000,a+delta))
        else:obj.end=max(a+1000,min(self.project.duration,b+delta))
        self.changed.emit();self.update()
    def mouseReleaseEvent(self,event):
        if self.drag:self.history.commit('timeline '+self.drag[-1]);self.drag=None;self.changed.emit()
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self.drag:self.history.cancel();self.drag=None;self.changed.emit();self.update();return
        if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right):
            from fractions import Fraction
            step=US if event.modifiers()&Qt.KeyboardModifier.ShiftModifier else round(US/Fraction(self.project.fps))
            self.time=max(0,min(self.project.duration,self.time+(-step if event.key()==Qt.Key.Key_Left else step)));self.seek.emit(self.time);self.update();return
        super().keyPressEvent(event)
