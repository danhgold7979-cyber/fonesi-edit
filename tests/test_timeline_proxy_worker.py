"""Timeline integration for the cancellable video proxy worker."""
import hashlib
import os
import sys
from pathlib import Path
from fractions import Fraction

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from fonesi_edit.media.proxy_cache import ProxyCacheKey
from fonesi_edit.media.proxy_encode import EncodedVideoProxy, ProxyProgress
from fonesi_edit.ui import proxy_worker
from test_timeline_preview_ui import _open, _close
from test_queue_view import wait_for


def test_timeline_starts_proxy_worker_and_reports_only_verified_result(
        tmp_path, qt_app, monkeypatch):
    store, window, timeline, source, source_bytes = _open(tmp_path)
    try:
        ffmpeg = tmp_path / "ffmpeg"
        ffprobe = tmp_path / "ffprobe"
        ffmpeg.write_bytes(b"test ffmpeg tool")
        ffmpeg.chmod(0o700)
        ffprobe.write_bytes(b"test probe tool")
        ffprobe.chmod(0o700)
        timeline.preview_path.setText(str(ffmpeg))
        timeline.preview_trust.setChecked(True)
        assert timeline.proxy_button.isEnabled()
        project_before = window.session.project.plan.to_dict()
        observed = []

        def fake_encode(source_path, ffmpeg_path, ffprobe_path, cache, **kwargs):
            assert source_path == source
            assert ffmpeg_path == ffmpeg
            assert ffprobe_path == ffprobe
            kwargs["progress"](ProxyProgress(30, 30.0, 1000000, "1x", "end"))
            key = ProxyCacheKey("a"*64, "b"*64, 3, 640, 360, "proxy-test")
            proxy_path = cache.root / "test-proxy.mp4"
            proxy_path.parent.mkdir(parents=True, exist_ok=True)
            proxy_path.write_bytes(b"verified proxy fixture")
            return EncodedVideoProxy(proxy_path, key, hashlib.sha256(proxy_path.read_bytes()).hexdigest(),
                                     proxy_path.stat().st_size, Fraction(1), 640, 360,
                                     "mpeg4", "yuv420p", False)

        monkeypatch.setattr(proxy_worker, "encode_video_proxy", fake_encode)
        timeline.proxy_button.click()
        assert timeline.proxy_progress.isVisible()
        wait_for(qt_app, lambda: timeline.proxy_worker is None)
        assert "Proxy sẵn sàng" in timeline.proxy_status.text()
        assert "640×360" in timeline.proxy_status.text()
        assert "đã mã hóa và full-decode" in timeline.proxy_status.text()
        assert window.session.project.plan.to_dict() == project_before
        assert source.read_bytes() == source_bytes
        assert not timeline.proxy_progress.isVisible()
    finally:
        _close(store, window, qt_app)



def test_timeline_cancel_button_waits_for_worker_retirement(tmp_path, qt_app, monkeypatch):
    import threading
    import time
    from fonesi_edit.media.proxy_encode import ProxyEncodeCanceled
    store, window, timeline, source, source_bytes = _open(tmp_path)
    started = threading.Event()
    try:
        ffmpeg = tmp_path / "ffmpeg"
        ffprobe = tmp_path / "ffprobe"
        ffmpeg.write_bytes(b"test ffmpeg tool")
        ffprobe.write_bytes(b"test ffprobe tool")
        ffmpeg.chmod(0o700); ffprobe.chmod(0o700)
        timeline.preview_path.setText(str(ffmpeg))
        timeline.preview_trust.setChecked(True)

        def cancellable_encode(*args, **kwargs):
            started.set()
            while not kwargs["cancel"]():
                time.sleep(0.005)
            raise ProxyEncodeCanceled("test cancellation after process retirement")

        monkeypatch.setattr(proxy_worker, "encode_video_proxy", cancellable_encode)
        timeline.proxy_button.click()
        wait_for(qt_app, started.is_set)
        assert timeline.proxy_cancel_button.isEnabled()
        timeline.proxy_cancel_button.click()
        wait_for(qt_app, lambda: timeline.proxy_worker is None)
        assert "Đã hủy video proxy" in timeline.proxy_status.text()
        assert source.read_bytes() == source_bytes
        assert window.session.project.plan.to_dict() == project_before
        assert not timeline.proxy_progress.isVisible()
    finally:
        _close(store, window, qt_app)
