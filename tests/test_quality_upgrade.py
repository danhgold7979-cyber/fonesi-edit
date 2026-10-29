"""P05 quality variants: actual FFmpeg/FFprobe source and fake yt-dlp network.

No provider, Chrome cookie or third-party network requests are made.
"""
from pathlib import Path
from threading import Event
import os
import shutil
import pytest

from fonesi_edit.downloads import (
    selected_quality_upgrade_payloads, execute_download_job,
    validated_quality_source,
)
from fonesi_edit.storage import Store
from fonesi_edit.prototypes.media import create_fixture, run_checked, probe


URL = 'https://example.test/video/123'
ROOT_URL = 'https://example.test/channel'


def baseline_fixture(tmp_path):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'media tiếng Việt'
    baseline=root/'Generic'/'Creator__id'/'videos'/'video-id.mp4'
    baseline.parent.mkdir(parents=True)
    run_checked(['ffmpeg','-v','error','-nostdin','-n','-i',str(fixture['source']),
                 '-vf','scale=320:180','-c:v','libx264','-threads','2',
                 '-c:a','copy',str(baseline)])
    assert probe(baseline).height==180
    assert probe(fixture['source']).height==360
    store=Store(tmp_path/'state.db')
    download={'url':URL,'folder':str(root),'engine':'video','media':'videos',
              'limit':1,'height':240,'subtitles':False,'account_ref':None}
    source_id=store.submit('download',download)
    store.claim(allowed={'download'})
    store.finish(source_id,{'platform':'Generic','count':1,'files':[{
        'path':str(baseline),'id':'video-id','kind':'video'}]})
    scan={'kind':'scan','state':'succeeded','payload':{
        'url':ROOT_URL,'folder':str(root),'engine':'video',
        'media':'videos','limit':2,'height':240,'account_ref':None},
        'result':{'platform':'Generic','items':[{
            'id':'video-id','kind':'video','engine':'video',
            'url':URL,'selectable':True}]}}
    request=selected_quality_upgrade_payloads(scan,[0],store.jobs(),720)[0]
    return store,root,baseline,fixture['source'],scan,request


def fake_quality_ydl(monkeypatch, root, source, *, output_height='good',
                     outside=False, wrong_id=False):
    import yt_dlp
    import fonesi_edit.downloads as downloads
    seen=[]
    monkeypatch.setattr(downloads,'locate_tool',lambda _:None)

    class FakeYDL:
        def __init__(self,options):
            self.options=options
            seen.append(options)
            self.post=None

        def __enter__(self):return self

        def __exit__(self,*_):return False

        def add_post_processor(self,post,when=None):
            assert when=='after_move'
            self.post=post

        def extract_info(self,url,*,download):
            assert url==URL and download is True
            assert self.options['overwrites'] is False
            assert self.options['noplaylist'] is True
            assert self.options['skip_download'] is False
            assert self.options['writesubtitles'] is False
            assert self.options['writeautomaticsub'] is False
            assert self.options['writethumbnail'] is False
            assert self.options['writeinfojson'] is False
            assert 'height>180' in self.options['format']
            assert 'height<=720' in self.options['format']
            assert '/quality-upgrades/720p/videos/' in self.options['outtmpl']['default'].replace('\\','/')
            path=(root.parent/'foreign.mp4' if outside else
                  root/'Generic'/'Creator__id'/'quality-upgrades'/'720p'/'videos'/'video-id.mp4')
            path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():
                if output_height=='low':
                    low=root/'Generic'/'Creator__id'/'videos'/'video-id.mp4'
                    shutil.copyfile(low,path)
                else:
                    shutil.copyfile(source,path)
            info={'id':'changed-id' if wrong_id else 'video-id',
                  'filepath':str(path),'ext':'mp4'}
            assert self.post is not None
            self.post.run(info)
            return info

    monkeypatch.setattr(yt_dlp,'YoutubeDL',FakeYDL)
    return seen


def test_quality_upgrade_preserves_original_and_verifies_higher_variant(tmp_path,monkeypatch):
    store,root,baseline,high,scan,request=baseline_fixture(tmp_path)
    original_bytes=baseline.read_bytes()
    old=baseline.stat()
    options=fake_quality_ydl(monkeypatch,root,high)
    job={'kind':'download','payload':request}
    first=execute_download_job(store,job,lambda _:None,Event())
    assert first['download_mode']=='quality_upgrade'
    assert first['count']==1
    assert first['source_height']==180
    assert first['target_height']==720
    assert first['actual_height']==360
    assert first['files'][0]['height']==360
    assert first['files'][0]['id']=='video-id'
    path=Path(first['files'][0]['path'])
    assert path.parent.name=='videos'
    assert path.parent.parent.name=='720p'
    assert path.parent.parent.parent.name=='quality-upgrades'
    assert path.read_bytes()==high.read_bytes()
    assert baseline.read_bytes()==original_bytes
    assert baseline.stat().st_mtime_ns==old.st_mtime_ns
    variant_stat=path.stat()
    old_variant_time=max(1,variant_stat.st_mtime_ns-60_000_000_000)
    os.utime(path,ns=(variant_stat.st_atime_ns,old_variant_time))
    again=execute_download_job(store,job,lambda _:None,Event())
    assert again['files']==first['files']
    assert path.read_bytes()==high.read_bytes()
    assert path.stat().st_mtime_ns==old_variant_time
    assert baseline.read_bytes()==original_bytes
    assert baseline.stat().st_mtime_ns==old.st_mtime_ns
    assert len(options)==2


