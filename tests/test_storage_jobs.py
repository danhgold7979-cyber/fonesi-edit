import sqlite3
import time
import pytest
from fonesi_edit.domain import Composition, Layer, checked_payload
from fonesi_edit.worker import sanitize_error_message
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


def test_same_queue_cannot_be_managed_by_two_schedulers(tmp_path):
    store=Store(tmp_path/'state.db');first=Scheduler(store)
    with pytest.raises(RuntimeError):Scheduler(store)
    first.shutdown();second=Scheduler(store);second.shutdown()


def test_v1_migration_backs_up_data_before_altering_jobs(tmp_path):
    from fonesi_edit.storage import SCHEMA
    path=tmp_path/'state.db'
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA);conn.execute('PRAGMA user_version=1');conn.execute('INSERT INTO settings VALUES(?,?)',('keep','42'))
    store=Store(path);assert store.setting('keep')==42
    backup=next(tmp_path.glob('state.before-v2-*.db'))
    with sqlite3.connect(backup) as conn:
        assert conn.execute('PRAGMA user_version').fetchone()[0]==1
        assert 'started' not in {r[1] for r in conn.execute('PRAGMA table_info(jobs)')}


def test_orphan_recovered_after_startup_and_live_worker_can_be_excluded(tmp_path):
    store=Store(tmp_path/'state.db');job=store.submit('scan',{});store.claim();scheduler=Scheduler(store);scheduler.paused=True
    with store.connect() as conn:conn.execute('UPDATE jobs SET heartbeat=0 WHERE id=?',(job,))
    assert store.recover(exclude=[job])==0
    scheduler.tick();assert store.job(job)['state']=='pending';scheduler.shutdown()



@pytest.mark.parametrize("secret_key", [
    "api-key",
    "Authorization",
    "session_cookie",
    "clientSecret",
    "refresh-token",
    "bearerToken",
    "ACCESS_TOKEN",
    "passwd",
    "private_key",
    "apiSecret",
    "sessionId",
    "signature",
    "jwtToken",
])
def test_secret_key_aliases_are_rejected_recursively(secret_key):
    with pytest.raises(ValueError, match="Secret values cannot be stored"):
        checked_payload({"nested": [{"safe": "ok", secret_key: "synthetic-secret-value"}]})


def test_worker_error_sanitizer_removes_secrets_but_keeps_diagnostic_context():
    message = (
        "HTTP 403 for https://example.test/media/item?token=query-secret&signature=signed-secret "
        "Authorization: Bearer bearer-secret api-key=api-secret "
        "session_cookie=cookie-secret signature=standalone-signature-secret path=/media/item"
    )
    sanitized = sanitize_error_message(message)

    for secret in (
        "query-secret",
        "signed-secret",
        "bearer-secret",
        "api-secret",
        "cookie-secret",
        "standalone-signature-secret",
    ):
        assert secret not in sanitized
    assert "HTTP 403" in sanitized
    assert "https://example.test/media/item" in sanitized
    assert "path=/media/item" in sanitized


def test_backup_is_validated_published_without_overwrite_and_cleans_temporary_files(tmp_path):
    store = Store(tmp_path / "state.db")
    job_id = store.submit("scan", {"url": "https://example.test/item"})
    store.claim()
    store.finish(job_id, {"items": [{"id": "synthetic-item"}]})

    destination = tmp_path / "nested" / "backups" / "state.db"
    store.backup(destination)
    assert destination.is_file()
    with sqlite3.connect(destination) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT state FROM jobs WHERE id=?", (job_id,)).fetchone()[0] == "succeeded"

    original = destination.read_bytes()
    with pytest.raises(FileExistsError):
        store.backup(destination)
    assert destination.read_bytes() == original
    assert list(destination.parent.glob(".fonesi-backup-*.tmp")) == []


def test_backup_publication_failure_does_not_leave_a_partial_backup(tmp_path, monkeypatch):
    import fonesi_edit.storage as storage_module

    store = Store(tmp_path / "state.db")
    destination = tmp_path / "backup" / "state.db"
    destination.parent.mkdir(parents=True)

    def unsupported_link(*args, **kwargs):
        raise OSError("operation not supported")

    monkeypatch.setattr(storage_module.os, "link", unsupported_link)
    with pytest.raises(RuntimeError, match="hard-link support"):
        store.backup(destination)

    assert not destination.exists()
    assert list(destination.parent.glob(".fonesi-backup-*.tmp")) == []



