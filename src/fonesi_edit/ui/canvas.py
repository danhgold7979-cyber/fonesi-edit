from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QGraphicsScene, QGraphicsView


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
            font = QFont(layer.style.get('font_family', 'Arial'))
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
        super().mousePressEvent(event)
        if self.layer.locked:
            return
        self.begin()
        self.origin = event.scenePos()
        self.original = self.layer.x, self.layer.y, self.layer.width, self.layer.height, self.layer.rotation
        local = event.pos()
        self.mode = 'resize' if (local - self.boundingRect().bottomRight()).manhattanLength() < 25 else 'rotate' if local.y() < 15 and abs(local.x() - self.boundingRect().width() / 2) < 15 else 'move'

    def mouseMoveEvent(self, event):
        if not self.mode or self.layer.locked:
            return
        delta = event.scenePos() - self.origin
        x, y, w, h, rotation = self.original
        if self.mode == 'move':
            nx, ny = x + delta.x() / self.cw, y + delta.y() / self.ch
            if not event.modifiers() & Qt.KeyboardModifier.AltModifier:
                if abs(nx - 0.5) < 0.01: nx = 0.5
                if abs(ny - 0.5) < 0.01: ny = 0.5
            self.layer.x, self.layer.y = min(1, max(0, nx)), min(1, max(0, ny))
            self.setPos(self.layer.x * self.cw, self.layer.y * self.ch)
        elif self.mode == 'resize':
            self.prepareGeometryChange()
            self.layer.width = max(0.02, w + delta.x() / self.cw)
            self.layer.height = max(0.02, h + delta.y() / self.ch)
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.layer.height = h * self.layer.width / w
        else:
            self.layer.rotation = rotation + delta.x() / 2
            self.setRotation(self.layer.rotation)
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.mode:
            self.mode = None
            self.commit('Kéo/biến đổi đối tượng')


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

    def rebuild(self, frame=None,reference=False):
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
        safe = self.scene().addRect(c.width * .05, c.height * .05, c.width * .9, c.height * .9, QPen(QColor('#667088'), 1, Qt.PenStyle.DashLine))
        safe.setZValue(10000)
        for index, layer in enumerate(c.layers):
            if reference:break
            item = Overlay(layer, c.width, c.height, self.editor.begin, self.editor.commit)
            item.setZValue(index + 1)
            self.scene().addItem(item)
            if layer.id == selected:
                item.setSelected(True)
        self.scene().blockSignals(False)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(self.zoom, self.zoom)

    def selection(self):
        items = [item for item in self.scene().selectedItems() if isinstance(item, Overlay)]
        if items:
            self.selected.emit(items[0].layer.id)

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
