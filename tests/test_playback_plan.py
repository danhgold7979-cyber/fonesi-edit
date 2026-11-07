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


def test_playback_frame_maps_overlapping_clips_and_audio_independently(tmp_path):
    plan, clip_id, asset_id = _base_plan(tmp_path)
    def mutate(data):
        clip = data["clips"][0]
        clip.update(output_start=[1, 2], source_in=[1, 10], source_out=[9, 10], speed=[2, 1])
        audio = data["audio"]["clips"][0]
        audio.update(output_start=[0, 1], source_in=[1, 5], source_out=[1, 1], speed=[1, 1])
        other = dict(clip)
        other["id"] = "00000000-0000-0000-0000-000000000010"
        other["output_start"] = [0, 1]
        other["speed"] = [1, 1]
        other["source_in"] = [0, 1]
        other["source_out"] = [9, 10]
        data["clips"].append(other)
    changed = _parse_changed(plan, mutate)
    result = plan_playback_frame(changed, 15)
    assert result.output_time == Fraction(1, 2)
    assert len(result.video) == 2
    assert len(result.audio) == 1
    by_id = {sample.clip_id: sample for sample in result.video}
    assert by_id[clip_id].source_time == Fraction(1, 10)
    assert by_id["00000000-0000-0000-0000-000000000010"].source_time == Fraction(1, 2)
    assert result.audio[0].source_time == Fraction(7, 10)


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
