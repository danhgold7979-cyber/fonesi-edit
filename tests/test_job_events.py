from dataclasses import replace
import sqlite3
import uuid
import pytest
from fonesi_edit.jobs.events import Event,EventCode,EventStage,describe
from fonesi_edit.jobs.event_store import EventRecord,EventStore,EventStoreError,event_path,read_events,APPLICATION_ID,VERSION,SCHEMA_HASH
from fonesi_edit.jobs.diagnostics import DiagnosticStatus,record_job_event
from fonesi_edit.jobs.commands import apply_queue_command
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.storage.db_ownership import receipt_path
from test_queue_view import queue
from test_coordinator_inbox import request


def record(job_id=None,token='a'*64):
    return EventRecord(token,job_id or str(uuid.uuid4()),0,1,1000,Event(EventCode.PROCESS_EXIT,EventStage.DECODE,2))


def test_event_allowlist_roundtrip_cannot_hold_raw_secret():
    event=record().event;assert Event.parse(event.canonical())==event
    assert describe(event)==('process_failure','Tiến trình kết thúc với mã lỗi (2)')
    with pytest.raises(ValueError):Event('SECRET',EventStage.DECODE)
    with pytest.raises(ValueError):Event(EventCode.PROCESS_EXIT,EventStage.DECODE,'SECRET')
    with pytest.raises(ValueError):Event.parse(event.canonical()[:-1]+',"stderr":"SECRET"}')
    with pytest.raises(ValueError):Event.parse('{"code":"PROCESS_EXIT","code":"SECRET","stage":"DECODE","exit_code":2}')
    with pytest.raises(ValueError):Event(EventCode.CANCEL_REQUESTED,EventStage.DECODE)


def test_retention_reopen_and_store_token_selection(tmp_path):
    path=tmp_path/'events.db';first=record();other=record()
    with EventStore(path,global_limit=3,per_job_limit=2) as store:
        for i in range(5):store.append(replace(first,observed_ms=i))
        store.append(other);store.append(replace(other,store_token='b'*64))
        assert store.db.execute('SELECT count(*) FROM events').fetchone()[0]==3
    assert [r.observed_ms for r in read_events(path,first.store_token,first.job_id)]==[4]
    assert read_events(path,'b'*64,other.job_id)==(replace(other,store_token='b'*64),)
    assert read_events(tmp_path/'missing'/'events.db','a'*64,first.job_id)==()
    assert not (tmp_path/'missing').exists()


@pytest.mark.parametrize('kind',['empty','foreign','future','malformed','receipt'])
def test_existing_foreign_future_corrupt_remain_unchanged(tmp_path,kind):
    path=tmp_path/'events.db'
    if kind in ('future','malformed','receipt'):
        with EventStore(path):pass
        if kind=='receipt':receipt_path(path).write_bytes(b'FOREIGN')
        else:
            with sqlite3.connect(path) as db:
                if kind=='future':db.execute('PRAGMA user_version=999')
                else:db.execute('ALTER TABLE events ADD COLUMN foreign_value TEXT')
    else:
        with sqlite3.connect(path) as db:
            if kind=='foreign':db.execute('CREATE TABLE foreign_data(secret TEXT)')
    before=path.read_bytes()
    with pytest.raises((EventStoreError,ValueError)):EventStore(path)
    assert path.read_bytes()==before


def test_unknown_append_retires_store_and_never_replays(tmp_path):
    path=tmp_path/'events.db';item=record()
    with EventStore(path) as store:
        original=store.db
        class Unknown:
            def __getattr__(self,name):return getattr(original,name)
            def execute(self,sql,*args):
                result=original.execute(sql,*args)
                if sql=='COMMIT':raise sqlite3.OperationalError('SECRET unknown commit')
                return result
        store.db=Unknown()
        with pytest.raises(sqlite3.OperationalError):store.append(item)
        with pytest.raises(EventStoreError,match='revoked'):store.append(item)
        store.db=original
    assert read_events(path,item.store_token,item.job_id)==(item,)


def test_logging_failure_does_not_undo_or_repeat_committed_command(queue,tmp_path):
    repo,jobs=queue;path=tmp_path/'foreign-events.db';path.write_bytes(b'FOREIGN')
    result=apply_queue_command(repo.path,request(repo,jobs[0],'pause'),events_path=path)
    assert result.state=='paused' and result.diagnostic_status is DiagnosticStatus.UNAVAILABLE
    assert repo.get(jobs[0].id).version==jobs[0].version+1 and path.read_bytes()==b'FOREIGN'


