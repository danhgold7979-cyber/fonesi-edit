"""Tests for bounded, stream-explicit FFmpeg PCM decoding."""
import hashlib
import math
import struct

import pytest

from fonesi_edit.jobs.process import ProcessResult, ProcessCanceled, ProcessError
from fonesi_edit.media import audio_decode as audio


def _source(tmp_path):
    path = tmp_path / "audio.mp4"
    path.write_bytes(b"audio-source-fixture")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_audio_decode_uses_explicit_stream_and_returns_interleaved_pcm(tmp_path, monkeypatch):
    source, digest = _source(tmp_path)
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_bytes(b"ffmpeg-test")
    payload = struct.pack("<ffff", 0.1, -0.1, 0.2, -0.2)
    commands = []
    def fake_run(argv, **kwargs):
        commands.append(argv)
        return ProcessResult(0, payload, b"")
    monkeypatch.setattr(audio, "run_owned", fake_run)
    result = audio.decode_audio_pcm(source, ffmpeg, expected_sha256=digest,
        stream_index=4, sample_rate=48000, channels=2, duration_seconds=1.0)
    assert result.sample_count == 2 and result.channels == 2
    assert result.samples == pytest.approx((0.1, -0.1, 0.2, -0.2))
    argv = commands[0]
    assert argv[argv.index("-map") + 1] == "0:4"
    assert argv[argv.index("-f") + 1] == "f32le"
    assert argv[argv.index("-ac") + 1] == "2"


@pytest.mark.parametrize("payload", [b"x", struct.pack("<f", float("nan"))])
def test_audio_decode_rejects_misaligned_or_nonfinite_pcm(tmp_path, monkeypatch, payload):
    source, digest = _source(tmp_path)
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_bytes(b"ffmpeg-test")
    monkeypatch.setattr(audio, "run_owned",
                        lambda *a, **k: ProcessResult(0, payload, b""))
    with pytest.raises(audio.AudioDecodeError):
        audio.decode_audio_pcm(source, ffmpeg, expected_sha256=digest,
            stream_index=0, channels=2, duration_seconds=1.0)


def test_audio_decode_refuses_invalid_window_and_source_fingerprint(tmp_path, monkeypatch):
    source, digest = _source(tmp_path)
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_bytes(b"ffmpeg-test")
    monkeypatch.setattr(audio, "run_owned", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(audio.AudioDecodeError, match="at most 5"):
        audio.decode_audio_pcm(source, ffmpeg, expected_sha256=digest,
            stream_index=0, duration_seconds=6.0)
    with pytest.raises(audio.AudioDecodeError, match="fingerprint"):
        audio.decode_audio_pcm(source, ffmpeg, expected_sha256="0"*64,
            stream_index=0, duration_seconds=1.0)


def test_audio_decode_distinguishes_cancellation_and_unknown_retirement(tmp_path, monkeypatch):
    source, digest = _source(tmp_path)
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_bytes(b"ffmpeg-test")
    monkeypatch.setattr(audio, "run_owned",
                        lambda *a, **k: (_ for _ in ()).throw(ProcessCanceled("cancelled")))
    with pytest.raises(audio.AudioDecodeCanceled):
        audio.decode_audio_pcm(source, ffmpeg, expected_sha256=digest,
            stream_index=0, duration_seconds=1.0)
    monkeypatch.setattr(audio, "run_owned",
                        lambda *a, **k: (_ for _ in ()).throw(ProcessError("retirement unconfirmed")))
    with pytest.raises(audio.AudioDecodeRetirementUnknown):
        audio.decode_audio_pcm(source, ffmpeg, expected_sha256=digest,
            stream_index=0, duration_seconds=1.0)
