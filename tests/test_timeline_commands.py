"""Pure timeline admission requires exact, complete and source-bound frame facts."""
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import uuid

import pytest

from fonesi_edit.domain.media_library import MediaRecord,MediaPath
from fonesi_edit.media.probe import ProbeResult
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.media.frames import FrameScan,FrameObservation
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.timeline_commands import add_video_clip,TimelineImportError


def _record(path,content=b'video'):
    digest=sha256(content).hexdigest()
    raw={'streams':[
        {'index':3,'codec_type':'video','codec_name':'mpeg4','time_base':'1/1000',
         'start_pts':-20,'duration_ts':1000,'width':32,'height':24,
         'sample_aspect_ratio':'4:3','disposition':{'attached_pic':0},
         'side_data_list':[{'side_data_type':'Display Matrix',
             'displaymatrix':'00000000: 65536 0 0\n00000001: 0 65536 0\n00000002: 0 0 1073741824',
             'rotation':'0'}]},
        {'index':5,'codec_type':'audio','codec_name':'aac','time_base':'1/48000',
         'start_pts':0,'duration_ts':48000,'sample_rate':'48000',
         'channels':2,'channel_layout':'stereo'}],
        'format':{'duration':'1'}}
    observation=normalize_probe(ProbeResult(digest,__import__('json').dumps(raw),'/trusted/ffprobe',()))
    item=MediaRecord(str(uuid.uuid4()),digest,len(content),MediaPath('absolute',str(path),digest),
                     'OBSERVED',observation)
    return item


def _scan(record,frames=None,status='OBSERVED_EOF'):
    if frames is None:
        frames=(FrameObservation(-20,-20,40,40,()),
                FrameObservation(20,20,40,40,()),
                FrameObservation(980,980,20,20,()))
    return FrameScan(record.sha256,'b'*64,3,Fraction(1,1000),-20,status,tuple(frames),
                     ('NOT_MEDIA_VALIDITY_OR_RENDER_READINESS',),False)


def _project():
    return empty_project(NewProjectIntent('Timeline',1920,1080,Fraction(30),Fraction(10)))


def test_exact_frame_map_builds_video_asset_clip_and_original_audio_clip(tmp_path):
    record=_record(tmp_path/'video.mp4')
    addition=add_video_clip(_project(),record,_scan(record),expected_revision=7)
    project=addition.command.project
    data=project.plan.to_dict()
    assert addition.command.expected_revision==7
    assert len(data['assets'])==1 and data['assets'][0]['sha256']==record.sha256
    video=next(s for s in data['assets'][0]['probe']['streams'] if s['type']=='video')
    assert video['frame_pts']==[[0,1],[1,25],[1,1]]
    clip=data['clips'][0]
    assert clip['asset_id']==addition.asset_id and clip['video_stream_index']==3
    assert clip['output_start']==[0,1] and clip['source_out']==[1,1]
    audio=data['audio']['clips'][0]
    assert audio['asset_id']==addition.asset_id and audio['audio_stream_index']==5
    assert audio['role']=='original' and audio['output_start']==[0,1]
    assert project.plan.to_dict()['revision']==1


def test_second_clip_appends_after_existing_video_and_audio(tmp_path):
    first=_record(tmp_path/'one.mp4',b'one')
    second=_record(tmp_path/'two.mp4',b'two')
    one=add_video_clip(_project(),first,_scan(first),expected_revision=0)
    two=add_video_clip(one.command.project,second,_scan(second),expected_revision=1)
    data=two.command.project.plan.to_dict()
    assert [x['output_start'] for x in data['clips']]==[[0,1],[1,1]]
    assert [x['output_start'] for x in data['audio']['clips']]==[[0,1],[1,1]]
    assert data['output']['duration']==[10,1]
    assert two.command.expected_revision==1


@pytest.mark.parametrize('status',['INCOMPLETE','REFUSED','UNKNOWN'])
def test_incomplete_or_unknown_frame_scan_never_creates_asset(tmp_path,status):
    record=_record(tmp_path/'bad.mp4')
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),record,_scan(record,status=status),expected_revision=0)


@pytest.mark.parametrize('frames',[
    (FrameObservation(None,-20,40,40,()),),
    (FrameObservation(-20,-20,40,40,()),FrameObservation(-20,-20,40,40,())),
    (FrameObservation(-30,-30,40,40,()),),
    (),
])
def test_missing_duplicate_out_of_range_or_empty_pts_refused(tmp_path,frames):
    record=_record(tmp_path/'bad-pts.mp4')
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),record,_scan(record,frames),expected_revision=0)


def test_source_hash_and_stream_identity_must_match(tmp_path):
    record=_record(tmp_path/'identity.mp4')
    wrong=replace(_scan(record),source_sha256='c'*64)
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),record,wrong,expected_revision=0)
    wrong_stream=replace(_scan(record),stream_index=4)
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),record,wrong_stream,expected_revision=0)


def test_non_absolute_source_and_unknown_track_are_refused(tmp_path):
    record=_record(tmp_path/'relative.mp4')
    relative=replace(record,path_ref=MediaPath('project','relative.mp4',record.sha256))
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),relative,_scan(record),expected_revision=0)
    raw=record.observation.to_dict()
    from fonesi_edit.domain.media_library import observation_from_dict
    extra=replace(record,observation=observation_from_dict({
        **raw,'streams':raw['streams']+[{
            **raw['streams'][0],'index':9,'kind':'data','diagnostics':['NON_TIMELINE_OR_UNKNOWN_TRACK']
        }]
    }))
    with pytest.raises(TimelineImportError):
        add_video_clip(_project(),extra,_scan(record),expected_revision=0)
