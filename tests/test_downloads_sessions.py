from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread,Event
import os
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
        images=execute_download_job(store,{'kind':'download','payload':image_payload},lambda p:None,Event())
        assert images['count']==1 and images['files'][0]['kind']=='images'
        assert Path(images['files'][0]['path']).is_file()
    finally:server.shutdown();server.server_close();thread.join(timeout=3)
