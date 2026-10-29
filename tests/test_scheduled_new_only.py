"""P05/P10 scheduled scan-first sync: bounded synthetic reconciliation.

No live providers, account credentials or paid APIs are contacted.
"""
import json
import shutil
from pathlib import Path

import pytest

from fonesi_edit.automation import Automation
from fonesi_edit.domain import canonical
from fonesi_edit.storage import Store
from fonesi_edit.sync import selectable_sync_indices
from fonesi_edit.prototypes.media import create_fixture


OLD='https://example.test/video/old'
NEW='https://example.test/video/new'
CHANNEL='https://example.test/channel'


def put_schedule(store, folder, *, mode='scan_new_only', limit=0,
                 account_ref=None, expected_identity=None):
    payload={'url':CHANNEL,'folder':str(folder),'engine':'video',
             'media':'videos','limit':limit,'account_ref':account_ref,
             'expected_identity':expected_identity}
    body={'payload':payload,'interval':60}
    if mode is not None:
        body['mode']=mode
    with store.connect() as conn:
        conn.execute('INSERT INTO schedules(id,data,next_run) VALUES(?,?,?)',
                     ('channel-1',canonical(body),0))
    return payload


def items(*urls):
    return [{'id':url.rsplit('/',1)[-1], 'title':url,
             'kind':'video','engine':'video','url':url,'selectable':True}
            for url in urls]


def finish_scan(store, scan_id, entries, complete=None):
    assert store.claim(allowed={'scan'})['id']==scan_id
    store.finish(scan_id,{'platform':'Generic','items':entries,
                          'count':len(entries),'complete':complete})


def put_download(store, folder, url, path):
    payload={'url':url,'folder':str(folder),'engine':'video',
             'media':'videos','limit':1,'account_ref':None}
    job_id=store.submit('download',payload)
    assert store.claim(allowed={'download'})['id']==job_id
    store.finish(job_id,{'platform':'Generic','files':[{
        'id':url.rsplit('/',1)[-1],'kind':'video','path':str(path)}],
        'count':1})
    return job_id


@pytest.mark.parametrize('mode',[None,'scan_new_only'])
def test_scheduled_sync_scans_first_reconciles_old_and_new_idempotently(tmp_path,mode):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    folder=tmp_path/'media'
    old=folder/'Generic'/'Creator__id'/'videos'/'old.mp4'
    old.parent.mkdir(parents=True)
    shutil.copyfile(fixture['source'],old)
    store=Store(tmp_path/'state.db')
    put_download(store,folder,OLD,old)
    put_schedule(store,folder,mode=mode,limit=0)
    auto=Automation(store)
    scheduled=auto.schedules()
    assert len(scheduled)==1
    scan=store.job(scheduled[0])
    assert scan['kind']=='scan' and scan['state']=='pending'
    assert scan['payload']['limit']==100
    assert scan['payload']['sync_schedule_id']=='channel-1'
    assert len([j for j in store.jobs() if j['kind']=='download'])==1
    # The next due slot is not started while the previous scan is pending.
    with store.connect() as conn:
        conn.execute('UPDATE schedules SET next_run=1')
    assert auto.schedules()==[]
    finish_scan(store,scan['id'],items(OLD,NEW),complete=None)
    # A successful but not-yet-reconciled scan cannot be replaced, either.
    assert auto.schedules()==[]
    processed=auto.completed_scheduled_scans()
    assert len(processed)==1
    assert processed[0]['new_jobs']==1
    assert processed[0]['already_valid']==1
    assert processed[0]['complete'] is None
    assert auto.completed_scheduled_scans()==[]
    assert len([j for j in store.jobs() if j['kind']=='download'])==2
    new=next(j for j in store.jobs() if j['kind']=='download'
             and j['payload']['url']==NEW)
    assert new['payload']['engine']=='video'
    assert 'sync_schedule_id' not in new['payload']
    assert store.cached('schedule-synced:'+scan['id'])==processed[0]
    # A following due scan uses a fresh slot, but its results still
    # skip the valid old file and the pending new media job.
    following=auto.schedules()
    assert len(following)==1 and following[0]!=scan['id']
    finish_scan(store,following[0],items(OLD,NEW),complete=False)
    next_result=auto.completed_scheduled_scans()
    assert len(next_result)==1
    assert next_result[0]['new_jobs']==0
    assert next_result[0]['already_valid']==1
    assert next_result[0]['already_queued']==1
    assert next_result[0]['complete'] is False
    assert len([j for j in store.jobs() if j['kind']=='download'])==2


