from pathlib import Path
from fractions import Fraction
import copy
from PySide6.QtWidgets import QDialog,QVBoxLayout,QFormLayout,QComboBox,QDoubleSpinBox,QSpinBox,QCheckBox,QPushButton,QDialogButtonBox,QLabel,QFileDialog,QTabWidget,QWidget
from ..core.model import US,AudioTrack,uid,Project
from ..services.batch import fit_duration

class ClipDialog(QDialog):
    """Edits a draft only; caller commits one undo command after validation."""
    def __init__(self,project,parent=None):
        super().__init__(parent);self.setWindowTitle('Clip / âm thanh / đầu ra');self.project=project;self.setMinimumWidth(560)
        layout=QVBoxLayout(self);self.tabs=QTabWidget();layout.addWidget(self.tabs);video=QWidget();vf=QFormLayout(video);self.tabs.addTab(video,'Video')
        self.clip=QComboBox();self.clip.addItems([f'{i+1}: {Path(next(a.path for a in project.assets if a.id==c.asset_id)).name}' for i,c in enumerate(project.clips)]);vf.addRow('Clip này',self.clip)
        self.fields={}
        for key,label,low,high,step in [('source_in','Cắt đầu (giây)',0,1000000,.1),('source_out','Cắt đến (giây)',.001,1000000,.1),('speed','Tốc độ',.05,16,.05),('volume','Âm gốc clip',0,4,.05),('brightness','Sáng',-1,1,.05),('contrast','Tương phản',.1,4,.05),('saturation','Bão hòa',0,4,.05),('gamma','Gamma',.1,4,.05)]:
            f=QDoubleSpinBox();f.setRange(low,high);f.setSingleStep(step);f.setDecimals(3);vf.addRow(label,f);self.fields[key]=f
        self.fit=QComboBox();self.fit.addItems(['fit','crop','blur']);vf.addRow('Khớp khung',self.fit);self.flip=QCheckBox('Lật ngang');vf.addRow(self.flip)
        self.rotation=QComboBox();self.rotation.addItems(['0','90','180','270']);vf.addRow('Xoay',self.rotation)
        self.ratio=QComboBox();self.ratio.addItems(['Giữ canvas','9:16 (720×1280)','16:9 (1280×720)','1:1 (1080×1080)','4:5 (864×1080)']);vf.addRow('Tỷ lệ đầu ra',self.ratio)
        self.target=QDoubleSpinBox();self.target.setRange(0,1000000);self.target.setDecimals(3);self.target.setSpecialValueText('Không đổi');vf.addRow('Thời lượng clip đích (s)',self.target)
        self.policy=QComboBox();self.policy.addItems(['error','speed','cut','loop','freeze']);vf.addRow('Nếu không khớp',self.policy)
        self.clip.currentIndexChanged.connect(self.load_clip);self.load_clip(0)
        audio=QWidget();af=QFormLayout(audio);self.tabs.addTab(audio,'Âm thanh');self.track=QComboBox();self.track.addItems([f'{a.role}: {Path(a.path).name}' for a in project.audio]);af.addRow('Track',self.track)
        self.audio_fields={}
        for key,label,low,high in [('start','Điểm bắt đầu (s)',0,1000000),('trim_in','Trim vào (s)',0,1000000),('trim_out','Trim ra (s)',0,1000000),('gain','Gain',0,4),('fade_in','Fade vào (s)',0,1000000),('fade_out','Fade ra (s)',0,1000000)]:
            f=QDoubleSpinBox();f.setRange(low,high);f.setDecimals(3);af.addRow(label,f);self.audio_fields[key]=f
        self.role=QComboBox();self.role.addItems(['main','music','sfx']);af.addRow('Vai trò',self.role);self.loop=QCheckBox('Lặp');self.mute=QCheckBox('Mute');self.solo=QCheckBox('Solo')
        for box in [self.loop,self.mute,self.solo]:af.addRow(box)
        self.mute_original=QCheckBox('Tắt tiếng gốc cả project');self.mute_original.setChecked(project.settings.get('mute_original',False));af.addRow(self.mute_original)
        self.normalize=QCheckBox('Chuẩn hóa loudnorm -16 LUFS / -1.5 dBTP (single-pass)');self.normalize.setChecked(project.settings.get('normalize_audio',False));af.addRow(self.normalize)
        af.addRow(QLabel('Thêm audio bằng nút “＋ Audio” ở editor. Duration/track được probe ở nền. Limiter tổng bật trong pipeline; nghe thử qua proxy.'))
        self.track.currentIndexChanged.connect(self.load_audio);self.load_audio(0)
        self.error=QLabel();self.error.setWordWrap(True);layout.addWidget(self.error);buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.accepted.connect(self.apply);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def load_clip(self,index):
        if index<0 or not self.project.clips:return
        c=self.project.clips[index]
        for key,f in self.fields.items():f.setValue(float(Fraction(c.speed)) if key=='speed' else getattr(c,key)/(US if key.startswith('source_') else 1))
        self.fit.setCurrentText(c.fit);self.flip.setChecked(c.flip);self.rotation.setCurrentText(str(c.rotation))
    def load_audio(self,index):
        if index<0 or not self.project.audio:return
        a=self.project.audio[index]
        for key,f in self.audio_fields.items():f.setValue(getattr(a,key)/(1 if key=='gain' else US))
        self.role.setCurrentText(a.role);self.loop.setChecked(a.loop);self.mute.setChecked(a.muted);self.solo.setChecked(a.solo)
    def apply(self):
        before=self.project.to_dict()
        try:
            if self.project.clips:
                index=self.clip.currentIndex();c=self.project.clips[index]
                if c.locked:raise ValueError('Clip bị khóa')
                old=c.time_map;old_total=self.project.duration
                for key,f in self.fields.items():setattr(c,key,str(Fraction(str(f.value()))) if key=='speed' else round(f.value()*US) if key.startswith('source_') else f.value())
                asset=next(a for a in self.project.assets if a.id==c.asset_id)
                if c.source_out>asset.duration:raise ValueError('Trim vượt thời lượng nguồn')
                c.fit=self.fit.currentText();c.flip=self.flip.isChecked();c.rotation=int(self.rotation.currentText())
                parts=fit_duration(c,round(self.target.value()*US),self.policy.currentText(),fps=self.project.fps) if self.target.value() else [c]
                delta=sum(x.time_map.duration for x in parts)-old.duration
                self.project.clips[index:index+1]=parts
                for after in self.project.clips[index+len(parts):]:after.offset+=delta
                # Source-time map preserved for subtitles in the affected clip, then later cues ripple.
                from ..services.subtitles import map_cues
                from dataclasses import replace
                source_cues=[];others=[]
                for cue in self.project.cues:
                    if cue.start>=old.offset+old.duration:others.append(replace(cue,start=cue.start+delta,end=cue.end+delta))
                    elif cue.end<=old.offset:others.append(cue)
                    else:source_cues.append(replace(cue,start=old.source_in+round(Fraction(max(cue.start,old.offset)-old.offset)*Fraction(old.speed)),end=old.source_in+round(Fraction(min(cue.end,old.offset+old.duration)-old.offset)*Fraction(old.speed))))
                self.project.cues=sorted(others+map_cues(source_cues,[part.time_map for part in parts]),key=lambda cue:cue.start)
                for layer in self.project.layers:
                    if layer.end==old_total:layer.end=self.project.duration
            size={1:(720,1280),2:(1280,720),3:(1080,1080),4:(864,1080)}.get(self.ratio.currentIndex())
            if size:self.project.width,self.project.height=size
            if self.project.audio:
                a=self.project.audio[self.track.currentIndex()]
                for key,f in self.audio_fields.items():setattr(a,key,f.value() if key=='gain' else round(f.value()*US))
                a.role=self.role.currentText();a.loop=self.loop.isChecked();a.muted=self.mute.isChecked();a.solo=self.solo.isChecked()
                if a.trim_out and a.trim_out<=a.trim_in:raise ValueError('Audio trim phải có thời lượng dương')
            self.project.settings.update(mute_original=self.mute_original.isChecked(),normalize_audio=self.normalize.isChecked());self.project.validate();self.accept()
        except Exception as exc:
            self.project.__dict__.update(Project.from_dict(before).__dict__);self.error.setText(str(exc))
