"""Tests for asynchronous bounded video frame queue lifecycle."""
from pathlib import Path
from threading import Event, Thread, Timer
import time

import pytest

from fonesi_edit.media.video_decode import (
    RGBVideoFrame, VideoFrameBatch, VideoDecodeCanceled,
    VideoDecodeError, VideoDecodeRetirementUnknown,
)
from fonesi_edit.media import playback_worker


def _worker(tmp_path):
    source, ffmpeg = tmp_path / "source.mp4", tmp_path / "ffmpeg"
    source.write_bytes(b"source")
    ffmpeg.write_bytes(b"tool")
    return playback_worker.VideoFrameQueueWorker(
        source, ffmpeg, expected_sha256="a"*64, stream_index=0,
        start_seconds=0.0, fps_num=24, fps_den=1, total_frames=10,
        width=16, height=16, batch_size=4,
    )


def _batch(start, count):
    frame = RGBVideoFrame(0, 16, 16, float(start), b"x" * (16*16*3))
    return VideoFrameBatch("a"*64, 0, 16, 16,
                           tuple(RGBVideoFrame(i, 16, 16, start+i/24,
                                               b"x"*(16*16*3))
                                 for i in range(count)), count == 4)


def test_queue_worker_emits_batches_and_progress(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    batches, progress, errors = [], [], []
    worker.batch_ready.connect(batches.append)
    worker.progress_changed.connect(lambda a,b: progress.append((a,b)))
    worker.decode_failed.connect(errors.append)
    calls = []
    def fake_decode(*args, **kwargs):
        calls.append(kwargs["frame_count"])
        return _batch(len(calls)*4, kwargs["frame_count"])
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch", fake_decode)
    worker.run()
    assert calls == [4,4,2]
    assert [x[0] for x in progress] == [4,8,10]
    assert len(batches) == 3 and worker.frames_decoded == 10
    assert [frame.index for batch in batches for frame in batch.frames] == list(range(10))
    assert errors == []


def test_queue_worker_stops_on_short_eof_batch(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    batches = []
    worker.batch_ready.connect(batches.append)
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch",
                        lambda *a, **k: _batch(0, 2))
    worker.run()
    assert len(batches) == 1 and worker.frames_decoded == 2


def test_queue_worker_distinguishes_cancel_failure_and_retirement(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    canceled, failed, unknown = [], [], []
    worker.decode_canceled.connect(lambda: canceled.append(True))
    worker.decode_failed.connect(failed.append)
    worker.retirement_unknown.connect(unknown.append)
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch",
                        lambda *a, **k: (_ for _ in ()).throw(VideoDecodeCanceled("cancel")))
    worker.run()
    assert canceled == [True] and not failed and not unknown

    worker = _worker(tmp_path)
    worker.decode_failed.connect(failed.append)
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch",
                        lambda *a, **k: (_ for _ in ()).throw(VideoDecodeError("bad decode")))
    worker.run()
    assert failed == ["bad decode"]

    worker = _worker(tmp_path)
    worker.retirement_unknown.connect(unknown.append)
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch",
                        lambda *a, **k: (_ for _ in ()).throw(VideoDecodeRetirementUnknown("unknown")))
    worker.run()
    assert unknown == ["unknown"]


def test_queue_worker_cancel_before_launch_does_not_decode(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    canceled = []
    worker.decode_canceled.connect(lambda: canceled.append(True))
    worker.request_cancel()
    monkeypatch.setattr(playback_worker, "decode_video_frame_batch",
                        lambda *a, **k: pytest.fail("decoder must not launch"))
    worker.run()
    assert canceled == [True] and worker.frames_decoded == 0


def test_queue_worker_validates_bounds(tmp_path):
    with pytest.raises(ValueError):
        playback_worker.VideoFrameQueueWorker(
            tmp_path/"s", tmp_path/"f", expected_sha256="a"*64,
            stream_index=0, start_seconds=0, fps_num=24, fps_den=1,
            total_frames=100001,
        )



def test_queue_worker_applies_frame_credit_backpressure_until_consumer_retires(
        tmp_path, monkeypatch):
    worker = playback_worker.VideoFrameQueueWorker(
        tmp_path/"source.mp4", tmp_path/"ffmpeg", expected_sha256="a"*64,
        stream_index=0, start_seconds=0.0, fps_num=24, fps_den=1,
        total_frames=8, width=16, height=16, batch_size=4,
        max_inflight_frames=4,
    )
    calls, batches, timers = [], [], []
    first_batch = Event()

    def fake_decode(*args, **kwargs):
        calls.append(kwargs["frame_count"])
        return _batch((len(calls)-1)*4, kwargs["frame_count"])

    def consume(batch):
        batches.append(batch)
        if len(batches) == 1:
            first_batch.set()
        timer = Timer(0.08, lambda: worker.acknowledge_frames(len(batch.frames)))
        timers.append(timer)
        timer.start()

    monkeypatch.setattr(playback_worker, "decode_video_frame_batch", fake_decode)
    worker.batch_ready.connect(consume)
    thread = Thread(target=worker.run)
    thread.start()
    assert first_batch.wait(1)
    time.sleep(0.02)
    assert calls == [4]
    assert worker.inflight_frames == 4
    thread.join(2)
    for timer in timers:
        timer.join(1)
    assert not thread.is_alive()
    assert calls == [4, 4]
    assert worker.inflight_frames == 0
    assert worker.frames_decoded == 8


def test_queue_worker_cancel_wakes_waiting_frame_credit_producer(tmp_path, monkeypatch):
    worker = playback_worker.VideoFrameQueueWorker(
        tmp_path/"source.mp4", tmp_path/"ffmpeg", expected_sha256="a"*64,
        stream_index=0, start_seconds=0.0, fps_num=24, fps_den=1,
        total_frames=8, width=16, height=16, batch_size=4,
        max_inflight_frames=4,
    )
    calls, canceled = [], []
    first_batch = Event()

    def fake_decode(*args, **kwargs):
        calls.append(kwargs["frame_count"])
        return _batch(0, kwargs["frame_count"])

    monkeypatch.setattr(playback_worker, "decode_video_frame_batch", fake_decode)
    worker.batch_ready.connect(lambda _batch: first_batch.set())
    worker.decode_canceled.connect(lambda: canceled.append(True))
    thread = Thread(target=worker.run)
    thread.start()
    assert first_batch.wait(1)
    time.sleep(0.02)
    assert calls == [4] and worker.inflight_frames == 4
    worker.request_cancel()
    thread.join(1)
    assert not thread.is_alive()
    assert calls == [4]
    assert canceled == [True]


def test_queue_worker_validates_inflight_frame_bound(tmp_path):
    with pytest.raises(ValueError, match="max_inflight_frames"):
        playback_worker.VideoFrameQueueWorker(
            tmp_path/"s", tmp_path/"f", expected_sha256="a"*64,
            stream_index=0, start_seconds=0, fps_num=24, fps_den=1,
            total_frames=8, batch_size=4, max_inflight_frames=3,
        )
