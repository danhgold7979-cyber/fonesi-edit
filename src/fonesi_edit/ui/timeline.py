"""Read-only exact-time timeline overview; no playback, trim or render claim."""
from copy import deepcopy
from fractions import Fraction

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QGraphicsScene,QGraphicsView,
    QGraphicsRectItem,QGraphicsTextItem,QListWidget,QListWidgetItem,QSlider,QPushButton,QCheckBox,
    QDoubleSpinBox,QFormLayout)
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.timeline_edit_commands import split_video_clip,trim_video_clip,TimelineEditError


def _q(value):
    return Fraction(value[0],value[1])


class TimelinePanel(QWidget):
    project_changed=Signal()
    def __init__(self,get_session,parent=None):
        super().__init__(parent)
        self.get_session=get_session
        self.selected_clip_id=None;self._fps=Fraction(30);self._playhead=0
        self._last_project_id=None;self._crop_original=None;self._crop_revision=None
        self._fit_transform=None;self._playhead_marker=None;self._timeline_left=120;self._timeline_scale=1.0
        self._zoom_percent=100
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

    def _select_clip(self,row):
        item=self.clip_list.item(row) if row>=0 else None
        self.selected_clip_id=None if item is None else item.data(Qt.ItemDataRole.UserRole)
        self._refresh_crop_inspector()
        self.update_actions()

    def _playhead_changed(self,value):
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
