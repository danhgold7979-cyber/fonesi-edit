"""Regression coverage for strict video proxy validation."""
import hashlib
import json
from pathlib import Path
import pytest

from fonesi_edit.jobs.process import ProcessResult
from fonesi_edit.media import proxy_encode as enc
from fonesi_edit.media.proxy_cache import PersistentProxyCache


def _case(tmp_path):
    files = [tmp_path / name for name in ("source.mp4", "ffmpeg", "ffprobe")]
    for path in files:
        path.write_bytes((path.name + "-test-data").encode())
        path.chmod(0o700)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1048576,
                                 max_total_bytes=2097152)
    return (*files, cache, hashlib.sha256(files[0].read_bytes()).hexdigest())


def test_zero_fps_denominator_rejected():
    with pytest.raises(enc.ProxyEncodeError, match="FPS"):
        enc.ProxySpec(fps_den=0)


def test_ffprobe_refuses_audio_in_video_only_proxy(tmp_path, monkeypatch):
    def fake_run(*args, **kwargs):
        return ProcessResult(0, json.dumps({
            "streams": [
                {"codec_type": "video", "codec_name": "mpeg4",
                 "width": 96, "height": 64, "pix_fmt": "yuv420p"},
                {"codec_type": "audio", "codec_name": "aac"}
            ],
            "format": {"duration": "1.0"},
        }).encode(), b"")
    monkeypatch.setattr(enc, "run_owned", fake_run)
    with pytest.raises(enc.ProxyEncodeError, match="metadata"):
        enc._probe_proxy(tmp_path / "ffprobe", tmp_path / "proxy.mp4",
                         cancel=lambda: False, timeout=10, expected_codec="mpeg4")


def test_encoder_wrong_dimensions_does_not_publish(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, cache, digest = _case(tmp_path)

    def fake_run(argv, **kwargs):
        if argv[0] == str(ffmpeg):
            Path(argv[-1]).write_bytes(b"fake output")
            return ProcessResult(0, b"", b"")
        return ProcessResult(0, json.dumps({
            "streams": [{"codec_type": "video", "codec_name": "mpeg4",
                         "width": 32, "height": 32, "pix_fmt": "yuv420p"}],
            "format": {"duration": "1.0"},
        }).encode(), b"")

    monkeypatch.setattr(enc, "run_owned", fake_run)
    with pytest.raises(enc.ProxyEncodeError, match="dimensions"):
        enc.encode_video_proxy(source, ffmpeg, ffprobe, cache,
            expected_source_sha256=digest, stream_index=0,
            spec=enc.ProxySpec(width=96, height=64, codec="mpeg4"), timeout=10)
    assert list(cache.root.iterdir()) == []
