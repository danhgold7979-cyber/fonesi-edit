import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView, QInputDialog

_FONT_FAMILIES={}


def snap_layer_position(x, y, width, height, *, enabled=True, grid=False, tolerance=.012):
    """Snap normalized layer edges/center to canvas guides; never leave its bounds."""
    def axis(value, span):
        maximum = max(0.0, 1.0 - span)
        value = max(0.0, min(maximum, value))
        if not enabled:
            return value
        # Canvas centre is a guide for the *layer centre*, not its top-left.
        guides = [0.5 - span / 2, 0.05, 0.95 - span]
        if grid:
            guides.append(round(value / .05) * .05)
        nearest = min(guides, key=lambda target: abs(value - target))
        if abs(value - nearest) <= tolerance:
            value = nearest
        return max(0.0, min(maximum, value))

    return axis(x, width), axis(y, height)


def snap_layer_to_peers_with_guides(x, y, width, height, peers, *, enabled=True, tolerance=.012):
    """Snap to nearby peer guides and return their normalized X/Y guide positions."""
    values = (x, y, width, height, tolerance)
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
               and math.isfinite(float(value)) for value in values):
        raise ValueError("Snap geometry must be finite numbers")
    if width < 0 or height < 0 or tolerance < 0:
        raise ValueError("Snap dimensions and tolerance must be non-negative")
    x = max(0.0, min(max(0.0, 1.0 - width), float(x)))
    y = max(0.0, min(max(0.0, 1.0 - height), float(y)))
    if not enabled:
        return x, y, None, None

    rectangles = list(peers)

    def nearest_axis(position, span, axis):
        moving_guides = (0.0, span / 2.0, span)
        candidates = []
        for peer in rectangles:
            if len(peer) != 4:
                raise ValueError("Peer rectangles must contain x, y, width and height")
            px, py, pw, ph = peer
            if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                       and math.isfinite(float(value)) for value in peer):
                raise ValueError("Peer geometry must be finite numbers")
            if pw < 0 or ph < 0 or px < 0 or py < 0 or px + pw > 1 or py + ph > 1:
                continue
            peer_start, peer_span = (px, pw) if axis == 0 else (py, ph)
            peer_guides = (peer_start, peer_start + peer_span / 2.0, peer_start + peer_span)
            for moving_offset in moving_guides:
                for peer_guide in peer_guides:
                    target = peer_guide - moving_offset
                    if 0.0 <= target <= max(0.0, 1.0 - span):
                        distance = abs(target - position)
                        if distance <= tolerance:
                            candidates.append((distance, target, peer_guide))
        if not candidates:
            return position, None
        _, target, guide = min(candidates, key=lambda candidate: (candidate[0], candidate[1], candidate[2]))
        return target, guide

    snapped_x, vertical_guide = nearest_axis(x, width, 0)
    snapped_y, horizontal_guide = nearest_axis(y, height, 1)
    return snapped_x, snapped_y, vertical_guide, horizontal_guide


def snap_layer_to_peers(x, y, width, height, peers, *, enabled=True, tolerance=.012):
    """Compatibility helper returning only the snapped normalized position."""
    snapped_x, snapped_y, _, _ = snap_layer_to_peers_with_guides(
        x, y, width, height, peers, enabled=enabled, tolerance=tolerance)
    return snapped_x, snapped_y


def constrained_group_delta(rectangles, dx, dy):
    """Clamp a group translation against its *original* union of rectangles."""
    if not rectangles:
        return dx, dy
    left = min(x for x, y, width, height in rectangles)
    top = min(y for x, y, width, height in rectangles)
    right = max(x + width for x, y, width, height in rectangles)
    bottom = max(y + height for x, y, width, height in rectangles)
    return (max(-left, min(1.0 - right, dx)),
            max(-top, min(1.0 - bottom, dy)))



