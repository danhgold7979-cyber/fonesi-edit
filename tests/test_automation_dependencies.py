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



def test_watcher_does_not_auto_edit_quality_upgrade_variants(tmp_path):
    """Upgrades are opt-in for Batch/Automation, not duplicate new source media."""
    import shutil
    store=Store(tmp_path/'state.db')
    fixture=create_fixture(tmp_path/'Channel'/'videos',duration=.5)
    original=fixture['source']
    upgrade=tmp_path/'Channel'/'quality-upgrades'/'720p'/'videos'/'high.mp4'
    upgrade.parent.mkdir(parents=True)
    shutil.copyfile(original,upgrade)
    store.set_setting('watches',[{
        'folder':str(tmp_path/'Channel'),
        'preset':Composition(width=320,height=180).to_dict()}])
    auto=Automation(store)
    auto.watch();auto.watch();auto.watch()
    render_jobs=[j for j in store.jobs() if j['kind']=='render']
    assert len(render_jobs)==1
    assert str(original) in render_jobs[0]['payload']['composition']['clips'][0]['path']
    assert upgrade.is_file()


def test_submit_many_once_single_transaction_rollback_and_idempotence(tmp_path):
    """An injected failure on the second INSERT never leaves a partial sync."""
    import sqlite3
    from fonesi_edit.automation import submit_many_once
    store=Store(tmp_path/'batch-state.db')
    old={'url':'https://example.test/first','folder':str(tmp_path/'media'),
         'engine':'video','media':'videos'}
    new={**old,'url':'https://example.test/second'}
    batch=[(old,'sync:first'),(new,'sync:second')]
    with store.connect() as conn:
        conn.execute("""
            CREATE TRIGGER deny_second_sync BEFORE INSERT ON jobs
            WHEN json_extract(NEW.payload,'$.url')='https://example.test/second'
            BEGIN SELECT RAISE(ABORT, 'injected-second-insert'); END
        """)
    with pytest.raises(sqlite3.IntegrityError,match='injected-second-insert'):
        submit_many_once(store,'download',batch)
    assert store.jobs()==[]
    with store.connect() as conn:
        conn.execute('DROP TRIGGER deny_second_sync')
    accepted=submit_many_once(store,'download',batch)
    assert accepted['created']==2 and accepted['existing']==0
    assert len(set(accepted['ids']))==2
    repeated=submit_many_once(store,'download',batch)
    assert repeated['ids']==accepted['ids']
    assert repeated['created']==0 and repeated['existing']==2
    assert len(store.jobs())==2
    with pytest.raises(ValueError,match='snapshot khác'):
        submit_many_once(store,'download',[
            ({**old,'account_ref':'changed-account'},'sync:first'),
            ({**new,'url':'https://example.test/third'},'sync:third')])
    with pytest.raises(ValueError,match='snapshot khác'):
        submit_many_once(store,'scan',[(old,'sync:first')])
    assert len(store.jobs())==2
    assert all(j['kind']=='download' for j in store.jobs())


def test_submit_many_once_rejects_untrusted_and_duplicate_batch_before_writing(tmp_path):
    from fonesi_edit.automation import submit_many_once
    store=Store(tmp_path/'batch-state.db')
    good={'url':'https://example.test/first','folder':str(tmp_path/'media')}
    with pytest.raises(ValueError,match='Secret'):
        submit_many_once(store,'download',[
            (good,'safe'),
            ({'api_key':'do-not-store'},'second')])
    assert store.jobs()==[]
    with pytest.raises(ValueError,match='trùng'):
        submit_many_once(store,'download',[(good,'repeated'),(good,'repeated')])
    with pytest.raises(ValueError,match='500'):
        submit_many_once(store,'download',[(good,str(i)) for i in range(501)])
    assert store.jobs()==[]