def test_actual_command_records_only_typed_job_fields_and_stale_worker_refused(queue):
    repo,jobs=queue;path=event_path(repo.path)
    command=request(repo,jobs[0],'pause');result=apply_queue_command(repo.path,command,events_path=path)
    assert result.diagnostic_status is DiagnosticStatus.RECORDED
    rows=read_events(path,command.store_token,jobs[0].id);assert len(rows)==1
    assert rows[0].event.code is EventCode.QUEUE_PAUSED and 'secret-sentinel' not in repr(rows)
    with CoordinatorOwnership(repo) as owner:
        assert record_job_event(repo,owner,jobs[0],Event(EventCode.STORAGE_FAILURE,EventStage.PUBLISH),path) is DiagnosticStatus.UNAVAILABLE
    assert read_events(path,command.store_token,jobs[0].id)==rows


def test_corrupt_payload_never_displayed(tmp_path):
    path=tmp_path/'events.db';item=record()
    with EventStore(path) as store:
        store.append(item);store.db.execute('UPDATE events SET payload=?',('{"secret":"TOKEN"}',))
    with pytest.raises(EventStoreError,match='unavailable'):read_events(path,item.store_token,item.job_id)


def test_real_process_error_diagnostic_is_typed_not_execution_authority(queue):
    import sys
    from fonesi_edit.jobs.process import run_owned
    repo,jobs=queue;path=event_path(repo.path)
    with CoordinatorOwnership(repo) as owner:
        running=repo.claim(jobs[0]);result=run_owned([sys.executable,'-c','import sys;sys.stderr.write("SECRET token/path");raise SystemExit(7)'])
        assert record_job_event(repo,owner,running,Event(EventCode.PROCESS_EXIT,EventStage.DECODE,result.returncode),path) is DiagnosticStatus.RECORDED
        assert repo.get(running.id)==running
    from fonesi_edit.jobs.view import read_queue
    rows=read_events(path,read_queue(repo.path).store_token,running.id)
    assert rows[0].event.exit_code==7 and 'SECRET' not in repr(rows)
    with sqlite3.connect(path) as db:assert 'SECRET' not in repr(db.execute('SELECT * FROM events').fetchall())


def test_original_store_identity_loss_permanently_refuses_after_restore(tmp_path):
    import shutil
    path=tmp_path/'events.db';old=tmp_path/'original.db';item=record()
    with EventStore(path) as store:
        try:path.rename(old)
        except PermissionError:
            # Native pin denied the attempted namespace change; no mutation injected.
            store.guard();return
        shutil.copyfile(old,path)
        with pytest.raises(EventStoreError):store.append(item)
        path.unlink();old.rename(path)
        with pytest.raises(EventStoreError,match='revoked'):store.append(item)


def test_initialization_baseexception_closes_original_fd(tmp_path,monkeypatch):
    import os
    import fonesi_edit.jobs.event_store as module
    seen=[];guard=module.EventStore.guard
    def observed(self):seen.append(self.fd);return guard(self)
    def interrupted(*a,**k):raise KeyboardInterrupt()
    monkeypatch.setattr(module.EventStore,'guard',observed);monkeypatch.setattr(module,'open_versioned',interrupted)
    with pytest.raises(KeyboardInterrupt):EventStore(tmp_path/'events.db')
    assert seen
    with pytest.raises(OSError):os.fstat(seen[0])


def test_readonly_existing_logs_create_no_sidecars_or_change_bytes(tmp_path):
    path=tmp_path/'events.db';item=record()
    with EventStore(path) as store:store.append(item)
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    assert read_events(path,item.store_token,item.job_id)==(item,)
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


def test_busy_diagnostic_store_returns_unavailable_without_delaying_or_retrying_job(queue):
    repo,jobs=queue;path=event_path(repo.path)
    with EventStore(path) as store:
        store.db.execute('BEGIN EXCLUSIVE')
        try:
            result=apply_queue_command(repo.path,request(repo,jobs[0],'pause'),events_path=path)
            assert result.state=='paused' and result.diagnostic_status is DiagnosticStatus.UNAVAILABLE
        finally:store.db.execute('ROLLBACK')
    assert repo.get(jobs[0].id).version==jobs[0].version+1


def test_owned_wal_refused_before_sqlite_without_auxiliary_creation(tmp_path,monkeypatch):
    import fonesi_edit.jobs.event_store as module
    path=tmp_path/'events.db';item=record()
    with EventStore(path) as store:store.append(item)
    db=sqlite3.connect(path);assert db.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal';db.close()
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    assert not any(name.endswith(('-wal','-shm')) for name in before)
    monkeypatch.setattr(module.sqlite3,'connect',lambda *a,**k:pytest.fail('Unsupported WAL must not reach SQLite'))
    with pytest.raises(EventStoreError,match='header/journal'):read_events(path,item.store_token,item.job_id)
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


def test_windows_unsigned_crash_exit_and_posix_signal_are_bounded():
    for code in (0xC0000005,-9):
        event=Event(EventCode.PROCESS_EXIT,EventStage.DECODE,code)
        assert Event.parse(event.canonical())==event and str(code) in describe(event)[1]
    for code in (2**32,-2**31-1):
        with pytest.raises(ValueError):Event(EventCode.PROCESS_EXIT,EventStage.DECODE,code)
