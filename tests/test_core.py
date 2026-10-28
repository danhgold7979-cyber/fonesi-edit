from fractions import Fraction
from pathlib import Path
import json
import sys
import time
import pytest
from fonesi_edit.core.model import *
from fonesi_edit.core.paths import *
from fonesi_edit.core.process import run, Cancelled, ProcessFailure, redact
from fonesi_edit.core.storage import Store, save_project, load_project
from fonesi_edit.services.media import inspect_asset, validate_media, validate_image


def test_time_map_clips_before_mapping():
    m=TimeMap(2*US,8*US,'3/2',US)
    assert m.duration==4*US
    assert m.interval(0,3*US)==(US,round(Fraction(5*US,3)))
    assert m.interval(8*US,9*US) is None

@pytest.mark.parametrize('args',[(0,0,'1'),(-1,10,'1'),(0,10,'0'),(0,10,'-1')])
def test_invalid_time_map(args):
    with pytest.raises(ValueError):TimeMap(*args)


def test_project_roundtrip_command_gesture(tmp_path):
    p=Project(layers=[Layer()]); h=CommandHistory(p)
    h.begin()
    for x in range(30):p.layers[0].x=x/100
    h.commit('drag');assert len(h.undo_items)==1
    h.undo();assert p.layers[0].x==.1
    h.redo();assert p.layers[0].x==.29
    h.begin();p.layers[0].x=.8;h.cancel();assert p.layers[0].x==.29
    file=tmp_path/'dự án.json';save_project(p,file);assert load_project(file).to_dict()==p.to_dict()
    save_project(p,file);assert file.with_suffix('.json.bak').exists()


def test_unsupported_schema_and_secret_are_rejected(tmp_path):
    p=Project().to_dict();p['settings']['api_key']='secret'
    with pytest.raises(ValueError):Project.from_dict(p)
    p=Project().to_dict();p['schema_version']=99
    with pytest.raises(ValueError):Project.from_dict(p)


def test_auto_respects_overrides_locks():
    result,changed=apply_auto({'x':1,'y':2,'z':3},{'x':8,'y':8,'z':8},{'x'},{'y'})
    assert result=={'x':1,'y':2,'z':8};assert changed==['z']


def test_output_collision_is_never_overwritten(tmp_path):
    target=tmp_path/'out.mp4';target.write_bytes(b'old')
    temp=tmp_path/'x.part';temp.write_bytes(b'new')
    out=publish_no_clobber(temp,target)
    assert target.read_bytes()==b'old';assert out.read_bytes()==b'new';assert not temp.exists()


def test_paths_unicode_reserved_and_renamed_channel(tmp_path):
    assert safe_name('CON.txt').startswith('_');assert '/' not in safe_name('../a')
    old=channel_directory(tmp_path,'yt','Tên cũ','123');old.mkdir(parents=True)
    assert channel_directory(tmp_path,'yt','Tên mới','123')==old
    assert not contained(tmp_path/'../outside',tmp_path)


def test_queue_snapshot_dedupe_dependencies_and_lease(tmp_path):
    s=Store(tmp_path/'state.db');snapshot={'x':[1]}
    a=s.enqueue('test',snapshot,dedupe_key='a');snapshot['x'][0]=9
    assert json.loads(s.get(a)['snapshot'])=={'x':[1]}
    assert s.enqueue('test',{},dedupe_key='a')==a
    b=s.enqueue('test',{},dependencies=[(a,False)])
    claim=s.claim('worker');assert claim['id']==a
    assert s.claim('other') is None
    with pytest.raises(ValueError):s.finish(a,'worker','succeeded',result={})
    s.finish(a,'worker','succeeded',result={'validated':True})
    assert s.claim('other')['id']==b
    assert s.recover(time.time()+60)==[b]
    assert s.get(a)['state']=='succeeded';assert s.get(b)['state']=='interrupted'
    s.retry(b);assert s.get(b)['state']=='pending'


def test_failed_dependency_can_be_allowed(tmp_path):
    s=Store(tmp_path/'s.db');a=s.enqueue('download',{});b=s.enqueue('batch',{},dependencies=[(a,True)])
    assert s.claim('x')['id']==a;s.finish(a,'x','failed',error='bad media')
    assert s.claim('y')['id']==b


def test_cache_account_scoped_and_cancel_pending(tmp_path):
    s=Store(tmp_path/'s.db');s.cache_put('A','item',{'private':1})
    assert s.cache_get('B','item') is None
    j=s.enqueue('test',{});s.cancel(j);assert s.get(j)['state']=='canceled';assert s.claim('x') is None


def test_process_failure_timeout_cancel_and_redaction():
    assert run([sys.executable,'-c','print("ok")']).strip()=='ok'
    with pytest.raises(ProcessFailure):run([sys.executable,'-c','raise SystemExit(4)'])
    with pytest.raises(TimeoutError):run([sys.executable,'-c','import time;time.sleep(5)'],timeout=.1)
    with pytest.raises(Cancelled):run([sys.executable,'-c','import time;time.sleep(5)'],cancel=lambda:True)
    assert 'secret' not in redact('api_key=secret Bearer secret https://x/?token=secret')


def test_actual_media_validation_and_source_unchanged(media):
    before=content_hash(media);a=inspect_asset(media)
    assert a.width==320 and a.has_audio and a.duration==1200000
    result=validate_media(media,duration=1200000,audio=True)
    assert result['validated'] and content_hash(media)==before
    with pytest.raises(ValueError):validate_media(media,duration=3000000)


def test_corrupt_media_never_validated(tmp_path):
    p=tmp_path/'bad.mp4';p.write_bytes(b'not media')
    with pytest.raises(ProcessFailure):validate_media(p)
    with pytest.raises(Exception):validate_image(p)


def test_keyframe_independent_fps_and_zoom():
    l=Layer(keyframes={'x':[Keyframe(0,.1),Keyframe(US,.9)]})
    assert l.at(US//2)['x']==.5
    assert l.at(US)['x']==.9
