"""Real-media cache recovery and cancellation boundary for video proxies."""
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess

import pytest

from fonesi_edit.media.proxy_cache import PersistentProxyCache
from fonesi_edit.media.proxy_encode import (ProxySpec, encode_video_proxy,
                                             ProxyEncodeCanceled)
from fonesi_edit.media import proxy_encode as encoder


def test_valid_manifest_with_invalid_video_is_reencoded(tmp_path):
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        pytest.skip('Native media tools unavailable')
    ffmpeg, ffprobe = Path(ffmpeg).resolve(), Path(ffprobe).resolve()
    source = tmp_path / 'source.mp4'
    subprocess.run([str(ffmpeg), '-nostdin', '-hide_banner', '-v', 'error',
                    '-f', 'lavfi', '-i', 'testsrc2=size=96x64:rate=10:duration=1',
                    '-an', '-c:v', 'mpeg4', '-threads', '1', '-y', str(source)],
                   capture_output=True, timeout=30, check=True)
    source_hash = sha256(source.read_bytes()).hexdigest()
    cache = PersistentProxyCache(tmp_path / 'cache', max_entry_bytes=16*1024**2,
                                 max_total_bytes=32*1024**2)
    spec = ProxySpec(width=96, height=64, fps_num=10, codec='mpeg4')
    opts = dict(expected_source_sha256=source_hash, stream_index=0, spec=spec, timeout=45)
    first = encode_video_proxy(source, ffmpeg, ffprobe, cache, **opts)
    assert first.path.is_file()
    cache.put(first.cache_key, b'garbled-but-checksum-valid-video')
    second = encode_video_proxy(source, ffmpeg, ffprobe, cache, **opts)
    assert second.cache_hit is False
    assert second.path.is_file() and second.path.read_bytes() != b'garbled-but-checksum-valid-video'
    third = encode_video_proxy(source, ffmpeg, ffprobe, cache, **opts)
    assert third.cache_hit is True and third.payload_sha256 == second.payload_sha256
    assert sha256(source.read_bytes()).hexdigest() == source_hash


def test_cached_probe_cancellation_never_invalidates(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe = (tmp_path / name for name in ('source.mp4', 'ffmpeg', 'ffprobe'))
    for path in (source, ffmpeg, ffprobe):
        path.write_bytes((path.name + '-synthetic').encode())
    digest = sha256(source.read_bytes()).hexdigest()
    cache = PersistentProxyCache(tmp_path / 'cache', max_entry_bytes=1024*1024,
                                 max_total_bytes=2*1024*1024)
    monkeypatch.setattr(cache, 'get', lambda _key: b'cached-proxy')
    invalidations = []
    monkeypatch.setattr(cache, 'invalidate', lambda _key: invalidations.append(_key))
    monkeypatch.setattr(encoder, '_probe_proxy', lambda *a, **kw: (_ for _ in ()).throw(
        ProxyEncodeCanceled('cancelled while probing')))
    with pytest.raises(ProxyEncodeCanceled):
        encode_video_proxy(source, ffmpeg, ffprobe, cache,
                           expected_source_sha256=digest, stream_index=0,
                           spec=ProxySpec(width=96, height=64, codec='mpeg4'))
    assert invalidations == []
