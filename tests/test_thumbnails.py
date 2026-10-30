"""Real FFmpeg source thumbnail checks; do not claim compositor parity."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from dataclasses import replace
from threading import Event

import pytest
from PySide6.QtGui import QImageReader

from fonesi_edit.domain import Clip
from fonesi_edit.prototypes.media import create_fixture
from fonesi_edit.thumbnails import thumbnail_identity,thumbnail_strip,thumbnail_times


def test_source_thumbnail_times_respect_trim_and_known_duration():
    clip=Clip('not-needed.mp4',start=.2,end=.8,speed=2,source_duration=1)
    times=thumbnail_times(clip,1,count=3)
    assert len(times)==3
    assert all(.2<t<.8 for t in times)
    assert times==sorted(times)
    assert abs(times[1]-.5)<1e-9
    with pytest.raises(ValueError):
        thumbnail_times(replace(clip,start=.9,end=1.2),.8)


def test_thumbnail_strip_generated_from_video_is_decodable_cached_and_atomic(tmp_path):
    media=create_fixture(tmp_path/'source',duration=1)
    clip=Clip(str(media['source']),start=.1,end=.9,source_duration=1)
    original_bytes=media['source'].read_bytes()
    original_stamp=media['source'].stat().st_mtime_ns
    folder=tmp_path/'cache'
    first=thumbnail_strip(clip,folder)
    assert first['key']==thumbnail_identity(clip)
    assert len(first['frames'])==3
    assert all(QImageReader(name).canRead() for name in first['frames'])
    stamps=[__import__('pathlib').Path(name).stat().st_mtime_ns for name in first['frames']]
    second=thumbnail_strip(clip,folder)
    assert first==second
    assert [__import__('pathlib').Path(name).stat().st_mtime_ns for name in second['frames']]==stamps
    assert media['source'].read_bytes()==original_bytes
    assert media['source'].stat().st_mtime_ns==original_stamp
    assert not list(folder.glob('*.tmp')) and not list(folder.glob('.fonesi-thumbnail-*.png'))
    changed=thumbnail_strip(replace(clip,start=.2),folder)
    assert changed['key']!=first['key']


def test_thumbnail_cancel_has_no_validated_cache_output(tmp_path):
    media=create_fixture(tmp_path/'media',duration=.5)
    clip=Clip(str(media['source']),end=.5)
    canceled=Event();canceled.set()
    with pytest.raises(RuntimeError,match='canceled'):
        thumbnail_strip(clip,tmp_path/'cache',canceled)
    assert not list((tmp_path/'cache').glob('*.png'))
