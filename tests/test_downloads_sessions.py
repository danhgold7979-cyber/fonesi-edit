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
        assert Path(images['files'][0]['path']).is_file()
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
    {'media':'everything'},
    {'limit':-2},
    {'limit':'many'},
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
    class Handler(SimpleHTTPRequestHandler):
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
        from pathlib import Path
        assert Path(result['files'][0]['path']).is_file()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
