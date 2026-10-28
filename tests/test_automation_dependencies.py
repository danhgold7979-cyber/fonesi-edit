import hashlib
import os
import zipfile
from pathlib import Path
import pytest
from fonesi_edit.automation import submit_once,Automation,recommended_parallel
from fonesi_edit.dependencies import extract_zip,install
from fonesi_edit.domain import Composition
from fonesi_edit.storage import Store
from fonesi_edit.prototypes.media import create_fixture


def test_submit_once_and_watcher_are_idempotent(tmp_path):
    store=Store(tmp_path/'state.db')
    first=submit_once(store,'scan',{'url':'https://example.invalid'},'same')
    assert submit_once(store,'scan',{'url':'https://example.invalid'},'same')==first
    with pytest.raises(ValueError):submit_once(store,'scan',{'password':'never store'},'secret')
    files=create_fixture(tmp_path/'watch/videos',duration=.5)
    store.set_setting('watches',[{'folder':str(tmp_path/'watch'),'preset':Composition(width=320,height=180).to_dict()}])
    auto=Automation(store);auto.watch();auto.watch();auto.watch()
    assert sum(j['kind']=='render' for j in store.jobs())==1


def test_low_resources_stop_admission_without_fake_gpu():
    data={'ram_available':100,'disk_free':10**10,'cores':16}
    assert recommended_parallel(data)==0
    data['ram_available']=8*1024**3
    assert recommended_parallel(data,'quiet')==1 and recommended_parallel(data,'balanced')==2
    data['cpu_percent']=99;assert recommended_parallel(data)==0


def test_archive_traversal_and_bad_hash_never_activate(tmp_path):
    archive=tmp_path/'evil.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape','bad')
    with pytest.raises(ValueError):extract_zip(archive,tmp_path/'unpack')
    assert not (tmp_path/'escape').exists()
    store=Store(tmp_path/'state.db')
    manifest={'name':'ffmpeg','version':'test','url':'https://example.invalid/tool','sha256':'0'*64,'executable':'ffmpeg'}
    def fetch(url,path,*args):path.write_bytes(b'invalid')
    with pytest.raises(ValueError,match='SHA256'):install(store,manifest,fetch=fetch)
    assert not store.setting('tool_paths',{})


@pytest.mark.skipif(os.name=='nt',reason='POSIX fixture tool; Windows installer requires native acceptance')
def test_verified_fixture_tool_install_is_versioned_repeatable_and_not_system_wide(tmp_path):
    store=Store(tmp_path/'state.db');body=b'#!/bin/sh\nprintf "fixture-tool 1\\n"\n'
    manifest={'name':'fixture-tool','version':'1','url':'https://example.invalid/tool','sha256':hashlib.sha256(body).hexdigest(),'executable':'fixture-tool'}
    def fetch(url,path,*args):path.write_bytes(body)
    first=install(store,manifest,fetch=fetch);second=install(store,manifest,fetch=fetch)
    assert first==second and Path(first['path']).is_file()
    assert str(tmp_path) in first['path']
    original=Path(first['path']);original.write_bytes(b'broken, must remain untouched')
    repaired=install(store,manifest,fetch=fetch)
    assert repaired['path']!=first['path'] and original.read_bytes()==b'broken, must remain untouched'
    assert Path(repaired['path']).read_bytes()==body


def test_download_workflow_translates_subtitle_layers_once_then_waits_for_translation(tmp_path):
    from fonesi_edit.domain import Layer
    f=create_fixture(tmp_path/'channel/videos',duration=.5);source=f['source'];sub=source.with_suffix('.srt');sub.write_text('1\n00:00:00,000 --> 00:00:00,400\nSource\n')
    store=Store(tmp_path/'state.db');preset=Composition(layers=[Layer(kind='subtitle',path='stale.srt')])
    download=store.submit('download',{'workflow':{'preset':preset.to_dict(),'translate':True,'language':'vi'}})
    store.finish(download,{'files':[{'kind':'video','path':str(source)}]})
    auto=Automation(store);auto.completed_downloads();auto.completed_downloads()
    assert len(store.jobs())==3
    render=next(j for j in store.jobs() if j['kind']=='render');translation=next(j for j in store.jobs() if j['kind']=='translate')
    assert render['payload']['composition']['layers'][0]['path']==translation['payload']['output']
    assert translation['id'] in render['depends_on']


def test_invalid_resource_profile_does_not_default_to_maximum():
    data={'ram_available':8*1024**3,'disk_free':10**10,'cores':16,'cpu_percent':1}
    with pytest.raises(ValueError,match='Unknown resource profile'):
        recommended_parallel(data,'maax')


def test_gpu_sampler_drops_stale_data_when_binary_missing(monkeypatch):
    import fonesi_edit.automation as module
    original=dict(module._GPU)
    try:
        module._GPU.update({'data':[{'name':'stale-GPU'}],'busy':True,'checked':0})
        monkeypatch.setattr(module.shutil,'which',lambda _:None)
        module.update_gpu()
        assert module._GPU['data'] is None
        assert module._GPU['busy'] is False
        assert module._GPU['checked']>0
    finally:
        module._GPU.clear();module._GPU.update(original)


def test_automation_error_reports_are_sanitized(tmp_path):
    store=Store(tmp_path/'state.db')
    automation=Automation(store)
    def fail():
        raise RuntimeError('HTTP 403 https://example.test/a?token=private Authorization: Bearer hidden-secret')
    automation.tick=fail
    class TwoSteps:
        def __init__(self):self.calls=0
        def wait(self,seconds):
            self.calls+=1
            return self.calls>1
    automation.stop_event=TwoSteps()
    automation.loop()
    assert len(automation.errors)==1
    assert 'HTTP 403' in automation.errors[0]
    assert 'private' not in automation.errors[0]
    assert 'hidden-secret' not in automation.errors[0]
