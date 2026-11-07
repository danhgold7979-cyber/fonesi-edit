"""Asynchronous bounded audio chunk producer for a future playback engine.

It decodes active tracks to PCM and mixes one output chunk. It is not a
continuous audio device clock, resampler or complete Timeline playback system.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from fonesi_edit.media.audio_decode import (
    AudioDecodeCanceled, AudioDecodeError, AudioDecodeRetirementUnknown,
    decode_audio_pcm,
)
from fonesi_edit.media.audio_mix import AudioMixInput, mix_pcm_buffers


@dataclass(frozen=True)
class AudioTrackSpec:
    source: Path
    expected_sha256: str
    stream_index: int
    output_start_sample: int
    source_start_seconds: float
    gain: float = 1.0


class AudioChunkWorker(QThread):
    chunk_ready = Signal(object)
    chunk_failed = Signal(str)
    chunk_canceled = Signal()
    retirement_unknown = Signal(str)

    def __init__(
        self, tracks: tuple[AudioTrackSpec, ...] | list[AudioTrackSpec],
        ffmpeg: Path | str, *, chunk_start_sample: int, chunk_samples: int,
        sample_rate: int = 48000, channels: int = 2,
        timeout: float = 30.0, parent=None,
    ):
        super().__init__(parent)
        if not isinstance(tracks, (tuple, list)) or len(tracks) > 32:
            raise ValueError("Audio chunk supports at most 32 tracks.")
        if type(chunk_start_sample) is not int or chunk_start_sample < 0:
            raise ValueError("Chunk start must be a non-negative sample index.")
        if type(chunk_samples) is not int or not 1 <= chunk_samples <= sample_rate * 5:
            raise ValueError("Audio chunk must be 1..5 seconds.")
        self.tracks = tuple(tracks)
        self.ffmpeg = Path(ffmpeg)
        self.chunk_start_sample = chunk_start_sample
        self.chunk_samples = chunk_samples
        self.sample_rate = sample_rate
        self.channels = channels
        self.timeout = timeout
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True
        self.requestInterruption()

    def _cancelled(self):
        return self._cancel_requested or self.isInterruptionRequested()

    def run(self):
        try:
            mix_inputs = []
            chunk_end = self.chunk_start_sample + self.chunk_samples
            for track in self.tracks:
                if not isinstance(track, AudioTrackSpec):
                    raise AudioDecodeError("Unvalidated audio track specification.")
                if self._cancelled():
                    raise AudioDecodeCanceled("Audio chunk canceled.")
                if type(track.output_start_sample) is not int or track.output_start_sample < 0:
                    raise AudioDecodeError("Invalid audio track output offset.")
                overlap_start = max(self.chunk_start_sample, track.output_start_sample)
                if overlap_start >= chunk_end:
                    continue
                offset = overlap_start - self.chunk_start_sample
                count = chunk_end - overlap_start
                source_offset = track.source_start_seconds + (
                    overlap_start - track.output_start_sample
                ) / self.sample_rate
                pcm = decode_audio_pcm(
                    track.source, self.ffmpeg,
                    expected_sha256=track.expected_sha256,
                    stream_index=track.stream_index,
                    sample_rate=self.sample_rate, channels=self.channels,
                    source_start_seconds=source_offset,
                    duration_seconds=count / self.sample_rate,
                    cancel=self._cancelled, timeout=self.timeout,
                )
                if self._cancelled():
                    raise AudioDecodeCanceled("Audio chunk canceled before mix.")
                mix_inputs.append(AudioMixInput(pcm, offset, track.gain))
            mixed = mix_pcm_buffers(
                mix_inputs, output_samples=self.chunk_samples,
                sample_rate=self.sample_rate, channels=self.channels,
            )
            if self._cancelled():
                raise AudioDecodeCanceled("Audio chunk canceled before adoption.")
            self.chunk_ready.emit(mixed)
        except AudioDecodeRetirementUnknown as exc:
            self.retirement_unknown.emit(str(exc))
        except AudioDecodeCanceled:
            self.chunk_canceled.emit()
        except AudioDecodeError as exc:
            self.chunk_failed.emit(str(exc))
        except BaseException:
            self.chunk_failed.emit("Audio chunk worker failed; no PCM chunk was adopted.")
