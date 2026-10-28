"""FFmpeg proxy cache tests with synthetic media. Source is never altered."""
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest

from fonesi_edit.prototypes.media import create_fixture,probe
from fonesi_edit.proxy import PROXY_LEVELS,playback_proxy,proxy_identity


@pytest.mark.parametrize('quality',sorted(PROXY_LEVELS))
def test_local_proxy_levels_are_valid_no_upscale_and_cache_reused(tmp_path,quality):
    media=create_fixture(tmp_path/'media',duration=.5)
    source=media['source'];stamp=source.stat().st_mtime_ns
    original=source.read_bytes()
    cache=tmp_path/'cache'
    first=playback_proxy(source,cache,quality)
    file=Path(first['path'])
    assert file.is_file() and first['key']==proxy_identity(source,quality)
    encoded=probe(file);raw=probe(source)
    assert encoded.width<=raw.width and encoded.height<=raw.height
    assert abs(encoded.duration-raw.duration)<.15
    last_change=file.stat().st_mtime_ns
    assert playback_proxy(source,cache,quality)==first
    assert file.stat().st_mtime_ns==last_change
    assert source.read_bytes()==original
    assert source.stat().st_mtime_ns==stamp
    assert not list(cache.glob('.fonesi-proxy-*'))


def test_proxy_cancel_and_bad_quality_do_not_publish_media(tmp_path):
    media=create_fixture(tmp_path/'media',duration=.5)
    with pytest.raises(ValueError,match='Unknown proxy quality'):
        playback_proxy(media['source'],tmp_path/'cache','unsupported')
    flag=Event();flag.set()
    with pytest.raises(RuntimeError,match='canceled'):
        playback_proxy(media['source'],tmp_path/'cache','fast',flag)
    assert not list((tmp_path/'cache').glob('*.mp4'))
