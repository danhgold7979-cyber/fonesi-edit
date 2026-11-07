"""Frame-exact timeline split/trim commands with explicit gap vs ripple semantics."""
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from uuid import uuid4

from fonesi_edit.domain.composition import CompositionPlan
from .projects import Project
from .autosave import CompletedCommand


class TimelineEditError(ValueError):
    pass


@dataclass(frozen=True)
class TimelineEditResult:
    command: CompletedCommand
    created_ids: tuple[str, ...] = ()


def _fraction(pair):
    return Fraction(pair[0],pair[1])


def _pair(value):
    if type(value) is not Fraction:
        raise TimelineEditError('Exact rational frame time required')
    return [value.numerator,value.denominator]


def _span(clip):
    start=_fraction(clip['output_start'])
    source_in=_fraction(clip['source_in'])
    source_out=_fraction(clip['source_out'])
    speed=_fraction(clip['speed'])
    freeze=_fraction(clip.get('freeze_duration',[0,1]))
    if speed<=0 or freeze!=0 or source_out<=source_in:
        raise TimelineEditError('Only positive-speed non-freeze clips can be split/trimmed')
    return start,start+(source_out-source_in)/speed,source_in,source_out,speed


def _command(project,data,expected_revision,created=()):
    if type(expected_revision) is not int or expected_revision<0:
        raise TimelineEditError('Exact project session revision required')
    data['revision']+=1
    data['provenance']['project_revision']=data['revision']
    try:
        plan=CompositionPlan.parse(data)
    except Exception as exc:
        raise TimelineEditError('Timeline edit violates CompositionPlan invariants') from exc
    return TimelineEditResult(CompletedCommand(project.with_plan(plan),expected_revision),tuple(created))



def move_timeline_marker(project:Project,marker_id:str,frame:int,*,expected_revision:int):
    """Move one persisted Timeline marker to an exact bounded output frame."""
    if type(project) is not Project or type(marker_id) is not str or type(frame) is not int:
        raise TimelineEditError('Typed project, marker ID and exact integer frame required')
    data=project.plan.to_dict()
    markers=data.get('timeline_markers',[])
    marker=next((item for item in markers if item['id']==marker_id),None)
    if marker is None:
        raise TimelineEditError('Selected Timeline marker does not exist')
    duration=_fraction(data['output']['duration'])
    fps=_fraction(data['output']['fps'])
    frame_count=duration*fps
    frame_total=(frame_count.numerator+frame_count.denominator-1)//frame_count.denominator
    if not 0<=frame<frame_total:
        raise TimelineEditError('Timeline marker frame is outside the output range')
    if marker['frame']==frame:
        raise TimelineEditError('Timeline marker is already at the requested frame')
    if any(item['id']!=marker_id and item['frame']==frame for item in markers):
        raise TimelineEditError('Another Timeline marker already occupies that frame')
    marker['frame']=frame
    return _command(project,data,expected_revision)


def move_video_clip(project:Project,clip_id:str,new_output_start:Fraction,*,expected_revision:int):
    """Move a video clip to an exact rational output time, keeping its linked original audio aligned."""
    if type(project) is not Project or type(new_output_start) is not Fraction:
        raise TimelineEditError('Typed project and exact rational output time required')
    if new_output_start<0:
        raise TimelineEditError('Clip output start cannot be negative')
    data=project.plan.to_dict()
    clip=next((item for item in data['clips'] if item['id']==clip_id),None)
    if clip is None:
        raise TimelineEditError('Selected video clip does not exist')
    old_start,old_end,source_in,source_out,speed=_span(clip)
    delta=new_output_start-old_start
    if delta==0:
        return _command(project,data,expected_revision)
    clip['output_start']=_pair(new_output_start)
    # Only move original-audio segments that have the exact same source interval,
    # playback speed and output origin as the selected video segment.
    for audio in data['audio']['clips']:
        if audio['asset_id']!=clip['asset_id']:
            continue
        audio_start,audio_end,audio_in,audio_out,audio_speed=_span(audio)
        if (audio_start==old_start and audio_in==source_in and
                audio_out==source_out and audio_speed==speed):
            audio['output_start']=_pair(new_output_start)
    return _command(project,data,expected_revision)

