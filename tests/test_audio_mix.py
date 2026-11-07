"""Tests for deterministic bounded float PCM mixing."""
import pytest

from fonesi_edit.media.audio_decode import PCMBuffer
from fonesi_edit.media.audio_mix import AudioMixError, AudioMixInput, mix_pcm_buffers


def _pcm(samples, *, rate=48000, channels=2):
    return PCMBuffer("a"*64, 0, rate, channels, len(samples)//channels,
                     tuple(samples), len(samples)//channels)


def test_mixer_aligns_tracks_applies_gain_and_sums_overlaps():
    a = _pcm((0.2, -0.2, 0.4, -0.4))
    b = _pcm((0.3, 0.3, 0.1, 0.1))
    result = mix_pcm_buffers([
        AudioMixInput(a, 0, 1.0),
        AudioMixInput(b, 1, 0.5),
    ], output_samples=3, sample_rate=48000, channels=2)
    assert result.samples == pytest.approx((0.2, -0.2, 0.55, -0.25, 0.05, 0.05))
    assert result.sample_count == 3 and result.duration_seconds == pytest.approx(3/48000)


def test_mixer_limits_peak_and_preserves_silence():
    a = _pcm((0.9, -0.9, 0.0, 0.0))
    b = _pcm((0.9, -0.9, 0.0, 0.0))
    result = mix_pcm_buffers([AudioMixInput(a, 0), AudioMixInput(b, 0)],
                             output_samples=3, sample_rate=48000, channels=2,
                             peak_limit=0.95)
    assert result.samples == pytest.approx((0.95, -0.95, 0, 0, 0, 0))


def test_mixer_rejects_implicit_conversion_bad_gain_and_bounds():
    a = _pcm((0.1, 0.1))
    with pytest.raises(AudioMixError, match="resampling"):
        mix_pcm_buffers([AudioMixInput(_pcm((0.1,), rate=44100, channels=1), 0)],
                        output_samples=1, sample_rate=48000, channels=2)
    with pytest.raises(AudioMixError, match="gain"):
        mix_pcm_buffers([AudioMixInput(a, 0, float("nan"))],
                        output_samples=1, sample_rate=48000, channels=2)
    with pytest.raises(AudioMixError):
        mix_pcm_buffers([AudioMixInput(a, 0)], output_samples=0,
                        sample_rate=48000, channels=2)
