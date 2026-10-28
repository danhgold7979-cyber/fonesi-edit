from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread,Event
import os
import sys
import pytest
from fonesi_edit.browser import create_profile,bind,pairing_code,pair,receive_session,profiles,bindings,cookie_identity
from fonesi_edit.downloads import platform_for,safe_name,execute_download_job
from fonesi_edit.storage import Store
from fonesi_edit.prototypes.media import create_fixture


def test_platforms_and_windows_names_are_unambiguous():
    assert platform_for('https://youtu.be/a')=='YouTube'
    assert platform_for('https://www.facebook.com/a')=='Facebook'
    assert platform_for('https://facebook.com.attacker.invalid/')=='Generic'
    with pytest.raises(ValueError):platform_for('https://user:secret@example.invalid/')
    assert safe_name('CON').startswith('_') and '/' not in safe_name('a/b:c')


def test_profiles_bindings_pairing_single_use_and_no_plaintext_fallback(tmp_path):
    store=Store(tmp_path/'state.db');a=create_profile(store,'A');b=create_profile(store,'B')
    first=bind(store,a,'Facebook');second=bind(store,b,'Facebook');third=bind(store,a,'TikTok')
    assert len({first,second,third})==3 and len(profiles(store))==2 and len(bindings(store))==3
    code=pairing_code(store,a);token=pair(store,code)
    with pytest.raises(PermissionError):pair(store,code)
    if os.name!='nt':
        with pytest.raises(PermissionError,match='DPAPI'):
            receive_session(store,token,'Facebook',[{'name':'c_user','value':'test-account','domain':'.facebook.com'}])
    assert cookie_identity('X',[{'name':'twid','value':'u=test-id'}])=='test-id'


def test_real_generic_download_and_second_run_preserves_file(tmp_path,monkeypatch):
    monkeypatch.setenv('NO_PROXY','127.0.0.1,localhost')
    media=create_fixture(tmp_path/'served',duration=.5)
    # ASCII URL; Unicode destination is exercised by the output directory.
    source=tmp_path/'served/movie.mp4';source.write_bytes(media['source'].read_bytes())
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(source.parent)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    store=Store(tmp_path/'state.db')
    try:
        payload={'url':f'http://127.0.0.1:{server.server_port}/movie.mp4','folder':str(tmp_path/'tải 中文'),'subtitles':False}
        job={'kind':'download','payload':payload};result=execute_download_job(store,job,lambda p:None,Event())
        assert result['count']==1 and result['files'][0]['kind']=='video'
        from pathlib import Path
        output=Path(result['files'][0]['path']);stamp=output.stat().st_mtime_ns
        result2=execute_download_job(store,job,lambda p:None,Event())
        assert result2['count']==1 and output.stat().st_mtime_ns==stamp
        image_payload={**payload,'engine':'gallery','media':'images','url':f'http://127.0.0.1:{server.server_port}/logo.png'}
        class LegacyWindowsConsole:
            encoding='cp1252'
            def write(self,value):
                value.encode(self.encoding,'strict')
                return len(value)
            def flush(self):pass
            def isatty(self):return False
        # A desktop worker must not print Unicode output paths to a legacy Windows
        # console. This reproduces the frozen-app UnicodeEncodeError without relying
        # on pytest's Unicode-capable stdout capture.
        monkeypatch.setattr(sys,'stdout',LegacyWindowsConsole())
        images=execute_download_job(store,{'kind':'download','payload':image_payload},lambda p:None,Event())
        assert images['count']==1 and images['files'][0]['kind']=='images'
        image_output=Path(images['files'][0]['path'])
        assert image_output.is_file()
        from PySide6.QtGui import QImageReader
        assert QImageReader(str(image_output)).canRead()
        image_stamp=image_output.stat().st_mtime_ns
        images_again=execute_download_job(store,{'kind':'download','payload':image_payload},lambda p:None,Event())
        assert images_again['count']==1 and images_again['files'][0]['kind']=='images'
        assert Path(images_again['files'][0]['path'])==image_output
        assert image_output.stat().st_mtime_ns==image_stamp
        assert QImageReader(str(image_output)).canRead()
    finally:server.shutdown();server.server_close();thread.join(timeout=3)


