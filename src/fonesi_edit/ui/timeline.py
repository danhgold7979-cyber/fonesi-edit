from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView


def clip_positions(composition):
    cursor, result = 0.0, []
    for clip in composition.clips:
        length = max(.01, ((clip.end or clip.source_duration or 1)-clip.start)/clip.speed+clip.freeze)
        offset = cursor if clip.offset is None else clip.offset
        result.append((clip, offset, length))
        cursor = offset + length - composition.transition
    return result


class Segment(QGraphicsRectItem):
    def __init__(self, timeline, item, start, duration, row, color, label, is_clip=False):
        super().__init__(0, 0, max(8,duration*timeline.scale_x), 30)
        self.timeline,self.item,self.is_clip = timeline,item,is_clip
        self.start,self.duration = start,duration
        self.setPos(70+start*timeline.scale_x,row)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor('#8996b4')))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setToolTip(label)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.timeline.editor.begin()
        self.origin = event.scenePos().x()
        self.mode = 'trim' if event.pos().x() > self.rect().width()-10 else 'move'

    def mouseMoveEvent(self, event):
        if getattr(self.item,'locked',False): return
        delta = (event.scenePos().x()-self.origin)/self.timeline.scale_x
        if self.mode == 'move':
            value = max(0,self.start+delta)
            if not event.modifiers() & Qt.KeyboardModifier.AltModifier:
                value = round(value*10)/10
            if self.is_clip: self.item.offset=value
            else:
                self.item.start=value
                self.item.end=value+self.duration
            self.setX(70+value*self.timeline.scale_x)
        else:
            length=max(.05,self.duration+delta)
            if self.is_clip:
                end=self.item.start+length*self.item.speed
                self.item.end=min(self.item.source_duration or end,end)
                length=(self.item.end-self.item.start)/self.item.speed
            else: self.item.end=self.item.start+length
            self.setRect(0,0,length*self.timeline.scale_x,30)

    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        self.timeline.editor.commit('Chỉnh timeline')


class Timeline(QGraphicsView):
    seek=Signal(float)

    def __init__(self,editor):
        super().__init__()
        self.editor=editor
        self.scale_x=60
        self.playhead=0.0
        self.setScene(QGraphicsScene(self))
        self.setMinimumHeight(180)
        self.markers=[]

    def rebuild(self):
        scene=self.scene()
        scene.clear()
        positions=clip_positions(self.editor.composition)
        duration=max([offset+length for _,offset,length in positions]+[10])
        for second in range(0,int(duration)+2):
            x=70+second*self.scale_x
            scene.addLine(x,0,x,210,QPen(QColor('#28364c')))
            label=scene.addText(str(second)+'s');label.setDefaultTextColor(QColor('#aab6ce'));label.setPos(x,0)
        for label,row in [('Video',36),('Mask',76),('Logo',116),('Chữ/Sub',156),('Audio',196)]:
            item=scene.addText(label);item.setDefaultTextColor(QColor('#bbc9e6'));item.setPos(0,row)
        for clip,offset,length in positions:
            item=Segment(self,clip,offset,length,36,'#345f95',clip.path,True)
            scene.addItem(item)
        for layer in self.editor.composition.layers:
            row={'mask':76,'image':116,'text':156,'subtitle':156}[layer.kind]
            item=Segment(self,layer,layer.start,max(.1,(layer.end or duration)-layer.start),row,'#6c52a8',layer.name)
            scene.addItem(item)
        for marker in self.markers:
            scene.addLine(70+marker*self.scale_x,0,70+marker*self.scale_x,220,QPen(QColor('#ffc773')))
        self.head=scene.addLine(70+self.playhead*self.scale_x,0,70+self.playhead*self.scale_x,230,QPen(QColor('#ec7f99'),2))
        self.setSceneRect(0,0,100+duration*self.scale_x,240)

    def position(self,seconds):
        self.playhead=seconds
        if hasattr(self,'head'):self.head.setLine(70+seconds*self.scale_x,0,70+seconds*self.scale_x,230)

    def mousePressEvent(self,event):
        point=self.mapToScene(event.pos())
        if point.y()<30:
            self.playhead=max(0,(point.x()-70)/self.scale_x)
            self.seek.emit(self.playhead)
            self.rebuild()
        super().mousePressEvent(event)

    def wheelEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.scale_x=max(10,min(500,self.scale_x*(1.2 if event.angleDelta().y()>0 else 1/1.2)))
            self.rebuild()
        else: super().wheelEvent(event)
