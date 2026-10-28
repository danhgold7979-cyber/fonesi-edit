from copy import deepcopy
import math
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QDialogButtonBox,QSpinBox,QDoubleSpinBox,QComboBox,
    QCheckBox,QTableWidget,QTableWidgetItem,QPushButton,QFileDialog,QMessageBox,QHeaderView,QScrollArea,QWidget,QLabel)
from PySide6.QtCore import Qt
from ..batch import fit_duration
from ..render import audio_duration
from ..prototypes.media import extract_frame, probe


class CropCanvas(QLabel):
    """QLabel that forwards real Qt mouse events to its crop dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crop_dialog = None

    def mousePressEvent(self, event):
        if self.crop_dialog is not None:
            self.crop_dialog._press(event)

    def mouseMoveEvent(self, event):
        if self.crop_dialog is not None:
            self.crop_dialog._move(event)

    def mouseReleaseEvent(self, event):
        if self.crop_dialog is not None:
            self.crop_dialog._release(event)


def crop_drag_rect(start_rect, drag, start, current, *, ratio_locked=False,
                   source_width=1, source_height=1, min_size=.01):
    """Return a bounded normalized crop rectangle for a drag gesture.

    Ratio lock preserves the crop's pixel aspect ratio using source dimensions.
    For side handles, the opposite side stays fixed and the orthogonal axis
    expands symmetrically around its centre.
    """
    if drag not in {"new", "move", "left", "right", "top", "bottom",
                    "left_top", "left_bottom", "right_top", "right_bottom"}:
        raise ValueError("Unknown crop drag handle")
    values = tuple(start_rect) + tuple(start) + tuple(current) + (min_size, source_width, source_height)
    if (len(start_rect) != 4 or len(start) != 2 or len(current) != 2
            or not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                       and math.isfinite(float(value)) for value in values)
            or source_width <= 0 or source_height <= 0):
        raise ValueError("Crop drag geometry must contain finite numbers")
    x, y, width, height = (float(value) for value in start_rect)
    sx, sy = (max(0.0, min(1.0, float(value))) for value in start)
    cx, cy = (max(0.0, min(1.0, float(value))) for value in current)
    minimum = float(min_size)
    if (minimum <= 0 or minimum > 0.5 or width <= 0 or height <= 0
            or x < 0 or y < 0 or x + width > 1 or y + height > 1):
        raise ValueError("Starting crop rectangle is outside normalized bounds")
    dx, dy = cx - sx, cy - sy

    if drag == "move":
        return (max(0.0, min(1.0 - width, x + dx)),
                max(0.0, min(1.0 - height, y + dy)), width, height)

    if not ratio_locked:
        if drag == "new":
            x2, y2 = min(sx, cx), min(sy, cy)
            width2, height2 = abs(dx), abs(dy)
        else:
            left, top, right, bottom = x, y, x + width, y + height
            if "left" in drag:
                left = max(0.0, min(right - minimum, x + dx))
            if "right" in drag:
                right = max(left + minimum, min(1.0, x + width + dx))
            if "top" in drag:
                top = max(0.0, min(bottom - minimum, y + dy))
            if "bottom" in drag:
                bottom = max(top + minimum, min(1.0, y + height + dy))
            x2, y2, width2, height2 = left, top, right - left, bottom - top
        x2 = max(0.0, min(1.0 - minimum, x2))
        y2 = max(0.0, min(1.0 - minimum, y2))
        width2 = max(minimum, min(1.0 - x2, width2))
        height2 = max(minimum, min(1.0 - y2, height2))
        return x2, y2, width2, height2

    ratio = width * float(source_width) / (height * float(source_height))
    if drag == "new":
        sign_x = 1 if dx >= 0 else -1
        sign_y = 1 if dy >= 0 else -1
        requested_width = max(minimum, abs(dx), abs(dy) * ratio)
        available_width = (1.0 - sx) if sign_x > 0 else sx
        available_height = (1.0 - sy) if sign_y > 0 else sy
        max_width = min(available_width, available_height * ratio)
        width2 = min(requested_width, max_width)
        if width2 <= 0:
            return x, y, width, height
        height2 = width2 * float(source_width) / (ratio * float(source_height))
        x2 = sx if sign_x > 0 else sx - width2
        y2 = sy if sign_y > 0 else sy - height2
        return x2, y2, width2, height2

    left_handle = "left" in drag
    right_handle = "right" in drag
    top_handle = "top" in drag
    bottom_handle = "bottom" in drag
    corner = (left_handle or right_handle) and (top_handle or bottom_handle)

    if corner:
        fixed_x = x + width if left_handle else x
        fixed_y = y + height if top_handle else y
        requested_width = max(minimum, width + (-dx if left_handle else dx))
        requested_height = max(minimum, height + (-dy if top_handle else dy))
        requested_width = max(requested_width, requested_height * ratio)
        available_width = fixed_x if left_handle else 1.0 - fixed_x
        available_height = fixed_y if top_handle else 1.0 - fixed_y
        max_width = min(available_width, available_height * ratio)
        width2 = min(requested_width, max_width)
        if width2 <= 0:
            return x, y, width, height
        height2 = width2 * float(source_width) / (ratio * float(source_height))
        x2 = fixed_x - width2 if left_handle else fixed_x
        y2 = fixed_y - height2 if top_handle else fixed_y
        return x2, y2, width2, height2

    if left_handle or right_handle:
        fixed_x = x + width if left_handle else x
        center_y = y + height / 2.0
        requested_width = max(minimum, width + (-dx if left_handle else dx))
        available_width = fixed_x if left_handle else 1.0 - fixed_x
        available_height = 2.0 * min(center_y, 1.0 - center_y)
        max_width = min(available_width, available_height * ratio)
        width2 = min(requested_width, max_width)
        if width2 <= 0:
            return x, y, width, height
        height2 = width2 * float(source_width) / (ratio * float(source_height))
        x2 = fixed_x - width2 if left_handle else fixed_x
        y2 = center_y - height2 / 2.0
        return x2, y2, width2, height2

    fixed_y = y + height if top_handle else y
    center_x = x + width / 2.0
    requested_height = max(minimum, height + (-dy if top_handle else dy))
    available_height = fixed_y if top_handle else 1.0 - fixed_y
    available_width = 2.0 * min(center_x, 1.0 - center_x)
    max_height = min(available_height, available_width / ratio)
    height2 = min(requested_height, max_height)
    if height2 <= 0:
        return x, y, width, height
    width2 = height2 * ratio
    x2 = center_x - width2 / 2.0
    y2 = fixed_y - height2 if top_handle else fixed_y
    return x2, y2, width2, height2


class CropDialog(QDialog):
    """Interactive crop editor; edits only its local normalized rectangle."""

    def __init__(self, clip, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop video nguồn")
        self.setMinimumSize(720, 520)
        self.clip = deepcopy(clip)
        self.info = probe(__import__("pathlib").Path(clip.path))
        self.rect = [clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height]
        self.ratio_locked = False
        self._drag = None
        self._start_rect = None
        self._frame_size = (self.info.width, self.info.height)
        layout = QVBoxLayout(self)
        self.canvas = CropCanvas(self)
        self.canvas.crop_dialog = self
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setMinimumSize(560, 320)
        self.canvas.setMouseTracking(True)
        layout.addWidget(self.canvas, 1)
        row = QHBoxLayout()
        self.lock_ratio = QCheckBox("Khóa tỷ lệ crop")
        self.lock_ratio.toggled.connect(lambda value: setattr(self, "ratio_locked", value))
        row.addWidget(self.lock_ratio)
        self.handle_size = 8
        self.handle_points = []

        for label, callback in (("Toàn khung", self.reset_crop), ("Giữa khung", self.center_crop)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            row.addWidget(button)
        self.status = QLabel()
        row.addWidget(self.status, 1)
        layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._load_frame()

    def _load_frame(self):
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import QSize
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix="fonesi-crop-") as folder:
            frame = Path(folder) / "source.png"
            extract_frame(Path(self.clip.path), frame, second=min(self.clip.start, max(0, self.info.duration - .05)))
            pixmap = QPixmap(str(frame))
        self._pixmap = pixmap
        self._paint_crop()

    def _paint_crop(self):
        from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
        from PySide6.QtCore import QRectF
        if self._pixmap.isNull():
            self.status.setText("Không đọc được frame nguồn")
            return
        target = self.canvas.size()
        scaled = self._pixmap.scaled(target, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self._display = scaled
        canvas_pixmap = QPixmap(scaled.size())
        canvas_pixmap.fill(QColor("#202020"))
        painter = QPainter(canvas_pixmap)
        painter.drawPixmap(0, 0, scaled)
        sx, sy, sw, sh = self.rect
        x, y, w, h = sx*scaled.width(), sy*scaled.height(), sw*scaled.width(), sh*scaled.height()
        # Darken only the four regions outside the crop. Clearing the crop
        # rectangle would erase the source pixels rather than reveal them.
        shade = QColor(0, 0, 0, 145)
        width, height = scaled.width(), scaled.height()
        painter.fillRect(QRectF(0, 0, width, y), shade)
        painter.fillRect(QRectF(0, y, x, h), shade)
        painter.fillRect(QRectF(x + w, y, max(0, width - x - w), h), shade)
        painter.fillRect(QRectF(0, y + h, width, max(0, height - y - h)), shade)
        painter.setPen(QPen(QColor("#40d9ff"), 2))
        painter.drawRect(QRectF(x, y, w, h))
        painter.setPen(QPen(QColor("#ffffff"), 1))
        self.handle_points = []
        for hx in (x, x+w/2, x+w):
            for hy in (y, y+h/2, y+h):
                if (hx, hy) not in ((x+w/2, y+h/2),):
                    self.handle_points.append((int(hx), int(hy)))
        painter.setBrush(QColor("#ffffff"))
        for hx, hy in self.handle_points:
            painter.drawRect(hx-4, hy-4, self.handle_size, self.handle_size)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        for fx in (1/3, 2/3):
            painter.drawLine(int(x+fx*w), int(y), int(x+fx*w), int(y+h))
            painter.drawLine(int(x), int(y+fx*h), int(x+w), int(y+fx*h))
        painter.end()
        self.canvas.setPixmap(canvas_pixmap)
        self.status.setText(f"x={sx:.3f} y={sy:.3f} w={sw:.3f} h={sh:.3f}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_pixmap"):
            self._paint_crop()

    def _position(self, event):
        from PySide6.QtCore import QPoint
        shown = self.canvas.pixmap()
        if shown is None or shown.isNull():
            return None
        offset_x = (self.canvas.width() - shown.width()) / 2
        offset_y = (self.canvas.height() - shown.height()) / 2
        x = (event.position().x() - offset_x) / shown.width()
        y = (event.position().y() - offset_y) / shown.height()
        if not (0 <= x <= 1 and 0 <= y <= 1):
            return None
        return x, y

    def _press(self, event):
        pos = self._position(event)
        if pos is None:
            return
        x, y, w, h = self.rect
        edges = {"left": abs(pos[0]-x), "right": abs(pos[0]-(x+w)),
                 "top": abs(pos[1]-y), "bottom": abs(pos[1]-(y+h))}
        near_x = min(edges["left"], edges["right"]) < .04
        near_y = min(edges["top"], edges["bottom"]) < .04
        handle = (("left" if edges["left"] < edges["right"] else "right") if near_x else "") + "_" + (("top" if edges["top"] < edges["bottom"] else "bottom") if near_y else "")
        if near_x and near_y:
            self._drag = handle
        elif near_x:
            self._drag = "left" if edges["left"] < edges["right"] else "right"
        elif near_y:
            self._drag = "top" if edges["top"] < edges["bottom"] else "bottom"
        elif x <= pos[0] <= x+w and y <= pos[1] <= y+h:
            self._drag = "move"
        else:
            self._drag = "new"
        self._start = pos
        self._start_rect = list(self.rect)

    def _move(self, event):
        if self._drag is None or self._start is None:
            return
        pos = self._position(event)
        if pos is None:
            return
        self.rect = list(crop_drag_rect(
            self._start_rect, self._drag, self._start, pos,
            ratio_locked=self.ratio_locked,
            source_width=self.info.width, source_height=self.info.height,
        ))
        self._paint_crop()

    def _release(self, event):
        self._move(event)
        self._drag = None
        self._start = None
        self._start_rect = None

    def reset_crop(self):
        self.rect=[0.0,0.0,1.0,1.0]
        self._paint_crop()

    def center_crop(self):
        x,y,w,h=self.rect
        self.rect=[(1-w)/2,(1-h)/2,w,h]
        self._paint_crop()


class ClipDialog(QDialog):
    def __init__(self,editor,index):
        super().__init__(editor);self.editor=editor;self.index=index;self.setWindowTitle('Trim / tốc độ / hình / âm gốc');self.fields={}
        layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form);clip=editor.composition.clips[index]
        for key,label,lo,hi,value in [('start','Cắt đầu tại s',0,100000,clip.start),('end','Cắt cuối tại s',.001,100000,clip.end or clip.source_duration or 1),('speed','Tốc độ (1=bình thường)',.1,10,clip.speed),('rotation','Xoay °',-360,360,clip.rotation),('volume','Âm gốc (0=tắt)',0,4,clip.volume),('freeze','Giữ khung cuối s',0,3600,clip.freeze)]:
            field=QDoubleSpinBox();field.setDecimals(3);field.setRange(lo,hi);field.setValue(value);self.fields[key]=field;form.addRow(label,field)
        self.flip=QCheckBox();self.flip.setChecked(clip.flip);form.addRow('Lật ngang',self.flip)
        self.crop_rect = [clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height]
        self.crop_button = QPushButton("Chọn vùng crop…")
        self.crop_button.clicked.connect(self.edit_crop)
        form.addRow("Crop thủ công", self.crop_button)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def edit_crop(self):
        from dataclasses import replace
        from ..domain import Clip
        from pathlib import Path
        source = self.editor.composition.clips[self.index]
        draft = deepcopy(source)
        for key, value in zip(("crop_x", "crop_y", "crop_width", "crop_height"), self.crop_rect):
            setattr(draft, key, value)
        try:
            dialog = CropDialog(draft, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.crop_rect = list(dialog.rect)
                self.crop_button.setText(
                    f"Crop: {self.crop_rect[2]:.0%} × {self.crop_rect[3]:.0%}"
                )
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "Không mở được crop", str(exc))

    def apply(self):
        c=deepcopy(self.editor.composition);clip=c.clips[self.index]
        for key,field in self.fields.items():setattr(clip,key,field.value())
        clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height = self.crop_rect
        clip.flip=self.flip.isChecked();c.duration_target=None
        try:
            c.validate()
            if clip.source_duration and clip.end>clip.source_duration+.001:raise ValueError('Điểm cuối vượt video nguồn')
        except ValueError as exc:QMessageBox.warning(self,'Clip chưa hợp lệ',str(exc));return
        self.editor.begin();self.editor.composition=c;self.editor.commit('Sửa clip');self.accept()


class OutputDialog(QDialog):
    def __init__(self,editor):
        super().__init__(editor);self.editor=editor;self.setWindowTitle('Đầu ra / màu / phần cứng');self.values={}
        layout=QVBoxLayout(self);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();form=QFormLayout(body);scroll.setWidget(body);layout.addWidget(scroll);self.resize(620,760);c=editor.composition
        for key,label,lo,hi,value,integer in [('width','Rộng px',64,7680,c.width,True),('height','Cao px',64,7680,c.height,True),('fps','FPS',1,120,c.fps,True),
                ('quality','CRF / chất lượng',0,51,c.quality,True),('transition','Chuyển cảnh s',0,5,c.transition,False),('seed','Seed',0,2147483647,c.seed,True),
                ('brightness','Sáng',-1,1,c.adjustments.get('brightness',0),False),('contrast','Tương phản',.1,3,c.adjustments.get('contrast',1),False),
                ('saturation','Bão hòa',.1,3,c.adjustments.get('saturation',1),False),('gamma','Gamma',.1,3,c.adjustments.get('gamma',1),False)]:
            widget=QSpinBox() if integer else QDoubleSpinBox();widget.setRange(lo,hi);widget.setValue(value);self.values[key]=widget;form.addRow(label,widget)
        self.ratio=QComboBox();self.ratio.addItems(['Tùy chỉnh','16:9 (1280×720)','9:16 (720×1280)','1:1 (1080×1080)','4:5 (1080×1350)']);form.addRow('Tỷ lệ nhanh',self.ratio)
        self.ratio.activated.connect(lambda index:self.ratio_changed(index))
        self.fit=QComboBox();self.fit.addItems(['fit','crop','blur']);self.fit.setCurrentText(c.fit);form.addRow('Fit / crop / nền mờ',self.fit)
        self.encoder=QComboBox();self.encoder.addItems(['auto','cpu','nvidia','intel','amd']);self.encoder.setCurrentText(c.encoder);form.addRow('CPU / GPU / Auto',self.encoder)
        self.normalize=QCheckBox();self.normalize.setChecked(c.adjustments.get('normalize',False));form.addRow('Chuẩn hóa âm lượng',self.normalize)
        self.duck=QCheckBox();self.duck.setChecked(c.adjustments.get('ducking',False));form.addRow('Giảm nhạc khi có âm chính',self.duck)
        form.addRow(QLabel('Thiết lập cho clip mới khi lập lô / ma trận'))
        config=c.adjustments.get('batch_video',{});self.batch_values={}
        for key,label,lo,hi,default in [('trim_head','Cắt đầu s',0,3600,0),('trim_tail','Cắt đuôi s',0,3600,0),('speed','Tốc độ mặc định',.1,10,1),('volume','Âm gốc mặc định',0,4,1),('rotation','Xoay mặc định °',-360,360,0),('random_flip','Xác suất lật thêm (0–1)',0,1,0),('rotation_min','Random xoay min °',-360,360,-5),('rotation_max','Random xoay max °',-360,360,5),('zoom_min','Zoom min',1,2,1),('zoom_max','Zoom max',1,2,1.1)]:
            field=QDoubleSpinBox();field.setDecimals(3);field.setRange(lo,hi);field.setValue(config.get(key,default));self.batch_values[key]=field;form.addRow(label,field)
        for key,label in [('flip','Lật ngang mặc định'),('random_rotate','Bật random xoay'),('random_zoom','Bật zoom in/out random (cả editor)')]:
            field=QCheckBox();field.setChecked(config.get(key,False));self.batch_values[key]=field;form.addRow(label,field)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def ratio_changed(self,index):
        sizes={1:(1280,720),2:(720,1280),3:(1080,1080),4:(1080,1350)}
        if index in sizes:self.values['width'].setValue(sizes[index][0]);self.values['height'].setValue(sizes[index][1])
    def apply(self):
        c=deepcopy(self.editor.composition)
        for key,widget in self.values.items():
            if key in {'brightness','contrast','saturation','gamma'}:c.adjustments[key]=widget.value()
            else:setattr(c,key,widget.value())
        c.fit=self.fit.currentText();c.encoder=self.encoder.currentText();c.adjustments['normalize']=self.normalize.isChecked();c.adjustments['ducking']=self.duck.isChecked()
        c.adjustments['batch_video']={key:field.isChecked() if isinstance(field,QCheckBox) else field.value() for key,field in self.batch_values.items()}
        if c.adjustments['batch_video']['zoom_min']>c.adjustments['batch_video']['zoom_max'] or c.adjustments['batch_video']['rotation_min']>c.adjustments['batch_video']['rotation_max']:QMessageBox.warning(self,'Khoảng chưa hợp lệ','Min phải ≤ max');return
        try:c.validate()
        except ValueError as exc:QMessageBox.warning(self,'Thiết lập chưa hợp lệ',str(exc));return
        self.editor.begin();self.editor.composition=c;self.editor.commit('Thiết lập đầu ra');self.accept()


class AudioDialog(QDialog):
    def __init__(self,editor):
        super().__init__(editor);self.editor=editor;self.setWindowTitle('Âm thanh / nhạc / sound effect');self.resize(1200,600)
        layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row)
        add=QPushButton('Thêm âm thanh');add.clicked.connect(self.add);row.addWidget(add)
        delete=QPushButton('Bỏ track chọn');delete.clicked.connect(self.remove);row.addWidget(delete)
        self.mute=QCheckBox('Tắt tiếng video gốc');self.mute.setChecked(editor.composition.mute_original);row.addWidget(self.mute)
        layout.addWidget(QLabel('SFX: Offset là giây sau mốc (đầu cảnh / phần trăm), hoặc giây TRƯỚC mốc (cuối cảnh / cuối video). Cảnh đánh số từ 1.'))
        self.table=QTableWidget(0,17);self.table.setHorizontalHeaderLabels(['Tệp','Vai trò','Volume','Offset s','Lặp','Fade in s','Fade out s','Cắt đầu s','Cắt cuối s (0=hết)','Mute','Solo','Mốc SFX','Vị trí %','Cảnh #','Crossfade lặp (s)','SFX số lần','SFX cách (s)']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(self.table,1)
        for track in editor.composition.audio:self.add_track(track)
        row=QHBoxLayout();layout.addLayout(row);self.fit=QCheckBox('Khớp video theo âm thanh chính');row.addWidget(self.fit);self.policy=QComboBox();self.policy.addItems(['speed','trim','loop','freeze']);row.addWidget(self.policy)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def add_track(self,track):
        row=self.table.rowCount();self.table.insertRow(row);self.table.setItem(row,0,QTableWidgetItem(track['path']))
        mode=QComboBox();mode.addItems(['main','music','sfx']);mode.setCurrentText(track.get('mode','music'));self.table.setCellWidget(row,1,mode)
        for col,key,default in [(2,'volume',.2),(3,'offset',0),(5,'fade_in',0),(6,'fade_out',0),(7,'trim_start',0),(8,'trim_end',0),(12,'position_pct',50),(13,'scene_index',1),(14,'loop_crossfade',0),(15,'repeat_count',1),(16,'repeat_interval',0)]:self.table.setItem(row,col,QTableWidgetItem(str(track.get(key) if track.get(key) is not None else default)))
        placement=QComboBox()
        for label,mode in [('Giây tuyệt đối','absolute'),('Theo % video','percent'),('Trước cuối video','video_end'),('Sau đầu cảnh','scene_start'),('Trước cuối cảnh','scene_end')]:placement.addItem(label,mode)
        choice=placement.findData(track.get('placement','absolute'))
        if choice>=0:placement.setCurrentIndex(choice)
        self.table.setCellWidget(row,11,placement)
        for col,key in [(4,'loop'),(9,'mute'),(10,'solo')]:
            check=QTableWidgetItem();check.setCheckState(Qt.CheckState.Checked if track.get(key) else Qt.CheckState.Unchecked);self.table.setItem(row,col,check)
    def add(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Thêm âm thanh',filter='Audio/video (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.mp4 *.mkv)')
        for path in paths:self.add_track({'path':path,'mode':'main' if not self.table.rowCount() else 'music','volume':1 if not self.table.rowCount() else .2})
    def remove(self):
        for row in sorted({i.row() for i in self.table.selectedIndexes()},reverse=True):self.table.removeRow(row)
    def apply(self):
        try:
            c=deepcopy(self.editor.composition);tracks=[]
            for row in range(self.table.rowCount()):
                track={'path':self.table.item(row,0).text(),'mode':self.table.cellWidget(row,1).currentText(),'loop':self.table.item(row,4).checkState()==Qt.CheckState.Checked}
                for col,key in [(2,'volume'),(3,'offset'),(5,'fade_in'),(6,'fade_out'),(7,'trim_start'),(14,'loop_crossfade'),(16,'repeat_interval')]:
                    value=float(self.table.item(row,col).text())
                    if value<0 or (key=='volume' and value>4):raise ValueError('Giá trị audio phải không âm; volume ≤4')
                    track[key]=value
                count_text=self.table.item(row,15).text().strip()
                if not count_text.isdecimal():raise ValueError('SFX repeat count phải là số nguyên dương')
                track['repeat_count']=int(count_text)
                track['trim_end']=float(self.table.item(row,8).text()) or None
                placement=self.table.cellWidget(row,11).currentData()
                if placement!='absolute':
                    if track['mode']!='sfx':raise ValueError('Mốc theo cảnh / % chỉ dùng cho SFX')
                    track['placement']=placement
                    if placement=='percent':track['position_pct']=float(self.table.item(row,12).text())
                    if placement in {'scene_start','scene_end'}:track['scene_index']=int(self.table.item(row,13).text())
                for col,key in [(9,'mute'),(10,'solo')]:track[key]=self.table.item(row,col).checkState()==Qt.CheckState.Checked
                tracks.append(track)
            c.audio=tracks;c.mute_original=self.mute.isChecked()
            if self.fit.isChecked():
                main=next((t for t in tracks if t['mode']=='main'),None)
                if not main:raise ValueError('Chưa có âm thanh chính')
                c=fit_duration(c,audio_duration(main['path'])-main['trim_start']+main['offset'],policy=self.policy.currentText())
            c.validate()
        except Exception as exc:QMessageBox.warning(self,'Audio chưa hợp lệ',str(exc));return
        self.editor.begin();self.editor.composition=c;self.editor.commit('Thiết lập âm thanh');self.accept()


class KeyframeDialog(QDialog):
    def __init__(self,editor):
        super().__init__(editor);self.editor=editor;self.setWindowTitle('Keyframes — time / property / value');self.resize(650,500)
        layout=QVBoxLayout(self);self.relative=QCheckBox('Thời gian tương đối 0–1 theo thời lượng layer');self.relative.setChecked(editor.layer().motion.get('relative_time',False));layout.addWidget(self.relative)
        row=QHBoxLayout();layout.addLayout(row)
        for label,callback in [('Thêm',self.add),('Xóa dòng chọn',self.remove)]:b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        self.table=QTableWidget(0,3);self.table.setHorizontalHeaderLabels(['Time (s hoặc 0–1)','Thuộc tính','Giá trị']);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);layout.addWidget(self.table,1)
        for key,points in editor.layer().keyframes.items():
            for point in points:self.add(point['time'],key,point['value'])
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def add(self,t=None,key='x',value=None):
        if isinstance(t,bool):t=None
        row=self.table.rowCount();self.table.insertRow(row);self.table.setItem(row,0,QTableWidgetItem(str(self.editor.timeline.playhead if t is None else t)))
        prop=QComboBox();prop.addItems(['x','y','rotation','opacity','scale']);prop.setCurrentText(key);self.table.setCellWidget(row,1,prop)
        self.table.setItem(row,2,QTableWidgetItem(str(self.editor.layer().x if value is None else value)))
    def remove(self):
        for row in sorted({i.row() for i in self.table.selectedIndexes()},reverse=True):self.table.removeRow(row)
    def apply(self):
        try:
            points={}
            for row in range(self.table.rowCount()):
                t=float(self.table.item(row,0).text());key=self.table.cellWidget(row,1).currentText();value=float(self.table.item(row,2).text())
                if self.relative.isChecked() and not 0<=t<=1:raise ValueError('Thời gian tương đối phải từ 0 tới 1')
                if key=='opacity' and not 0<=value<=1:raise ValueError('Opacity phải từ 0 tới 1')
                if key=='scale' and not .01<=value<=10:raise ValueError('Scale phải từ .01 tới 10')
                points.setdefault(key,[]).append({'time':t,'value':value})
            layer=deepcopy(self.editor.layer());layer.keyframes={k:sorted(v,key=lambda p:p['time']) for k,v in points.items()};layer.validate()
        except Exception as exc:QMessageBox.warning(self,'Keyframe chưa hợp lệ',str(exc));return
        self.editor.begin();self.editor.layer().keyframes=layer.keyframes;self.editor.layer().motion['relative_time']=self.relative.isChecked();self.editor.commit('Sửa keyframe');self.accept()