def delete_video_clip(project:Project,clip_id:str,*,ripple:bool,expected_revision:int):
    """Delete a timeline clip without touching its source; optionally close the resulting time gap."""
    if type(project) is not Project or type(ripple) is not bool:
        raise TimelineEditError('Typed project and explicit ripple boolean required')
    data=project.plan.to_dict()
    clip=next((item for item in data['clips'] if item['id']==clip_id),None)
    if clip is None:
        raise TimelineEditError('Selected video clip does not exist')
    start,end,source_in,source_out,speed=_span(clip)
    duration=end-start
    asset_id=clip['asset_id']
    original_audio=[]
    for audio in data['audio']['clips']:
        if (audio['asset_id']==asset_id and audio.get('role')=='original'
                and audio['output_start']==clip['output_start']
                and audio['source_in']==clip['source_in']
                and audio['speed']==clip['speed']):
            original_audio.append(audio['id'])
    data['clips']=[item for item in data['clips'] if item['id']!=clip_id]
    data['audio']['clips']=[item for item in data['audio']['clips']
                            if item['id'] not in set(original_audio)]
    if ripple:
        for item in data['clips']:
            item_start=_fraction(item['output_start'])
            if item_start>=end:
                item['output_start']=_pair(item_start-duration)
        for item in data['audio']['clips']:
            item_start=_fraction(item['output_start'])
            if item_start>=end:
                item['output_start']=_pair(item_start-duration)
    return _command(project,data,expected_revision)
def split_video_clip(project:Project,clip_id:str,output_time:Fraction,*,expected_revision:int):
    if type(project) is not Project or type(output_time) is not Fraction:
        raise TimelineEditError('Typed project and exact rational playhead required')
    data=project.plan.to_dict()
    clip=next((x for x in data['clips'] if x['id']==clip_id),None)
    if clip is None:raise TimelineEditError('Selected video clip does not exist')
    start,end,source_in,source_out,speed=_span(clip)
    if not start<output_time<end:raise TimelineEditError('Split must be strictly inside the selected clip')
    source_split=source_in+(output_time-start)*speed
    if not source_in<source_split<source_out:raise TimelineEditError('Split maps to a zero-length source segment')
    left=clip
    right=deepcopy(clip);right['id']=str(uuid4())
    left['source_out']=_pair(source_split)
    right['source_in']=_pair(source_split);right['output_start']=_pair(output_time)
    data['clips'].append(right)
    created=[right['id']]
    for audio in list(data['audio']['clips']):
        if audio['asset_id']!=clip['asset_id']:continue
        astart,aend,ain,aout,aspeed=_span(audio)
        if not astart<output_time<aend:continue
        split=ain+(output_time-astart)*aspeed
        if not ain<split<aout:raise TimelineEditError('Audio split maps to a zero-length segment')
        audio_right=deepcopy(audio);audio_right['id']=str(uuid4())
        audio['source_out']=_pair(split)
        audio_right['source_in']=_pair(split);audio_right['output_start']=_pair(output_time)
        data['audio']['clips'].append(audio_right);created.append(audio_right['id'])
    return _command(project,data,expected_revision,created)


def trim_video_clip(project:Project,clip_id:str,output_time:Fraction,*,edge:str,
                    ripple:bool,expected_revision:int):
    if type(project) is not Project or type(output_time) is not Fraction or type(ripple) is not bool:
        raise TimelineEditError('Typed project, exact playhead and explicit ripple flag required')
    if edge not in {'in','out'}:raise TimelineEditError('Trim edge must be in or out')
    data=project.plan.to_dict()
    clip=next((x for x in data['clips'] if x['id']==clip_id),None)
    if clip is None:raise TimelineEditError('Selected video clip does not exist')
    start,end,source_in,source_out,speed=_span(clip)
    if not start<output_time<end:raise TimelineEditError('Trim point must be strictly inside the selected clip')
    boundary=source_in+(output_time-start)*speed
    if edge=='in':
        removed=output_time-start
        old_end=end
        clip['source_in']=_pair(boundary)
        if not ripple:
            clip['output_start']=_pair(output_time)
        for audio in data['audio']['clips']:
            if audio['asset_id']!=clip['asset_id']:continue
            astart,aend,ain,aout,aspeed=_span(audio)
            if astart<output_time<aend:
                audio['source_in']=_pair(ain+(output_time-astart)*aspeed)
                if not ripple:audio['output_start']=_pair(output_time)
        if ripple:
            for other in data['clips']:
                if other['id']==clip_id:continue
                ostart=_fraction(other['output_start'])
                if ostart>=old_end:other['output_start']=_pair(ostart-removed)
            for audio in data['audio']['clips']:
                astart=_fraction(audio['output_start'])
                if astart>=old_end:audio['output_start']=_pair(astart-removed)
    else:
        removed=end-output_time
        old_end=end
        clip['source_out']=_pair(boundary)
        for audio in data['audio']['clips']:
            if audio['asset_id']!=clip['asset_id']:continue
            astart,aend,ain,aout,aspeed=_span(audio)
            if astart<output_time<aend:
                audio['source_out']=_pair(ain+(output_time-astart)*aspeed)
        if ripple:
            for other in data['clips']:
                if other['id']==clip_id:continue
                ostart=_fraction(other['output_start'])
                if ostart>=old_end:other['output_start']=_pair(ostart-removed)
            for audio in data['audio']['clips']:
                astart=_fraction(audio['output_start'])
                if astart>=old_end:audio['output_start']=_pair(astart-removed)
    return _command(project,data,expected_revision)
