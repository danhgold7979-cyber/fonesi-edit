"""Exact-time timeline editing with explicit, still-frame-only source preview."""
from copy import deepcopy
from fractions import Fraction

from pathlib import Path
from uuid import uuid4
from PySide6.QtCore import QRectF, QPointF, Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QBrush, QPen, QImage, QPixmap, QPainter
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QGraphicsScene,QGraphicsView,
    QGraphicsRectItem,QGraphicsTextItem,QListWidget,QListWidgetItem,QSlider,QPushButton,QCheckBox,
    QDoubleSpinBox,QFormLayout,QLineEdit,QFileDialog,QComboBox)
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.ui.project_history import ProjectCommandHistory
from fonesi_edit.storage.timeline_edit_commands import split_video_clip,trim_video_clip,TimelineEditError
from fonesi_edit.media.preview import (PreviewFrame,AudioWaveform,PreviewError,PreviewCanceled,PreviewRetirementUnknown,
    extract_preview_frame,extract_audio_waveform,resolve_asset_path)
from fonesi_edit.ui.shortcuts import ShortcutRegistry,ShortcutEventRouter


def _q(value):
    return Fraction(value[0],value[1])



class PreviewWorker(QThread):
    """One explicit still-frame request; owns its decoder until retirement."""
    def __init__(self,source,ffmpeg,expected_sha256,stream_index,decoder_time,parent=None,decoder_times=None,
                 max_width=1280,max_height=720):
        super().__init__(parent)
        self.source=Path(source);self.ffmpeg=Path(ffmpeg)
        self.expected_sha256=expected_sha256;self.stream_index=stream_index
        self.decoder_time=decoder_time;self.decoder_times=tuple(decoder_times or (decoder_time,))
        self.max_width=max_width;self.max_height=max_height
        if not 1<=len(self.decoder_times)<=4:raise ValueError('Preview worker supports one to four timestamps')
        if type(max_width) is not int or not 1<=max_width<=1280 or type(max_height) is not int or not 1<=max_height<=720:
            raise ValueError('Preview dimensions must remain within the decoder bounds')
        self.frames=[];self.frame=None;self.error=None;self.canceled=False;self.retirement_unknown=False
    def run(self):
        try:
            for timestamp in self.decoder_times:
                if self.isInterruptionRequested():raise PreviewCanceled('Preview sequence canceled')
                frame=extract_preview_frame(self.source,self.ffmpeg,
                    expected_sha256=self.expected_sha256,stream_index=self.stream_index,
                    decoder_time=timestamp,cancel=self.isInterruptionRequested,
                    timeout=30,max_width=self.max_width,max_height=self.max_height)
                self.frames.append(frame)
            if len(self.frames)==1:self.frame=self.frames[0]
        except PreviewCanceled:
            self.canceled=True;self.frames.clear()
        except PreviewRetirementUnknown as exc:
            self.retirement_unknown=True;self.error=str(exc);self.frames.clear()
        except PreviewError as exc:
            self.error=str(exc);self.frames.clear()
        except BaseException:
            self.error='Không thể tạo ảnh xem nhanh; không áp dụng kết quả chưa xác nhận.'
            self.frames.clear()




class WaveformWorker(QThread):
    """One bounded mono PCM waveform observation; no audio playback."""
    def __init__(self,source,ffmpeg,expected_sha256,stream_index,decoder_start,duration,parent=None):
        super().__init__(parent)
        self.source=Path(source);self.ffmpeg=Path(ffmpeg);self.expected_sha256=expected_sha256
        self.stream_index=stream_index;self.decoder_start=decoder_start;self.duration=duration
        self.waveform=None;self.error=None;self.canceled=False;self.retirement_unknown=False
    def run(self):
        try:
            self.waveform=extract_audio_waveform(self.source,self.ffmpeg,
                expected_sha256=self.expected_sha256,stream_index=self.stream_index,
                decoder_start=self.decoder_start,duration=self.duration,
                cancel=self.isInterruptionRequested,timeout=30,bucket_count=256)
        except PreviewCanceled:
            self.canceled=True
        except PreviewRetirementUnknown as exc:
            self.retirement_unknown=True;self.error=str(exc)
        except PreviewError as exc:
            self.error=str(exc)
        except BaseException:
            self.error='Không thể tạo waveform; không áp dụng kết quả chưa xác nhận.'


class WaveformWidget(QWidget):
    """Simple min/max amplitude envelope; deliberately not an audio meter."""
    def __init__(self,parent=None):
        super().__init__(parent);self.peaks=()
        self.setMinimumSize(320,72);self.setMaximumHeight(96)
    def set_peaks(self,peaks):
        self.peaks=tuple(peaks);self.update()
    def clear(self):
        self.peaks=();self.update()
    def paintEvent(self,event):
        painter=QPainter(self)
        painter.fillRect(self.rect(),QColor('#111820'))
        if not self.peaks:
            painter.setPen(QPen(QColor('#aab6c5')))
            painter.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'Chưa có waveform')
            painter.end();return
        painter.setPen(QPen(QColor('#75b7a2'),1))
        middle=self.height()/2;amplitude=max(1,middle-5);width=max(1,self.width())
        count=len(self.peaks)
        for index,(low,high) in enumerate(self.peaks):
            x=int((index+.5)*width/count)
            y1=int(middle-high*amplitude);y2=int(middle-low*amplitude)
            painter.drawLine(x,y1,x,y2)
        painter.end()

