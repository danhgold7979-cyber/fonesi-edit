"""Repeat-scan new-only synchronization, without live provider access."""
from pathlib import Path
import json
import shutil
import pytest

from fonesi_edit.downloads import selected_download_payloads
from fonesi_edit.sync import plan_new_only_sync
from fonesi_edit.storage import Store
from fonesi_edit.prototypes.media import create_fixture

OLD = 'https://example.test/video/old'
NEW = 'https://example.test/video/new'


def scan_snapshot(folder, urls=(OLD, NEW), **overrides):
    payload={'url':'https://example.test/channel','folder':str(folder),
             'engine':'video','media':'videos','limit':10,
             'account_ref':None,'expected_identity':None,**overrides}
    items=[{'id':url.rsplit('/',1)[-1], 'title':url.rsplit('/',1)[-1],
            'kind':'video','engine':'video','url':url,'selectable':True}
           for url in urls]
    return {'kind':'scan','state':'succeeded','payload':payload,
            'result':{'platform':'Generic','items':items,'complete':None}}


def finish_video(store, payload, file):
    jid=store.submit('download',payload)
    store.claim(allowed={'download'})
    store.finish(jid,{'platform':'Generic','files':[{
        'path':str(file),'id':'video-id','kind':'video'}],'count':1})
    return jid


def test_second_scan_skips_verified_old_video_and_plans_only_new(tmp_path):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'tải 中文'
    existing=root/'Generic'/'Creator__id'/'videos'/'old.mp4'
    existing.parent.mkdir(parents=True)
    shutil.copyfile(fixture['source'],existing)
    store=Store(tmp_path/'state.db')
    first=scan_snapshot(root,(OLD,))
    finish_video(store,selected_download_payloads(first,[0])[0],existing)
    second=scan_snapshot(root)
    plan=plan_new_only_sync(second,[0,1],store.download_jobs_for_urls([OLD,NEW]))
    assert plan['already_valid']==1 and plan['already_queued']==0
    assert len(plan['payloads'])==1 and plan['payloads'][0]['url']==NEW
    assert existing.read_bytes()==fixture['source'].read_bytes()
    assert second['result']['complete'] is None


@pytest.mark.parametrize('failure',['missing','corrupt','wrong-path'])
def test_corrupt_or_missing_successful_media_aborts_entire_sync(tmp_path,failure):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'media'
    existing=root/'Generic'/'Creator__id'/'videos'/'old.mp4'
    existing.parent.mkdir(parents=True)
    shutil.copyfile(fixture['source'],existing)
    store=Store(tmp_path/'state.db')
    scan=scan_snapshot(root)
    req=selected_download_payloads(scan,[0])[0]
    jid=finish_video(store,req,existing)
    if failure=='missing':
        existing.unlink()
    elif failure=='corrupt':
        existing.write_bytes(b'corrupt')
    else:
        foreign=root.parent/'foreign.mp4'
        shutil.copyfile(existing,foreign)
        with store.connect() as conn:
            conn.execute("UPDATE jobs SET result=? WHERE id=?",(
                json.dumps({'platform':'Generic','files':[{
                    'kind':'video','path':str(foreign)}]}), jid))
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        plan_new_only_sync(scan,[0,1],store.download_jobs_for_urls([OLD,NEW]))
    assert not [j for j in store.jobs() if j['payload'].get('url')==NEW
                and j['kind']=='download']


@pytest.mark.parametrize('state',['pending','running','failed','canceled','blocked'])
def test_history_states_are_not_silently_redownloaded(tmp_path,state):
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(tmp_path/'out',(OLD,))
    jid=store.submit('download',selected_download_payloads(scan,[0])[0])
    if state=='running':store.claim(allowed={'download'})
    elif state=='failed':store.fail(jid,'failure')
    elif state=='canceled':store.cancel(jid)
    elif state=='blocked':store.fail(jid,'configuration',blocked=True)
    history=store.download_jobs_for_urls([OLD])
    if state in ('pending','running'):
        plan=plan_new_only_sync(scan,[0],history)
        assert plan['already_queued']==1 and not plan['payloads']
    else:
        with pytest.raises(ValueError,match='Retry'):
            plan_new_only_sync(scan,[0],history)


@pytest.mark.parametrize('changed',[
    {'engine':'gallery'}, {'media':'images'},
    {'account_ref':'other'}, {'expected_identity':'different'},
])
def test_repeated_url_different_adapter_or_account_is_blocked(tmp_path,changed):
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(tmp_path/'out',(OLD,))
    old=selected_download_payloads(scan,[0])[0]
    store.submit('download',{**old,**changed})
    with pytest.raises(PermissionError,match='adapter/tài khoản'):
        plan_new_only_sync(scan,[0],store.download_jobs_for_urls([OLD]))


