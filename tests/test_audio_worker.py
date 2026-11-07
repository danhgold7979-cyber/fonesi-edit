"""Tests for asynchronous bounded multi-track audio chunk production."""
from pathlib import Path

import pytest

from fonesi_edit.media.audio_decode import (
    AudioDecodeCanceled, AudioDecodeError, AudioDecodeRetirementUnknown, PCMBuffer,
)
from fonesi_edit.media import audio_worker


def _track(tmp_path, start=0, gain=1.0):
    source = tmp_path / f"track-{start}.mp4"
    source.write_bytes(b"audio")
    return audio_worker.AudioTrackSpec(source, "a"*64, 2, start, 0.0, gain)


def _pcm(count=4, channels=2):
    return PCMBuffer("a"*64, 2, 48000, channels, count,
                     tuple([0.1, -0.1] * count), count)


def test_audio_chunk_worker_aligns_tracks_and_emits_one_mixed_chunk(tmp_path, monkeypatch):
    worker = audio_worker.AudioChunkWorker(
        [_track(tmp_path, 0), _track(tmp_path, 2, 0.5)],
        tmp_path / "ffmpeg", chunk_start_sample=0, chunk_samples=4,
    )
    calls, results, failures = [], [], []
    def fake_decode(source, ffmpeg, **kwargs):
        calls.append((source.name, kwargs["source_start_seconds"], kwargs["duration_seconds"]))
        return _pcm(round(kwargs["duration_seconds"] * 48000))
    monkeypatch.setattr(audio_worker, "decode_audio_pcm", fake_decode)
    worker.chunk_ready.connect(results.append)
    worker.chunk_failed.connect(failures.append)
    worker.run()
    assert len(calls) == 2
    assert calls[0][2] == pytest.approx(4/48000)
    assert calls[1][2] == pytest.approx(2/48000)
    assert len(results) == 1 and not failures
    assert results[0].sample_count == 4
    assert results[0].samples[0:4] == pytest.approx((0.1, -0.1, 0.1, -0.1))


def test_audio_chunk_worker_omits_nonoverlapping_tracks(tmp_path, monkeypatch):
    worker = audio_worker.AudioChunkWorker(
        [_track(tmp_path, 100)], tmp_path / "ffmpeg",
        chunk_start_sample=0, chunk_samples=4,
    )
    results = []
    monkeypatch.setattr(audio_worker, "decode_audio_pcm",
                        lambda *a, **k: pytest.fail("non-overlapping track must not decode"))
    worker.chunk_ready.connect(results.append)
    worker.run()
    assert len(results) == 1
    assert results[0].samples == (0.0,) * 8


def test_audio_chunk_worker_distinguishes_cancel_decode_error_and_retirement(tmp_path, monkeypatch):
    worker = audio_worker.AudioChunkWorker([_track(tmp_path)], tmp_path/"ffmpeg",
                                            chunk_start_sample=0, chunk_samples=4)
    canceled, failed, unknown = [], [], []
    worker.chunk_canceled.connect(lambda: canceled.append(True))
    worker.chunk_failed.connect(failed.append)
    worker.retirement_unknown.connect(unknown.append)
    monkeypatch.setattr(audio_worker, "decode_audio_pcm",
        lambda *a, **k: (_ for _ in ()).throw(AudioDecodeCanceled("cancel")))
    worker.run()
    assert canceled == [True]

    worker = audio_worker.AudioChunkWorker([_track(tmp_path)], tmp_path/"ffmpeg",
                                            chunk_start_sample=0, chunk_samples=4)
    worker.chunk_failed.connect(failed.append)
    monkeypatch.setattr(audio_worker, "decode_audio_pcm",
        lambda *a, **k: (_ for _ in ()).throw(AudioDecodeError("bad")))
    worker.run()
    assert failed == ["bad"]

    worker = audio_worker.AudioChunkWorker([_track(tmp_path)], tmp_path/"ffmpeg",
                                            chunk_start_sample=0, chunk_samples=4)
    worker.retirement_unknown.connect(unknown.append)
    monkeypatch.setattr(audio_worker, "decode_audio_pcm",
        lambda *a, **k: (_ for _ in ()).throw(AudioDecodeRetirementUnknown("unknown")))
    worker.run()
    assert unknown == ["unknown"]


def test_audio_chunk_worker_refuses_oversized_chunk_and_cancels_before_decode(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        audio_worker.AudioChunkWorker([], tmp_path/"ffmpeg",
            chunk_start_sample=0, chunk_samples=48000*6)
    worker = audio_worker.AudioChunkWorker([_track(tmp_path)], tmp_path/"ffmpeg",
        chunk_start_sample=0, chunk_samples=4)
    canceled = []
    worker.chunk_canceled.connect(lambda: canceled.append(True))
    worker.request_cancel()
    monkeypatch.setattr(audio_worker, "decode_audio_pcm",
        lambda *a, **k: pytest.fail("must not decode"))
    worker.run()
    assert canceled == [True]