@pytest.mark.parametrize("blocked,expected",[(False,"failed"),(True,"blocked")])
def test_storage_failure_boundary_redacts_secrets_from_sqlite(tmp_path, blocked, expected):
    store=Store(tmp_path/'state.db')
    job=store.submit('scan',{'url':'https://example.test/source'})
    store.claim()
    error=('HTTP 403 https://example.test/video?token=private-query&signature=private-sign '
           'Authorization: Bearer private-bearer api-key=private-api')
    store.fail(job,error,blocked=blocked)
    row=store.job(job)
    assert row['state']==expected
    assert 'HTTP 403' in row['error']
    for secret in ['private-query','private-sign','private-bearer','private-api']:
        assert secret not in row['error']
    with store.connect() as conn:
        persisted=conn.execute('SELECT error FROM jobs WHERE id=?',(job,)).fetchone()[0]
    assert persisted==row['error']


@pytest.mark.parametrize('failing_pragma',[
    'PRAGMA journal_mode=WAL',
    'PRAGMA busy_timeout=15000',
])
def test_wal_initialization_errors_always_close_sqlite_handles(tmp_path,monkeypatch,failing_pragma):
    """A PRAGMA failure before yield must not leak a Windows database handle."""
    import fonesi_edit.storage as storage_module
    store=Store(tmp_path/'durable-state.db')
    original_connect=storage_module.sqlite3.connect
    created=[]
    class TracedConnection:
        def __init__(self,*args,**kwargs):
            self.inner=original_connect(*args,**kwargs)
            self.close_count=0
            self.rollback_count=0
        @property
        def row_factory(self):
            return self.inner.row_factory
        @row_factory.setter
        def row_factory(self,value):
            self.inner.row_factory=value
        def execute(self,statement,*args):
            if statement==failing_pragma:
                raise sqlite3.OperationalError('synthetic PRAGMA setup failure')
            return self.inner.execute(statement,*args)
        def close(self):
            self.close_count+=1
            self.inner.close()
        def commit(self):
            return self.inner.commit()
        def rollback(self):
            self.rollback_count+=1
            return self.inner.rollback()
    def traced_connect(*args,**kwargs):
        wrapped=TracedConnection(*args,**kwargs)
        created.append(wrapped)
        return wrapped
    with monkeypatch.context() as patch:
        patch.setattr(storage_module.sqlite3,'connect',traced_connect)
        with pytest.raises(sqlite3.OperationalError,match='PRAGMA setup failure'):
            with store.connect():
                pytest.fail('SQLite context must never yield after PRAGMA failure')
    assert len(created)==1
    assert created[0].close_count==1
    assert created[0].rollback_count==0  # No transaction has been entered.
    # A normal connection must remain usable after the injected setup fault.
    store.set_setting('healthy',{'after':'failure'})
    assert store.setting('healthy')=={'after':'failure'}
    with sqlite3.connect(store.path) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_store_connection_rollback_behavior_stays_intact(tmp_path):
    store=Store(tmp_path/'durable-state.db')
    with pytest.raises(RuntimeError,match='synthetic rollback'):
        with store.connect() as conn:
            conn.execute('INSERT INTO settings(key,value) VALUES(?,?)',
                         ('interrupted','42'))
            raise RuntimeError('synthetic rollback')
    assert store.setting('interrupted') is None
    with store.connect() as conn:
        conn.execute('INSERT INTO settings(key,value) VALUES(?,?)',
                     ('committed','42'))
    assert store.setting('committed')==42


