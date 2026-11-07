"""Exact frame-boundary split/trim preserves audio sync and gap/ripple intent."""
import pytest
from fractions import Fraction
from pathlib import Path

from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.storage.timeline_edit_commands import split_video_clip,trim_video_clip,move_video_clip,delete_video_clip,TimelineEditError
from test_timeline_commands import _record,_scan,_project


def _two_clips(tmp_path):
    first_path=tmp_path/'first.mp4';first_path.write_bytes(b'first')
    second_path=tmp_path/'second.mp4';second_path.write_bytes(b'second')
    first=_record(first_path,b'first')
    second=_record(second_path,b'second')
    one=add_video_clip(_project(),first,_scan(first),expected_revision=0)
    two=add_video_clip(one.command.project,second,_scan(second),expected_revision=1)
    return two.command.project,one.clip_id,one.asset_id,two.clip_id


def test_split_at_exact_playhead_creates_two_video_and_audio_segments(tmp_path):
    project,clip_id,asset_id,_=_two_clips(tmp_path)
    result=split_video_clip(project,clip_id,Fraction(1,2),expected_revision=2)
    data=result.command.project.plan.to_dict()
    video=sorted([x for x in data['clips'] if x['asset_id']==asset_id],key=lambda x:x['output_start'])
    audio=sorted([x for x in data['audio']['clips'] if x['asset_id']==asset_id],key=lambda x:x['output_start'])
    assert len(video)==2 and len(audio)==2
    assert [x['output_start'] for x in video]==[[0,1],[1,2]]
    assert [x['source_in'] for x in video]==[[0,1],[1,2]]
    assert [x['source_out'] for x in video]==[[1,2],[1,1]]
    assert [x['output_start'] for x in audio]==[[0,1],[1,2]]
    assert [x['source_out'] for x in audio]==[[1,2],[1,1]]
    assert result.command.expected_revision==2


def test_trim_in_gap_and_ripple_have_distinct_timing(tmp_path):
    project,clip_id,asset_id,second_id=_two_clips(tmp_path)
    gap=trim_video_clip(project,clip_id,Fraction(1,2),edge='in',ripple=False,expected_revision=2)
    gap_data=gap.command.project.plan.to_dict()
    first=next(x for x in gap_data['clips'] if x['id']==clip_id)
    second=next(x for x in gap_data['clips'] if x['id']==second_id)
    audio=next(x for x in gap_data['audio']['clips'] if x['asset_id']==asset_id)
    assert first['output_start']==[1,2] and first['source_in']==[1,2]
    assert second['output_start']==[1,1]
    assert audio['output_start']==[1,2] and audio['source_in']==[1,2]

    ripple=trim_video_clip(project,clip_id,Fraction(1,2),edge='in',ripple=True,expected_revision=2)
    ripple_data=ripple.command.project.plan.to_dict()
    first=next(x for x in ripple_data['clips'] if x['id']==clip_id)
    second=next(x for x in ripple_data['clips'] if x['id']==second_id)
    audio=next(x for x in ripple_data['audio']['clips'] if x['asset_id']==asset_id)
    assert first['output_start']==[0,1] and first['source_in']==[1,2]
    assert second['output_start']==[1,2]
    assert audio['output_start']==[0,1] and audio['source_in']==[1,2]


def test_trim_out_gap_and_ripple_have_distinct_timing(tmp_path):
    project,clip_id,asset_id,second_id=_two_clips(tmp_path)
    gap=trim_video_clip(project,clip_id,Fraction(1,2),edge='out',ripple=False,expected_revision=2)
    gap_data=gap.command.project.plan.to_dict()
    first=next(x for x in gap_data['clips'] if x['id']==clip_id)
    second=next(x for x in gap_data['clips'] if x['id']==second_id)
    audio=next(x for x in gap_data['audio']['clips'] if x['asset_id']==asset_id)
    assert first['source_out']==[1,2] and first['output_start']==[0,1]
    assert second['output_start']==[1,1]
    assert audio['source_out']==[1,2]

    ripple=trim_video_clip(project,clip_id,Fraction(1,2),edge='out',ripple=True,expected_revision=2)
    ripple_data=ripple.command.project.plan.to_dict()
    second=next(x for x in ripple_data['clips'] if x['id']==second_id)
    assert second['output_start']==[1,2]


