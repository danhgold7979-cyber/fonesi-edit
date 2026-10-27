import sqlite3
import time
import pytest
from fonesi_edit.domain import Composition, Layer
from fonesi_edit.jobs import Scheduler
from fonesi_edit.storage import Store
from fonesi_edit.prototypes.media import create_fixture, probe


def test_snapshot_is_immutable_claim_is_exclusive_and_secrets_rejected(tmp_path):
    store = Store(tmp_path / 'state.db')
    payload = {'source': 'a', 'settings': {'title': 'old'}}
    job = store.submit('render', payload)
    payload['settings']['title'] = 'new'
    assert store.job(job)['payload']['settings']['title'] == 'old'
    assert store.claim()['id'] == job
    assert Store(store.path).claim() is None
    with pytest.raises(ValueError):
        store.submit('render', {'nested': {'api_key': 'never save'}})


def test_recovery_dependencies_cancel_retry_and_backup(tmp_path):
    store = Store(tmp_path / 'state.db')
    first = store.submit('scan', {})
    second = store.submit('download', {}, depends_on=[first])
    assert store.claim()['id'] == first
    assert store.claim() is None
    assert store.recover(stale_seconds=-1) == 1
    assert store.claim()['id'] == first
    store.finish(first, {'items': []})
    assert store.claim()['id'] == second
    store.cancel(second)
    store.fail(second, 'canceled')
    assert store.job(second)['state'] == 'canceled'
    store.retry(second)
    assert store.job(second)['state'] == 'pending'
    store.backup(tmp_path / 'backup.db')
    assert Store(tmp_path / 'backup.db').job(first)['state'] == 'succeeded'


def test_unknown_newer_schema_is_not_modified(tmp_path):
    path = tmp_path / 'state.db'
    with sqlite3.connect(path) as conn:
        conn.execute('PRAGMA user_version=99')
    with pytest.raises(ValueError):
        Store(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute('PRAGMA user_version').fetchone()[0] == 99


def test_real_render_runs_in_independent_worker_and_survives_store_reopen(tmp_path):
    source = create_fixture(tmp_path / 'media', duration=0.5)['source']
    output = tmp_path / 'out.mp4'
    store = Store(tmp_path / 'state.db')
    job_id = store.submit('render', {'source': str(source), 'output': str(output)})
    scheduler = Scheduler(store)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        scheduler.tick()
        if store.job(job_id)['state'] in {'succeeded', 'failed'} and not scheduler.active:
            break
        time.sleep(0.05)
    result = Store(store.path).job(job_id)
    assert result['state'] == 'succeeded', result['error']
    assert result['result']['validated'] and probe(output).duration > 0


def test_composition_round_trip_and_invalid_keyframes():
    composition = Composition(layers=[Layer(text='Tiếng Việt 中文')])
    assert Composition.from_dict(composition.to_dict()).to_dict() == composition.to_dict()
    composition.layers[0].keyframes = {'x': [{'time': 2, 'value': 1}, {'time': 1, 'value': 0}]}
    with pytest.raises(ValueError):
        composition.validate()
