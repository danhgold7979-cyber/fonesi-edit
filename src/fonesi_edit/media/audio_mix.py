"""Deterministic float PCM mixer for bounded audio clip segments."""
from __future__ import annotations

from dataclasses import dataclass
import math

from fonesi_edit.media.audio_decode import PCMBuffer


class AudioMixError(ValueError):
    pass


@dataclass(frozen=True)
class AudioMixInput:
    pcm: PCMBuffer
    start_sample: int
    gain: float = 1.0
    pan: float = 0.0
    fade_in_samples: int = 0
    fade_out_samples: int = 0


def mix_pcm_buffers(
    inputs: tuple[AudioMixInput, ...] | list[AudioMixInput], *,
    output_samples: int, sample_rate: int, channels: int,
    peak_limit: float = 0.98,
) -> PCMBuffer:
    """Mix aligned PCM clips into one bounded float buffer with hard peak limiting.

    Inputs must already share the output sample rate/channel layout; this function
    intentionally refuses implicit resampling or channel remapping.
    """
    if type(output_samples) is not int or not 1 <= output_samples <= 48000 * 30:
        raise AudioMixError("Output mix duration must be 1..30 seconds.")
    if type(sample_rate) is not int or not 8000 <= sample_rate <= 96000:
        raise AudioMixError("Output sample rate must be 8..96 kHz.")
    if type(channels) is not int or channels not in (1, 2):
        raise AudioMixError("Output channel count must be mono or stereo.")
    if type(peak_limit) not in (float, int) or not math.isfinite(peak_limit) or not 0 < peak_limit <= 1:
        raise AudioMixError("Peak limit must be finite and in (0, 1].")
    if not isinstance(inputs, (tuple, list)) or len(inputs) > 32:
        raise AudioMixError("At most 32 validated audio inputs are supported.")
    accumulator = [0.0] * (output_samples * channels)
    hashes = []
    for item in inputs:
        if not isinstance(item, AudioMixInput) or not isinstance(item.pcm, PCMBuffer):
            raise AudioMixError("Every input must contain a validated PCMBuffer.")
        pcm = item.pcm
        if type(item.start_sample) is not int or item.start_sample < 0:
            raise AudioMixError("Audio clip start sample must be a non-negative integer.")
        if not math.isfinite(item.gain) or not 0 <= item.gain <= 16:
            raise AudioMixError("Clip gain must be finite and between 0 and 16.")
        if not math.isfinite(item.pan) or not -1 <= item.pan <= 1:
            raise AudioMixError("Clip pan must be finite and between -1 and 1.")
        if type(item.fade_in_samples) is not int or item.fade_in_samples < 0:
            raise AudioMixError("Fade-in sample count must be non-negative.")
        if type(item.fade_out_samples) is not int or item.fade_out_samples < 0:
            raise AudioMixError("Fade-out sample count must be non-negative.")
        if pcm.sample_rate != sample_rate or pcm.channels != channels:
            raise AudioMixError("Implicit resampling/channel conversion is not supported.")
        if pcm.sample_count * channels != len(pcm.samples):
            raise AudioMixError("PCM sample count is inconsistent.")
        hashes.append(pcm.source_sha256)
        count = min(pcm.sample_count, max(0, output_samples - item.start_sample))
        if item.fade_in_samples > count or item.fade_out_samples > count:
            raise AudioMixError("Fade duration exceeds the decoded clip segment.")
        # Equal-power stereo pan: center preserves unity on both channels.
        left_pan = math.sqrt(1.0 - item.pan)
        right_pan = math.sqrt(1.0 + item.pan)
        for frame in range(count):
            envelope = 1.0
            if item.fade_in_samples:
                envelope = min(envelope, (frame + 1) / item.fade_in_samples)
            if item.fade_out_samples:
                remaining = count - frame
                envelope = min(envelope, remaining / item.fade_out_samples)
            destination = (item.start_sample + frame) * channels
            origin = frame * channels
            for channel in range(channels):
                sample = pcm.samples[origin + channel]
                if not math.isfinite(sample):
                    raise AudioMixError("Non-finite input PCM sample.")
                pan_gain = left_pan if channels == 2 and channel == 0 else (
                    right_pan if channels == 2 and channel == 1 else 1.0
                )
                accumulator[destination + channel] += sample * item.gain * envelope * pan_gain
    mixed = tuple(max(-peak_limit, min(peak_limit, sample)) for sample in accumulator)
    # The digest describes the ordered source fingerprints, not the PCM bytes.
    import hashlib
    digest = hashlib.sha256("|".join(hashes).encode("ascii")).hexdigest()
    return PCMBuffer(digest, -1, sample_rate, channels, output_samples,
                     mixed, output_samples)
