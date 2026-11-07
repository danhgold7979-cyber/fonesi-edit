"""Exact multi-clip playback-frame source mapping (planner only)."""
from fractions import Fraction

import pytest

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.media.playback import PlaybackPlanError, plan_playback_frame
from fonesi_edit.storage.timeline_commands import add_video_clip
from test_preview_seek import _base_plan, _parse_changed


def test_playback_frame_maps_video_and_audio_with_exact_rational_clock(tmp_path):
    plan, clip_id, asset_id = _base_plan(tmp_path)
    result = plan_playback_frame(plan, 15)
    assert result.plan_id == plan.to_dict()["id"]
    assert result.plan_revision == plan.to_dict()["revision"]
    assert result.output_frame == 15
    assert result.output_time == Fraction(1, 2)
    assert len(result.video) == len(result.audio) == 1
    video, audio = result.video[0], result.audio[0]
    assert (video.clip_id, video.asset_id, video.stream_index) == (clip_id, asset_id, 3)
    assert video.source_time == Fraction(1, 2)
    assert video.decoder_time == Fraction(12, 25)
    assert audio.stream_index == 5
    assert audio.source_time == audio.decoder_time == Fraction(1, 2)


def test_playback_frame_maps_video_and_audio_independent_offsets_and_speeds(tmp_path):
    plan, clip_id, asset_id = _base_plan(tmp_path)
    def mutate(data):
        clip = data["clips"][0]
        clip.update(source_in=[1, 10], source_out=[9, 10],
                    output_start=[0, 1], speed=[2, 1])
        audio = data["audio"]["clips"][0]
        audio.update(source_in=[1, 5], source_out=[1, 1],
                     output_start=[0, 1], speed=[1, 1])
    changed = _parse_changed(plan, mutate)
    result = plan_playback_frame(changed, 10)
    assert result.output_time == Fraction(1, 3)
    assert len(result.video) == len(result.audio) == 1
    video, audio = result.video[0], result.audio[0]
    assert (video.clip_id, video.asset_id, video.stream_index) == (clip_id, asset_id, 3)
    assert video.source_time == Fraction(23, 30)
    assert video.decoder_time == Fraction(23, 30) - Fraction(1, 50)
    assert audio.source_time == Fraction(8, 15)
    assert audio.decoder_time == Fraction(8, 15)


def test_playback_frame_returns_silence_and_video_gap_and_rejects_bad_frame(tmp_path):
    plan, _clip_id, _asset_id = _base_plan(tmp_path)
    def mutate(data):
        data["audio"]["clips"] = []
        data["clips"][0]["output_start"] = [1, 1]
    changed = _parse_changed(plan, mutate)
    result = plan_playback_frame(changed, 15)
    assert result.video == () and result.audio == ()
    for frame in (-1, True, 300):
        with pytest.raises(PlaybackPlanError):
            plan_playback_frame(plan, frame)
