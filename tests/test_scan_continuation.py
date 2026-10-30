"""Bounded playlist scan windows; fake yt-dlp, no live social network."""
from copy import deepcopy
from threading import Event
import pytest

from fonesi_edit.downloads import (
    MAX_SCAN_PAGE_SIZE, MAX_SCAN_SNAPSHOT_ITEMS,
    SCAN_WINDOW_MODE, continuation_scan_payload,
    execute_download_job, selected_download_payloads,
)
from fonesi_edit.storage import Store


def install_fake_extractor(monkeypatch, entries, options_seen):
    import yt_dlp
    import fonesi_edit.downloads as downloads

    monkeypatch.setattr(downloads, 'locate_tool', lambda _name: None)

    class FakeYDL:
        def __init__(self, options):
            self.options = options
            options_seen.append(options)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def add_post_processor(self, _post, when=None):
            assert when == 'after_move'

        def extract_info(self, _url, *, download):
            assert download is False
            start = self.options['playliststart']
            end = self.options['playlistend']
            return {'_type': 'playlist', 'entries': deepcopy(entries[start-1:end])}

    monkeypatch.setattr(yt_dlp, 'YoutubeDL', FakeYDL)


def scan_once(store, payload):
    job_id=store.submit('scan', payload)
    assert store.claim(allowed={'scan'}) is not None
    result=execute_download_job(store,store.job(job_id),lambda _v:None,Event())
    store.finish(job_id,result)
    return store.job(job_id)


def test_bounded_scan_continuation_builds_immutable_cumulative_snapshots(tmp_path,monkeypatch):
    entries=[{'id':str(i),'title':f'Video {i}',
              'webpage_url':f'https://example.test/video/{i}'}
             for i in range(5)]
    opts=[]
    install_fake_extractor(monkeypatch,entries,opts)
    store=Store(tmp_path/'db.sqlite')
    original={'url':'https://example.test/channel','folder':str(tmp_path/'output'),
              'engine':'video','media':'videos','limit':2,'height':720}
    first=scan_once(store,original)
    assert [x['id'] for x in first['result']['items']]==['0','1']
    assert first['result']['scan_window']=={
        'mode':SCAN_WINDOW_MODE,'start':1,'limit':2,'next_start':3}
    parent_snapshot=deepcopy(first['result'])
    p2=continuation_scan_payload(first)
    assert p2['scan_parent_id']==first['id'] and p2['scan_start']==3
    assert p2['height']==720 and '_tools' not in p2
    second=scan_once(store,p2)
    assert [x['id'] for x in second['result']['items']]==['0','1','2','3']
    assert second['result']['scan_window']['next_start']==5
    assert store.job(first['id'])['result']==parent_snapshot
    p3=continuation_scan_payload(second)
    third=scan_once(store,p3)
    assert [x['id'] for x in third['result']['items']]==['0','1','2','3','4']
    assert third['result']['scan_window']['next_start'] is None
    assert third['result']['complete'] is None  # Never infer whole-channel completion.
    with pytest.raises(ValueError,match='Không có vị trí'):
        continuation_scan_payload(third)
    assert [(x['playliststart'],x['playlistend']) for x in opts]==[(1,2),(3,4),(5,6)]
    chosen=selected_download_payloads(second,[0,2])
    assert [x['url'] for x in chosen]==[
        'https://example.test/video/0','https://example.test/video/2']
    assert all(x['height']==720 and x['engine']=='video' for x in chosen)
    assert all('scan_parent_id' not in x and 'scan_start' not in x for x in chosen)


def test_scan_continuation_rejects_payload_tampering_before_new_source_io(tmp_path,monkeypatch):
    entries=[{'id':str(i),'webpage_url':f'https://example.test/{i}'} for i in range(4)]
    opts=[]
    install_fake_extractor(monkeypatch,entries,opts)
    store=Store(tmp_path/'db.sqlite')
    parent=scan_once(store,{'url':'https://example.test/playlist',
                            'folder':str(tmp_path/'download'),'engine':'video',
                            'limit':2,'expected_identity':'user-A'})
    valid=continuation_scan_payload(parent)
    assert len(opts)==1
    scenarios=[
        {'url':'https://other.example.test/playlist'},
        {'folder':str(tmp_path/'unwanted-output')},
        {'expected_identity':'user-B'},
        {'account_ref':'other-account'},
        {'engine':'gallery'},
        {'limit':1},
        {'scan_start':999},
        {'scan_parent_id':'nonexistent'},
    ]
    for changes in scenarios:
        payload={**valid,**changes}
        with pytest.raises(ValueError):
            execute_download_job(store,{'kind':'scan','payload':payload},lambda _v:None,Event())
    with pytest.raises(ValueError,match='Scan continuation'):
        execute_download_job(store,{'kind':'download','payload':valid},lambda _v:None,Event())
    with pytest.raises(ValueError,match='Scan continuation'):
        execute_download_job(store,{'kind':'scan','payload':{
            **valid,'scan_start':True}},lambda _v:None,Event())
    assert len(opts)==1
    assert not (tmp_path/'unwanted-output').exists()


def test_scan_continuation_stops_on_repeat_window_without_silent_download(tmp_path,monkeypatch):
    entries=[{'id':str(i),'webpage_url':f'https://example.test/{i}'} for i in (0,1,0,1)]
    opts=[]
    install_fake_extractor(monkeypatch,entries,opts)
    store=Store(tmp_path/'db.sqlite')
    previous=scan_once(store,{'url':'https://example.test/channel',
                              'folder':str(tmp_path/'out'),'limit':2,
                              'engine':'video'})
    next_scan=scan_once(store,continuation_scan_payload(previous))
    items=next_scan['result']['items']
    assert len(items)==4
    assert [x['selectable'] for x in items]==[True,True,False,False]
    assert next_scan['result']['scan_window']['next_start'] is None
    with pytest.raises(ValueError,match='an toàn'):
        selected_download_payloads(next_scan,[2])
    with pytest.raises(ValueError):
        continuation_scan_payload(next_scan)


def test_scan_older_results_gallery_unbounded_or_snapshot_cap_cannot_continue(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    src={'url':'https://example.test/channel','engine':'video','limit':2}
    scan=store.submit('scan',src)
    store.claim(allowed={'scan'})
    store.finish(scan,{'platform':'Generic','items':[{'id':'1','url':'https://example.test/1'}]})
    with pytest.raises(ValueError,match='khoảng yt-dlp'):
        continuation_scan_payload(store.job(scan))
    assert MAX_SCAN_PAGE_SIZE==200 and MAX_SCAN_SNAPSHOT_ITEMS==2000
    window={'mode':SCAN_WINDOW_MODE,'start':1,'limit':2,'next_start':3}
    previous={'id':'test','kind':'scan','state':'succeeded','payload':src,
              'result':{'platform':'Generic','items':[{'url':'https://example.test/1'}],
                        'scan_window':window}}
    assert continuation_scan_payload(previous)['scan_start']==3
    previous['payload']['engine']='gallery'
    with pytest.raises(ValueError,match='bộ tải video'):
        continuation_scan_payload(previous)
    previous['payload']['engine']='video'
    previous['payload']['limit']=0
    with pytest.raises(ValueError,match='khoảng yt-dlp'):
        continuation_scan_payload(previous)
    previous['payload']['limit']=2
    previous['result']['items']=[{'id':str(i),'url':None} for i in range(MAX_SCAN_SNAPSHOT_ITEMS)]
    with pytest.raises(ValueError,match='Snapshot quét đầy'):
        continuation_scan_payload(previous)
