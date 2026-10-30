from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QBrush, QPen, QPixmap
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
    def __init__(self, timeline, item, start, duration, row, color, label, is_clip=False,is_audio=False):
        super().__init__(0, 0, max(8,duration*timeline.scale_x), 30)
        self.timeline,self.item,self.is_clip = timeline,item,is_clip
        self.start,self.duration = start,duration
        self.is_audio=is_audio
        self.setPos(70+start*timeline.scale_x,row)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor('#8996b4')))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setToolTip(label)
        self.thumbnail_pixmaps=[]
        if is_clip:
            for path in timeline.editor.thumbnail_assets(item):
                pixmap=QPixmap(str(path))
                if not pixmap.isNull():self.thumbnail_pixmaps.append(pixmap)

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
            if self.is_audio:self.item['offset']=value
            elif self.is_clip: self.item.offset=value
            else:
                self.item.start=value
                self.item.end=value+self.duration
            self.setX(70+value*self.timeline.scale_x)
        else:
            length=max(.05,self.duration+delta)
            if self.is_audio:
                end=self.item.get('trim_start',0)+length;source=self.timeline.editor.waveforms.get(self.item['path'],{}).get('duration')
                self.item['trim_end']=min(end,source) if source else end;length=self.item['trim_end']-self.item.get('trim_start',0)
            elif self.is_clip:
                end=self.item.start+length*self.item.speed
                self.item.end=min(self.item.source_duration or end,end)
                length=(self.item.end-self.item.start)/self.item.speed
            else: self.item.end=self.item.start+length
            self.setRect(0,0,length*self.timeline.scale_x,30)

    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        self.timeline.editor.commit('Chỉnh timeline')

    def paint(self,painter,option,widget=None):
        super().paint(painter,option,widget)
        if self.is_clip and self.thumbnail_pixmaps:
            area=self.rect().adjusted(2,2,-2,-2)
            count=len(self.thumbnail_pixmaps)
            for index,pixmap in enumerate(self.thumbnail_pixmaps):
                target=QRectF(area.left()+index*area.width()/count,area.top(),
                              area.width()/count,area.height())
                painter.drawPixmap(target,pixmap,QRectF(pixmap.rect()))
            painter.setPen(QPen(QColor('#8996b4')))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect())
        path=self.item.get('path') if self.is_audio else self.item.path if self.is_clip else None
        wave=self.timeline.editor.waveforms.get(path)
        if wave and wave.get('path'):
            image=QPixmap(wave['path']);duration=wave['duration'];start=self.item.get('trim_start',0) if self.is_audio else self.item.start
            source_length=self.duration if self.is_audio else self.duration*self.item.speed
            if not image.isNull() and duration>0:
                rect=self.rect().adjusted(1,2,-1,-2)
                if self.is_clip and self.thumbnail_pixmaps:
                    rect.setTop(rect.top()+rect.height()*.65)
                painter.setOpacity(.7)
                painter.drawPixmap(rect,image,QRectF(image.width()*start/duration,0,max(1,min(image.width()-image.width()*start/duration,image.width()*source_length/duration)),image.height()))


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

    def visible_clips(self,limit=8):
        if not self.editor.composition.clips:
            return []
        viewport=self.mapToScene(self.viewport().rect()).boundingRect()
        low=max(0,(viewport.left()-70)/self.scale_x)
        high=max(low,(viewport.right()-70)/self.scale_x)
        visible=[clip for clip,offset,duration in clip_positions(self.editor.composition)
                 if offset<high and offset+duration>low]
        return visible[:limit]

    def rebuild(self):
        scene=self.scene()
        scene.clear()
        positions=clip_positions(self.editor.composition)
        duration=max([offset+length for _,offset,length in positions]+[10])
        stride=max(1,int(duration/300))
        height=240+36*len(self.editor.composition.audio)
        for second in range(0,int(duration)+2,stride):
            x=70+second*self.scale_x
            scene.addLine(x,0,x,height,QPen(QColor('#28364c')))
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
        for i,track in enumerate(self.editor.composition.audio):
            row=196+i*36;start=track.get('offset',0);wave=self.editor.waveforms.get(track['path'],{})
            end=track.get('trim_end') or wave.get('duration',duration)
            length=max(.05,end-track.get('trim_start',0))
            if track.get('loop'):length=max(.05,duration-start)
            item=Segment(self,track,start,min(length,max(.05,duration-start)),row,'#286958',track['path'],is_audio=True);scene.addItem(item)
        for marker in self.markers:
            scene.addLine(70+marker*self.scale_x,0,70+marker*self.scale_x,220,QPen(QColor('#ffc773')))
        self.head=scene.addLine(70+self.playhead*self.scale_x,0,70+self.playhead*self.scale_x,height,QPen(QColor('#ec7f99'),2))
        self.setSceneRect(0,0,100+duration*self.scale_x,height)

    def position(self,seconds):
        self.playhead=seconds
        if hasattr(self,'head'):self.head.setLine(70+seconds*self.scale_x,0,70+seconds*self.scale_x,230)

    def keyPressEvent(self,event):
        if event.key() in {Qt.Key.Key_Left,Qt.Key.Key_Right}:
            step=1 if event.modifiers()&Qt.KeyboardModifier.ShiftModifier else 1/self.editor.composition.fps
            self.position(max(0,self.playhead+(-step if event.key()==Qt.Key.Key_Left else step)));self.seek.emit(self.playhead)
        elif event.key() in {Qt.Key.Key_Plus,Qt.Key.Key_Equal,Qt.Key.Key_Minus}:
            self.scale_x=max(10,min(500,self.scale_x*(1/1.2 if event.key()==Qt.Key.Key_Minus else 1.2)));self.rebuild()
        else:super().keyPressEvent(event)

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
            self.editor.load_thumbnails()
        else: super().wheelEvent(event)

    def scrollContentsBy(self,dx,dy):
        super().scrollContentsBy(dx,dy)
        if hasattr(self.editor,'timeline') and self.editor.timeline is self:
            self.editor.load_thumbnails()