def test_pairing_code_is_consumed_once_under_concurrent_requests(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    store=Store(tmp_path/'state.db');profile=create_profile(store,'A');code=pairing_code(store,profile)
    def attempt():
        try:pair(store,code);return True
        except PermissionError:return False
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(lambda _:attempt(),range(2)))==[False,True]


def test_revoking_one_profile_does_not_revoke_the_other(tmp_path):
    import hashlib
    from fonesi_edit.browser import revoke_pairing
    store=Store(tmp_path/'state.db');a=create_profile(store,'A');b=create_profile(store,'B');ta=pair(store,pairing_code(store,a));tb=pair(store,pairing_code(store,b))
    revoke_pairing(store,a)
    assert store.setting('bridge:'+hashlib.sha256(ta.encode()).hexdigest()) is None
    assert store.setting('bridge:'+hashlib.sha256(tb.encode()).hexdigest())['profile_id']==b
    with pytest.raises(PermissionError,match='paired'):receive_session(store,ta,'Facebook',[])


@pytest.mark.parametrize('overrides',[
    {'engine':'unsupported'},
    {'engine':[]},
    {'media':'everything'},
    {'media':[]},
    {'limit':-2},
    {'limit':'many'},
    {'limit':1.5},
    {'limit':True},
    {'limit':None},
    {'url':[]},
    {'url':''},
    {'url':'ftp://example.test/media.mp4'},
])
def test_download_options_fail_before_creating_outputs(tmp_path,overrides):
    from threading import Event
    store=Store(tmp_path/'state.db')
    destination=tmp_path/'should-not-exist'
    payload={'url':'http://127.0.0.1/example.mp4','folder':str(destination),**overrides}
    with pytest.raises(ValueError):
        execute_download_job(store,{'kind':'download','payload':payload},lambda _:None,Event())
    assert not destination.exists()


def test_gallery_cookiejar_is_attached_after_extractor_session_exists(tmp_path,monkeypatch):
    """Exercise real gallery-dl transport with a synthetic cookie, not Chrome/auth."""
    from http.cookiejar import Cookie,CookieJar
    from fonesi_edit.downloads import _gallery
    monkeypatch.setenv('NO_PROXY','127.0.0.1,localhost')
    media=create_fixture(tmp_path/'served',duration=.5)
    jar=CookieJar()
    jar.set_cookie(Cookie(
        version=0,name='synthetic_session',value='local-only',port=None,
        port_specified=False,domain='127.0.0.1',domain_specified=False,
        domain_initial_dot=False,path='/',path_specified=True,secure=False,
        expires=None,discard=True,comment=None,comment_url=None,rest={},
        rfc2109=False))
    authenticated_requests=[]
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/logo.png':
                authenticated=self.headers.get('Cookie')=='synthetic_session=local-only'
                authenticated_requests.append(authenticated)
                if not authenticated:
                    self.send_error(403,'Synthetic cookie required')
                    return
            super().do_GET()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),
        partial(Handler,directory=str(media['logo'].parent)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        payload={'url':f'http://127.0.0.1:{server.server_port}/logo.png',
                 'media':'images','limit':0}
        store=Store(tmp_path/'state.db')
        result=_gallery(store,{'kind':'download','payload':payload},'Generic',
                        tmp_path/'Unicode 中文',jar,lambda _:None,Event())
        assert result['count']==1
        assert authenticated_requests and all(authenticated_requests)
        from pathlib import Path
        assert Path(result['files'][0]['path']).is_file()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)


