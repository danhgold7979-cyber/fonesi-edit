"""Apply Slice AS: exact rational preview seek planning and integration."""
from pathlib import Path


def replace_exact(text: str, old: str, new: str, *, expected: int = 1, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} source match(es), found {count}")
    return text.replace(old, new, expected)


seek_path = Path("src/fonesi_edit/media/seek.py")
if seek_path.exists():
    raise RuntimeError("seek.py already exists; refusing to overwrite an unreviewed implementation")
seek_path.write_text(r'''"""Pure exact mapping from output frames to source decoder timestamps.

This module plans still-preview seeks only. It does not open media, choose a
fallback stream, play audio/video, generate proxies or prove render parity.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.domain.timebase import frame_count, rational


class PreviewSeekError(ValueError):
    """The validated composition cannot supply the requested preview seek."""


@dataclass(frozen=True)
class StreamSeek:
    kind: str
    clip_id: str
    asset_id: str
    stream_index: int
    output_time: Fraction
    source_time: Fraction
    decoder_time: Fraction
    speed: Fraction


@dataclass(frozen=True)
class PreviewSeekPlan:
    plan_id: str
    plan_revision: int
    output_frame: int
    output_time: Fraction
    video: StreamSeek
    audio: tuple[StreamSeek, ...]


def _stream(asset: dict, index: object, kind: str) -> dict:
    if type(index) is not int:
        raise PreviewSeekError(f"Clip không chọn {kind} stream hợp lệ.")
    stream = next((item for item in asset["probe"]["streams"]
                   if item["index"] == index and item["type"] == kind), None)
    if stream is None:
        raise PreviewSeekError(f"Không tìm thấy {kind} stream đã chọn trong asset.")
    return stream


def _interval(clip: dict) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
    source_in = rational(clip["source_in"])
    source_out = rational(clip["source_out"])
    output_start = rational(clip["output_start"])
    speed = rational(clip["speed"])
    output_end = output_start + (source_out - source_in) / speed
    return source_in, source_out, output_start, output_end, speed


def _seek(kind: str, clip: dict, asset: dict, stream: dict,
          output_time: Fraction) -> StreamSeek:
    source_in, _source_out, output_start, output_end, speed = _interval(clip)
    if not output_start <= output_time < output_end:
        raise PreviewSeekError(f"Playhead nằm ngoài khoảng {kind} đang hoạt động.")
    source_time = source_in + (output_time - output_start) * speed
    return StreamSeek(
        kind=kind,
        clip_id=clip["id"],
        asset_id=asset["id"],
        stream_index=stream["index"],
        output_time=output_time,
        source_time=source_time,
        decoder_time=rational(stream["start_time"]) + source_time,
        speed=speed,
    )


def plan_preview_seek(plan: CompositionPlan, clip_id: str,
                      output_frame: int) -> PreviewSeekPlan:
    """Return exact video/audio decoder positions for one selected output frame.

    The selected video interval and every included audio interval are half-open.
    Audio is limited to active ``role == original`` clips from the same asset and
    returned in deterministic ``(stream_index, clip_id)`` order.
    """
    if not isinstance(plan, CompositionPlan):
        raise PreviewSeekError("Cần CompositionPlan đã xác thực để lập seek.")
    if type(clip_id) is not str or not clip_id:
        raise PreviewSeekError("Clip ID phải là chuỗi không rỗng.")
    if type(output_frame) is not int or output_frame < 0:
        raise PreviewSeekError("Output frame phải là số nguyên không âm.")

    data = plan.to_dict()
    fps = rational(data["output"]["fps"])
    duration = rational(data["output"]["duration"])
    if output_frame >= frame_count(duration, fps):
        raise PreviewSeekError("Output frame nằm ngoài project.")
    output_time = Fraction(output_frame, 1) / fps

    clip = next((item for item in data["clips"] if item["id"] == clip_id), None)
    if clip is None:
        raise PreviewSeekError("Không tìm thấy video clip đã chọn.")
    asset = next((item for item in data["assets"]
                  if item["id"] == clip["asset_id"]), None)
    if asset is None:
        raise PreviewSeekError("Không tìm thấy asset của video clip.")
    if asset["kind"] == "image" or clip["video_stream_index"] is None:
        raise PreviewSeekError("Still preview seek cần motion video clip.")
    if rational(clip["freeze_duration"]) != 0:
        raise PreviewSeekError("Preview seek hiện chưa hỗ trợ clip freeze.")

    video_stream = _stream(asset, clip["video_stream_index"], "video")
    try:
        video = _seek("video", clip, asset, video_stream, output_time)
    except PreviewSeekError as exc:
        raise PreviewSeekError("Playhead phải nằm trong phần video đang chọn.") from exc

    audio_seeks: list[StreamSeek] = []
    for audio_clip in data["audio"]["clips"]:
        if audio_clip["asset_id"] != asset["id"] or audio_clip.get("role") != "original":
            continue
        _source_in, _source_out, output_start, output_end, _speed = _interval(audio_clip)
        if not output_start <= output_time < output_end:
            continue
        audio_stream = _stream(asset, audio_clip["audio_stream_index"], "audio")
        audio_seeks.append(_seek("audio", audio_clip, asset, audio_stream, output_time))
    audio_seeks.sort(key=lambda item: (item.stream_index, item.clip_id))

    return PreviewSeekPlan(
        plan_id=data["id"],
        plan_revision=data["revision"],
        output_frame=output_frame,
        output_time=output_time,
        video=video,
        audio=tuple(audio_seeks),
    )
''', encoding="utf-8")


