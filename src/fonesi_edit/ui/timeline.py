"""Exact-time timeline editing with explicit, still-frame-only source preview."""
from copy import deepcopy
from fractions import Fraction

from pathlib import Path
from PySide6.QtCore import QRectF, Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QBrush, QPen, QImage, QPixmap
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QGraphicsScene,QGraphicsView,
    QGraphicsRectItem,QGraphicsTextItem,QListWidget,QListWidgetItem,QSlider,QPushButton,QCheckBox,
    QDoubleSpinBox,QFormLayout,QLineEdit,QFileDialog)
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.timeline_edit_commands import split_video_clip,trim_video_clip,TimelineEditError
from fonesi_edit.media.preview import (PreviewFrame,PreviewError,PreviewCanceled,
    extract_preview_frame,resolve_asset_path)


def _q(value):
    return Fraction(value[0],value[1])



class PreviewWorker(QThread):
    """One explicit still-frame request; owns its decoder until retirement."""
    def __init__(self,source,ffmpeg,expected_sha256,stream_index,decoder_time,parent=None):
        super().__init__(parent)
        self.source=Path(source);self.ffmpeg=Path(ffmpeg)
        self.expected_sha256=expected_sha256;self.stream_index=stream_index
        self.decoder_time=decoder_time;self.frame=None;self.error=None;self.canceled=False
    def run(self):
        try:
            self.frame=extract_preview_frame(self.source,self.ffmpeg,
                expected_sha256=self.expected_sha256,stream_index=self.stream_index,
                decoder_time=self.decoder_time,cancel=self.isInterruptionRequested,
                timeout=30,max_width=1280,max_height=720)
        except PreviewCanceled:
            self.canceled=True
        except PreviewError as exc:
            self.error=str(exc)
        except BaseException:
            self.error='Không thể tạo ảnh xem nhanh; không áp dụng kết quả chưa xác nhận.'


