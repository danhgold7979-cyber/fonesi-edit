"""Require independent full decode before an encoded proxy is published."""
import hashlib
import json
from pathlib import Path

import pytest

from fonesi_edit.jobs.process import ProcessResult
from fonesi_edit.media import proxy_encode as encoder
from fonesi_edit.media.proxy_cache import PersistentProxyCache


def test_full_decode_failure_blocks_cache_publication(tmp_path, monkeypatch):
    source, ffmpeg, ffprobe = (tmp_path / name for name in ('source.mp4', 'ffmpeg', 'ffprobe'))
    for path in (source, ffmpeg, ffprobe):
        path.write_bytes(('fixture:' + path.name).encode())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    cache = PersistentProxyCache(tmp_path / 'cache', max_entry_bytes=1024 * 1024,
                                 max_total_bytes=2 * 1024 * 1024)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if argv[0] == str(ffprobe):
            return ProcessResult(0, json.dumps({
                'streams': [{'codec_type': 'video', 'codec_name': 'mpeg4',
                             'width': 96, 'height': 64, 'pix_fmt': 'yuv420p'}],
                'format': {'duration': '1.0'},
            }).encode(), b'')
        if argv[0] == str(ffmpeg) and '-f' in argv and argv[argv.index('-f') + 1] == 'null':
            return ProcessResult(1, b'', b'corrupt video payload')
        if argv[0] == str(ffmpeg):
            Path(argv[-1]).write_bytes(b'valid-looking MP4 but undecodable frames')
            return ProcessResult(0, b'', b'')
        raise AssertionError('unexpected child command')

    monkeypatch.setattr(encoder, 'run_owned', fake_run)
    with pytest.raises(encoder.ProxyEncodeError, match='full-decode validation failed'):
        encoder.encode_video_proxy(source, ffmpeg, ffprobe, cache,
            expected_source_sha256=digest, stream_index=0,
            spec=encoder.ProxySpec(width=96, height=64, codec='mpeg4'), timeout=20)
    assert any(argv[0] == str(ffprobe) for argv in calls)
    assert any(argv[0] == str(ffmpeg) and '-f' in argv and
               argv[argv.index('-f') + 1] == 'null' for argv in calls)
    assert list(cache.root.iterdir()) == []