@pytest.mark.parametrize("existing", [False, True])
def test_project_selection_and_save_rollback_together_after_sqlite_fault(tmp_path, existing):
    """A failed last_project write must never leave a committed orphan/stale row."""
    store = Store(tmp_path / "state.db")
    project_id = "a" * 32
    initial = {"layers": [{"text": "Bản SQLite cũ"}]}
    if existing:
        store.save_named("projects", "Original", initial, project_id, select_as_last=True)
    before = store.list_named("projects")
    selected_before = store.setting("last_project")
    action = "UPDATE OF value" if existing else "INSERT"
    with store.connect() as conn:
        conn.execute(
            f"CREATE TRIGGER fail_selection BEFORE {action} ON settings "
            "WHEN NEW.key='last_project' BEGIN "
            "SELECT RAISE(ABORT, 'synthetic last_project failure'); END"
        )

    changed = {"layers": [{"text": "Bản mới không được ghi nửa chừng"}]}
    with pytest.raises(sqlite3.DatabaseError, match="synthetic last_project failure"):
        store.save_named("projects", "New", changed, project_id, select_as_last=True)
    # Both row and pointer are exactly the previous committed values.
    assert store.list_named("projects") == before
    assert store.setting("last_project") == selected_before
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    with store.connect() as conn:
        conn.execute("DROP TRIGGER fail_selection")
    assert store.save_named("projects", "New", changed, project_id, select_as_last=True) == project_id
    assert store.setting("last_project") == project_id
    rows = store.list_named("projects")
    assert len(rows) == 1 and rows[0]["id"] == project_id
    assert rows[0]["name"] == "New" and rows[0]["data"] == changed


def test_selected_project_save_is_opt_in_and_presets_cannot_be_selected(tmp_path):
    store = Store(tmp_path / "state.db")
    project = store.save_named("projects", "Unselected", {"a": 1})
    preset = store.save_named("presets", "Keep", {"b": 2})
    assert project != preset and store.setting("last_project") is None
    with pytest.raises(ValueError, match="Only projects"):
        store.save_named("presets", "Rejected", {"b": 3}, select_as_last=True)
    assert [row["id"] for row in store.list_named("presets")] == [preset]
    assert store.setting("last_project") is None

def test_submit_many_sqlite_fault_rolls_back_entire_batch(tmp_path):
    """The second INSERT must not leave the first item pending after a fault."""
    from copy import deepcopy

    store=Store(tmp_path/'state.db')
    store.set_setting('tool_paths',{'ffmpeg':'synthetic-tool-path'})
    prior=store.submit('scan',{})
    payloads=[{'composition':{'name':'first'},'output':'first.mp4'},
              {'composition':{'name':'second'},'output':'second.mp4'}]
    unchanged=deepcopy(payloads)
    with store.connect() as conn:
        conn.execute(
            "CREATE TRIGGER fail_batch_second BEFORE INSERT ON jobs "
            "WHEN instr(NEW.payload,'second.mp4') > 0 BEGIN "
            "SELECT RAISE(ABORT,'synthetic second batch failure'); END")
    with pytest.raises(sqlite3.DatabaseError,match='synthetic second batch failure'):
        store.submit_many('render',payloads)
    assert [j['id'] for j in store.jobs()]==[prior]
    assert payloads==unchanged
    with sqlite3.connect(store.path) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'

    with store.connect() as conn:
        conn.execute('DROP TRIGGER fail_batch_second')
    new=store.submit_many('render',payloads)
    assert len(new)==2 and len(set(new))==2
    assert len(store.jobs())==3
    for index,job_id in enumerate(new):
        job=store.job(job_id)
        assert job['state']=='pending'
        assert job['payload']['composition']==payloads[index]['composition']
        assert job['payload']['output']==payloads[index]['output']
        assert job['payload']['_tools']=={'ffmpeg':'synthetic-tool-path'}
    assert store.job(prior)['state']=='pending'
    assert payloads==unchanged


def test_submit_many_validates_every_payload_before_any_insert(tmp_path):
    store=Store(tmp_path/'state.db')
    valid={'composition':{},'output':'first.mp4'}
    rejected={'composition':{'api_key':'synthetic-must-not-save'},'output':'second.mp4'}
    with pytest.raises(ValueError,match='Secret values'):
        store.submit_many('render',[valid,rejected])
    assert store.jobs()==[]
    with pytest.raises(ValueError,match='Job payload'):
        store.submit_many('render',[valid,object()])
    assert store.jobs()==[]
    assert store.submit_many('render',[])==[]
