"""Single-cue timing lane for the existing Subtitle tab; never edits source media."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsView


def retime_cue(start_ms, end_ms, delta_ms, mode="move"):
    """Apply an integer drag to one cue without modifying its contents."""
    if any(type(value) is not int for value in (start_ms,end_ms,delta_ms)):
        raise ValueError("Cue timing drag requires integer milliseconds")
    if start_ms<0 or end_ms<=start_ms:
        raise ValueError("Cue timing interval is invalid")
    if mode=="move":
        new_start=max(0,start_ms+delta_ms)
        return new_start,new_start+(end_ms-start_ms)
    if mode=="start":
        return max(0,min(end_ms-1,start_ms+delta_ms)),end_ms
    if mode=="end":
        return start_ms,max(start_ms+1,end_ms+delta_ms)
    raise ValueError("Unknown cue timing drag mode")


class CueTimingBar(QGraphicsRectItem):
    """A single selected cue. Preview follows the pointer, commit only on release."""
    def __init__(self,view,start_ms,end_ms):
        self.view=view
        self.start_ms,self.end_ms=start_ms,end_ms
        super().__init__(0,0,1,26)
        self.setBrush(QBrush(QColor("#5f79c9")))
        self.setPen(QPen(QColor("#d0daf9")))
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptHoverEvents(True)
        self.origin=None
        self.mode=None
        self.preview=(start_ms,end_ms)
        view._position_bar(self,start_ms,end_ms)

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:
            event.ignore()
            return
        width=self.rect().width()
        edge=min(8.0,width/4)
        cursor=event.pos().x()
        self.mode="start" if cursor<=edge else "end" if cursor>=width-edge else "move"
        self.origin=event.scenePos().x()
        self.preview=(self.start_ms,self.end_ms)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mouseMoveEvent(self,event):
        if self.origin is None:
            event.ignore()
            return
        difference=event.scenePos().x()-self.origin
        delta_ms=int(round(difference/(self.view.pixels_per_ms*10)))*10
        new_start,new_end=retime_cue(self.start_ms,self.end_ms,delta_ms,self.mode)
        self.preview=(new_start,new_end)
        self.view._position_bar(self,new_start,new_end)
        event.accept()

    def mouseReleaseEvent(self,event):
        if self.origin is None:
            event.ignore()
            return
        self.origin=None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if self.preview!=(self.start_ms,self.end_ms):
            self.view.timingChanged.emit(*self.preview)
        event.accept()

    def cancel_drag(self):
        if self.origin is None:
            return
        self.origin=None
        self.preview=(self.start_ms,self.end_ms)
        self.view._position_bar(self,self.start_ms,self.end_ms)
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class CueTimingView(QGraphicsView):
    """Scrollable, absolute-time ruler for one selected subtitle cue."""
    timingChanged=Signal(int,int)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.start_x=64
        self.pixels_per_ms=.035  # 35 horizontal pixels per second.
        self._scene=QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFixedHeight(115)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.bar=None
        self.show_cue(None)

    def _position_bar(self,bar,start_ms,end_ms):
        x=self.start_x+start_ms*self.pixels_per_ms
        width=max(18,(end_ms-start_ms)*self.pixels_per_ms)
        bar.setPos(x,52)
        bar.setRect(0,0,width,26)
        bar.setToolTip(f"{start_ms/1000:.3f}s → {end_ms/1000:.3f}s")

    def show_cue(self,interval):
        self._scene.clear()
        self.bar=None
        if interval is None:
            self._scene.addText("Chọn một câu có thời gian hợp lệ để kéo tại đây.")
            self._scene.setSceneRect(0,0,700,90)
            return
        start_ms,end_ms=interval
        if (type(start_ms) is not int or type(end_ms) is not int
                or not 0<=start_ms<end_ms):
            raise ValueError("Cue timing ruler requires a valid interval")
        width=max(700,min(2_000_000,self.start_x+end_ms*self.pixels_per_ms+140))
        self._scene.setSceneRect(0,0,width,96)
        self._scene.addLine(self.start_x,48,width-20,48,QPen(QColor("#8996b4")))
        label=self._scene.addText("Kéo giữa: dịch cả câu   |   Kéo mép: đổi đầu/cuối   |   Esc: hủy kéo")
        label.setDefaultTextColor(QColor("#d8e1f7"))
        label.setPos(4,0)
        self.bar=CueTimingBar(self,start_ms,end_ms)
        self._scene.addItem(self.bar)
        self.ensureVisible(self.bar)

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self.bar is not None and self.bar.origin is not None:
            self.bar.cancel_drag()
            event.accept()
            return
        super().keyPressEvent(event)
