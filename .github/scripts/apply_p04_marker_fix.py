"""Apply the reviewed P04 marker viewport fix with exact source guards."""
from pathlib import Path


def replace_exact(text: str, old: str, new: str, *, expected: int = 1, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} source match(es), found {count}")
    return text.replace(old, new, expected)


timeline_path = Path("src/fonesi_edit/ui/timeline.py")
timeline = timeline_path.read_text(encoding="utf-8")

marker_view_class = '''

class TimelineGraphicsView(QGraphicsView):
    """Route marker drags from viewport coordinates, independent of scene mouse synthesis."""
    def __init__(self,scene,parent=None):
        super().__init__(scene,parent)
        self._marker_drag=None;self._marker_origin=None
        self._marker_pointer_offset=0.0;self._marker_canceled=False

    def _marker_at(self,position):
        # itemAt() returns only the top visual item, which may be the mouse-transparent
        # playhead. Search the complete stack and return the first marker or child.
        for candidate in self.items(position):
            item=candidate
            while item is not None and not isinstance(item,TimelineMarkerItem):
                item=item.parentItem()
            if item is not None:return item
        return None

    def _scene_x(self,event):
        return self.mapToScene(event.position().toPoint()).x()

    def _clear_marker_drag(self):
        self._marker_drag=None;self._marker_origin=None
        self._marker_pointer_offset=0.0;self._marker_canceled=False

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            marker=self._marker_at(event.position().toPoint())
            movable=(marker is not None and
                bool(marker.flags()&QGraphicsItem.GraphicsItemFlag.ItemIsMovable))
            if movable:
                self._marker_drag=marker;self._marker_origin=QPointF(marker.pos())
                self._marker_pointer_offset=self._scene_x(event)-marker.pos().x()
                self._marker_canceled=False
                if marker.selected is not None:marker.selected(marker.marker_id)
                marker.setSelected(True);marker.setFocus(Qt.FocusReason.MouseFocusReason)
                self.setFocus(Qt.FocusReason.MouseFocusReason)
                event.accept();return
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        marker=self._marker_drag
        if marker is None:
            super().mouseMoveEvent(event);return
        if self._marker_canceled:
            marker.setPos(self._marker_origin);event.accept();return
        marker.setPos(self._scene_x(event)-self._marker_pointer_offset,0)
        event.accept()

    def cancel_marker_drag(self):
        marker=self._marker_drag
        if marker is None:return False
        marker.setPos(self._marker_origin);self._marker_canceled=True
        return True

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self.cancel_marker_drag():
            event.accept();return
        super().keyPressEvent(event)

    def mouseReleaseEvent(self,event):
        marker=self._marker_drag;origin=self._marker_origin
        if marker is None or origin is None:
            super().mouseReleaseEvent(event);return
        canceled=self._marker_canceled
        if canceled:
            marker.setPos(origin)
        else:
            marker.setPos(self._scene_x(event)-self._marker_pointer_offset,0)
        current=QPointF(marker.pos())
        self._clear_marker_drag();event.accept()
        if not canceled and current!=origin:
            marker._defer(marker.moved,marker.marker_id,current.x(),
                          marker.project_id,marker.revision)
'''

timeline = replace_exact(
    timeline,
    "\n\n\nclass TimelinePanel(QWidget):",
    marker_view_class + "\n\nclass TimelinePanel(QWidget):",
    label="insert TimelineGraphicsView",
)
timeline = replace_exact(
    timeline,
    "self.view=QGraphicsView(self.scene)",
    "self.view=TimelineGraphicsView(self.scene,self)",
    label="instantiate TimelineGraphicsView",
)
timeline = replace_exact(
    timeline,
    "self._select_marker_from_scene,data['id'],session.revision,movable=marker_movable)",
    "self._select_marker_from_scene,session.project.id,session.revision,movable=marker_movable)",
    label="bind canonical project identity",
)
timeline = replace_exact(
    timeline,
    "            ('timeline.clear_range',self.clear_range_markers),\n",
    "            ('timeline.clear_range',self._escape_timeline_context),\n",
    label="route Escape through drag cancellation",
)
timeline = replace_exact(
    timeline,
    "    def _install_timeline_shortcuts(self):\n",
    "    def _escape_timeline_context(self):\n"
    "        if self.view.cancel_marker_drag():return\n"
    "        self.clear_range_markers()\n\n"
    "    def _install_timeline_shortcuts(self):\n",
    label="insert contextual Escape handler",
)
timeline_path.write_text(timeline, encoding="utf-8")

