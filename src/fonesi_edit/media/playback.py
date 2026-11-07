"""Exact rational source-time mapping for a future continuous playback clock.

This is a pure planner, not a decoder, audio device, video renderer or player.
It describes every active video/audio clip at one output frame so a playback
backend can seek/queue the correct source samples without floating-point drift.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.domain.timebase import frame_count, rational


class PlaybackPlanError(ValueError):
    pass


@dataclass(frozen=True)
class PlaybackSample:
    kind: str
    clip_id: str
    asset_id: str
    stream_index: int
    output_time: Fraction
    source_time: Fraction
    decoder_time: Fraction
    speed: Fraction
    gain: Fraction = Fraction(1)


@dataclass(frozen=True)
class PlaybackFramePlan:
    plan_id: str
    plan_revision: int
    output_frame: int
    output_time: Fraction
    video: tuple[PlaybackSample, ...]
    audio: tuple[PlaybackSample, ...]


def _active(clip: dict, output_time: Fraction) -> bool:
    start = rational(clip["output_start"])
    source_in = rational(clip["source_in"])
    source_out = rational(clip["source_out"])
    speed = rational(clip["speed"])
    freeze = rational(clip.get("freeze_duration", [0, 1]))
    end = start + (source_out - source_in) / speed + freeze
    return start <= output_time < end


def _sample(kind: str, clip: dict, asset: dict, stream: dict,
            output_time: Fraction, *, freeze: bool = False) -> PlaybackSample:
    source_in = rational(clip["source_in"])
    output_start = rational(clip["output_start"])
    speed = rational(clip["speed"])
    source_time = source_in if freeze else source_in + (output_time - output_start) * speed
    gain = rational(clip.get("gain", [1, 1])) if kind == "audio" else Fraction(1)
    return PlaybackSample(
        kind=kind, clip_id=clip["id"], asset_id=asset["id"],
        stream_index=stream["index"], output_time=output_time,
        source_time=source_time,
        decoder_time=rational(stream["start_time"]) + source_time,
        speed=speed, gain=gain,
    )


def plan_playback_frame(plan: CompositionPlan, output_frame: int) -> PlaybackFramePlan:
    """Map one output frame to all active video and audio source positions."""
    if not isinstance(plan, CompositionPlan):
        raise PlaybackPlanError("A validated CompositionPlan is required.")
    if type(output_frame) is not int or output_frame < 0:
        raise PlaybackPlanError("Output frame must be a non-negative integer.")
    data = plan.to_dict()
    fps = rational(data["output"]["fps"])
    duration = rational(data["output"]["duration"])
    if output_frame >= frame_count(duration, fps):
        raise PlaybackPlanError("Output frame is outside the project.")
    output_time = Fraction(output_frame, 1) / fps
    assets = {asset["id"]: asset for asset in data["assets"]}
    video_samples: list[PlaybackSample] = []
    audio_samples: list[PlaybackSample] = []

    for clip in data["clips"]:
        if not _active(clip, output_time):
            continue
        asset = assets.get(clip["asset_id"])
        if asset is None or asset["kind"] == "image":
            continue
        stream_index = clip.get("video_stream_index")
        if stream_index is None:
            continue
        stream = next((item for item in asset["probe"]["streams"]
                       if item["index"] == stream_index and item["type"] == "video"), None)
        if stream is None:
            raise PlaybackPlanError("Selected video stream is missing from asset metadata.")
        freeze = rational(clip.get("freeze_duration", [0, 1])) > 0 and (
            output_time >= rational(clip["output_start"]) +
            (rational(clip["source_out"]) - rational(clip["source_in"])) /
            rational(clip["speed"]))
        video_samples.append(_sample("video", clip, asset, stream, output_time, freeze=freeze))

    for clip in data["audio"]["clips"]:
        if not _active(clip, output_time):
            continue
        asset = assets.get(clip["asset_id"])
        if asset is None:
            raise PlaybackPlanError("Audio clip asset is missing.")
        stream_index = clip.get("audio_stream_index")
        if stream_index is None:
            raise PlaybackPlanError("Active audio clip has no selected stream.")
        stream = next((item for item in asset["probe"]["streams"]
                       if item["index"] == stream_index and item["type"] == "audio"), None)
        if stream is None:
            raise PlaybackPlanError("Selected audio stream is missing from asset metadata.")
        audio_samples.append(_sample("audio", clip, asset, stream, output_time))

    video_samples.sort(key=lambda x: (x.clip_id, x.stream_index))
    audio_samples.sort(key=lambda x: (x.clip_id, x.stream_index))
    return PlaybackFramePlan(
        plan_id=data["id"], plan_revision=data["revision"], output_frame=output_frame,
        output_time=output_time, video=tuple(video_samples), audio=tuple(audio_samples),
    )