timeline_path = Path("src/fonesi_edit/ui/timeline.py")
timeline = timeline_path.read_text(encoding="utf-8")
timeline = replace_exact(
    timeline,
    "from fonesi_edit.media.preview import (PreviewFrame,AudioWaveform,PreviewError,PreviewCanceled,PreviewRetirementUnknown,\n"
    "    extract_preview_frame,extract_audio_waveform,resolve_asset_path)\n",
    "from fonesi_edit.media.preview import (PreviewFrame,AudioWaveform,PreviewError,PreviewCanceled,PreviewRetirementUnknown,\n"
    "    extract_preview_frame,extract_audio_waveform,resolve_asset_path)\n"
    "from fonesi_edit.media.seek import plan_preview_seek,PreviewSeekError\n",
    label="import preview seek contract",
)
old_single = '''            else:
                playhead=Fraction(self._playhead,1)/self._fps
                if not start<=playhead<start+(source_out-source_in)/speed:
                    raise PreviewError('Playhead phải nằm trong phần video đang chọn.')
                source_time=source_in+(playhead-start)*speed
                decoder_times=(stream_start+source_time,)
'''
new_single = '''            else:
                seek=plan_preview_seek(session.project.plan,clip['id'],self._playhead)
                stream_index=seek.video.stream_index
                decoder_times=(seek.video.decoder_time,)
'''
timeline = replace_exact(timeline, old_single, new_single,
                         label="route one-frame preview through exact seek plan")
timeline = replace_exact(
    timeline,
    "        except (StopIteration,KeyError,ValueError,OSError,RuntimeError,PreviewError) as exc:\n"
    "            self.preview_message.setText(str(exc) if isinstance(exc,PreviewError)\n"
    "                else 'Không xác định được asset/stream của clip; không chạy decoder.')\n",
    "        except (StopIteration,KeyError,ValueError,OSError,RuntimeError,PreviewError,PreviewSeekError) as exc:\n"
    "            self.preview_message.setText(str(exc) if isinstance(exc,(PreviewError,PreviewSeekError))\n"
    "                else 'Không xác định được asset/stream của clip; không chạy decoder.')\n",
    expected=1,
    label="surface exact seek refusal in preview UI",
)
timeline_path.write_text(timeline, encoding="utf-8")


test_path = Path("tests/test_preview_seek.py")
if test_path.exists():
    raise RuntimeError("test_preview_seek.py already exists")
test_path.write_text(r'''"""Exact rational still-preview seek planning for selected video and original audio."""
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
''', encoding="utf-8")
