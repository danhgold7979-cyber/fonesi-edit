"""Tests for bounded FFmpeg RGB24 frame batches."""
import hashlib

import pytest

from fonesi_edit.jobs.process import ProcessResult, ProcessCanceled, ProcessError
from fonesi_edit.media import video_decode as video


def _files(tmp_path):
    source = tmp_path / "source.mp4"
    ffmpeg = tmp_path / "ffmpeg"
    source.write_bytes(b"video-source-fixture")
    ffmpeg.write_bytes(b"ffmpeg-tool-fixture")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return source, ffmpeg, digest


def test_video_decode_maps_explicit_stream_and_splits_rgb_frames(tmp_path, monkeypatch):
    source, ffmpeg, digest = _files(tmp_path)
    frame_bytes = 16 * 16 * 3
    payload = bytes(range(256)) * 6
    calls = []
    def fake_run(argv, **kwargs):
        calls.append(argv)
        return ProcessResult(0, payload, b"")
    monkeypatch.setattr(video, "run_owned", fake_run)
    result = video.decode_video_frame_batch(source, ffmpeg,
        expected_sha256=digest, stream_index=2, start_seconds=1.5,
        fps_num=24, fps_den=1, frame_count=2, width=16, height=16,
        max_output_bytes=frame_bytes * 2)
    assert result.stream_index == 2 and len(result.frames) == 2
    assert result.complete
    assert len(result.frames[0].rgb24) == frame_bytes
    assert result.frames[0].pts_seconds == 1.5
    assert result.frames[1].pts_seconds == pytest.approx(1.5 + 1/24)
    argv = calls[0]
    assert argv[argv.index("-map") + 1] == "0:2"
    assert argv[argv.index("-f") + 1] == "rawvideo"
    assert argv[argv.index("-pix_fmt") + 1] == "rgb24"


def test_video_decode_accepts_short_eof_batch_but_marks_incomplete(tmp_path, monkeypatch):
    source, ffmpeg, digest = _files(tmp_path)
    frame_bytes = 16 * 16 * 3
    monkeypatch.setattr(video, "run_owned",
        lambda *a, **k: ProcessResult(0, b"x" * frame_bytes, b""))
    result = video.decode_video_frame_batch(source, ffmpeg,
        expected_sha256=digest, stream_index=0, start_seconds=0,
        fps_num=25, frame_count=4, width=16, height=16,
        max_output_bytes=frame_bytes * 4)
    assert len(result.frames) == 1 and not result.complete


@pytest.mark.parametrize("payload", [b"x", b""])
def test_video_decode_rejects_partial_or_empty_frame_payload(tmp_path, monkeypatch, payload):
    source, ffmpeg, digest = _files(tmp_path)
    monkeypatch.setattr(video, "run_owned",
        lambda *a, **k: ProcessResult(0, payload, b""))
    with pytest.raises(video.VideoDecodeError):
        video.decode_video_frame_batch(source, ffmpeg,
            expected_sha256=digest, stream_index=0, start_seconds=0,
            fps_num=25, frame_count=1, width=16, height=16,
            max_output_bytes=16*16*3)


def test_video_decode_rejects_unbounded_profile_and_source_drift(tmp_path, monkeypatch):
    source, ffmpeg, digest = _files(tmp_path)
    monkeypatch.setattr(video, "run_owned", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(video.VideoDecodeError, match="1..32"):
        video.decode_video_frame_batch(source, ffmpeg, expected_sha256=digest,
            stream_index=0, start_seconds=0, fps_num=25, frame_count=33,
            width=16, height=16, max_output_bytes=16*16*3*33)
    with pytest.raises(video.VideoDecodeError, match="fingerprint"):
        video.decode_video_frame_batch(source, ffmpeg, expected_sha256="0"*64,
            stream_index=0, start_seconds=0, fps_num=25, frame_count=1,
            width=16, height=16, max_output_bytes=16*16*3)


def test_video_decode_distinguishes_cancel_and_unknown_retirement(tmp_path, monkeypatch):
    source, ffmpeg, digest = _files(tmp_path)
    args = dict(expected_sha256=digest, stream_index=0, start_seconds=0,
                fps_num=25, frame_count=1, width=16, height=16,
                max_output_bytes=16*16*3)
    monkeypatch.setattr(video, "run_owned",
        lambda *a, **k: (_ for _ in ()).throw(ProcessCanceled("cancelled")))
    with pytest.raises(video.VideoDecodeCanceled):
        video.decode_video_frame_batch(source, ffmpeg, **args)
    monkeypatch.setattr(video, "run_owned",
        lambda *a, **k: (_ for _ in ()).throw(ProcessError("retirement unconfirmed")))
    with pytest.raises(video.VideoDecodeRetirementUnknown):
        video.decode_video_frame_batch(source, ffmpeg, **args)
