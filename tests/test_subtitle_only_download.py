"""P05-06 subtitle-only yt-dlp work with fake extractor, no live account."""
from pathlib import Path
from threading import Event
import os
import pytest

from fonesi_edit.downloads import (
    execute_download_job, selected_download_payloads, verified_subtitle_artifacts,
)
from fonesi_edit.storage import Store


CAPTIONS = "1\n00:00:00,000 --> 00:00:01,500\nXin chào!\n\n"


def make_fake_ydl(monkeypatch, platform_root, *, missing=False, corrupt=False,
                  external=False, no_filepath=False, media_marker=None):
    import yt_dlp
    import fonesi_edit.downloads as downloads
    calls=[]
    monkeypatch.setattr(downloads,'locate_tool',lambda _name:None)

    class FakeYDL:
        def __init__(self, options):
            self.options=options
            calls.append(options)

        def __enter__(self):return self

        def __exit__(self,*_args):return False

        def add_post_processor(self,*_args,**_kwargs):
            raise AssertionError('Sub-only must not install a video recorder')

        def prepare_filename(self, info, outtmpl_type=None):
            assert outtmpl_type=='subtitle'
            return str(platform_root/'Creator__id'/'subtitles'/'video-id.mp4')

        def extract_info(self, url, *, download):
            assert download is True and url=='https://example.test/video'
            assert self.options['skip_download'] is True
            assert self.options['noplaylist'] is True
            assert self.options['writesubtitles'] is True
            assert self.options['writeautomaticsub'] is True
            assert self.options['writethumbnail'] is False
            assert self.options['writeinfojson'] is False
            assert self.options['overwrites'] is False
            if missing:
                return {'id':'video-id','requested_subtitles':{}}
            target=platform_root/'Creator__id'/'subtitles'/'video-id.en.srt'
            target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():
                target.write_text('not a caption' if corrupt else CAPTIONS,encoding='utf-8')
            spec={'ext':'srt'}
            if not no_filepath:
                spec['filepath']=str(platform_root.parent/'foreign.en.srt' if external else target)
            if media_marker is not None:
                assert media_marker.read_bytes()==b'original video'
            return {'id':'video-id','ext':'mp4','requested_subtitles':{'en':spec}}

    monkeypatch.setattr(yt_dlp,'YoutubeDL',FakeYDL)
    return calls


def test_subtitle_only_download_reuses_sidecar_without_touching_video(tmp_path,monkeypatch):
    store=Store(tmp_path/'state.db')
    folder=tmp_path/'tiếng Việt 中文'
    marker=folder/'Generic'/'Creator__id'/'videos'/'video-id.mp4'
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b'original video')
    opts=make_fake_ydl(monkeypatch,folder/'Generic',media_marker=marker)
    payload={'url':'https://example.test/video','folder':str(folder),
             'engine':'video','media':'videos','limit':1,
             'download_mode':'subtitles_only','languages':['en'],'thumbnail':False,
             'subtitles':True,'auto_subtitles':True}
    job={'kind':'download','payload':payload}
    result=execute_download_job(store,job,lambda _p:None,Event())
    assert result['count']==1 and result['download_mode']=='subtitles_only'
    sidecar=Path(result['files'][0]['path'])
    assert sidecar.read_text(encoding='utf-8')==CAPTIONS
    assert result['files'][0]['kind']=='subtitle'
    assert result['files'][0]['language']=='en'
    assert result['files'][0]['cues']==1
    assert marker.read_bytes()==b'original video'
    old=sidecar.stat()
    old_mtime=max(1,old.st_mtime_ns-60_000_000_000)
    os.utime(sidecar,ns=(old.st_atime_ns,old_mtime))
    result2=execute_download_job(store,job,lambda _p:None,Event())
    assert result2['files']==result['files']
    assert sidecar.read_text(encoding='utf-8')==CAPTIONS
    assert sidecar.stat().st_mtime_ns==old_mtime
    assert marker.read_bytes()==b'original video'
    assert len(opts)==2 and all(x['skip_download'] for x in opts)


def test_subtitle_only_falls_back_to_expected_file_if_yt_dlp_skips_existing(tmp_path,monkeypatch):
    store=Store(tmp_path/'db.sqlite')
    folder=tmp_path/'out'
    make_fake_ydl(monkeypatch,folder/'Generic',no_filepath=True)
    payload={'url':'https://example.test/video','engine':'video','media':'videos',
             'download_mode':'subtitles_only','folder':str(folder),'limit':1}
    assert execute_download_job(store,{'kind':'download','payload':payload},
                                lambda _:None,Event())['files'][0]['cues']==1


@pytest.mark.parametrize(('missing','corrupt','external'),[
    (True,False,False),(False,True,False),(False,False,True),
])
def test_subtitle_only_refuses_absent_corrupt_or_external_artifacts(tmp_path,monkeypatch,
                                                                     missing,corrupt,external):
    store=Store(tmp_path/'db.sqlite')
    folder=tmp_path/'output'
    make_fake_ydl(monkeypatch,folder/'Generic',
                  missing=missing,corrupt=corrupt,external=external)
    with pytest.raises((RuntimeError,ValueError)):
        execute_download_job(store,{'kind':'download','payload':{
            'url':'https://example.test/video','folder':str(folder),
            'engine':'video','media':'videos','limit':1,
            'download_mode':'subtitles_only'}},lambda _:None,Event())