def anchor_group_delta(rectangles, horizontal, vertical, margin=0.05):
    """Return one translation placing a group's bounds at a 3x3 canvas anchor.

    Coordinates and dimensions are normalized to the canvas. A 5% safe margin
    is used when possible and reduced only when necessary for a group to fit.
    Returns None when the group's union cannot fit inside the canvas.
    """
    if horizontal not in {"left", "center", "right"}:
        raise ValueError("Unknown horizontal anchor")
    if vertical not in {"top", "center", "bottom"}:
        raise ValueError("Unknown vertical anchor")
    if (not isinstance(margin, (int, float)) or isinstance(margin, bool)
            or not math.isfinite(float(margin)) or not 0 <= margin < 0.5):
        raise ValueError("Anchor margin must be finite and between 0 and 0.5")

    boxes = []
    for rectangle in rectangles:
        if len(rectangle) != 4:
            raise ValueError("Each layer rectangle must contain x, y, width and height")
        x, y, width, height = (float(value) for value in rectangle)
        if (not all(math.isfinite(value) for value in (x, y, width, height))
                or width < 0 or height < 0):
            raise ValueError("Layer rectangle must contain finite coordinates and non-negative size")
        boxes.append((x, y, width, height))
    if not boxes:
        return (0.0, 0.0)

    left = min(x for x, y, width, height in boxes)
    top = min(y for x, y, width, height in boxes)
    right = max(x + width for x, y, width, height in boxes)
    bottom = max(y + height for x, y, width, height in boxes)
    group_width, group_height = right - left, bottom - top
    if group_width > 1.0 or group_height > 1.0:
        return None

    margin_x = min(float(margin), max(0.0, (1.0 - group_width) / 2.0))
    margin_y = min(float(margin), max(0.0, (1.0 - group_height) / 2.0))
    if horizontal == "left":
        target_left = margin_x
    elif horizontal == "center":
        target_left = (1.0 - group_width) / 2.0
    else:
        target_left = 1.0 - margin_x - group_width

    if vertical == "top":
        target_top = margin_y
    elif vertical == "center":
        target_top = (1.0 - group_height) / 2.0
    else:
        target_top = 1.0 - margin_y - group_height
    return target_left - left, target_top - top