tests_path = Path("tests/test_timeline_panel_controls.py")
tests = tests_path.read_text(encoding="utf-8")

tests = replace_exact(
    tests,
    "from PySide6.QtCore import QCoreApplication,QEvent\n",
    "from PySide6.QtCore import QCoreApplication,QEvent,QPointF,Qt\n"
    "from PySide6.QtGui import QMouseEvent\n",
    label="import exact viewport event types",
)

viewport_helpers = '''def _send_viewport_mouse(view,event_type,pos,button,buttons):
    """Send exact local coordinates through the real viewport event path.

    Qt's offscreen platform clamps the virtual global cursor to its small screen.
    QTest.mouseMove can therefore report a different local coordinate for wide
    timeline views. Explicit local events keep the production viewport dispatch
    path while making the requested frame coordinate deterministic.
    """
    viewport=view.viewport()
    local=QPointF(pos)
    global_pos=QPointF(viewport.mapToGlobal(pos))
    event=QMouseEvent(event_type,local,global_pos,button,buttons,
                      Qt.KeyboardModifier.NoModifier)
    QCoreApplication.sendEvent(viewport,event)


def _drag_viewport(view,start,end,app):
    _send_viewport_mouse(view,QEvent.Type.MouseButtonPress,start,
        Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton)
    app.processEvents()
    _send_viewport_mouse(view,QEvent.Type.MouseMove,end,
        Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton)
    app.processEvents()
    _send_viewport_mouse(view,QEvent.Type.MouseButtonRelease,end,
        Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton)
    app.processEvents()


'''

tests = replace_exact(
    tests,
    "from test_queue_view import wait_for\n\n\n",
    "from test_queue_view import wait_for\n\n\n" + viewport_helpers,
    label="insert exact viewport helpers",
)

plain_drag = (
    "            QTest.mousePress(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))\n"
    "            QTest.mouseMove(timeline.view.viewport(),QPoint(end))\n"
    "            QTest.mouseRelease(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(end))\n"
)
tests = replace_exact(
    tests,
    plain_drag,
    "            _drag_viewport(timeline.view,QPoint(start),QPoint(end),qt_app)\n",
    expected=2,
    label="replace successful and collision drags",
)

escape_press_move = (
    "            QTest.mousePress(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))\n"
    "            QTest.mouseMove(timeline.view.viewport(),QPoint(end))\n"
    "            qt_app.processEvents()\n"
)
tests = replace_exact(
    tests,
    escape_press_move,
    "            _send_viewport_mouse(timeline.view,QEvent.Type.MouseButtonPress,QPoint(start),\n"
    "                Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton)\n"
    "            qt_app.processEvents()\n"
    "            _send_viewport_mouse(timeline.view,QEvent.Type.MouseMove,QPoint(end),\n"
    "                Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton)\n"
    "            qt_app.processEvents()\n",
    label="replace escape drag press and move",
)

tests = replace_exact(
    tests,
    "            QTest.mouseRelease(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(end))\n"
    "            qt_app.processEvents()\n"
    "            assert window.session.revision==before\n",
    "            _send_viewport_mouse(timeline.view,QEvent.Type.MouseButtonRelease,QPoint(end),\n"
    "                Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton)\n"
    "            qt_app.processEvents()\n"
    "            assert window.session.revision==before\n",
    label="replace canceled release",
)

no_op = (
    "            QTest.mousePress(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))\n"
    "            QTest.mouseRelease(timeline.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))\n"
    "            qt_app.processEvents()\n"
)
tests = replace_exact(
    tests,
    no_op,
    "            _drag_viewport(timeline.view,QPoint(start),QPoint(start),qt_app)\n",
    label="replace no-op drag",
)
tests_path.write_text(tests, encoding="utf-8")