def test_subtitle_and_quality_jobs_do_not_mark_media_downloaded(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(tmp_path/'out',(OLD,))
    payload=selected_download_payloads(scan,[0])[0]
    for mode in ('subtitles_only','quality_upgrade'):
        store.submit('download',{**payload,'download_mode':mode})
    plan=plan_new_only_sync(scan,[0],store.download_jobs_for_urls([OLD]))
    assert len(plan['payloads'])==1 and plan['already_valid']==0


def test_sqlite_sync_history_does_not_truncate_after_2000_jobs(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(tmp_path/'out',(OLD,))
    old=store.submit('download',selected_download_payloads(scan,[0])[0])
    with store.connect() as conn:
        payload=json.dumps({'url':'https://example.test/unrelated'})
        rows=[(f'unrelated-{i}','download','pending',payload,
               float(i+100),float(i+100),'[]') for i in range(2050)]
        conn.executemany("INSERT INTO jobs(id,kind,state,payload,created,updated,depends_on) VALUES(?,?,?,?,?,?,?)",rows)
    # The matching job is *older* than every filler and absent from the usual UI cap.
    with store.connect() as conn:
        conn.execute("UPDATE jobs SET created=0 WHERE id=?", (old,))
    assert len(store.jobs(limit=2000))==2000
    assert old not in {j['id'] for j in store.jobs(limit=2000)}
    assert [j['id'] for j in store.download_jobs_for_urls([OLD])]==[old]
    assert store.download_jobs_for_urls([])==[]
    with pytest.raises(ValueError,match='500'):
        store.download_jobs_for_urls([f'https://example.test/{i}' for i in range(501)])
    with pytest.raises(ValueError):
        store.download_jobs_for_urls([False])


def test_gallery_image_must_still_decode_before_being_skipped(tmp_path):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'out'
    image=root/'Generic'/'Creator__id'/'images'/'cover.png'
    image.parent.mkdir(parents=True)
    shutil.copyfile(fixture['logo'],image)
    scan={'kind':'scan','state':'succeeded',
          'payload':{'url':'https://example.test/gallery','folder':str(root),
                     'engine':'gallery','media':'images'},
          'result':{'platform':'Generic','items':[{
              'id':'cover','kind':'images','engine':'gallery',
              'url':'https://example.test/cover','selectable':True}]}}
    store=Store(tmp_path/'db.sqlite')
    req=selected_download_payloads(scan,[0])[0]
    jid=store.submit('download',req)
    store.claim(allowed={'download'})
    store.finish(jid,{'platform':'Generic','files':[{
        'kind':'images','path':str(image),'id':'cover'}]})
    assert plan_new_only_sync(scan,[0],store.download_jobs_for_urls([req['url']]))['already_valid']==1
    image.write_bytes(b'not an image')
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        plan_new_only_sync(scan,[0],store.download_jobs_for_urls([req['url']]))




def test_media_job_symlink_is_not_accepted_as_existing_download(tmp_path,monkeypatch):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'output'
    media=root/'Generic'/'Creator__id'/'videos'/'original.mp4'
    media.parent.mkdir(parents=True)
    shutil.copyfile(fixture['source'],media)
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(root,(OLD,))
    finish_video(store,selected_download_payloads(scan,[0])[0],media)
    original=Path.is_symlink
    monkeypatch.setattr(Path,'is_symlink',
                        lambda path: True if path==media else original(path))
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        plan_new_only_sync(scan,[0],store.download_jobs_for_urls([OLD]))


def test_existing_media_rejects_symlinked_channel_directory(tmp_path,monkeypatch):
    """A symlink in the directory chain must not masquerade as valid history."""
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    root=tmp_path/'out'
    file=root/'Generic'/'Creator__id'/'videos'/'old.mp4'
    file.parent.mkdir(parents=True)
    shutil.copyfile(fixture['source'],file)
    store=Store(tmp_path/'db.sqlite')
    scan=scan_snapshot(root,(OLD,))
    finish_video(store,selected_download_payloads(scan,[0])[0],file)
    actual_is_symlink=Path.is_symlink
    channel=file.parent.parent
    monkeypatch.setattr(Path,'is_symlink',
        lambda path: path==channel or actual_is_symlink(path))
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        plan_new_only_sync(scan,[0],store.download_jobs_for_urls([OLD]))
    assert file.read_bytes()==fixture['source'].read_bytes()
