import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from fonesi_edit.jobs.process import ProcessResult
from fonesi_edit.media import proxy_encode as module
from fonesi_edit.media.proxy_cache import PersistentProxyCache


def _files(tmp_path):
    source = tmp_path / "source.mp4"
    ffmpeg = tmp_path / "ffmpeg"
    ffprobe = tmp_path / "ffprobe"
    source.write_bytes(b"synthetic source media bytes")
    ffmpeg.write_bytes(b"synthetic ffmpeg executable")
    ffprobe.write_bytes(b"synthetic ffprobe executable")
    ffmpeg.chmod(0o700)
    ffprobe.chmod(0o700)
    return source, ffmpeg, ffprobe, hashlib.sha256(source.read_bytes()).hexdigest()


def test_proxy_spec_and_command_are_explicit_video_only(tmp_path):
    source, ffmpeg, _, _ = _files(tmp_path)
    output = tmp_path / "proxy.mp4"
    spec = module.ProxySpec(width=640, height=360, fps_num=30000, fps_den=1001)
    command = module.build_proxy_command(ffmpeg, source, output, stream_index=2, spec=spec)
    assert command[command.index("-map") + 1] == "0:2"
    assert command[command.index("-an") ] == "-an"
    assert "-progress" in command and "pipe:1" in command
    assert "fps=30000/1001" in command[command.index("-vf") + 1]
    assert command[-1] == str(output)
    assert "-y" in command and "-nostdin" in command
    with pytest.raises(module.ProxyEncodeError):
        module.ProxySpec(width=4096)
    with pytest.raises(module.ProxyEncodeError):
        module.build_proxy_command(ffmpeg, source, output, stream_index=-1, spec=spec)


def test_progress_parser_handles_chunk_boundaries_and_bounds():
    events = []
    parser = module._ProgressParser(events.append)
    parser.feed(b"frame=12\nfps=24.5\nout_time_us=500000\nspeed=1.2x\nprog")
    parser.feed(b"ress=continue\n")
    assert len(events) == 1
    assert events[0].frame == 12
    assert events[0].fps == 24.5
    assert events[0].out_time_us == 500000
    assert events[0].progress == "continue"
    with pytest.raises(module.ProxyEncodeError):
        module._ProgressParser(None).feed(b"x" * (module._PROGRESS_LINE_BYTES + 1))


def test_encode_video_proxy_validates_and_publishes_then_reuses_cache(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, digest = _files(tmp_path)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024, max_entries=8)
    calls = []
    encoded = b"synthetic but independently-probed MP4 payload"

    def fake_run(argv, **kwargs):
        calls.append(tuple(argv))
        if argv[0] == str(ffmpeg):
            Path(argv[-1]).write_bytes(encoded)
            callback = kwargs.get("on_stdout")
            if callback:
                callback(b"frame=30\nout_time_us=1000000\nprogress=end\n")
            return ProcessResult(0, b"", b"")
        if argv[0] == str(ffprobe):
            return ProcessResult(0, json.dumps({
                "streams": [{"codec_type": "video", "codec_name": "h264",
                             "width": 640, "height": 360, "pix_fmt": "yuv420p"}],
                "format": {"duration": "1.0"},
            }).encode(), b"")
        raise AssertionError("unexpected executable")

    monkeypatch.setattr(module, "run_owned", fake_run)
    events = []
    first = module.encode_video_proxy(
        source, ffmpeg, ffprobe, cache, expected_source_sha256=digest,
        stream_index=0, spec=module.ProxySpec(width=640, height=360),
        progress=events.append,
    )
    assert first.size_bytes == len(encoded)
    assert first.duration == Fraction(1, 1)
    assert first.cache_hit is False
    assert first.path.is_file()
    assert len(events) == 1
    assert [Path(call[0]).name for call in calls].count("ffmpeg") == 1

    calls.clear()
    second = module.encode_video_proxy(
        source, ffmpeg, ffprobe, cache, expected_source_sha256=digest,
        stream_index=0, spec=module.ProxySpec(width=640, height=360),
    )
    assert second.cache_hit is True
    assert second.path.is_file()
    assert second.payload_sha256 == first.payload_sha256
    assert [Path(call[0]).name for call in calls] == ["ffprobe"]


def test_encoder_rejects_source_hash_mismatch_before_process(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, _ = _files(tmp_path)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024, max_entries=8)
    calls = []
    monkeypatch.setattr(module, "run_owned", lambda *a, **k: calls.append(a))
    with pytest.raises(module.ProxyEncodeError, match="source hash"):
        module.encode_video_proxy(source, ffmpeg, ffprobe, cache,
                                  expected_source_sha256="0" * 64, stream_index=0)
    assert calls == []


def test_encoder_cancel_before_launch_does_not_publish(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, digest = _files(tmp_path)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024, max_entries=8)
    calls = []
    monkeypatch.setattr(module, "run_owned", lambda *a, **k: calls.append(a))
    with pytest.raises(module.ProxyEncodeCanceled):
        module.encode_video_proxy(source, ffmpeg, ffprobe, cache,
                                  expected_source_sha256=digest, stream_index=0,
                                  cancel=lambda: True)
    assert calls == []
    assert list(cache.root.iterdir()) == []



def test_invalid_ffprobe_metadata_never_publishes_and_cleans_staging(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, digest = _files(tmp_path)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024, max_entries=8)
    def fake_run(argv, **kwargs):
        if argv[0] == str(ffmpeg):
            Path(argv[-1]).write_bytes(b"not-a-real-mp4")
            return ProcessResult(0, b"", b"")
        return ProcessResult(0, json.dumps({
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
            "format": {"duration": "1.0"},
        }).encode(), b"")
    monkeypatch.setattr(module, "run_owned", fake_run)
    with pytest.raises(module.ProxyEncodeError, match="metadata is invalid"):
        module.encode_video_proxy(source, ffmpeg, ffprobe, cache,
                                  expected_source_sha256=digest, stream_index=0,
                                  spec=module.ProxySpec(width=640, height=360))
    entries = list(cache.root.iterdir())
    assert entries == []


def test_encoder_progress_callback_failure_retires_and_does_not_publish(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe, digest = _files(tmp_path)
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024, max_entries=8)
    def fake_run(argv, **kwargs):
        if argv[0] == str(ffmpeg):
            Path(argv[-1]).write_bytes(b"synthetic output")
            callback = kwargs.get("on_stdout")
            if callback:
                callback(b"frame=1\nprogress=end\n")
            return ProcessResult(0, b"", b"")
        return ProcessResult(0, json.dumps({
            "streams": [{"codec_type": "video", "codec_name": "h264",
                         "width": 640, "height": 360, "pix_fmt": "yuv420p"}],
            "format": {"duration": "1.0"},
        }).encode(), b"")
    monkeypatch.setattr(module, "run_owned", fake_run)
    def bad_progress(_event):
        raise RuntimeError("UI observer failed")
    with pytest.raises(RuntimeError, match="UI observer failed"):
        module.encode_video_proxy(source, ffmpeg, ffprobe, cache,
                                  expected_source_sha256=digest, stream_index=0,
                                  spec=module.ProxySpec(width=640, height=360),
                                  progress=bad_progress)
    assert list(cache.root.iterdir()) == []
