"""Native FFmpeg proxy smoke test; skips only when both tools are unavailable."""
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess

import pytest

from fonesi_edit.media.proxy_cache import PersistentProxyCache
from fonesi_edit.media.proxy_encode import ProxySpec, encode_video_proxy


def test_native_video_only_encode_full_decode_and_cache_hit(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("FFmpeg and FFprobe required for optional native smoke test")
    ffmpeg, ffprobe = Path(ffmpeg).resolve(), Path(ffprobe).resolve()
    source = tmp_path / "fixture.mp4"
    result = subprocess.run(
        [str(ffmpeg), "-nostdin", "-hide_banner", "-v", "error", "-f", "lavfi",
         "-i", "testsrc2=size=96x64:rate=10:duration=1", "-an", "-c:v", "mpeg4",
         "-threads", "1", "-y", str(source)],
        capture_output=True, check=False, timeout=30,
    )
    assert result.returncode == 0, "Native MPEG-4 fixture generation failed"
    before = sha256(source.read_bytes()).hexdigest()
    cache = PersistentProxyCache(tmp_path / "proxy-cache", max_entry_bytes=16 * 1024**2,
                                 max_total_bytes=32 * 1024**2, max_entries=8)
    spec = ProxySpec(width=96, height=64, fps_num=10, fps_den=1, codec="mpeg4")
    events = []
    first = encode_video_proxy(source, ffmpeg, ffprobe, cache,
                               expected_source_sha256=before, stream_index=0,
                               spec=spec, progress=events.append, timeout=60)
    assert first.path.is_file() and first.size_bytes > 0 and first.cache_hit is False
    assert (first.width, first.height) == (96, 64)
    assert first.duration > 0 and events and events[-1].progress == "end"
    assert first.payload_sha256 == sha256(first.path.read_bytes()).hexdigest()
    decoded = subprocess.run([str(ffmpeg), "-nostdin", "-hide_banner", "-v", "error",
                              "-i", str(first.path), "-map", "0:v:0", "-f", "null", "-"],
                             capture_output=True, timeout=30)
    assert decoded.returncode == 0, "Full proxy decode failed"
    second = encode_video_proxy(source, ffmpeg, ffprobe, cache,
                                expected_source_sha256=before, stream_index=0,
                                spec=spec, timeout=60)
    assert second.cache_hit is True and second.path == first.path
    assert second.payload_sha256 == first.payload_sha256
    assert sha256(source.read_bytes()).hexdigest() == before
