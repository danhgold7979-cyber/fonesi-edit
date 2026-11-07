"""Headless Qt proxy worker lifecycle tests (no UI or media tool launch)."""
from fractions import Fraction

import pytest

from fonesi_edit.media.proxy_cache import PersistentProxyCache, ProxyCacheKey
from fonesi_edit.media.proxy_encode import (
    EncodedVideoProxy, ProxyEncodeCanceled, ProxyEncodeError,
    ProxyEncodeRetirementUnknown, ProxyProgress,
)
from fonesi_edit.ui import proxy_worker as workers


def _worker(tmp_path):
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024*1024,
                                 max_total_bytes=2*1024*1024)
    return workers.ProxyEncodeWorker(
        tmp_path / "source.mp4", tmp_path / "ffmpeg", tmp_path / "ffprobe",
        cache, expected_source_sha256="a"*64, stream_index=0, timeout=15,
    )


def _result(tmp_path):
    return EncodedVideoProxy(
        path=tmp_path / "cache" / "content.mp4",
        cache_key=ProxyCacheKey("a"*64, "b"*64, 0, 960, 540, "video-proxy-v1"),
        payload_sha256="c"*64, size_bytes=1234, duration=Fraction(1),
        width=960, height=540, codec="h264", pixel_format="yuv420p",
    )


def test_worker_emits_progress_and_adopts_completed_result(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    expected = _result(tmp_path)
    events = []
    worker.progress_changed.connect(events.append)

    def fake_encode(*args, **kwargs):
        assert kwargs["stream_index"] == 0
        assert kwargs["timeout"] == 15
        assert not kwargs["cancel"]()
        kwargs["progress"](ProxyProgress(12, 30.0, 400000, "1x", "continue"))
        return expected

    monkeypatch.setattr(workers, "encode_video_proxy", fake_encode)
    worker.run()
    assert worker.result is expected
    assert worker.error is None
    assert not worker.canceled and not worker.retirement_unknown
    assert len(events) == 1 and events[0].frame == 12


def test_worker_cancel_before_launch_never_invokes_encoder(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    monkeypatch.setattr(workers, "encode_video_proxy",
                        lambda *a, **k: pytest.fail("must not launch"))
    worker.request_cancel()
    worker.run()
    assert worker.canceled and worker.result is None
    assert worker.error is None


@pytest.mark.parametrize("error,attribute", [
    (ProxyEncodeCanceled("cancelled"), "canceled"),
    (ProxyEncodeRetirementUnknown("job remains active"), "retirement_unknown"),
    (ProxyEncodeError("invalid proxy"), "error"),
])
def test_worker_distinguishes_cancellation_retirement_and_failure(
        tmp_path, monkeypatch, error, attribute):
    worker = _worker(tmp_path)
    def failing(*args, **kwargs):
        raise error
    monkeypatch.setattr(workers, "encode_video_proxy", failing)
    worker.run()
    assert worker.result is None
    assert getattr(worker, attribute)
    if attribute == "retirement_unknown":
        assert not worker.canceled
        assert worker.error == "job remains active"


def test_worker_does_not_adopt_result_if_canceled_after_encoder_returns(
        tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    def finish_after_cancel(*args, **kwargs):
        worker.request_cancel()
        return _result(tmp_path)
    monkeypatch.setattr(workers, "encode_video_proxy", finish_after_cancel)
    worker.run()
    assert worker.canceled
    assert worker.result is None


def test_worker_redacts_unexpected_exception(tmp_path, monkeypatch):
    worker = _worker(tmp_path)
    def unexpected(*args, **kwargs):
        raise RuntimeError("private path /users/secret/file.mp4")
    monkeypatch.setattr(workers, "encode_video_proxy", unexpected)
    worker.run()
    assert worker.result is None
    assert worker.error and "secret" not in worker.error


def test_worker_refuses_unvalidated_cache(tmp_path):
    with pytest.raises(ValueError):
        workers.ProxyEncodeWorker(tmp_path / "source", tmp_path / "ffmpeg",
                                  tmp_path / "ffprobe", object(),
                                  expected_source_sha256="a"*64, stream_index=0)
