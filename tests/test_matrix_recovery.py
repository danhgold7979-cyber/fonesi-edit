"""P11 Matrix worker recovery: preserve atomic reservation across interruption/retry."""
from pathlib import Path
import time

import pytest

from fonesi_edit.domain import Composition
from fonesi_edit.jobs import Scheduler
from fonesi_edit.matrix import Angle, enqueue_rows, history
from fonesi_edit.prototypes.media import create_fixture, probe
from fonesi_edit.storage import Store


def _prepared(tmp_path, scope):
    source=create_fixture(tmp_path/"media",duration=.6)["source"]
    row=[[Angle(1,1,str(source),"scene-a"),
          Angle(2,1,str(source),"scene-b")]]
    store=Store(tmp_path/"state.db")
    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    ids=enqueue_rows(store,scope,row,preset,tmp_path/"out")
    return store,ids[0],row


def _mark_worker_orphaned(store,job_id):
    claimed=store.claim({"render"})
    assert claimed and claimed["id"]==job_id
    with store.connect() as conn:
        conn.execute("UPDATE jobs SET heartbeat=0 WHERE id=?",(job_id,))
    return claimed


def _run_to_success(store,job_id):
    scheduler=Scheduler(store)
    deadline=time.monotonic()+25
    try:
        while time.monotonic()<deadline:
            scheduler.tick()
            if store.job(job_id)["state"]=="succeeded" and not scheduler.active:
                break
            time.sleep(.04)
        job=store.job(job_id)
        assert job["state"]=="succeeded",job["error"]
        assert not scheduler.active
        output=Path(job["payload"]["output"])
        assert output.is_file() and output.stat().st_size>0
        assert probe(output).duration==pytest.approx(.6,abs=.15)
        assert job["result"]["validated"] is True
    finally:
        scheduler.shutdown()


def test_orphaned_matrix_worker_recovers_same_reserved_snapshot_then_succeeds(tmp_path):
    store,job_id,_=_prepared(tmp_path,"orphan-scope")
    before=store.job(job_id)
    _mark_worker_orphaned(store,job_id)
    assert store.recover(stale_seconds=1)==1
    recovered=store.job(job_id)
    assert recovered["state"]=="pending"
    assert recovered["attempts"]==1
    assert recovered["payload"]==before["payload"]
    with store.connect() as conn:
        state,linked=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("orphan-scope",)).fetchone()
        assert (state,linked)==("reserved",job_id)
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("orphan-scope",)).fetchone()[0]==1
    assert history(store,"orphan-scope")==[["scene-a","scene-b"]]
    _run_to_success(store,job_id)
    assert history(store,"orphan-scope")==[["scene-a","scene-b"]]
    with store.connect() as conn:
        state,linked=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("orphan-scope",)).fetchone()
        assert (state,linked)==("succeeded",job_id)


def test_cancelled_orphaned_matrix_job_retries_same_identity_once(tmp_path):
    store,job_id,_=_prepared(tmp_path,"cancel-retry-scope")
    _mark_worker_orphaned(store,job_id)
    store.cancel(job_id)
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT cancel_requested,state FROM jobs WHERE id=?",
            (job_id,)).fetchone())==(1,"running")
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone())==("reserved",job_id)
        conn.execute("UPDATE jobs SET heartbeat=0 WHERE id=?",(job_id,))
    assert store.recover(stale_seconds=1)==1
    canceled=store.job(job_id)
    assert canceled["state"]=="canceled" and canceled["cancel_requested"]==1
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone())==("failed",job_id)
    assert history(store,"cancel-retry-scope")==[]

    store.retry(job_id)
    retried=store.job(job_id)
    assert retried["id"]==job_id and retried["state"]=="pending"
    assert retried["cancel_requested"]==0 and retried["attempts"]==1
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone())==("reserved",job_id)
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone()[0]==1
        assert conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE id=?",(job_id,)).fetchone()[0]==1
    assert history(store,"cancel-retry-scope")==[["scene-a","scene-b"]]
    _run_to_success(store,job_id)
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone())==("succeeded",job_id)
        assert conn.execute(
            "SELECT attempts FROM jobs WHERE id=?",(job_id,)).fetchone()[0]==2
    assert history(store,"cancel-retry-scope")==[["scene-a","scene-b"]]