@pytest.mark.parametrize('time',[Fraction(0),Fraction(1)])
def test_split_at_clip_boundary_is_rejected(tmp_path,time):
    project,clip_id,_,_=_two_clips(tmp_path)
    with pytest.raises(TimelineEditError):
        split_video_clip(project,clip_id,time,expected_revision=2)


def test_move_video_clip_uses_exact_rational_time_and_keeps_original_audio_aligned(tmp_path):
    project,clip_id,asset_id,_=_two_clips(tmp_path)
    moved=move_video_clip(project,clip_id,Fraction(2),expected_revision=2)
    data=moved.command.project.plan.to_dict()
    video=next(item for item in data['clips'] if item['id']==clip_id)
    audio=next(item for item in data['audio']['clips'] if item['asset_id']==asset_id)
    assert video['output_start']==[2,1]
    assert audio['output_start']==[2,1]
    assert moved.command.expected_revision==2
    assert project.plan.to_dict()['clips'][0]['output_start']==[0,1]


@pytest.mark.parametrize('new_start',[Fraction(-1,2),Fraction(1,2),Fraction(10)])
def test_move_video_clip_rejects_negative_overlap_and_output_overrun(tmp_path,new_start):
    project,clip_id,_,_=_two_clips(tmp_path)
    with pytest.raises(TimelineEditError):
        move_video_clip(project,clip_id,new_start,expected_revision=2)
    assert project.plan.to_dict()['clips'][0]['output_start']==[0,1]


@pytest.mark.parametrize('new_start',[0,1.5,'3/2',None])
def test_move_video_clip_requires_exact_fraction_and_existing_clip(tmp_path,new_start):
    project,clip_id,_,_=_two_clips(tmp_path)
    with pytest.raises(TimelineEditError):
        move_video_clip(project,clip_id,new_start,expected_revision=2)
    with pytest.raises(TimelineEditError):
        move_video_clip(project,'missing-clip',Fraction(2),expected_revision=2)


def test_gap_delete_removes_selected_clip_and_matching_original_audio_but_keeps_later_timing(tmp_path):
    project,clip_id,asset_id,second_id=_two_clips(tmp_path)
    source_path=Path(next(item for item in project.plan.to_dict()['assets']
                          if item['id']==asset_id)['path_ref']['path'])
    source_bytes=source_path.read_bytes()
    result=delete_video_clip(project,clip_id,ripple=False,expected_revision=2)
    data=result.command.project.plan.to_dict()
    assert [item['id'] for item in data['clips']]==[second_id]
    assert data['clips'][0]['output_start']==[1,1]
    assert len(data['audio']['clips'])==1
    assert data['audio']['clips'][0]['output_start']==[1,1]
    assert source_path.exists() and source_path.read_bytes()==source_bytes
    assert result.command.expected_revision==2


def test_ripple_delete_removes_selected_clip_and_closes_video_audio_gap(tmp_path):
    project,clip_id,asset_id,second_id=_two_clips(tmp_path)
    source_path=Path(next(item for item in project.plan.to_dict()['assets']
                          if item['id']==asset_id)['path_ref']['path'])
    source_bytes=source_path.read_bytes()
    result=delete_video_clip(project,clip_id,ripple=True,expected_revision=2)
    data=result.command.project.plan.to_dict()
    assert [item['id'] for item in data['clips']]==[second_id]
    assert data['clips'][0]['output_start']==[0,1]
    assert len(data['audio']['clips'])==1
    assert data['audio']['clips'][0]['output_start']==[0,1]
    assert source_path.exists() and source_path.read_bytes()==source_bytes


@pytest.mark.parametrize('ripple',[0,1,'true',None])
def test_delete_video_clip_requires_explicit_boolean_and_never_mutates_source(tmp_path,ripple):
    project,clip_id,asset_id,_=_two_clips(tmp_path)
    source_path=Path(next(item for item in project.plan.to_dict()['assets']
                          if item['id']==asset_id)['path_ref']['path'])
    before=source_path.read_bytes()
    with pytest.raises(TimelineEditError):
        delete_video_clip(project,clip_id,ripple=ripple,expected_revision=2)
    with pytest.raises(TimelineEditError):
        delete_video_clip(project,'missing',ripple=False,expected_revision=2)
    assert source_path.exists() and source_path.read_bytes()==before
