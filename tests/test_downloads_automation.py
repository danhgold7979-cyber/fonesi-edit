from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
from PIL import Image
import pytest
from fonesi_edit.core.storage import Store
from fonesi_edit.services.downloads import *
from fonesi_edit.services.browser import *
from fonesi_edit.services.tools import *
from fonesi_edit.services.automation import *


def test_platform_normalize_dedupe_and_credentials():
    urls=identify_many('https://www.youtube.com/watch?v=abc&utm_source=x\nhttps://www.youtube.com/watch?v=abc')
    assert len(urls)==1 and urls[0]['platform']=='YouTube'
    with pytest.raises(ValueError):identify('https://user:pass@youtube.com/watch?v=a')
    with pytest.raises(ValueError):identify('https://youtube.com.evil.test/a')
    assert len(PLATFORMS)==10


def test_real_localhost_video_image_download_and_validate(media,tmp_path):
    image=tmp_path/'photo.png';Image.new('RGB',(16,12),'red').save(image)
    handler=partial(SimpleHTTPRequestHandler,directory=str(tmp_path));server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    from urllib.parse import quote
    try:
        for source,kind in [(media,'video'),(image,'image')]:
            result=download({'url':f'http://127.0.0.1:{server.server_port}/'+quote(source.name),'output_root':str(tmp_path/'downloads'),'media_kind':kind})
            assert result['validated'] and Path(result['path']).exists();assert result['evidence_scope']=='localhost transport only'
    finally:server.shutdown();server.server_close();thread.join()


def test_authenticated_download_never_public_fallback(tmp_path):
    with pytest.raises(ValueError,match='no public fallback'):download({'url':'https://youtube.com/watch?v=a','binding_id':'selected','output_root':str(tmp_path)})


def test_profiles_bindings_identity_scoped_and_unlink_preserves_data(tmp_path):
    store=Store(tmp_path/'s.db');manager=BrowserManager(tmp_path/'profiles',store);a=manager.create_profile('A');b=manager.create_profile('B')
    assert a!=b;facebook=manager.bind('Facebook',a);manager.bind('TikTok',a);manager.bind('Facebook',b)
    with pytest.raises(ValueError):manager.bind('Facebook',a)
    with pytest.raises(ValueError,match='not verified'):manager.preflight(facebook)
    binding=store.objects('account_binding')[facebook];binding.update(identity='A',web_state='verified',bridge_state='verified',source_state='verified');store.put('account_binding',facebook,binding)
    with pytest.raises(ValueError,match='mismatch'):manager.preflight(facebook,'B')
    assert manager.preflight(facebook,'A')['ready'];manager.unlink(facebook);assert Path(store.objects('browser_profile')[a]['path']).exists()


def test_tool_explicit_invalid_no_fallback_and_manifest_gate(tmp_path):
    assert inspect_tool('ffmpeg',str(tmp_path/'missing')).state=='invalid_path'
    manager=ToolManager(tmp_path/'tools',Store(tmp_path/'s.db'))
    with pytest.raises(ValueError,match='trusted pinned hash'):manager.install({'url':'https://example.invalid'},trusted_manifest_hash='0'*64)


def test_tool_lease_does_not_modify_previous_binary_and_rollback(tmp_path):
    s=Store(tmp_path/'s.db');m=ToolManager(tmp_path/'tools',s)
    for version in ['1','2']:s.put('tool_installation','ffmpeg:'+version,{'verified':True,'path':str(tmp_path/version)})
    m.activate('ffmpeg','1');m.lease('ffmpeg','1','job');m.activate('ffmpeg','2')
    assert s.objects('tool_lease')['job:ffmpeg']['version']=='1'
    m.rollback('ffmpeg');assert s.objects('tool_active')['ffmpeg']['version']=='1';m.release('job');assert not s.objects('tool_lease')


def test_watcher_stable_changed_no_loop(tmp_path):
    source=tmp_path/'source';source.mkdir();out=tmp_path/'output';out.mkdir();p=source/'a.mp4';p.write_bytes(b'1');(out/'b.mp4').write_bytes(b'2')
    w=StableWatcher([tmp_path],[out],stable_seconds=2)
    assert not w.poll(0);assert not w.poll(1);assert w.poll(2)==[p];assert not w.poll(3)
    p.write_bytes(b'changed');assert not w.poll(4);assert w.poll(6)==[p]


def test_schedule_no_overlap_missed_and_cache_safety(tmp_path):
    s=Store(tmp_path/'s.db');schedule=Schedule(s);schedule.add('x',10,{'source':'a'})
    item=s.objects('schedule')['x'];now=item['next']+1
    assert schedule.due(now)==[('x',{'source':'a'})];assert not schedule.due(now+20);schedule.finish('x');assert schedule.due(now+20)
    cache=tmp_path/'cache';cache.mkdir();(cache/'a').write_bytes(b'123')
    with pytest.raises(ValueError):cleanup_cache(cache,0)
    (cache/'.fonesi-cache').write_text('owned-cache-v1');assert cleanup_cache(cache,0,leased=[cache/'a'])==[]
    assert len(cleanup_cache(cache,0))==1


def test_resource_unknown_and_admission(tmp_path,monkeypatch):
    monkeypatch.setattr('fonesi_edit.services.automation.measure',lambda root:{'available_ram':1,'free_disk':10**12})
    assert not ResourcePolicy().admission(tmp_path)[0]