class CropEditorView(QWidget):
    """Normalized crop overlay on a user-requested still frame; never renders a crop."""
    crop_changed=Signal(object)

    def __init__(self,parent=None):
        super().__init__(parent)
        self._image=QImage()
        self._message='Ảnh tĩnh — chưa có preview'
        self.crop={'left':0.0,'top':0.0,'width':1.0,'height':1.0}
        self.grid=True;self.editing=False;self.ratio_locked=False
        self._active_handle=None;self._press=None;self._start_crop=None
        self._image_rect=QRectF()
        self.setMinimumSize(320,180);self.setMaximumHeight(260)
        self.setMouseTracking(True);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('Vùng chỉnh crop trên ảnh tĩnh')
        self.setAccessibleDescription('Kéo vùng crop để di chuyển; kéo tám tay nắm để đổi kích thước. Nhấn Escape để hủy thao tác kéo hiện tại. Đây không phải crop preview hay render.')
        self.setStyleSheet('background:#111820;color:#aab6c5;border:1px solid #56616f;')

    def setPixmap(self,pixmap):
        self._image=pixmap.toImage().copy();self._message=''
        self.update()

    def clear(self):
        self._image=QImage();self.update()

    def setText(self,text):
        self._message=str(text);self.update()

    def hasPixmap(self):
        return not self._image.isNull()

    def pixmap(self):
        return QPixmap.fromImage(self._image)

    def text(self):
        return self._message


    def set_crop(self,crop):
        self.crop={key:float(_q(crop[key])) if isinstance(crop[key],(list,tuple)) else float(crop[key])
                   for key in ('left','top','width','height')}
        self.update()

    def set_grid(self,enabled):
        self.grid=bool(enabled);self.update()

    def set_editing(self,enabled):
        self.editing=bool(enabled) and self.hasPixmap()
        if not self.editing:
            self._cancel_pointer_gesture()
        self.setCursor(Qt.CursorShape.CrossCursor if self.editing else Qt.CursorShape.ArrowCursor)
        self.update()

    def _cancel_pointer_gesture(self):
        if self._start_crop is not None:
            self.crop=dict(self._start_crop)
        self._active_handle=None;self._press=None;self._start_crop=None
        self.update()

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self._active_handle is not None:
            self._cancel_pointer_gesture()
            event.accept();return
        super().keyPressEvent(event)

    def set_ratio_locked(self,enabled):
        self.ratio_locked=bool(enabled)

    def _fit_rect(self):
        if not self.hasPixmap():return QRectF()
        margin=8
        available=QRectF(self.rect()).adjusted(margin,margin,-margin,-margin)
        scale=min(available.width()/self._image.width(),available.height()/self._image.height())
        width=self._image.width()*scale;height=self._image.height()*scale
        return QRectF(available.center().x()-width/2,available.center().y()-height/2,width,height)

    def _crop_rect(self):
        r=self._image_rect
        return QRectF(r.left()+self.crop['left']*r.width(),
                      r.top()+self.crop['top']*r.height(),
                      self.crop['width']*r.width(),self.crop['height']*r.height())

    def _handles(self,rect):
        cx=rect.center().x();cy=rect.center().y()
        return {'nw':rect.topLeft(),'n':QPointF(cx,rect.top()),'ne':rect.topRight(),
                'e':QPointF(rect.right(),cy),'se':rect.bottomRight(),'s':QPointF(cx,rect.bottom()),
                'sw':rect.bottomLeft(),'w':QPointF(rect.left(),cy)}

    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        painter.fillRect(self.rect(),QColor('#111820'))
        if not self.hasPixmap():
            painter.setPen(QPen(QColor('#aab6c5')))
            painter.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self._message)
            painter.end();return
        self._image_rect=self._fit_rect()
        painter.drawImage(self._image_rect,self._image,QRectF(self._image.rect()))
        crop=self._crop_rect();image=self._image_rect
        shade=QColor(0,0,0,145)
        painter.fillRect(QRectF(image.left(),image.top(),image.width(),max(0,crop.top()-image.top())),shade)
        painter.fillRect(QRectF(image.left(),crop.bottom(),image.width(),max(0,image.bottom()-crop.bottom())),shade)
        painter.fillRect(QRectF(image.left(),crop.top(),max(0,crop.left()-image.left()),crop.height()),shade)
        painter.fillRect(QRectF(crop.right(),crop.top(),max(0,image.right()-crop.right()),crop.height()),shade)
        painter.setPen(QPen(QColor('#f4d35e'),2))
        painter.drawRect(crop)
        if self.grid:
            painter.setPen(QPen(QColor(245,245,245,150),1,Qt.PenStyle.DashLine))
            for fraction in (1/3,2/3):
                x=crop.left()+crop.width()*fraction;y=crop.top()+crop.height()*fraction
                painter.drawLine(QPointF(x,crop.top()),QPointF(x,crop.bottom()))
                painter.drawLine(QPointF(crop.left(),y),QPointF(crop.right(),y))
        if self.editing:
            painter.setPen(QPen(QColor('#17212b'),1));painter.setBrush(QColor('#f5f7fa'))
            for point in self._handles(crop).values():
                painter.drawRect(QRectF(point.x()-4,point.y()-4,8,8))
        painter.end()

    def mousePressEvent(self,event):
        if not self.editing or not self.hasPixmap():return
        point=QPointF(event.position())
        crop=self._crop_rect()
        handle=next((name for name,p in self._handles(crop).items()
                     if (point-p).manhattanLength()<=13),None)
        if handle is None and crop.contains(point):handle='move'
        if handle is None:return
        self._active_handle=handle;self._press=point;self._start_crop=dict(self.crop)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        event.accept()

    def mouseMoveEvent(self,event):
        if self._active_handle is None or self._start_crop is None:return
        point=QPointF(event.position());image=self._image_rect
        if image.width()<=0 or image.height()<=0:return
        start=self._start_crop;handle=self._active_handle
        dx=(point.x()-self._press.x())/image.width()
        dy=(point.y()-self._press.y())/image.height()
        left=start['left'];top=start['top'];right=left+start['width'];bottom=top+start['height']
        minimum=.01
        if handle=='move':
            left=max(0,min(1-start['width'],left+dx))
            top=max(0,min(1-start['height'],top+dy))
            right=left+start['width'];bottom=top+start['height']
        else:
            if 'w' in handle:left=max(0,min(right-minimum,left+dx))
            if 'e' in handle:right=min(1,max(left+minimum,right+dx))
            if 'n' in handle:top=max(0,min(bottom-minimum,top+dy))
            if 's' in handle:bottom=min(1,max(top+minimum,bottom+dy))
            if self.ratio_locked:
                ratio=max(minimum,start['width'])/max(minimum,start['height'])
                if handle in ('nw','ne','sw','se'):
                    fixed_x=right if 'w' in handle else left
                    fixed_y=bottom if 'n' in handle else top
                    width=abs(right-left);height=abs(bottom-top)
                    if width/max(height,minimum)>ratio:
                        height=width/ratio
                    else:
                        width=height*ratio
                    max_width=fixed_x if 'w' in handle else 1-fixed_x
                    max_height=fixed_y if 'n' in handle else 1-fixed_y
                    factor=min(1.0,max_width/max(width,minimum),max_height/max(height,minimum))
                    width*=factor;height*=factor
                    if 'w' in handle:left=fixed_x-width;right=fixed_x
                    else:left=fixed_x;right=fixed_x+width
                    if 'n' in handle:top=fixed_y-height;bottom=fixed_y
                    else:top=fixed_y;bottom=fixed_y+height
                elif 'e' in handle or 'w' in handle:
                    fixed_x=left if 'e' in handle else right
                    max_width=1-fixed_x if 'e' in handle else fixed_x
                    width=min(max(minimum,abs(right-left)),max_width,ratio)
                    height=width/ratio
                    center=start['top']+start['height']/2
                    top=max(0,min(1-height,center-height/2));bottom=top+height
                    if 'e' in handle:left=fixed_x;right=fixed_x+width
                    else:left=fixed_x-width;right=fixed_x
                else:
                    fixed_y=top if 's' in handle else bottom
                    max_height=1-fixed_y if 's' in handle else fixed_y
                    height=min(max(minimum,abs(bottom-top)),max_height,1/ratio)
                    width=height*ratio
                    center=start['left']+start['width']/2
                    left=max(0,min(1-width,center-width/2));right=left+width
                    if 's' in handle:top=fixed_y;bottom=fixed_y+height
                    else:top=fixed_y-height;bottom=fixed_y
            left=max(0,min(left,1-minimum));top=max(0,min(top,1-minimum))
            right=max(left+minimum,min(1,right));bottom=max(top+minimum,min(1,bottom))
        self.crop={'left':left,'top':top,'width':right-left,'height':bottom-top}
        self.update();event.accept()

    def mouseReleaseEvent(self,event):
        if self._active_handle is None:return
        changed=dict(self.crop);original=self._start_crop
        self._active_handle=None;self._press=None;self._start_crop=None
        if original is not None and any(abs(changed[key]-original[key])>1e-12
                                        for key in ('left','top','width','height')):
            self.crop_changed.emit(changed)
        event.accept()