@pytest.mark.parametrize('patch',[
    {'download_mode':'unsupported'},
    {'download_mode':True},
    {'engine':'auto'},
    {'engine':'gallery'},
    {'media':'images'},
    {'limit':0},
    {'limit':2},
    {'languages':[]},
    {'languages':'en'},
    {'languages':['en','']},
    {'workflow':{'preset':{}}},
    {'thumbnail':True},
])
def test_subtitle_mode_rejects_invalid_job_before_output_folder(tmp_path,patch):
    store=Store(tmp_path/'db.sqlite')
    folder=tmp_path/'not-created'
    payload={'url':'https://example.test/video','folder':str(folder),
             'engine':'video','media':'videos','limit':1,
             'download_mode':'subtitles_only',**patch}
    with pytest.raises(ValueError):
        execute_download_job(store,{'kind':'download','payload':payload},
                             lambda _:None,Event())
    assert not folder.exists()


def test_subtitle_mode_does_not_run_as_scan(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    with pytest.raises(ValueError):
        execute_download_job(store,{'kind':'scan','payload':{
            'url':'https://example.test/video','folder':str(tmp_path/'unused'),
            'engine':'video','media':'videos','limit':1,
            'download_mode':'subtitles_only'}},lambda _:None,Event())
    assert not (tmp_path/'unused').exists()


def test_selected_scan_subtitle_payload_preserves_identity_and_disables_workflow():
    origin={'url':'https://www.youtube.com/channel/abc','folder':'D:/Media',
            'engine':'video','media':'videos','limit':25,'height':720,
            'account_ref':'youtube-account','expected_identity':'user-1',
            'languages':['vi','en'],'thumbnail':True,
            'subtitles':False,'auto_subtitles':False,
            'workflow':{'preset':{'clips':[]},'translate':True},
            'scan_parent_id':'cursor-parent','scan_start':26}
    scan={'kind':'scan','state':'succeeded','payload':origin,
          'result':{'platform':'YouTube','items':[{
              'kind':'video','engine':'video','id':'abc',
              'url':'https://www.youtube.com/watch?v=Abc_123-xyz',
              'selectable':True}]}}
    frozen=selected_download_payloads(scan,[0],subtitles_only=True)[0]
    assert frozen['download_mode']=='subtitles_only'
    assert frozen['engine']=='video' and frozen['limit']==1
    assert frozen['account_ref']=='youtube-account'
    assert frozen['expected_identity']=='user-1'
    assert frozen['languages']==['vi','en'] and frozen['height']==720
    assert frozen['subtitles'] is True and frozen['auto_subtitles'] is True
    assert frozen['thumbnail'] is False
    assert 'workflow' not in frozen
    assert 'scan_start' not in frozen and 'scan_parent_id' not in frozen
    assert 'download_mode' not in origin
    normal=selected_download_payloads(scan,[0])[0]
    assert 'download_mode' not in normal
    assert 'workflow' in normal
    bad={'kind':'images','engine':'gallery','url':'https://www.youtube.com/photo/abc',
         'selectable':True}
    scan['result']['items'].append(bad)
    with pytest.raises(ValueError,match='Chỉ tải phụ đề'):
        selected_download_payloads(scan,[0,1],subtitles_only=True)


def test_subtitle_validator_rejects_wrong_path_empty_and_symlink(tmp_path):
    class YDL:
        def prepare_filename(self, info, outtmpl_type=None):
            return str(tmp_path/'Generic'/'Creator__id'/'subtitles'/'video-id.mp4')
    root=tmp_path/'Generic'
    correct=root/'Creator__id'/'subtitles'/'video-id.en.srt'
    correct.parent.mkdir(parents=True)
    correct.write_text(CAPTIONS,encoding='utf-8')
    info={'id':'video-id','requested_subtitles':{'en':{
        'ext':'srt','filepath':str(correct)}}}
    assert verified_subtitle_artifacts(info,YDL(),root)[0]['cues']==1
    info['requested_subtitles']['en']['filepath']=str(tmp_path/'elsewhere.srt')
    with pytest.raises(ValueError,match='Đường dẫn'):
        verified_subtitle_artifacts(info,YDL(),root)
    info['requested_subtitles']['en']['filepath']=str(correct)
    correct.write_text('',encoding='utf-8')
    with pytest.raises(RuntimeError,match='trống'):
        verified_subtitle_artifacts(info,YDL(),root)
    if os.name!='nt':
        correct.unlink()
        outside=tmp_path/'outside.srt'
        outside.write_text(CAPTIONS,encoding='utf-8')
        correct.symlink_to(outside)
        with pytest.raises(ValueError,match='Đường dẫn'):
            verified_subtitle_artifacts(info,YDL(),root)