class Overlay(QGraphicsObject):
    def __init__(self, layer, width, height, begin, commit):
        super().__init__()
        self.layer, self.cw, self.ch = layer, width, height
        self.begin, self.commit = begin, commit
        self.mode = None
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPos(layer.x * width, layer.y * height)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setRotation(layer.rotation)
        self.setOpacity(layer.opacity)
        self.setVisible(layer.visible)
        self.image = QPixmap(layer.path) if layer.kind == 'image' and layer.path else QPixmap()

    def boundingRect(self):
        return QRectF(0, 0, max(12, self.layer.width * self.cw), max(12, self.layer.height * self.ch))

    def paint(self, painter, option, widget=None):
        rect, layer = self.boundingRect(), self.layer
        if layer.kind in {'text', 'subtitle'}:
            family=layer.style.get('font_family','Arial');font_path=layer.style.get('font_file')
            if font_path:
                if font_path not in _FONT_FAMILIES:
                    key=QFontDatabase.addApplicationFont(font_path);_FONT_FAMILIES[font_path]=QFontDatabase.applicationFontFamilies(key) if key>=0 else []
                if _FONT_FAMILIES[font_path] and family not in _FONT_FAMILIES[font_path]:family=_FONT_FAMILIES[font_path][0]
            font = QFont(family)
            font.setPixelSize(int(layer.style.get('font_size', 32)))
            font.setBold(layer.style.get('bold', False))
            font.setItalic(layer.style.get('italic', False))
            font.setUnderline(layer.style.get('underline', False))
            painter.setFont(font)
            if layer.style.get('background'):
                painter.fillRect(rect, QColor(layer.style['background']))
            painter.setPen(QColor(layer.style.get('color', '#ffffff')))
            align = {'left': Qt.AlignmentFlag.AlignLeft, 'center': Qt.AlignmentFlag.AlignHCenter, 'right': Qt.AlignmentFlag.AlignRight}.get(layer.style.get('align'), Qt.AlignmentFlag.AlignLeft)
            painter.drawText(rect, int(align | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap), layer.text)
        elif layer.kind == 'image' and not self.image.isNull():
            painter.drawPixmap(rect, self.image, QRectF(self.image.rect()))
        elif layer.kind == 'mask':
            painter.fillRect(rect, QColor(70, 70, 80, 150))
            painter.setPen(QColor('#ffffff'))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, 'Vùng che')
        if self.isSelected():
            pen = QPen(QColor('#ac99ff'), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor('#ac99ff'))
            painter.drawRect(rect)
            painter.drawRect(QRectF(rect.width() - 5, rect.height() - 5, 10, 10))
            painter.drawEllipse(QPointF(rect.width() / 2, 0), 5, 5)

    def mousePressEvent(self, event):
        # Qt normally deselects the other items when a selected item is pressed.
        # Preserve the pre-press multi-selection for a common drag gesture.
        preselected = set(self.scene().selectedItems()) if self.scene() and self.isSelected() else set()
        super().mousePressEvent(event)
        if self.layer.locked:
            return
        for item in preselected:
            if isinstance(item, Overlay):
                item.setSelected(True)
        self.begin()
        self.origin = event.scenePos()
        self.original = self.layer.x, self.layer.y, self.layer.width, self.layer.height, self.layer.rotation
        self.companions = {
            item: (item.layer.x, item.layer.y)
            for item in self.scene().items()
            if isinstance(item, Overlay) and item is not self and not item.layer.locked
            and (item.isSelected() or item in preselected
                 or (self.layer.group and item.layer.group == self.layer.group))
        }
        local = event.pos()
        self.mode = 'resize' if (local - self.boundingRect().bottomRight()).manhattanLength() < 25 else 'rotate' if local.y() < 15 and abs(local.x() - self.boundingRect().width() / 2) < 15 else 'move'

    def mouseMoveEvent(self, event):
        if not self.mode or self.layer.locked:
            return
        delta = event.scenePos() - self.origin
        x, y, w, h, rotation = self.original
        if self.mode == 'move':
            dx, dy = delta.x() / self.cw, delta.y() / self.ch
            original_bounds = [(x, y, w, h)] + [
                (sx, sy, item.layer.width, item.layer.height)
                for item, (sx, sy) in self.companions.items()]
            dx, dy = constrained_group_delta(original_bounds, dx, dy)
            disabled = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            view = next((view for view in self.scene().views() if isinstance(view, Canvas)), None)
            grid = bool(view and view.editor.composition.adjustments.get('canvas_grid', False))
            desired_x, desired_y = snap_layer_position(
                x + dx, y + dy, w, h, enabled=not disabled, grid=grid)
            peer_rectangles = [
                (item.layer.x, item.layer.y, item.layer.width, item.layer.height)
                for item in self.scene().items()
                if isinstance(item, Overlay) and item is not self
                and item not in self.companions and not item.isSelected()
                and item.layer.visible and not item.layer.locked
                and not (self.layer.group and item.layer.group == self.layer.group)
            ]
            desired_x, desired_y, vertical_guide, horizontal_guide = snap_layer_to_peers_with_guides(
                desired_x, desired_y, w, h, peer_rectangles,
                enabled=not disabled)
            if view:
                view.set_peer_snap_guides(vertical_guide, horizontal_guide)
            # One bounded delta preserves the relative positions of companions.
            dx, dy = constrained_group_delta(original_bounds, desired_x - x, desired_y - y)
            self.layer.x, self.layer.y = x + dx, y + dy
            self.setPos(self.layer.x * self.cw, self.layer.y * self.ch)
            for item, (sx, sy) in self.companions.items():
                item.layer.x, item.layer.y = sx + dx, sy + dy
                item.setPos(item.layer.x * self.cw, item.layer.y * self.ch)
        elif self.mode == 'resize':
            max_w, max_h = max(.02, 1.0 - x), max(.02, 1.0 - y)
            new_w = min(max_w, max(.02, w + delta.x() / self.cw))
            new_h = min(max_h, max(.02, h + delta.y() / self.ch))
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                ratio = min(new_w / max(w, .001), new_h / max(h, .001))
                new_w, new_h = w * ratio, h * ratio
            self.prepareGeometryChange()
            self.layer.width, self.layer.height = new_w, new_h
            self.setTransformOriginPoint(self.boundingRect().center())
        else:
            self.layer.rotation = rotation + delta.x() / 2
            self.setRotation(self.layer.rotation)
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.mode:
            self.mode = None
            view = next((view for view in self.scene().views() if isinstance(view, Canvas)), None)
            if view:
                view.set_peer_snap_guides(None, None)
            self.commit('Kéo/biến đổi đối tượng')

    def mouseDoubleClickEvent(self,event):
        if self.layer.kind=='text' and not self.layer.locked:
            text,ok=QInputDialog.getMultiLineText(None,'Sửa chữ trực tiếp','Nội dung',self.layer.text)
            if ok:self.begin();self.layer.text=text;self.commit('Sửa chữ trên preview')
        else:super().mouseDoubleClickEvent(event)


