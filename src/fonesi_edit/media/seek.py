"""Pure exact mapping from output frames to source decoder timestamps.

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