class TimelinePanel(QWidget):
    project_changed=Signal()
    idle=Signal()
    def __init__(self,get_session,parent=None):
        super().__init__(parent)
        self.get_session=get_session
        self.selected_clip_id=None;self._fps=Fraction(30);self._playhead=0
        self._last_project_id=None;self._crop_original=None;self._crop_revision=None
        self._fit_transform=None;self._playhead_marker=None;self._timeline_left=120;self._timeline_scale=1.0
        self._zoom_percent=100;self._last_revision=None;self._preview_generation=0
        self._preview_revision=None;self._preview_clip_id=None;self.preview_worker=None;self.stopping=False
        layout=QVBoxLayout(self)
        self.notice=QLabel('Timeline có playhead theo frame, tách và trim theo thời gian hữu tỷ. Chưa có phát lại, thumbnail, waveform hoặc render.')
        self.notice.setWordWrap(True);layout.addWidget(self.notice)
        self.summary=QLabel('Chưa có clip trong timeline.')
        self.summary.setTextFormat(Qt.TextFormat.PlainText);layout.addWidget(self.summary)
        self.clip_list=QListWidget();self.clip_list.currentRowChanged.connect(self._select_clip)
        layout.addWidget(self.clip_list)
        controls=QHBoxLayout()
        self.playhead_slider=QSlider(Qt.Orientation.Horizontal);self.playhead_slider.setRange(0,0)
        self.playhead_slider.valueChanged.connect(self._playhead_changed);controls.addWidget(self.playhead_slider)
        self.playhead_label=QLabel('Playhead: 0 frame');controls.addWidget(self.playhead_label)
        self.ripple=QCheckBox('Ripple (đóng khoảng trống)');controls.addWidget(self.ripple)
        self.split_button=QPushButton('Tách tại playhead');self.trim_in_button=QPushButton('Trim đầu');self.trim_out_button=QPushButton('Trim cuối')
        for button in (self.split_button,self.trim_in_button,self.trim_out_button):controls.addWidget(button)
        layout.addLayout(controls)
        self.action_message=QLabel('');self.action_message.setWordWrap(True);layout.addWidget(self.action_message)
        crop_title=QLabel('Crop clip — tọa độ chuẩn hóa 0..1')
        layout.addWidget(crop_title)
        crop_form=QFormLayout();self.crop_spins={}
        for name,label in (('left','Trái'),('top','Trên'),('width','Rộng'),('height','Cao')):
            spin=QDoubleSpinBox();spin.setDecimals(8);spin.setSingleStep(0.01)
            spin.setRange(0.00000001 if name in ('width','height') else 0.0,1.0)
            spin.editingFinished.connect(self.apply_crop)
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
        self.preview_trust=QCheckBox('Tin cậy FFmpeg và DLL/phụ thuộc cùng thư mục')
        self.preview_trust.toggled.connect(self.update_actions)
        self.preview_button=QPushButton('Xem ảnh tại playhead');self.preview_button.clicked.connect(self.request_preview)
        for widget in (self.preview_path,self.preview_browse,self.preview_trust,self.preview_button):preview_controls.addWidget(widget)
        layout.addLayout(preview_controls)
        self.preview_message=QLabel('Chưa có ảnh xem nhanh. Chỉ chạy FFmpeg sau khi chọn đường dẫn và xác nhận tin cậy.')
        self.preview_message.setWordWrap(True);layout.addWidget(self.preview_message)
        self.preview_image=QLabel('Ảnh tĩnh — chưa có preview')
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter);self.preview_image.setMinimumSize(320,180)
        self.preview_image.setMaximumHeight(240);self.preview_image.setStyleSheet('background:#111820;color:#aab6c5;border:1px solid #56616f;')
        layout.addWidget(self.preview_image)
        self.split_button.clicked.connect(self.split_at_playhead)
        self.trim_in_button.clicked.connect(lambda:self.trim_at_playhead('in'))
        self.trim_out_button.clicked.connect(lambda:self.trim_at_playhead('out'))
        self.scene=QGraphicsScene(self)
        self.view=QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QBrush(QColor('#111820')))
        layout.addWidget(self.view)
        self.update_project()

    def _selected_clip(self):
        session=self.get_session()
        if session is None or self.selected_clip_id is None:return None
        data=session.project.plan.to_dict()
        return next((x for x in data['clips'] if x['id']==self.selected_clip_id),None)

    @property
    def busy(self):
        return self.preview_worker is not None

    def _invalidate_preview(self,message='Đầu vào preview thay đổi; kết quả cũ không còn áp dụng.'):
        self._preview_generation+=1
        if self.preview_worker is not None:
            self.preview_worker.requestInterruption()
        if hasattr(self,'preview_message'):
            self.preview_message.setText(message)
            self.preview_image.clear()
            self.preview_image.setText('Ảnh tĩnh — preview chưa sẵn sàng')

    def _preview_path_changed(self,_value):
        self.preview_trust.setChecked(False)
        self._invalidate_preview('Đường dẫn FFmpeg đã đổi; xác nhận tin cậy lại trước khi chạy.')
        self.update_actions()

    def choose_preview_ffmpeg(self):
        filename,_=QFileDialog.getOpenFileName(self,'Chọn FFmpeg','','FFmpeg (ffmpeg.exe ffmpeg);;Chương trình (*)')
        if filename:self.preview_path.setText(filename)

    def request_preview(self):
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
            playhead=Fraction(self._playhead,1)/self._fps
            if not start<=playhead<start+(source_out-source_in)/speed:
                raise PreviewError('Playhead phải nằm trong phần video đang chọn.')
            source_time=source_in+(playhead-start)*speed
            decoder_time=_q(stream['start_time'])+source_time
            source=resolve_asset_path(asset,session.project_base)
            expected=asset['sha256']
        except (StopIteration,KeyError,ValueError,PreviewError) as exc:
            self.preview_message.setText(str(exc) if isinstance(exc,PreviewError)
                else 'Không xác định được asset/stream của clip; không chạy decoder.')
            return
        worker=PreviewWorker(source,ffmpeg,expected,stream_index,decoder_time,self)
        self._preview_generation+=1;generation=self._preview_generation
        self._preview_revision=session.revision;self._preview_clip_id=clip['id']
        self.preview_worker=worker
        worker.finished.connect(lambda:self._preview_finished(worker,generation))
        self.preview_message.setText('Đang tạo một ảnh tĩnh bằng FFmpeg đã chọn. Không phát video/âm thanh và không render project.')
        self.update_actions();worker.start()

    def _preview_finished(self,worker,generation):
        if self.preview_worker is not worker:return
        if not worker.wait(0):
            QTimer.singleShot(10,lambda:self._preview_finished(worker,generation))
            return
        session=self.get_session()
        current=(generation==self._preview_generation and not self.stopping and session is not None
                 and session.revision==self._preview_revision and self.selected_clip_id==self._preview_clip_id)
        if current and worker.frame is not None:
            image=QImage.fromData(worker.frame.png,'PNG')
            if image.isNull():
                self.preview_image.clear();self.preview_image.setText('Không giải mã được PNG preview.')
                self.preview_message.setText('Ảnh trả về không hợp lệ; không áp dụng cache vào project.')
            else:
                pixmap=QPixmap.fromImage(image)
                self.preview_image.setPixmap(pixmap.scaled(self.preview_image.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                stamp=worker.frame.decoder_time
                self.preview_message.setText(
                    f"Ảnh tĩnh {worker.frame.width}×{worker.frame.height} · stream {worker.frame.stream_index} · "
                    f"timestamp decoder {stamp} · {'cache' if worker.frame.cache_hit else 'FFmpeg'}; "
                    'không phải preview compositor, không đồng bộ audio và không chứng minh export parity.')
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
        self.fit_button.setEnabled(session is not None)
        self.zoom_slider.setEnabled(session is not None)
        preview_ready=(available and not self.busy and not self.stopping and self.preview_trust.isChecked()
                       and bool(self.preview_path.text()) and Path(self.preview_path.text()).is_absolute())
        self.preview_button.setEnabled(preview_ready)
        self.preview_path.setEnabled(not self.busy and not self.stopping)
        self.preview_browse.setEnabled(not self.busy and not self.stopping)
        self.preview_trust.setEnabled(not self.busy and not self.stopping)

    def _refresh_crop_inspector(self):
        session=self.get_session();clip=self._selected_clip()
        enabled=clip is not None and session is not None and not session.reconciliation_required
        self._crop_revision=None if session is None else session.revision
        self._crop_original=None if clip is None else deepcopy(clip['crop'])
        for name,spin in self.crop_spins.items():
            spin.setEnabled(enabled)
            if clip is not None:
                spin.setValue(float(_q(clip['crop'][name])))

    def apply_crop(self):
        session=self.get_session();clip=self._selected_clip()
        if session is None or clip is None or session.reconciliation_required:return
        if self._crop_revision!=session.revision:
            self.action_message.setText('Project đã đổi trong lúc mở inspector; đã tải lại crop, hãy kiểm tra trước khi sửa tiếp.')
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
        if not changed:return
        expected=session.revision
        data['revision']=expected+1
        data['provenance']['project_revision']=expected+1
        try:
            plan=CompositionPlan.parse(data)
            session.commit(CompletedCommand(session.project.with_plan(plan),expected))
        except Exception:
            self.action_message.setText('Crop không hợp lệ hoặc project đã đổi; dữ liệu đã lưu không bị thay đổi. Kiểm tra lại bốn cạnh.')
            return
        self.action_message.setText('Đã lưu crop chuẩn hóa; chưa có crop preview hoặc render.')
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
            self._last_project_id=data['id'];self.selected_clip_id=None;self._playhead=0
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