def test_corrupt_existing_download_blocks_entire_schedule_and_recovers_without_duplicates(tmp_path):
    fixture=create_fixture(tmp_path/'fixture',duration=.5)
    folder=tmp_path/'output'
    old=folder/'Generic'/'Creator__id'/'videos'/'old.mp4'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'broken media')
    store=Store(tmp_path/'state.db')
    put_download(store,folder,OLD,old)
    put_schedule(store,folder)
    auto=Automation(store)
    scan=auto.schedules()[0]
    with store.connect() as conn:
        conn.execute('UPDATE schedules SET next_run=1')
    finish_scan(store,scan,items(NEW,OLD),complete=None)
    with pytest.raises(ValueError,match='không còn hợp lệ'):
        auto.completed_scheduled_scans()
    assert not store.cached('schedule-synced:'+scan)
    assert auto.schedules()==[]
    assert len([j for j in store.jobs() if j['kind']=='download'])==1
    # Only a deliberate user correction can unblock the scan.
    shutil.copyfile(fixture['source'],old)
    result=auto.completed_scheduled_scans()
    assert len(result)==1 and result[0]['new_jobs']==1
    assert len([j for j in store.jobs() if j['kind']=='download'])==2


def test_failed_scheduled_scan_is_not_retried_or_rescheduled_silently(tmp_path):
    store=Store(tmp_path/'state.db')
    put_schedule(store,tmp_path/'output',limit=1000)
    auto=Automation(store)
    first=auto.schedules()[0]
    assert store.job(first)['payload']['limit']==200
    store.fail(first,'provider challenge, manual login required')
    with store.connect() as conn:
        conn.execute('UPDATE schedules SET next_run=1')
    assert auto.schedules()==[]
    assert len([j for j in store.jobs() if j['kind']=='scan'])==1
    store.retry(first)
    finish_scan(store,first,[],complete=None)
    result=auto.completed_scheduled_scans()
    assert len(result)==1 and result[0]['new_jobs']==0
    assert auto.schedules() and len([j for j in store.jobs() if j['kind']=='scan'])==2


def test_schedule_rejects_unknown_mode_without_starting_download(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    put_schedule(store,tmp_path/'output',mode='unsafe_download_channel')
    with pytest.raises(ValueError,match='Chỉ hỗ trợ lịch'):
        Automation(store).schedules()
    assert store.jobs()==[]


def test_scheduled_scan_uses_exact_account_and_rejects_cross_host(tmp_path):
    folder=tmp_path/'output'
    store=Store(tmp_path/'db.sqlite')
    put_schedule(store,folder,account_ref='browser-a',expected_identity='person-a')
    auto=Automation(store)
    scan=auto.schedules()[0]
    frozen=store.job(scan)['payload']
    assert frozen['account_ref']=='browser-a'
    assert frozen['expected_identity']=='person-a'
    finish_scan(store,scan,items(NEW),complete=None)
    outputs=auto.completed_scheduled_scans()
    assert outputs[0]['new_jobs']==1
    media=next(j for j in store.jobs() if j['kind']=='download')
    assert media['payload']['account_ref']=='browser-a'
    assert media['payload']['expected_identity']=='person-a'
    assert media['payload']['url']==NEW
    assert not media['payload'].get('sync_schedule_id')


def test_scheduled_scan_oversized_results_are_not_partially_enqueued(tmp_path):
    store=Store(tmp_path/'db.sqlite')
    put_schedule(store,tmp_path/'output')
    auto=Automation(store)
    scan=auto.schedules()[0]
    huge=items(*(f'https://example.test/video/{i}' for i in range(501)))
    finish_scan(store,scan,huge,complete=False)
    with pytest.raises(ValueError,match='500'):
        auto.completed_scheduled_scans()
    assert not store.cached('schedule-synced:'+scan)
    assert not [j for j in store.jobs() if j['kind']=='download']


def test_scheduled_safe_index_dedup_preserves_later_selectable_row():
    data=[{'url':OLD,'selectable':False},
          {'url':OLD,'selectable':True},
          {'url':OLD,'selectable':True},
          {'url':NEW,'selectable':True},
          {'url':'https://example.test/video/secret?token=abc',
           'selectable':True},
          {'url':None,'selectable':True}]
    assert selectable_sync_indices(data)==[1,3]
    with pytest.raises(ValueError,match='Danh sách'):
        selectable_sync_indices(None)