@pytest.mark.parametrize(('url','valid'),[
    ('https://www.youtube.com/watch?v=Abc_123-xyz',True),
    ('https://www.youtube.com/watch?v=Abc_123-xyz&list=PLtest001',True),
    ('https://www.bilibili.com/video/BV1example',True),
    ('http://127.0.0.1:8080/image.png',True),
    ('https://cdn.example.test/file.mp4?token=private',False),
    ('https://www.youtube.com/watch?v=abc&signature=private',False),
    ('https://user:private@example.test/image.png',False),
    ('https://example.test/image.png#hidden',False),
    ('javascript:alert(1)',False),
    ('/media/image.png',False),
    ('https://www.youtube.com/watch?v=',False),
])
def test_scan_entries_only_persist_public_redownloadable_urls(url,valid):
    from fonesi_edit.downloads import selectable_scan_url
    assert (selectable_scan_url(url) == url) is valid


def test_selected_download_payloads_preserve_account_and_settings_without_mutation():
    from fonesi_edit.downloads import selected_download_payloads
    original={'url':'https://www.youtube.com/playlist?list=PLtest001',
              'folder':'D:/tải 中文','engine':'video','media':'both',
              'limit':0,'height':720,'account_ref':'binding-original',
              'expected_identity':'user-1','subtitles':True,
              'workflow':{'translate':False,'preset':{}}}
    item={'id':'video-id','kind':'video','title':'Video from scan',
          'url':'https://www.youtube.com/watch?v=Abc_123-xyz','selectable':True}
    scan={'kind':'scan','state':'succeeded','payload':original,
          'result':{'platform':'YouTube','items':[item],'complete':None}}
    requests=selected_download_payloads(scan,[0])
    assert len(requests)==1 and requests[0]['url']==item['url']
    assert requests[0]['account_ref']=='binding-original'
    assert requests[0]['expected_identity']=='user-1'
    assert requests[0]['height']==720 and requests[0]['subtitles'] is True
    assert requests[0]['media']=='videos' and requests[0]['limit']==1
    assert original['url'].startswith('https://www.youtube.com/playlist?')
    assert original['limit']==0
    with pytest.raises(ValueError,match='trùng lặp'):
        selected_download_payloads(scan,[0,0])
    with pytest.raises(ValueError,match='Chỉ số'):
        selected_download_payloads(scan,[-1])
    with pytest.raises(PermissionError,match='host khác'):
        selected_download_payloads({**scan,'result':{'platform':'YouTube',
            'items':[{'url':'https://cdn.example.test/public.mp4','kind':'video'}]}},[0])
    with pytest.raises(ValueError,match='an toàn'):
        selected_download_payloads({**scan,'result':{'platform':'YouTube',
            'items':[{'url':None,'kind':'video','selectable':False}]}},[0])
    with pytest.raises(ValueError,match='đã hoàn tất'):
        selected_download_payloads({**scan,'state':'running'},[0])


def test_local_gallery_scan_select_and_download_preserves_valid_media(tmp_path,monkeypatch):
    from fonesi_edit.downloads import selected_download_payloads
    from pathlib import Path
    monkeypatch.setenv('NO_PROXY','127.0.0.1,localhost')
    fixture=create_fixture(tmp_path/'served',duration=.5)
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),
        partial(Handler,directory=str(fixture['logo'].parent)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    store=Store(tmp_path/'state.db')
    try:
        payload={'url':f'http://127.0.0.1:{server.server_port}/logo.png',
                 'folder':str(tmp_path/'tiếng Việt 中文'),'engine':'gallery',
                 'media':'images','limit':1}
        job_id=store.submit('scan',payload)
        store.claim(allowed={'scan'})
        scan=execute_download_job(store,{'kind':'scan','payload':payload},
                                  lambda _:None,Event())
        assert scan['count']==1 and scan['items'][0]['url']==payload['url']
        store.finish(job_id,scan)
        snapshot=store.job(job_id)
        selected=selected_download_payloads(snapshot,[0])
        assert selected[0]['engine']=='gallery'
        assert selected[0]['url']==payload['url']
        result=execute_download_job(store,{'kind':'download','payload':selected[0]},
                                    lambda _:None,Event())
        assert result['count']==1 and Path(result['files'][0]['path']).is_file()
        image_path=Path(result['files'][0]['path'])
        assert image_path.read_bytes().startswith(b'\x89PNG')

        # Make the existing good file's timestamp unambiguously older than the
        # repeat attempt, so a silent overwrite is detected even for identical bytes.
        import os
        before_bytes=image_path.read_bytes()
        before_stat=image_path.stat()
        old_mtime=max(1,before_stat.st_mtime_ns-60_000_000_000)
        os.utime(image_path,ns=(before_stat.st_atime_ns,old_mtime))
        before_stat=image_path.stat()

        repeated=execute_download_job(store,{'kind':'download','payload':selected[0]},
                                      lambda _:None,Event())
        assert repeated['count']==1
        assert Path(repeated['files'][0]['path'])==image_path
        assert image_path.read_bytes()==before_bytes
        assert image_path.stat().st_mtime_ns==before_stat.st_mtime_ns
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)