class Canvas(QGraphicsView):
    selected = Signal(str)
    edited = Signal(str)

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setMinimumSize(400, 250)
        self.scene().selectionChanged.connect(self.selection)
        self.zoom = 1
        self._peer_snap_guides = (None, None)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def rebuild(self, frame=None,reference=False):
        self.set_peer_snap_guides(None, None)
        selected = self.editor.selected_id
        self.scene().blockSignals(True)
        self.scene().clear()
        c = self.editor.composition
        self.setSceneRect(0, 0, c.width, c.height)
        if frame and not reference:
            self.editor.frame = frame
        selected_frame=frame if reference else self.editor.frame
        if selected_frame:
            image = QPixmap(str(selected_frame))
            if not image.isNull():
                image = image.scaled(c.width, c.height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                item = self.scene().addPixmap(image)
                item.setPos((c.width-image.width())/2, (c.height-image.height())/2)
        if not reference and c.adjustments.get('canvas_grid', False):
            grid_pen = QPen(QColor('#46516b'), 1, Qt.PenStyle.DotLine)
            grid_pen.setCosmetic(True)
            for tick in range(1, 20):
                x = c.width * tick / 20
                y = c.height * tick / 20
                vertical = self.scene().addLine(x, 0, x, c.height, grid_pen)
                horizontal = self.scene().addLine(0, y, c.width, y, grid_pen)
                vertical.setZValue(.2)
                horizontal.setZValue(.2)
        safe = self.scene().addRect(c.width * .05, c.height * .05, c.width * .9, c.height * .9, QPen(QColor('#667088'), 1, Qt.PenStyle.DashLine))
        safe.setZValue(10000)
        for index, layer in enumerate(c.layers):
            if reference:break
            item = Overlay(layer, c.width, c.height, self.editor.begin, self.editor.commit)
            item.setZValue(index + 1)
            self.scene().addItem(item)
            if layer.id in self.editor.selected_ids or layer.id==selected:
                item.setSelected(True)
        self.scene().blockSignals(False)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(self.zoom, self.zoom)

    def set_peer_snap_guides(self, vertical, horizontal):
        guides = (vertical, horizontal)
        if guides != self._peer_snap_guides:
            self._peer_snap_guides = guides
            self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        vertical, horizontal = self._peer_snap_guides
        if vertical is None and horizontal is None:
            return
        painter = QPainter(self.viewport())
        pen = QPen(QColor('#35d6e8'), 1, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        width = self.editor.composition.width
        height = self.editor.composition.height
        if vertical is not None:
            x = self.mapFromScene(QPointF(vertical * width, 0)).x()
            painter.drawLine(x, 0, x, self.viewport().height())
        if horizontal is not None:
            y = self.mapFromScene(QPointF(0, horizontal * height)).y()
            painter.drawLine(0, y, self.viewport().width(), y)
        painter.end()

    def selection(self):
        items = [item for item in self.scene().selectedItems() if isinstance(item, Overlay)]
        self.editor.select_ids([item.layer.id for item in items])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(self.zoom, self.zoom)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom = max(.25, min(4, self.zoom * (1.1 if event.angleDelta().y() > 0 else 1/1.1)))
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(self.zoom, self.zoom)
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        mapping = {Qt.Key.Key_Left: (-1,0), Qt.Key.Key_Right:(1,0),Qt.Key.Key_Up:(0,-1),Qt.Key.Key_Down:(0,1)}
        if event.key()==Qt.Key.Key_Escape:self.rebuild()
        elif event.key() in mapping and self.editor.layer() and not self.editor.layer().locked:
            self.editor.begin()
            dx, dy = mapping[event.key()]
            factor = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            layer, c = self.editor.layer(), self.editor.composition
            layer.x = max(0,min(1,layer.x + dx*factor/c.width))
            layer.y = max(0,min(1,layer.y + dy*factor/c.height))
            self.editor.commit('Dịch đối tượng')
        elif event.key() == Qt.Key.Key_Delete:
            self.editor.delete_layer()
        else:
            super().keyPressEvent(event)
