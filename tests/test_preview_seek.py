"""Exact rational still-preview seek planning for selected video and original audio."""
from fractions import Fraction
from pathlib import Path
import sys

import pytest

from fonesi_edit.domain.composition import CompositionPlan,canonical
from fonesi_edit.media.preview import PreviewFrame
from fonesi_edit.media.seek import (PreviewSeekError,PreviewSeekPlan,StreamSeek,
                                    plan_preview_seek)
from fonesi_edit.storage.timeline_commands import add_video_clip
from test_queue_view import wait_for
from test_timeline_commands import _project,_record,_scan
from test_timeline_preview_ui import _close,_open,_png


def _base_plan(tmp_path):
    record=_record(tmp_path/'seek.mp4',b'exact-seek')
    addition=add_video_clip(_project(),record,_scan(record),expected_revision=0)
    return addition.command.project.plan,addition.clip_id,addition.asset_id


def _parse_changed(plan,mutate):
    data=plan.to_dict();mutate(data);data['revision']+=1
    return CompositionPlan.parse(data)


def test_seek_maps_base_video_and_original_audio_without_mutating_plan(tmp_path):
    plan,clip_id,asset_id=_base_plan(tmp_path)
    before=canonical(plan.to_dict())
    result=plan_preview_seek(plan,clip_id,15)
    assert result.plan_id==plan.to_dict()['id'] and result.plan_revision==1
    assert result.output_frame==15 and result.output_time==Fraction(1,2)
    assert result.video==StreamSeek('video',clip_id,asset_id,3,Fraction(1,2),
                                    Fraction(1,2),Fraction(12,25),Fraction(1))
    assert len(result.audio)==1
    audio=result.audio[0]
    assert audio.kind=='audio' and audio.asset_id==asset_id and audio.stream_index==5
    assert audio.output_time==audio.source_time==audio.decoder_time==Fraction(1,2)
    assert canonical(plan.to_dict())==before


def test_seek_applies_independent_trim_speed_output_offset_and_stream_start(tmp_path):
    plan,clip_id,_asset_id=_base_plan(tmp_path)
    def mutate(data):
        data['clips'][0].update(source_in=[1,10],source_out=[9,10],
                                output_start=[2,1],speed=[2,1])
        data['audio']['clips'][0].update(source_in=[1,5],source_out=[1,1],
                                         output_start=[2,1],speed=[2,1])
    changed=_parse_changed(plan,mutate)
    result=plan_preview_seek(changed,clip_id,66)
    assert result.output_time==Fraction(11,5)
    assert result.video.source_time==Fraction(1,2)
    assert result.video.decoder_time==Fraction(12,25)
    assert result.video.speed==2
    assert result.audio[0].source_time==result.audio[0].decoder_time==Fraction(3,5)
    assert result.audio[0].speed==2


def test_seek_returns_all_active_original_audio_in_deterministic_order(tmp_path):
    plan,clip_id,_asset_id=_base_plan(tmp_path)
    def mutate(data):
        first=data['audio']['clips'][0]
        first['id']='00000000-0000-0000-0000-000000000002'
        duplicate=dict(first);duplicate['id']='00000000-0000-0000-0000-000000000001'
        data['audio']['clips'].append(duplicate)
    changed=_parse_changed(plan,mutate)
    result=plan_preview_seek(changed,clip_id,1)
    assert [item.clip_id for item in result.audio]==[
        '00000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000002']
    assert all(item.stream_index==5 for item in result.audio)


def test_seek_supports_no_audio_and_enforces_half_open_clip_end(tmp_path):
    plan,clip_id,_asset_id=_base_plan(tmp_path)
    no_audio=_parse_changed(plan,lambda data:data['audio'].__setitem__('clips',[]))
    assert plan_preview_seek(no_audio,clip_id,29).audio==()
    with pytest.raises(PreviewSeekError,match='Playhead'):
        plan_preview_seek(no_audio,clip_id,30)


def test_seek_refuses_invalid_frame_missing_clip_and_freeze(tmp_path):
    plan,clip_id,_asset_id=_base_plan(tmp_path)
    for frame in (-1,300,True):
        with pytest.raises(PreviewSeekError):plan_preview_seek(plan,clip_id,frame)
    with pytest.raises(PreviewSeekError,match='Không tìm thấy'):
        plan_preview_seek(plan,'missing-clip',0)
    frozen=_parse_changed(plan,lambda data:data['clips'][0].__setitem__('freeze_duration',[1,10]))
    with pytest.raises(PreviewSeekError,match='freeze'):
        plan_preview_seek(frozen,clip_id,0)


def test_one_frame_preview_consumes_shared_seek_contract(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    store,window,timeline,source,_payload=_open(tmp_path)
    try:
        planned=[];decoded=[]
        def fake_plan(plan,clip_id,frame):
            data=plan.to_dict();asset_id=data['clips'][0]['asset_id']
            planned.append((data['id'],clip_id,frame))
            video=StreamSeek('video',clip_id,asset_id,3,Fraction(1,2),
                             Fraction(9,10),Fraction(7,8),Fraction(1))
            return PreviewSeekPlan(data['id'],data['revision'],frame,Fraction(1,2),video,())
        def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,**kwargs):
            decoded.append((path,stream_index,decoder_time))
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,
                                decoder_time,16,9,False)
        monkeypatch.setattr(module,'plan_preview_seek',fake_plan)
        monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.request_preview()
        wait_for(qt_app,lambda:not timeline.busy and 'timestamp decoder' in timeline.preview_message.text())
        assert len(planned)==1 and planned[0][2]==15
        assert decoded==[(source,3,Fraction(7,8))]
    finally:
        _close(store,window,qt_app)