class TimelinePanel(QWidget):
    project_changed=Signal()
    idle=Signal()
    def __init__(self,get_session,parent=None,shortcut_registry=None,history=None):
        super().__init__(parent)
        self.get_session=get_session
        self.shortcut_registry=shortcut_registry or ShortcutRegistry(self)
        self.history=history or ProjectCommandHistory(get_session,self)
        self.history.changed.connect(self.update_actions)
        self.selected_clip_id=None;self._fps=Fraction(30);self._playhead=0
        self._last_project_id=None;self._crop_original=None;self._crop_revision=None;self._crop_overlay_pending=False
        self._fit_transform=None;self._playhead_marker=None;self._timeline_left=120;self._timeline_scale=1.0
        self._zoom_percent=100;self._last_revision=None;self._preview_generation=0;self._waveform_generation=0
        self._in_frame=None;self._out_frame=None;self._frame_total=0;self.selected_marker_id=None
        self._preview_revision=None;self._preview_clip_id=None;self.preview_worker=None
        self.waveform_worker=None;self.stopping=False
        self.preview_retirement_unknown=False
        layout=QVBoxLayout(self)
        self.notice=QLabel('Timeline có playhead theo frame, tách/trim và ảnh tĩnh nguồn qua FFmpeg do bạn chọn. Chưa có phát video/âm thanh, thumbnail/waveform tự động hoặc render.')
        self.notice.setWordWrap(True);layout.addWidget(self.notice)
        self.summary=QLabel('Chưa có clip trong timeline.')
        self.summary.setTextFormat(Qt.TextFormat.PlainText);layout.addWidget(self.summary)
        self.clip_list=QListWidget();self.clip_list.currentRowChanged.connect(self._select_clip)
        layout.addWidget(self.clip_list)
        controls=QHBoxLayout()
        self.playhead_slider=QSlider(Qt.Orientation.Horizontal);self.playhead_slider.setRange(0,0)
        self.playhead_slider.valueChanged.connect(self._playhead_changed);controls.addWidget(self.playhead_slider)
        self.playhead_label=QLabel('Playhead: 0 frame');controls.addWidget(self.playhead_label)
        self.set_in_button=QPushButton('Đặt In');self.set_out_button=QPushButton('Đặt Out')
        self.clear_range_button=QPushButton('Xóa In/Out')
        self.range_label=QLabel('Chưa chọn vùng In/Out')
        for widget in (self.set_in_button,self.set_out_button,self.clear_range_button,self.range_label):controls.addWidget(widget)
        self.ripple=QCheckBox('Ripple (đóng khoảng trống)');controls.addWidget(self.ripple)
        self.split_button=QPushButton('Tách tại playhead');self.trim_in_button=QPushButton('Trim đầu');self.trim_out_button=QPushButton('Trim cuối')
        for button in (self.split_button,self.trim_in_button,self.trim_out_button):controls.addWidget(button)
        layout.addLayout(controls)
        self.action_message=QLabel('');self.action_message.setWordWrap(True);layout.addWidget(self.action_message)
        marker_controls=QHBoxLayout()
        self.add_marker_button=QPushButton('Thêm marker (M)')
        self.remove_marker_button=QPushButton('Xóa marker chọn')
        self.marker_count_label=QLabel('Chưa có marker')
        marker_controls.addWidget(self.add_marker_button);marker_controls.addWidget(self.remove_marker_button)
        marker_controls.addWidget(self.marker_count_label);layout.addLayout(marker_controls)
        self.marker_list=QListWidget();self.marker_list.setMaximumHeight(88)
        self.marker_list.currentRowChanged.connect(self._select_timeline_marker)
        layout.addWidget(self.marker_list)
        self.add_marker_button.clicked.connect(self.add_timeline_marker)
        self.remove_marker_button.clicked.connect(self.remove_timeline_marker)
        crop_title=QLabel('Crop clip — tọa độ chuẩn hóa 0..1')
        layout.addWidget(crop_title)
        crop_form=QFormLayout();self.crop_spins={}
        for name,label in (('left','Trái'),('top','Trên'),('width','Rộng'),('height','Cao')):
            spin=QDoubleSpinBox();spin.setDecimals(8);spin.setSingleStep(0.01)
            spin.setRange(0.00000001 if name in ('width','height') else 0.0,1.0)
            spin.editingFinished.connect(self.stage_crop_from_spins)
            self.crop_spins[name]=spin;crop_form.addRow(label,spin)
        crop_widget=QWidget();crop_widget.setLayout(crop_form);layout.addWidget(crop_widget)
        zoom_row=QHBoxLayout();zoom_row.addWidget(QLabel('Zoom timeline'))
        self.zoom_slider=QSlider(Qt.Orientation.Horizontal);self.zoom_slider.setRange(50,400);self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._zoom_changed);zoom_row.addWidget(self.zoom_slider)
        self.zoom_label=QLabel('100%');zoom_row.addWidget(self.zoom_label)
        self.fit_button=QPushButton('Vừa khung');self.fit_button.clicked.connect(lambda:self.zoom_slider.setValue(100))
        zoom_row.addWidget(self.fit_button);layout.addLayout(zoom_row)
        preview_controls=QHBoxLayout()
        self.preview_path=QLineEdit();self.preview_path.setMaxLength(32767)
        self.preview_path.setPlaceholderText('Đường dẫn tuyệt đối tới FFmpeg do bạn chọn')
        self.preview_path.textChanged.connect(self._preview_path_changed)
        self.preview_browse=QPushButton('Chọn FFmpeg…');self.preview_browse.clicked.connect(self.choose_preview_ffmpeg)
        self.preview_quality=QComboBox()
        self.preview_quality.addItem('Nháp · 320×180',(320,180))
        self.preview_quality.addItem('Tiêu chuẩn · 640×360',(640,360))
        self.preview_quality.addItem('Cao · 1280×720',(1280,720))
        self.preview_quality.setCurrentIndex(1)
        self.preview_quality.currentIndexChanged.connect(self._preview_quality_changed)
        self.preview_trust=QCheckBox('Tin cậy FFmpeg và DLL/phụ thuộc cùng thư mục')
        self.preview_trust.toggled.connect(self.update_actions)
        self.preview_button=QPushButton('Xem ảnh tại playhead');self.preview_button.clicked.connect(self.request_preview)
        self.filmstrip_button=QPushButton('Tạo filmstrip 4 ảnh');self.filmstrip_button.clicked.connect(lambda:self.request_preview(filmstrip=True))
        self.waveform_button=QPushButton('Tạo waveform audio · 60s');self.waveform_button.clicked.connect(self.request_waveform)
        for widget in (self.preview_path,self.preview_browse,self.preview_quality,self.preview_trust,self.preview_button,self.filmstrip_button,self.waveform_button):preview_controls.addWidget(widget)
        layout.addLayout(preview_controls)
        self.preview_message=QLabel('Chưa có ảnh xem nhanh. Chỉ chạy FFmpeg sau khi chọn đường dẫn và xác nhận tin cậy.')
        self.preview_message.setWordWrap(True);layout.addWidget(self.preview_message)
        self.preview_image=CropEditorView(self)
        self.preview_image.setText('Ảnh tĩnh — chưa có preview')
        self.preview_image.crop_changed.connect(self._crop_overlay_changed)
        layout.addWidget(self.preview_image)
        crop_tools=QHBoxLayout()
        self.crop_edit_toggle=QCheckBox('Chỉnh crop trên ảnh tĩnh')
        self.crop_grid_check=QCheckBox('Lưới 1/3');self.crop_grid_check.setChecked(True)
        self.crop_ratio_lock=QCheckBox('Khóa tỷ lệ')
        self.crop_apply_button=QPushButton('Xác nhận crop')
        self.crop_cancel_button=QPushButton('Hủy crop')
        for widget in (self.crop_edit_toggle,self.crop_grid_check,self.crop_ratio_lock,self.crop_apply_button,self.crop_cancel_button):crop_tools.addWidget(widget)
        layout.addLayout(crop_tools)
        self.crop_edit_toggle.toggled.connect(self.preview_image.set_editing)
        self.crop_grid_check.toggled.connect(self.preview_image.set_grid)
        self.crop_ratio_lock.toggled.connect(self.preview_image.set_ratio_locked)
        self.crop_apply_button.clicked.connect(self.apply_crop)
        self.crop_cancel_button.clicked.connect(self.cancel_crop)
        filmstrip_row=QHBoxLayout();self.filmstrip_labels=[]
        for index in range(4):
            label=QLabel(f'Ảnh {index+1}');label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(160,90);label.setStyleSheet('background:#111820;color:#aab6c5;border:1px solid #56616f;')
            self.filmstrip_labels.append(label);filmstrip_row.addWidget(label)
        layout.addLayout(filmstrip_row)
        self.waveform_message=QLabel('Waveform chỉ là biên độ audio; chưa có phát âm thanh hoặc đồng bộ A/V.')
        self.waveform_message.setWordWrap(True);layout.addWidget(self.waveform_message)
        self.waveform_widget=WaveformWidget(self);self.waveform_widget.setStyleSheet('border:1px solid #56616f;')
        layout.addWidget(self.waveform_widget)
        self.set_in_button.clicked.connect(self.set_in_marker)
        self.set_out_button.clicked.connect(self.set_out_marker)
        self.clear_range_button.clicked.connect(self.clear_range_markers)
        self.split_button.clicked.connect(self.split_at_playhead)
        self.trim_in_button.clicked.connect(lambda:self.trim_at_playhead('in'))
        self.trim_out_button.clicked.connect(lambda:self.trim_at_playhead('out'))
        self.scene=QGraphicsScene(self)
        self.view=QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QBrush(QColor('#111820')))
        layout.addWidget(self.view)
        self._install_timeline_shortcuts()
        self.update_project()

    def _install_timeline_shortcuts(self):
        bindings=(
            ('timeline.previous_frame',lambda:self._step_playhead(-1)),
            ('timeline.next_frame',lambda:self._step_playhead(1)),
            ('timeline.previous_10',lambda:self._step_playhead(-10)),
            ('timeline.next_10',lambda:self._step_playhead(10)),
            ('timeline.start',lambda:self.playhead_slider.setValue(self.playhead_slider.minimum())),
            ('timeline.end',lambda:self.playhead_slider.setValue(self.playhead_slider.maximum())),
            ('timeline.mark_in',self.set_in_marker),
            ('timeline.mark_out',self.set_out_marker),
            ('timeline.add_marker',self.add_timeline_marker),
            ('timeline.clear_range',self.clear_range_markers),
        )
        self.timeline_shortcut_router=ShortcutEventRouter(
            self.shortcut_registry,bindings,self,
            repeatable=('timeline.previous_frame','timeline.next_frame',
                        'timeline.previous_10','timeline.next_10',
                        'timeline.start','timeline.end'),
        )
        for owner in (self.clip_list,self.clip_list.viewport(),self.marker_list,self.marker_list.viewport(),self.view,self.view.viewport()):
            owner.installEventFilter(self.timeline_shortcut_router)
        help_text='Timeline: M thêm marker; I/O đặt vùng; phím tắt có thể đổi trong Cài đặt. Ô crop giữ phím chỉnh sửa riêng.'
        self.clip_list.setToolTip(help_text);self.view.setToolTip(help_text)

    def _step_playhead(self,delta):
        if self.stopping or self.playhead_slider.isSliderDown():return
        self.playhead_slider.setValue(max(self.playhead_slider.minimum(),
            min(self.playhead_slider.maximum(),self.playhead_slider.value()+delta)))

    def _select_timeline_marker(self,row):
        item=self.marker_list.item(row) if row>=0 else None
        if item is None:
            self.selected_marker_id=None
            self.update_actions()
            return
        marker_id=item.data(Qt.ItemDataRole.UserRole)
        self.selected_marker_id=marker_id
        session=self.get_session()
        if session is not None:
            marker=next((x for x in session.project.plan.to_dict().get('timeline_markers',[])
                         if x['id']==marker_id),None)
            if marker is not None:self.playhead_slider.setValue(marker['frame'])
        self.update_actions()

    def _commit_timeline_markers(self,markers):
        session=self.get_session()
        if session is None or self.stopping:return False
        if session.reconciliation_required:
            self.action_message.setText('Project cần đối soát; không thay đổi timeline markers.')
            return False
        expected=session.revision
        data=session.project.plan.to_dict()
        if markers:data['timeline_markers']=markers
        else:data.pop('timeline_markers',None)
        data['revision']=expected+1
        data['provenance']['project_revision']=expected+1
        try:
            plan=CompositionPlan.parse(data)
            session.commit(CompletedCommand(session.project.with_plan(plan),expected))
        except Exception:
            self.action_message.setText('Không xác nhận được thay đổi marker; project không được tự gửi lại.')
            return False
        self.project_changed.emit()
        return True

    def add_timeline_marker(self):
        session=self.get_session()
        if session is None or self.stopping:return
        if session.reconciliation_required:
            self.action_message.setText('Project cần đối soát; không thêm marker.')
            return
        markers=list(session.project.plan.to_dict().get('timeline_markers',[]))
        if len(markers)>=1000:
            self.action_message.setText('Đã đạt giới hạn 1000 marker của project.')
            return
        frame=self._playhead
        if any(marker['frame']==frame for marker in markers):
            self.action_message.setText('Frame hiện tại đã có marker; hãy chuyển playhead tới frame khác.')
            return
        used={marker['label'] for marker in markers}
        number=1
        while f'M{number}' in used:number+=1
        marker={'id':str(uuid4()),'frame':frame,'label':f'M{number}'}
        markers.append(marker)
        previous=self.selected_marker_id
        self.selected_marker_id=marker['id']
        if not self._commit_timeline_markers(markers):
            self.selected_marker_id=previous
            return
        self.action_message.setText(f"Đã lưu marker {marker['label']} tại frame {frame}.")

    def remove_timeline_marker(self):
        session=self.get_session()
        if session is None or self.stopping:return
        if session.reconciliation_required:
            self.action_message.setText('Project cần đối soát; không xóa marker.')
            return
        if self.selected_marker_id is None:
            self.action_message.setText('Chọn marker cần xóa trong danh sách trước.')
            return
        markers=list(session.project.plan.to_dict().get('timeline_markers',[]))
        remaining=[marker for marker in markers if marker['id']!=self.selected_marker_id]
        if len(remaining)==len(markers):
            self.selected_marker_id=None
            self.action_message.setText('Marker đã không còn trong project; danh sách sẽ được làm mới.')
            self.update_project()
            return
        removed=self.selected_marker_id
        self.selected_marker_id=None
        if not self._commit_timeline_markers(remaining):
            self.selected_marker_id=removed
            return
        self.action_message.setText('Đã xóa marker khỏi project.')

    def _commit_range_markers(self,in_frame,out_frame):
        session=self.get_session()
        if session is None or self.stopping or session.reconciliation_required:return False
        expected=session.revision
        data=session.project.plan.to_dict()
        if in_frame is None and out_frame is None:
            data.pop('timeline_range',None)
        else:
            data['timeline_range']={'in_frame':in_frame,'out_frame':out_frame}
        data['revision']=expected+1
        data['provenance']['project_revision']=expected+1
        try:
            plan=CompositionPlan.parse(data)
            session.commit(CompletedCommand(session.project.with_plan(plan),expected))
        except Exception:
            self.action_message.setText('Không lưu được vùng In/Out; project chưa được xác nhận thay đổi. Kiểm tra trạng thái project trước khi thử lại.')
            return False
        self.project_changed.emit()
        return True

    def set_in_marker(self):
        if self.get_session() is None or self.stopping:return
        frame=self._playhead
        if self._out_frame is not None and frame>=self._out_frame:
            self.action_message.setText('Điểm In phải nằm trước điểm Out; vùng chọn không thay đổi.')
            return
        if not self._commit_range_markers(frame,self._out_frame):return
        self.action_message.setText('Đã lưu điểm In tại frame hiện tại. Vùng chọn dùng khoảng [In, Out).')

    def set_out_marker(self):
        if self.get_session() is None or self.stopping:return
        if self._in_frame is None:
            self.action_message.setText('Đặt điểm In trước khi đặt Out.')
            return
        frame=self._playhead+1
        if frame<=self._in_frame or frame>self._frame_total:
            self.action_message.setText('Điểm Out phải sau điểm In và không vượt quá cuối project.')
            return
        if not self._commit_range_markers(self._in_frame,frame):return
        self.action_message.setText('Đã lưu điểm Out sau frame hiện tại. Vùng chọn dùng khoảng [In, Out).')

    def clear_range_markers(self):
        if self._in_frame is None and self._out_frame is None:return
        if not self._commit_range_markers(None,None):return
        self.action_message.setText('Đã xóa vùng In/Out đã lưu trong project.')

    def _range_label(self):
        if self._in_frame is None:return 'Chưa chọn vùng In/Out'
        if self._out_frame is None:return f'In {self._in_frame} · chưa đặt Out'
        return f'In {self._in_frame} → Out {self._out_frame} · {self._out_frame-self._in_frame} frame'

    def _selected_clip(self):
        session=self.get_session()
        if session is None or self.selected_clip_id is None:return None
        data=session.project.plan.to_dict()
        return next((x for x in data['clips'] if x['id']==self.selected_clip_id),None)

    @property
    def busy(self):
        return self.preview_worker is not None or self.waveform_worker is not None or self.preview_retirement_unknown

    def _invalidate_preview(self,message='Đầu vào preview thay đổi; kết quả cũ không còn áp dụng.'):
        self._preview_generation+=1;self._waveform_generation+=1
        if self.preview_worker is not None:self.preview_worker.requestInterruption()
        if self.waveform_worker is not None:self.waveform_worker.requestInterruption()
        if hasattr(self,'preview_message'):
            if hasattr(self,'crop_edit_toggle'):
                self.crop_edit_toggle.setChecked(False)
            if getattr(self,'_crop_overlay_pending',False) and hasattr(self,'crop_cancel_button'):
                self.cancel_crop()
            self.preview_message.setText(message)
            self.preview_image.clear()
            self.preview_image.setText('Ảnh tĩnh — preview chưa sẵn sàng')
            for index,label in enumerate(self.filmstrip_labels):
                label.clear();label.setText(f'Ảnh {index+1}')
            self.waveform_widget.clear()
            self.waveform_message.setText('Waveform cũ đã bị loại bỏ do đầu vào thay đổi.')

    def _preview_quality_changed(self,_index):
        self._preview_generation+=1
        if self.preview_worker is not None:self.preview_worker.requestInterruption()
        self.crop_edit_toggle.setChecked(False)
        if self._crop_overlay_pending:self.cancel_crop()
        self.preview_message.setText('Chất lượng preview đã đổi; ảnh cũ bị loại bỏ và cache sẽ dùng khóa độ phân giải mới.')
        self.preview_image.clear();self.preview_image.setText('Ảnh tĩnh — preview chưa sẵn sàng')
        for index,label in enumerate(self.filmstrip_labels):
            label.clear();label.setText(f'Ảnh {index+1}')
        self.update_actions()

    def _preview_path_changed(self,_value):
        self.preview_trust.setChecked(False)
        self._invalidate_preview('Đường dẫn FFmpeg đã đổi; xác nhận tin cậy lại trước khi chạy.')
        self.update_actions()

    def choose_preview_ffmpeg(self):
        filename,_=QFileDialog.getOpenFileName(self,'Chọn FFmpeg','','FFmpeg (ffmpeg.exe ffmpeg);;Chương trình (*)')
        if filename:self.preview_path.setText(filename)

    def _selected_audio_clip(self,data=None):
        session=self.get_session();clip=self._selected_clip()
        if session is None or clip is None:return None
        data=session.project.plan.to_dict() if data is None else data
        return next((x for x in data['audio']['clips']
                     if x['asset_id']==clip['asset_id'] and x.get('role')=='original'),None)

    def request_waveform(self):
        session=self.get_session();clip=self._selected_clip()
        if self.busy or self.stopping or session is None or clip is None:return
        if session.reconciliation_required:
            self.waveform_message.setText('Project cần đối soát; không chạy waveform.')
            return
        if not self.preview_trust.isChecked():
            self.waveform_message.setText('Cần xác nhận tin cậy FFmpeg và DLL/phụ thuộc cùng thư mục.')
            return
        ffmpeg=Path(self.preview_path.text())
        if not ffmpeg.is_absolute():
            self.waveform_message.setText('Chọn đường dẫn FFmpeg tuyệt đối; không tự tìm công cụ thay thế.')
            return
        try:
            data=session.project.plan.to_dict()
            asset=next(x for x in data['assets'] if x['id']==clip['asset_id'])
            audio_clip=self._selected_audio_clip(data)
            if audio_clip is None:raise PreviewError('Clip không có audio gốc tương ứng.')
            stream_index=audio_clip['audio_stream_index']
            stream=next(x for x in asset['probe']['streams']
                        if x['index']==stream_index and x['type']=='audio')
            source_in=_q(audio_clip['source_in']);source_out=_q(audio_clip['source_out'])
            speed=_q(audio_clip['speed'])
            duration=min(source_out-source_in,Fraction(60))
            decoder_start=_q(stream['start_time'])+source_in
            source=resolve_asset_path(asset,session.project_base)
            expected=asset['sha256']
        except (StopIteration,KeyError,ValueError,OSError,RuntimeError,PreviewError) as exc:
            self.waveform_message.setText(str(exc) if isinstance(exc,PreviewError)
                else 'Không xác định được audio stream; không chạy decoder.')
            return
        self.waveform_widget.clear()
        self.waveform_message.setText('Đang giải mã tối đa 60 giây audio thành waveform; không phát âm thanh.')
        worker=WaveformWorker(source,ffmpeg,expected,stream_index,decoder_start,duration,self)
        self._waveform_generation+=1;generation=self._waveform_generation
        self._preview_revision=session.revision;self._preview_clip_id=clip['id']
        self.waveform_worker=worker
        worker.finished.connect(lambda:self._waveform_finished(worker,generation))
        self.update_actions();worker.start()

    def _waveform_finished(self,worker,generation):
        if self.waveform_worker is not worker:return
        if not worker.wait(0):
            QTimer.singleShot(10,lambda:self._waveform_finished(worker,generation))
            return
        session=self.get_session()
        current=(generation==self._waveform_generation and not self.stopping and session is not None
                 and session.revision==self._preview_revision and self.selected_clip_id==self._preview_clip_id)
        if worker.retirement_unknown:
            self.preview_retirement_unknown=True;self.stopping=True
            self.waveform_widget.clear()
            self.waveform_message.setText('KHÔNG THỂ XÁC NHẬN FFmpeg và tiến trình con đã dừng. Đã khóa chạy lại và đóng ứng dụng; kiểm tra Task Manager/tiến trình hệ thống rồi khởi động lại.')
        elif current and worker.waveform is not None:
            waveform=worker.waveform;self.waveform_widget.set_peaks(waveform.peaks)
            self.waveform_message.setText(
                f"Waveform biên độ · stream {waveform.stream_index} · {waveform.sample_rate} Hz · "
                f"{waveform.sample_count} samples · {len(waveform.peaks)} bins · "
                f"{float(waveform.duration):.2f}s tối đa 60s · {'cache' if waveform.cache_hit else 'FFmpeg'}; "
                'không phải loudness/clipping meter, playback, A/V sync hay render.')
        elif current and worker.error:
            self.waveform_widget.clear();self.waveform_message.setText(worker.error)
        elif current and worker.canceled:
            self.waveform_message.setText('Đã dừng waveform; không thay đổi project.')
        self.waveform_worker=None;worker.deleteLater();self.update_actions();self.idle.emit()

    def request_preview(self,filmstrip=False):
        session=self.get_session();clip=self._selected_clip()
        if self.busy or self.stopping or session is None or clip is None:return
        if session.reconciliation_required:
            self.preview_message.setText('Project cần đối soát; không chạy preview.')
            return
        if not self.preview_trust.isChecked():
            self.preview_message.setText('Cần xác nhận tin cậy FFmpeg và DLL/phụ thuộc cùng thư mục.')
            return
        ffmpeg=Path(self.preview_path.text())
        if not ffmpeg.is_absolute():
            self.preview_message.setText('Chọn đường dẫn FFmpeg tuyệt đối; không tự tìm công cụ thay thế.')
            return
        try:
            data=session.project.plan.to_dict()
            asset=next(x for x in data['assets'] if x['id']==clip['asset_id'])
            stream_index=clip['video_stream_index']
            stream=next(x for x in asset['probe']['streams']
                        if x['index']==stream_index and x['type']=='video')
            if _q(clip['freeze_duration'])!=0:
                raise PreviewError('Preview hiện chưa hỗ trợ clip freeze.')
            start=_q(clip['output_start']);source_in=_q(clip['source_in'])
            source_out=_q(clip['source_out']);speed=_q(clip['speed'])
            stream_start=_q(stream['start_time'])
            if filmstrip:
                source_length=source_out-source_in
                decoder_times=tuple(stream_start+source_in+source_length*offset
                    for offset in (Fraction(1,8),Fraction(3,8),Fraction(5,8),Fraction(7,8)))
            else:
                playhead=Fraction(self._playhead,1)/self._fps
                if not start<=playhead<start+(source_out-source_in)/speed:
                    raise PreviewError('Playhead phải nằm trong phần video đang chọn.')
                source_time=source_in+(playhead-start)*speed
                decoder_times=(stream_start+source_time,)
            source=resolve_asset_path(asset,session.project_base)
            expected=asset['sha256']
        except (StopIteration,KeyError,ValueError,OSError,RuntimeError,PreviewError) as exc:
            self.preview_message.setText(str(exc) if isinstance(exc,PreviewError)
                else 'Không xác định được asset/stream của clip; không chạy decoder.')
            return
        self.cancel_crop()
        self.crop_edit_toggle.setChecked(False)
        self.preview_image.clear()
        self.preview_image.setText('Đang tạo filmstrip…' if filmstrip else 'Đang tạo ảnh tĩnh…')
        for index,label in enumerate(self.filmstrip_labels):
            label.clear();label.setText(f'Ảnh {index+1}')
        dimensions=self.preview_quality.currentData()
        if (type(dimensions) is not tuple or len(dimensions)!=2 or
                any(type(value) is not int for value in dimensions)):
            self.preview_message.setText('Chất lượng preview không hợp lệ; không chạy decoder.')
            return
        max_width,max_height=dimensions
        worker=PreviewWorker(source,ffmpeg,expected,stream_index,decoder_times[0],self,
            decoder_times=decoder_times,max_width=max_width,max_height=max_height)
        self._preview_generation+=1;generation=self._preview_generation
        self._preview_revision=session.revision;self._preview_clip_id=clip['id']
        self.preview_worker=worker
        worker.finished.connect(lambda:self._preview_finished(worker,generation))
        self.preview_message.setText(
            'Đang tạo bốn ảnh tĩnh theo chiều dài clip bằng FFmpeg đã chọn; không phát video/âm thanh.'
            if filmstrip else 'Đang tạo một ảnh tĩnh bằng FFmpeg đã chọn. Không phát video/âm thanh và không render project.')
        self.update_actions();worker.start()

    def _preview_finished(self,worker,generation):
        if self.preview_worker is not worker:return
        if not worker.wait(0):
            QTimer.singleShot(10,lambda:self._preview_finished(worker,generation))
            return
        session=self.get_session()
        current=(generation==self._preview_generation and not self.stopping and session is not None
                 and session.revision==self._preview_revision and self.selected_clip_id==self._preview_clip_id)
        if worker.retirement_unknown:
            self.preview_retirement_unknown=True;self.stopping=True
            self.preview_image.clear();self.preview_image.setText('Tiến trình FFmpeg chưa xác nhận đã dừng.')
            self.preview_message.setText('KHÔNG THỂ XÁC NHẬN FFmpeg và tiến trình con đã dừng. Đã khóa chạy lại và đóng ứng dụng; kiểm tra Task Manager/tiến trình hệ thống rồi khởi động lại.')
        elif current and worker.frames:
            images=[QImage.fromData(frame.png,'PNG') for frame in worker.frames]
            if any(image.isNull() for image in images):
                self.preview_image.clear();self.preview_image.setText('Không giải mã được PNG preview.')
                self.preview_message.setText('Có ảnh trả về không hợp lệ; không áp dụng một phần kết quả.')
            elif len(worker.frames)==1:
                frame=worker.frames[0];pixmap=QPixmap.fromImage(images[0])
                self.preview_image.setPixmap(pixmap)
                self._refresh_crop_inspector()
                for index,label in enumerate(self.filmstrip_labels):
                    label.clear();label.setText(f'Ảnh {index+1}')
                self.preview_message.setText(
                    f"Ảnh tĩnh {frame.width}×{frame.height} · stream {frame.stream_index} · "
                    f"timestamp decoder {frame.decoder_time} · {'cache' if frame.cache_hit else 'FFmpeg'}; "
                    'không phải preview compositor, không đồng bộ audio và không chứng minh export parity.')
            else:
                self.preview_image.clear();self.preview_image.setText(f'Filmstrip {len(worker.frames)} ảnh tĩnh')
                for label,frame,image in zip(self.filmstrip_labels,worker.frames,images):
                    pixmap=QPixmap.fromImage(image)
                    label.setPixmap(pixmap.scaled(label.size(),Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation))
                    label.setToolTip(f'Stream {frame.stream_index} · decoder timestamp {frame.decoder_time}')
                hits=sum(frame.cache_hit for frame in worker.frames)
                self.preview_message.setText(
                    f"Filmstrip {len(worker.frames)} ảnh · {hits} cache hit · stream {worker.frames[0].stream_index}; "
                    'ảnh tĩnh rời rạc, không phải timeline thumbnail liên tục, playback hay A/V sync.')
        elif current and worker.error:
            self.preview_image.clear();self.preview_image.setText('Chưa có ảnh preview.')
            self.preview_message.setText(worker.error)
        elif current and worker.canceled:
            self.preview_message.setText('Đã dừng preview; không thay đổi project.')
        self.preview_worker=None;worker.deleteLater();self.update_actions();self.idle.emit()

    def request_stop(self):
        self.stopping=True
        self._invalidate_preview('Đang dừng preview; chờ FFmpeg và tiến trình con kết thúc an toàn.')
        self.update_actions()

    def _select_clip(self,row):
        item=self.clip_list.item(row) if row>=0 else None
        selected=None if item is None else item.data(Qt.ItemDataRole.UserRole)
        if selected!=self.selected_clip_id:
            self.crop_edit_toggle.setChecked(False)
            self.selected_clip_id=selected
            self._invalidate_preview('Clip đã đổi; ảnh preview cũ đã bị loại bỏ.')
        self._refresh_crop_inspector()
        self.update_actions()

    def _playhead_changed(self,value):
        if value!=self._playhead:
            self._invalidate_preview('Playhead đã đổi; yêu cầu ảnh tĩnh mới nếu cần.')
        self._playhead=value
        time=Fraction(value,1)/self._fps
        self.playhead_label.setText(f'Playhead: {value} frame · {float(time):.3f}s')
        self._move_playhead_marker()
        self.update_actions()

    def update_actions(self):
        session=self.get_session()
        clip=self._selected_clip()
        available=clip is not None and session is not None and not session.reconciliation_required
        inside=False
        if available:
            start=_q(clip['output_start']);end=start+(_q(clip['source_out'])-_q(clip['source_in']))/_q(clip['speed'])+_q(clip['freeze_duration'])
            playhead=Fraction(self._playhead,1)/self._fps
            inside=start<playhead<end
        self.split_button.setEnabled(available and inside)
        self.trim_in_button.setEnabled(available and inside)
        self.trim_out_button.setEnabled(available and inside)
        crop_enabled=available
        for spin in self.crop_spins.values():spin.setEnabled(crop_enabled)
        self.crop_edit_toggle.setEnabled(crop_enabled and self.preview_image.hasPixmap() and not self.busy and not self.stopping)
        self.crop_apply_button.setEnabled(crop_enabled and self._crop_overlay_pending and not self.busy and not self.stopping)
        self.crop_cancel_button.setEnabled(crop_enabled and self._crop_overlay_pending and not self.busy and not self.stopping)
        self.fit_button.setEnabled(session is not None)
        self.zoom_slider.setEnabled(session is not None)
        markers_ready=session is not None and not self.stopping
        for button in (self.set_in_button,self.set_out_button,self.clear_range_button):button.setEnabled(markers_ready)
        timeline_markers=[] if session is None else session.project.plan.to_dict().get('timeline_markers',[])
        marker_ready=markers_ready and not session.reconciliation_required
        self.add_marker_button.setEnabled(marker_ready and len(timeline_markers)<1000)
        self.remove_marker_button.setEnabled(marker_ready and any(x['id']==self.selected_marker_id for x in timeline_markers))
        preview_inside=False
        if available:
            preview_start=_q(clip['output_start'])
            preview_end=preview_start+(_q(clip['source_out'])-_q(clip['source_in']))/_q(clip['speed'])
            preview_time=Fraction(self._playhead,1)/self._fps
            preview_inside=preview_start<=preview_time<preview_end and _q(clip['freeze_duration'])==0
        preview_ready=(available and preview_inside and not self.busy and not self.stopping and self.preview_trust.isChecked()
                       and bool(self.preview_path.text()) and Path(self.preview_path.text()).is_absolute())
        self.preview_button.setEnabled(preview_ready and not self.preview_retirement_unknown)
        filmstrip_ready=(available and _q(clip['freeze_duration'])==0 and not self.busy and not self.stopping
                         and self.preview_trust.isChecked() and bool(self.preview_path.text())
                         and Path(self.preview_path.text()).is_absolute())
        self.filmstrip_button.setEnabled(filmstrip_ready and not self.preview_retirement_unknown)
        audio_clip=self._selected_audio_clip() if available else None
        waveform_ready=(available and audio_clip is not None and not self.busy and not self.stopping
                        and self.preview_trust.isChecked() and bool(self.preview_path.text())
                        and Path(self.preview_path.text()).is_absolute())
        self.waveform_button.setEnabled(waveform_ready and not self.preview_retirement_unknown)
        self.preview_path.setEnabled(not self.busy and not self.stopping and not self.preview_retirement_unknown)
        self.preview_browse.setEnabled(not self.busy and not self.stopping and not self.preview_retirement_unknown)
        self.preview_trust.setEnabled(not self.busy and not self.stopping and not self.preview_retirement_unknown)
        # Quality may change during a running still-frame request; that invalidates
        # the request generation and asks its owned worker to retire safely.
        self.preview_quality.setEnabled(not self.stopping and not self.preview_retirement_unknown)

    def _refresh_crop_inspector(self):
        session=self.get_session();clip=self._selected_clip()
        enabled=clip is not None and session is not None and not session.reconciliation_required
        self._crop_revision=None if session is None else session.revision
        self._crop_original=None if clip is None else deepcopy(clip['crop'])
        self._crop_overlay_pending=False
        for name,spin in self.crop_spins.items():
            spin.setEnabled(enabled)
            if clip is not None:
                spin.blockSignals(True);spin.setValue(float(_q(clip['crop'][name])));spin.blockSignals(False)
        if clip is not None:
            self.preview_image.set_crop(clip['crop'])
        self.crop_apply_button.setEnabled(False)
        self.crop_cancel_button.setEnabled(False)
        if not self.preview_image.hasPixmap():
            self.crop_edit_toggle.setChecked(False)

    def stage_crop_from_spins(self):
        if self._crop_original is None:return
        staged={name:self.crop_spins[name].value() for name in ('left','top','width','height')}
        self.preview_image.set_crop(staged)
        self._crop_overlay_pending=True
        self.crop_apply_button.setEnabled(True);self.crop_cancel_button.setEnabled(True)
        self.action_message.setText('Crop đang chỉnh tạm; nhấn Xác nhận để lưu hoặc Hủy để khôi phục.')

    def _crop_overlay_changed(self,crop):
        if not self.crop_edit_toggle.isChecked() or self._crop_original is None:return
        for name in ('left','top','width','height'):
            spin=self.crop_spins[name];spin.blockSignals(True);spin.setValue(crop[name]);spin.blockSignals(False)
        self._crop_overlay_pending=True
        self.crop_apply_button.setEnabled(True);self.crop_cancel_button.setEnabled(True)
        self.action_message.setText('Crop đang chỉnh tạm trên ảnh tĩnh; chưa thay đổi project.')

    def cancel_crop(self):
        self._refresh_crop_inspector()
        self.action_message.setText('Đã hủy thay đổi crop chưa xác nhận; project không đổi.')

    def apply_crop(self):
        session=self.get_session();clip=self._selected_clip()
        if session is None or clip is None or session.reconciliation_required:return
        if self._crop_revision!=session.revision:
            self.action_message.setText('Project đã đổi trong lúc mở inspector; thay đổi crop tạm bị hủy và dữ liệu mới được tải lại.')
            self._refresh_crop_inspector();return
        data=session.project.plan.to_dict()
        target=next((x for x in data['clips'] if x['id']==self.selected_clip_id),None)
        if target is None:return
        original=self._crop_original or deepcopy(target['crop'])
        changed=False
        for name,spin in self.crop_spins.items():
            exact=Fraction(original[name][0],original[name][1])
            shown=Fraction(str(spin.value())).limit_denominator(100000000)
            if abs(shown-exact)>Fraction(1,100000000):
                target['crop'][name]=[shown.numerator,shown.denominator]
                changed=True
        if not changed:
            self._refresh_crop_inspector();return
        expected=session.revision
        data['revision']=expected+1
        data['provenance']['project_revision']=expected+1
        try:
            plan=CompositionPlan.parse(data)
            session.commit(CompletedCommand(session.project.with_plan(plan),expected))
        except Exception:
            self.action_message.setText('Crop không hợp lệ hoặc project đã đổi; dữ liệu đã lưu không bị thay đổi. Kiểm tra lại bốn cạnh.')
            self._refresh_crop_inspector();return
        self._refresh_crop_inspector()
        self.action_message.setText('Đã lưu crop chuẩn hóa; chưa có crop preview compositor hoặc render.')
        self.project_changed.emit()

    def _zoom_changed(self,value):
        self._zoom_percent=value
        self.zoom_label.setText(f'{value}%')
        if self._fit_transform is not None:
            self.view.setTransform(self._fit_transform)
            factor=value/100.0
            self.view.scale(factor,factor)

    def _move_playhead_marker(self):
        if self._playhead_marker is None:return
        time=Fraction(self._playhead,1)/self._fps
        x=self._timeline_left+float(time)*self._timeline_scale
        self._playhead_marker.setRect(QRectF(x,18,2,174))

    def split_at_playhead(self):
        self._apply_timeline_edit('split')

    def trim_at_playhead(self,edge):
        self._apply_timeline_edit(edge)

    def _apply_timeline_edit(self,action):
        session=self.get_session();clip=self._selected_clip()
        if session is None or clip is None:return
        playhead=Fraction(self._playhead,1)/self._fps
        try:
            if action=='split':
                result=split_video_clip(session.project,clip['id'],playhead,expected_revision=session.revision)
            else:
                result=trim_video_clip(session.project,clip['id'],playhead,edge=action,
                    ripple=self.ripple.isChecked(),expected_revision=session.revision)
            session.commit(result.command)
        except TimelineEditError as exc:
            self.action_message.setText(f'Không thực hiện được: {exc}')
            return
        except Exception:
            self.action_message.setText('Không xác nhận được chỉnh sửa timeline; không tự gửi lại.')
            return
        self.action_message.setText('Đã lưu chỉnh sửa timeline theo frame/rational time. Chưa phát hoặc render.')
        self.project_changed.emit()

    def update_project(self):
        session=self.get_session()
        if session is None:
            if self._last_revision is not None:self._invalidate_preview('Project đã đóng; preview cũ bị loại bỏ.')
            self._last_revision=None
        else:
            if self._last_revision is not None and session.revision!=self._last_revision:
                self._invalidate_preview('Project đã thay đổi; preview cũ bị loại bỏ.')
            self._last_revision=session.revision
        self.scene.clear();self._playhead_marker=None
        if session is None:
            self._last_project_id=None;self.selected_clip_id=None;self._playhead=0
            self._in_frame=None;self._out_frame=None;self._frame_total=0;self.selected_marker_id=None
            self.range_label.setText('Chưa chọn vùng In/Out')
            blocked=self.marker_list.blockSignals(True)
            try:self.marker_list.clear()
            finally:self.marker_list.blockSignals(blocked)
            self.marker_count_label.setText('Chưa có marker')
            self._crop_original=None;self._crop_revision=None;self._fit_transform=None
            self.scene.setSceneRect(QRectF(0,0,1000,180))
            blocked=self.clip_list.blockSignals(True)
            try:self.clip_list.clear()
            finally:self.clip_list.blockSignals(blocked)
            blocked=self.playhead_slider.blockSignals(True)
            try:self.playhead_slider.setRange(0,0);self.playhead_slider.setValue(0)
            finally:self.playhead_slider.blockSignals(blocked)
            self.summary.setText('Mở dự án để xem timeline.')
            self.update_actions()
            return
        data=session.project.plan.to_dict()
        if self._last_project_id != data['id']:
            if self._last_project_id is not None:self._invalidate_preview('Project identity changed; previous preview discarded.')
            self._last_project_id=data['id'];self.selected_clip_id=None;self._playhead=0
            self._in_frame=None;self._out_frame=None;self.selected_marker_id=None
        output_duration=_q(data['output']['duration'])
        self._fps=_q(data['output']['fps'])
        blocked=self.clip_list.blockSignals(True)
        try:
            self.clip_list.clear()
            for clip in sorted(data['clips'],key=lambda x:(_q(x['output_start']),x['id'])):
                start=_q(clip['output_start']);length=(_q(clip['source_out'])-_q(clip['source_in']))/_q(clip['speed'])+_q(clip['freeze_duration'])
                row=QListWidgetItem(f"{float(start):.3f}s · {float(length):.3f}s · {clip['id'][:8]}")
                row.setData(Qt.ItemDataRole.UserRole,clip['id']);self.clip_list.addItem(row)
                if clip['id']==self.selected_clip_id:self.clip_list.setCurrentItem(row)
        finally:self.clip_list.blockSignals(blocked)
        frame_count=output_duration*self._fps
        frame_total=(frame_count.numerator+frame_count.denominator-1)//frame_count.denominator
        self._frame_total=frame_total
        stored_range=data.get('timeline_range')
        self._in_frame=None if stored_range is None else stored_range['in_frame']
        self._out_frame=None if stored_range is None else stored_range['out_frame']
        self.range_label.setText(self._range_label())
        timeline_markers=data.get('timeline_markers',[])
        marker_ids={marker['id'] for marker in timeline_markers}
        if self.selected_marker_id not in marker_ids:self.selected_marker_id=None
        blocked=self.marker_list.blockSignals(True)
        try:
            self.marker_list.clear()
            for marker in sorted(timeline_markers,key=lambda x:(x['frame'],x['id'])):
                item=QListWidgetItem(f"{marker['label']} · frame {marker['frame']}")
                item.setData(Qt.ItemDataRole.UserRole,marker['id'])
                self.marker_list.addItem(item)
                if marker['id']==self.selected_marker_id:self.marker_list.setCurrentItem(item)
        finally:self.marker_list.blockSignals(blocked)
        self.marker_count_label.setText(f'{len(timeline_markers)} marker' if timeline_markers else 'Chưa có marker')
        max_frame=max(0,frame_total-1)
        blocked=self.playhead_slider.blockSignals(True)
        try:
            self.playhead_slider.setRange(0,max_frame)
            self.playhead_slider.setValue(min(self._playhead,max_frame))
            self._playhead=self.playhead_slider.value()
        finally:self.playhead_slider.blockSignals(blocked)
        self.playhead_label.setText(f'Playhead: {self._playhead} frame · {float(Fraction(self._playhead,1)/self._fps):.3f}s')
        video=[];audio=[];layers=[]
        for clip in data['clips']:
            start=_q(clip['output_start'])
            length=(_q(clip['source_out'])-_q(clip['source_in']))/_q(clip['speed'])+_q(clip['freeze_duration'])
            video.append((start,length,clip['id']))
        for clip in data['audio']['clips']:
            start=_q(clip['output_start'])
            length=(_q(clip['source_out'])-_q(clip['source_in']))/_q(clip['speed'])
            audio.append((start,length,clip['id']))
        for layer in data['layers']:
            if not layer['visible']:continue
            for interval in layer['intervals']:
                layers.append((_q(interval['start']),_q(interval['end'])-_q(interval['start']),layer['type'],layer['id']))
        end=max([output_duration]+[s+d for s,d,_ in video]+[s+d for s,d,_ in audio]+[s+d for s,d,_,_ in layers])
        seconds=max(float(end),0.1)
        width=max(1000,min(4000,seconds*80))
        scale=width/seconds
        left=120
        scene_width=left+width+40
        self.scene.setSceneRect(QRectF(0,0,scene_width,210))
        background=QGraphicsRectItem(QRectF(left,20,width,170))
        background.setBrush(QBrush(QColor('#202832')))
        background.setPen(QPen(QColor('#56616f'),1))
        background.setZValue(-100)
        self.scene.addItem(background)
        for y,label in ((48,'VIDEO'),(105,'AUDIO'),(162,'LAYER')):
            text=QGraphicsTextItem(label);text.setDefaultTextColor(QColor('#d0d7de'))
            text.setPos(12,y-10);self.scene.addItem(text)
        step=1 if seconds<=30 else 5 if seconds<=150 else 10
        tick=0
        while tick<=seconds:
            x=left+tick*scale
            line=QGraphicsRectItem(QRectF(x,18,1,174))
            line.setBrush(QBrush(QColor('#3b4653')));line.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(line)
            label=QGraphicsTextItem(f'{tick:g}s');label.setDefaultTextColor(QColor('#aab6c5'))
            label.setPos(x+2,0);self.scene.addItem(label)
            tick+=step
        for index,(start,length,clip_id) in enumerate(video):
            rect=QGraphicsRectItem(QRectF(left+float(start)*scale,34,max(3,float(length)*scale),28))
            rect.setBrush(QBrush(QColor('#3979b9')));rect.setPen(QPen(QColor('#9cc8f0'),1))
            rect.setToolTip(f'Video clip {clip_id} · start={start} · duration={length}')
            self.scene.addItem(rect)
            label=QGraphicsTextItem(f'V{index+1}');label.setDefaultTextColor(QColor('white'))
            label.setPos(rect.rect().x()+4,rect.rect().y()+2);self.scene.addItem(label)
        for index,(start,length,clip_id) in enumerate(audio):
            rect=QGraphicsRectItem(QRectF(left+float(start)*scale,91,max(3,float(length)*scale),24))
            rect.setBrush(QBrush(QColor('#357b61')));rect.setPen(QPen(QColor('#9bd8bc'),1))
            rect.setToolTip(f'Audio clip {clip_id} · start={start} · duration={length}')
            self.scene.addItem(rect)
            label=QGraphicsTextItem(f'A{index+1}');label.setDefaultTextColor(QColor('white'))
            label.setPos(rect.rect().x()+4,rect.rect().y()+1);self.scene.addItem(label)
        for index,(start,length,kind,layer_id) in enumerate(layers):
            rect=QGraphicsRectItem(QRectF(left+float(start)*scale,148,max(3,float(length)*scale),20))
            rect.setBrush(QBrush(QColor('#8b6b3f')));rect.setPen(QPen(QColor('#e5c18a'),1))
            rect.setToolTip(f'Layer {kind} {layer_id} · start={start} · duration={length}')
            self.scene.addItem(rect)
        self.summary.setText(
            f"Thời lượng project: {output_duration} giây · {len(video)} video clip · "
            f"{len(audio)} audio clip · {len(layers)} layer interval. Đây là sơ đồ thời gian, không phải preview."
        )
        self._timeline_left=left;self._timeline_scale=scale
        if self._in_frame is not None:
            in_x=left+float(Fraction(self._in_frame,1)/self._fps)*scale
            if self._out_frame is not None:
                out_x=left+float(Fraction(self._out_frame,1)/self._fps)*scale
                region=QGraphicsRectItem(QRectF(in_x,20,max(1,out_x-in_x),170))
                region.setBrush(QBrush(QColor(75,145,215,45)))
                region.setPen(QPen(Qt.PenStyle.NoPen));region.setZValue(-50)
                region.setAcceptedMouseButtons(Qt.MouseButton.NoButton);self.scene.addItem(region)
            in_line=QGraphicsRectItem(QRectF(in_x-1,18,2,174))
            in_line.setBrush(QBrush(QColor('#70d6a5')));in_line.setPen(QPen(Qt.PenStyle.NoPen))
            in_line.setZValue(9000);in_line.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(in_line)
            in_text=QGraphicsTextItem('IN');in_text.setDefaultTextColor(QColor('#70d6a5'))
            in_text.setPos(in_x+2,18);in_text.setZValue(9001);self.scene.addItem(in_text)
        if self._out_frame is not None:
            out_x=left+float(Fraction(self._out_frame,1)/self._fps)*scale
            out_line=QGraphicsRectItem(QRectF(out_x-1,18,2,174))
            out_line.setBrush(QBrush(QColor('#f08a8a')));out_line.setPen(QPen(Qt.PenStyle.NoPen))
            out_line.setZValue(9000);out_line.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(out_line)
            out_text=QGraphicsTextItem('OUT');out_text.setDefaultTextColor(QColor('#f08a8a'))
            out_text.setPos(out_x+2,18);out_text.setZValue(9001);self.scene.addItem(out_text)
        for marker in sorted(timeline_markers,key=lambda x:(x['frame'],x['id'])):
            marker_x=left+float(Fraction(marker['frame'],1)/self._fps)*scale
            marker_line=QGraphicsRectItem(QRectF(marker_x-1,20,2,170))
            marker_line.setBrush(QBrush(QColor('#e6b44a')));marker_line.setPen(QPen(Qt.PenStyle.NoPen))
            marker_line.setZValue(8800);marker_line.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            marker_line.setToolTip(f"{marker['label']} · frame {marker['frame']}")
            self.scene.addItem(marker_line)
            marker_text=QGraphicsTextItem(marker['label']);marker_text.setDefaultTextColor(QColor('#e6b44a'))
            marker_text.setPos(marker_x+2,188);marker_text.setZValue(8801);self.scene.addItem(marker_text)
        self._playhead_marker=QGraphicsRectItem(QRectF(0,18,2,174))
        self._playhead_marker.setBrush(QBrush(QColor('#f4d35e')))
        self._playhead_marker.setPen(QPen(Qt.PenStyle.NoPen))
        self._playhead_marker.setZValue(10000);self.scene.addItem(self._playhead_marker)
        self._move_playhead_marker()
        self.view.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_transform=self.view.transform()
        self._zoom_changed(self._zoom_percent)
        self._refresh_crop_inspector()
        self.update_actions()