def test_flat_playlist_entries_can_be_selected_only_for_recognized_stable_ids():
    from fonesi_edit.downloads import scan_video_item_url
    assert scan_video_item_url({'_type':'url','ie_key':'Youtube',
        'id':'AbcDef123_-','url':'AbcDef123_-'}) == \
        'https://www.youtube.com/watch?v=AbcDef123_-'
    assert scan_video_item_url({'_type':'url','ie_key':'BiliBili',
        'id':'BV1ab2345c6d','url':'BV1ab2345c6d'}) == \
        'https://www.bilibili.com/video/BV1ab2345c6d'
    assert scan_video_item_url({'_type':'url','ie_key':'UnverifiedIE',
        'id':'AbcDef123_-','url':'AbcDef123_-'}) is None
    assert scan_video_item_url({'_type':'url','ie_key':'Youtube',
        'id':'wrong.id','url':'wrong.id'}) is None
    assert scan_video_item_url({'_type':'url','ie_key':'Youtube',
        'id':'AbcDef123_-','url':'https://cdn.example.test/m?token=private'}) == \
        'https://www.youtube.com/watch?v=AbcDef123_-'


def test_mixed_source_scan_preserves_each_item_extractor_and_account_scope():
    from fonesi_edit.downloads import selected_download_payloads
    original={'url':'https://www.facebook.com/page',
              'media':'both','engine':'auto','account_ref':'binding-facebook',
              'expected_identity':'user-123','folder':'D:/media'}
    scan={'kind':'scan','state':'succeeded','payload':original,
          'result':{'platform':'Facebook','items':[
              {'id':'v1','kind':'video','engine':'video',
               'url':'https://www.facebook.com/watch/123','selectable':True},
              {'id':'v2','kind':'videos','engine':'gallery',
               'url':'https://www.facebook.com/posts/456','selectable':True},
              {'id':'i1','kind':'images','engine':'gallery',
               'url':'https://www.facebook.com/photo/789','selectable':True},
          ]}}
    requests=selected_download_payloads(scan,[0,1,2])
    assert [p['engine'] for p in requests]==['video','gallery','gallery']
    assert [p['media'] for p in requests]==['videos','videos','images']
    assert all(p['account_ref']=='binding-facebook' for p in requests)
    assert all(p['expected_identity']=='user-123' for p in requests)
    scan['result']['items'][1]['engine']='invalid'
    with pytest.raises(ValueError,match='adapter'):
        selected_download_payloads(scan,[1])


def test_duplicate_scanned_urls_cannot_enqueue_two_jobs_for_same_item():
    from fonesi_edit.downloads import selected_download_payloads
    url='https://example.test/media/repeated.png'
    scan={'kind':'scan','state':'succeeded',
          'payload':{'url':'https://example.test/gallery','folder':'D:/output'},
          'result':{'platform':'Generic','items':[
              {'kind':'images','url':url,'id':'first','selectable':True},
              {'kind':'images','url':url,'id':'repeated','selectable':True},
          ]}}
    with pytest.raises(ValueError,match='URL lặp'):
        selected_download_payloads(scan,[0,1])
    assert len(selected_download_payloads(scan,[0]))==1