def test_quality_upgrade_rejects_lower_or_wrong_video_id_without_altering_source(tmp_path,monkeypatch):
    store,root,baseline,high,_scan,request=baseline_fixture(tmp_path)
    before=baseline.read_bytes()
    fake_quality_ydl(monkeypatch,root,high,output_height='low')
    with pytest.raises(ValueError,match='không nâng được'):
        execute_download_job(store,{'kind':'download','payload':request},
                             lambda _:None,Event())
    assert baseline.read_bytes()==before
    # Incompatible existing output cannot silently become success on retry.
    fake_quality_ydl(monkeypatch,root,high)
    with pytest.raises(ValueError,match='không nâng được'):
        execute_download_job(store,{'kind':'download','payload':request},
                             lambda _:None,Event())
    assert baseline.read_bytes()==before


def test_quality_upgrade_rejects_outside_variant_and_wrong_id(tmp_path,monkeypatch):
    store,root,baseline,high,_scan,request=baseline_fixture(tmp_path)
    for opts,expected in [({'outside':True},'ngoài'),
                          ({'wrong_id':True},'ID nguồn')]:
        fake_quality_ydl(monkeypatch,root,high,**opts)
        with pytest.raises(ValueError,match=expected):
            execute_download_job(store,{'kind':'download','payload':request},
                                 lambda _:None,Event())
    assert probe(baseline).height==180


@pytest.mark.parametrize('changes',[
    {'url':'https://example.test/other'},
    {'account_ref':'wrong-user'},
    {'expected_identity':'wrong-id'},
    {'folder':'not-the-original-folder'},
    {'upgrade_from_job_id':'does-not-exist'},
    {'download_mode':'subtitles_only'},
    {'engine':'gallery'},
    {'engine':'auto'},
    {'media':'images'},
    {'limit':2},
    {'height':180},
    {'height':True},
    {'height':'720'},
    {'height':4321},
    {'thumbnail':True},
    {'subtitles':True},
    {'auto_subtitles':True},
    {'workflow':{'preset':{}}},
])
def test_quality_upgrade_rejects_invalid_payload_before_extractor(tmp_path,changes):
    store,root,baseline,high,_scan,request=baseline_fixture(tmp_path)
    payload={**request,**changes}
    with pytest.raises((ValueError,PermissionError)):
        execute_download_job(store,{'kind':'download','payload':payload},
                             lambda _:None,Event())
    assert not (root/'Generic'/'Creator__id'/'quality-upgrades').exists()
    assert probe(baseline).height==180


def test_quality_upgrade_rejects_missing_or_invalid_baseline(tmp_path):
    store,root,baseline,high,scan,request=baseline_fixture(tmp_path)
    old=store.job(request['upgrade_from_job_id'])
    outside=root.parent/'not-in-platform.mp4'
    shutil.copyfile(baseline,outside)
    fake_result={'platform':'Generic','files':[{'path':str(outside),
                 'id':'video-id','kind':'video'}]}
    bad={**old,'result':fake_result}
    with pytest.raises(ValueError,match='ngoài'):
        validated_quality_source(bad,request,root,'Generic')
    baseline.unlink()
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        execute_download_job(store,{'kind':'download','payload':request},
                             lambda _:None,Event())
    assert not (root/'Generic'/'Creator__id'/'quality-upgrades').exists()


@pytest.mark.parametrize('height',[0,100,True,'720',720.5,4321])
def test_quality_upgrade_rejects_invalid_target_without_mutating_scan(tmp_path,height):
    store,root,baseline,high,scan,request=baseline_fixture(tmp_path)
    with pytest.raises(ValueError,match='144–4320'):
        selected_quality_upgrade_payloads(scan,[0],store.jobs(),height)
    assert 'download_mode' not in scan['payload']


def test_quality_upgrade_requires_a_matching_source_and_rejects_mixed_selection(tmp_path):
    store,root,baseline,high,scan,request=baseline_fixture(tmp_path)
    invalid={**scan,'payload':{**scan['payload'],'account_ref':'new-account'}}
    with pytest.raises(ValueError,match='Chưa có bản video nguồn'):
        selected_quality_upgrade_payloads(invalid,[0],store.jobs(),720)
    mixed={**scan,'result':{**scan['result'],'items':[
        *scan['result']['items'],
        {'id':'picture','kind':'images','engine':'gallery','selectable':True,
         'url':'https://example.test/picture'}]}}
    with pytest.raises(ValueError,match='Chỉ nâng chất lượng'):
        selected_quality_upgrade_payloads(mixed,[0,1],store.jobs(),720)
    assert selected_quality_upgrade_payloads(scan,[0],store.jobs(),720)[0]==request

