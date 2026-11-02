"""Promote fully observed local media to a canonical timeline asset/clip."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

from fonesi_edit.domain.media_library import MediaRecord
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.media.frames import FrameScan
from .projects import Project
from .autosave import CompletedCommand


class TimelineImportError(ValueError):
    pass


@dataclass(frozen=True)
class TimelineAddition:
    asset_id: str
    clip_id: str
    audio_clip_ids: tuple[str, ...]
    command: CompletedCommand


def _pair(value):
    if type(value) is not Fraction:
        raise TimelineImportError('Exact rational media timing required')
    return [value.numerator, value.denominator]


def _end_time(data):
    ends=[Fraction(c['output_start'][0],c['output_start'][1])+
          (Fraction(c['source_out'][0],c['source_out'][1])-
           Fraction(c['source_in'][0],c['source_in'][1]))/
          Fraction(c['speed'][0],c['speed'][1])+
          Fraction(c['freeze_duration'][0],c['freeze_duration'][1])
          for c in data['clips']]
    ends.extend(Fraction(c['output_start'][0],c['output_start'][1])+
          (Fraction(c['source_out'][0],c['source_out'][1])-
           Fraction(c['source_in'][0],c['source_in'][1]))/
          Fraction(c['speed'][0],c['speed'][1])
          for c in data['audio']['clips'])
    return max(ends,default=Fraction(0))


def add_video_clip(project: Project, record: MediaRecord, scan: FrameScan, *,
                   expected_revision: int) -> TimelineAddition:
    if type(project) is not Project or type(record) is not MediaRecord or type(scan) is not FrameScan:
        raise TimelineImportError('Typed project, media record and frame scan required')
    if type(expected_revision) is not int or expected_revision < 0:
        raise TimelineImportError('Exact session revision required')
    record.__post_init__()
    if record.observation_state != 'OBSERVED' or record.observation is None:
        raise TimelineImportError('Media must have an explicit typed observation')
    if record.path_ref.base != 'absolute' or not Path(record.path_ref.path).is_absolute():
        raise TimelineImportError('Timeline insertion requires an absolute verified source path')
    observation=record.observation
    if observation.container_duration is None or observation.container_duration <= 0:
        raise TimelineImportError('Known positive container duration required')
    videos=[s for s in observation.streams if s.kind=='video' and not s.attached_picture]
    if len(videos)!=1:
        raise TimelineImportError('Exactly one non-attached video stream is supported in this slice')
    video=videos[0]
    if (video.codec is None or video.time_base is None or video.start_pts is None or
            video.start is None or video.duration is None or video.duration<=0 or
            video.width is None or video.height is None or video.sar is None or
            video.rotation_degrees is None):
        raise TimelineImportError('Video stream timing, geometry and orientation must be fully observed')
    if (scan.status!='OBSERVED_EOF' or scan.render_ready is not False or
            scan.source_sha256!=record.sha256 or scan.stream_index!=video.index or
            scan.time_base!=video.time_base or scan.start_pts!=video.start_pts or
            not scan.frames or len(scan.frames)>100000):
        raise TimelineImportError('A complete matching bounded frame observation is required')
    frame_pts=[]
    previous=None
    for frame in scan.frames:
        if frame.pts is None:
            raise TimelineImportError('Every timeline frame needs an actual PTS')
        relative=(Fraction(frame.pts-video.start_pts,1)*video.time_base)
        if relative<0 or relative>video.duration or (previous is not None and relative<=previous):
            raise TimelineImportError('Frame PTS must be strictly increasing and within the selected stream')
        frame_pts.append(_pair(relative))
        previous=relative

    stream_records=[]
    audio_streams=[]
    for stream in observation.streams:
        if stream.kind=='video':
            if stream is not video:
                raise TimelineImportError('Additional video streams require explicit stream selection')
            matrix=None if stream.display_matrix is None else [[n,1] for n in stream.display_matrix]
            stream_records.append({
                'index':stream.index,'codec':stream.codec,'time_base':_pair(stream.time_base),
                'start_time':_pair(stream.start),'duration':_pair(stream.duration),'type':'video',
                'width':stream.width,'height':stream.height,'sar':_pair(stream.sar),
                'rotation_degrees':_pair(stream.rotation_degrees),'display_matrix':matrix,
                'frame_pts':frame_pts,
            })
        elif stream.kind=='audio':
            if (stream.codec is None or stream.time_base is None or stream.start is None or
                    stream.duration is None or stream.duration<=0 or stream.sample_rate is None or
                    stream.channels is None or stream.channel_layout not in ('mono','stereo')):
                raise TimelineImportError('Audio stream facts/layout are incomplete or unsupported')
            if stream.channels != (1 if stream.channel_layout=='mono' else 2):
                raise TimelineImportError('Audio channel count/layout mismatch')
            stream_records.append({
                'index':stream.index,'codec':stream.codec,'time_base':_pair(stream.time_base),
                'start_time':_pair(stream.start),'duration':_pair(stream.duration),'type':'audio',
                'sample_rate':stream.sample_rate,'channel_layout':stream.channel_layout,
                'channels':stream.channels,
            })
            audio_streams.append(stream)
        else:
            raise TimelineImportError('Subtitle/data/unknown streams require a separate import path')

    data=project.plan.to_dict()
    asset_id=str(uuid4())
    probe={'duration':_pair(observation.container_duration),'streams':stream_records}
    candidate_asset={'id':asset_id,'kind':'video','path_ref':record.path_ref.to_dict(),
                     'sha256':record.sha256,'probe':probe}
    existing=next((a for a in data['assets'] if a['sha256']==record.sha256),None)
    if existing is not None:
        if existing['probe']!=probe or existing['path_ref']!=record.path_ref.to_dict():
            raise TimelineImportError('Same content already exists with different path/stream facts; relink first')
        asset_id=existing['id']
    else:
        data['assets'].append(candidate_asset)

    start=_end_time(data)
    clip_id=str(uuid4())
    data['clips'].append({
        'id':clip_id,'asset_id':asset_id,'source_in':[0,1],
        'source_out':_pair(video.duration),'output_start':_pair(start),'speed':[1,1],
        'fit':'contain',
        'background':{'kind':'color','color':[0,0,0,255],'blur_amount':[0,1]},
        'crop':{'left':[0,1],'top':[0,1],'width':[1,1],'height':[1,1]},
        'transform':{'x':[1,2],'y':[1,2],'width':[1,1],'height':[1,1],
            'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
            'anchor':'center','flip_x':False,'flip_y':False},
        'color':{'brightness':[0,1],'contrast':[1,1],'saturation':[1,1],
                 'gamma':[1,1],'temperature':[0,1]},
        'freeze_duration':[0,1],'video_stream_index':video.index,
    })
    audio_ids=[]
    for stream in audio_streams:
        audio_id=str(uuid4());audio_ids.append(audio_id)
        data['audio']['clips'].append({
            'id':audio_id,'asset_id':asset_id,'source_in':[0,1],
            'source_out':_pair(stream.duration),'output_start':_pair(start),'speed':[1,1],
            'preserve_pitch':True,'gain_db':[0,1],'pan':[0,1],'mute':False,'solo':False,
            'fade_in':[0,1],'fade_out':[0,1],'role':'original',
            'audio_stream_index':stream.index,
        })
    end=start+video.duration
    for stream in audio_streams:
        end=max(end,start+stream.duration)
    old_duration=Fraction(data['output']['duration'][0],data['output']['duration'][1])
    data['output']['duration']=_pair(max(old_duration,end))
    data['revision']+=1
    data['provenance']['project_revision']=data['revision']
    plan=CompositionPlan.parse(data)
    command=CompletedCommand(project.with_plan(plan),expected_revision)
    return TimelineAddition(asset_id,clip_id,tuple(audio_ids),command)
