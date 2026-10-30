"""P11 Matrix worker recovery: preserve atomic reservation across interruption/retry."""
from pathlib import Path
import time

import pytest

from fonesi_edit.domain import Composition, canonical
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


def _add_unrelated_success(store,scope):
    with store.connect() as conn:
        conn.execute(
            "INSERT INTO matrix_history(scope,combination,state,job_id,created) "
            "VALUES(?,?,'succeeded',?,?)",
            (scope,canonical(["other-a","other-b"]),"other-success",1.0))


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
        assert .8<=probe(output).duration<=1.4
        assert job["result"]["validated"] is True
    finally:
        scheduler.shutdown()


def test_orphaned_matrix_worker_recovers_same_reserved_snapshot_then_succeeds(tmp_path):
    store,job_id,_=_prepared(tmp_path,"orphan-scope")
    _add_unrelated_success(store,"orphan-scope")
    before=store.job(job_id)
    _mark_worker_orphaned(store,job_id)
    assert store.recover(stale_seconds=1)==1
    recovered=store.job(job_id)
    assert recovered["state"]=="pending"
    assert recovered["attempts"]==1
    assert recovered["payload"]==before["payload"]
    with store.connect() as conn:
        state,linked=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("orphan-scope",canonical(["scene-a","scene-b"]))).fetchone()
        assert (state,linked)==("reserved",job_id)
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("orphan-scope",canonical(["other-a","other-b"]))).fetchone())==("succeeded","other-success")
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("orphan-scope",)).fetchone()[0]==2
    assert ["scene-a","scene-b"] in history(store,"orphan-scope")
    assert ["other-a","other-b"] in history(store,"orphan-scope")
    _run_to_success(store,job_id)
    assert ["scene-a","scene-b"] in history(store,"orphan-scope")
    assert ["other-a","other-b"] in history(store,"orphan-scope")
    with store.connect() as conn:
        state,linked=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("orphan-scope",canonical(["scene-a","scene-b"]))).fetchone()
        assert (state,linked)==("succeeded",job_id)
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("orphan-scope",canonical(["other-a","other-b"]))).fetchone())==("succeeded","other-success")


def test_cancelled_orphaned_matrix_job_retries_same_identity_once(tmp_path):
    store,job_id,_=_prepared(tmp_path,"cancel-retry-scope")
    _add_unrelated_success(store,"cancel-retry-scope")
    _mark_worker_orphaned(store,job_id)
    store.cancel(job_id)
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT cancel_requested,state FROM jobs WHERE id=?",
            (job_id,)).fetchone())==(1,"running")
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("cancel-retry-scope",canonical(["scene-a","scene-b"]))).fetchone())==("reserved",job_id)
        conn.execute("UPDATE jobs SET heartbeat=0 WHERE id=?",(job_id,))
    assert store.recover(stale_seconds=1)==1
    canceled=store.job(job_id)
    assert canceled["state"]=="canceled" and canceled["cancel_requested"]==1
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("cancel-retry-scope",canonical(["scene-a","scene-b"]))).fetchone())==("failed",job_id)
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("cancel-retry-scope",canonical(["other-a","other-b"]))).fetchone())==("succeeded","other-success")
    assert history(store,"cancel-retry-scope")==[["other-a","other-b"]]

    store.retry(job_id)
    retried=store.job(job_id)
    assert retried["id"]==job_id and retried["state"]=="pending"
    assert retried["cancel_requested"]==0 and retried["attempts"]==1
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("cancel-retry-scope",canonical(["scene-a","scene-b"]))).fetchone())==("reserved",job_id)
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("cancel-retry-scope",)).fetchone()[0]==2
        assert conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE id=?",(job_id,)).fetchone()[0]==1
    assert ["scene-a","scene-b"] in history(store,"cancel-retry-scope")
    assert ["other-a","other-b"] in history(store,"cancel-retry-scope")
    _run_to_success(store,job_id)
    with store.connect() as conn:
        assert tuple(conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("cancel-retry-scope",canonical(["scene-a","scene-b"]))).fetchone())==("succeeded",job_id)
        assert conn.execute(
            "SELECT attempts FROM jobs WHERE id=?",(job_id,)).fetchone()[0]==2
    assert ["scene-a","scene-b"] in history(store,"cancel-retry-scope")
    assert ["other-a","other-b"] in history(store,"cancel-retry-scope")


def test_retry_refuses_missing_matrix_reservation_without_requeueing_job(tmp_path):
    store,job_id,_=_prepared(tmp_path,"missing-reservation-scope")
    claimed=store.claim({"render"})
    assert claimed and claimed["id"]==job_id
    store.fail(job_id,"synthetic first attempt failure")
    with store.connect() as conn:
        conn.execute(
            "DELETE FROM matrix_history WHERE scope=? AND combination=?",
            ("missing-reservation-scope",canonical(["scene-a","scene-b"])))
    with pytest.raises(ValueError,match="reservation is missing"):
        store.retry(job_id)
    assert store.job(job_id)["state"]=="failed"
    with store.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("missing-reservation-scope",)).fetchone()[0]==0
        assert conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE id=? AND state='failed'",
            (job_id,)).fetchone()[0]==1


def test_retry_cannot_steal_failed_reservation_reassigned_to_newer_job(tmp_path):
    store,older_id,row=_prepared(tmp_path,"reassigned-reservation-scope")
    claimed=store.claim({"render"})
    assert claimed and claimed["id"]==older_id
    store.fail(older_id,"older attempt failed")

    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    newer_id=enqueue_rows(
        store,"reassigned-reservation-scope",row,preset,tmp_path/"out")[0]
    assert newer_id!=older_id
    claimed=store.claim({"render"})
    assert claimed and claimed["id"]==newer_id
    store.fail(newer_id,"newer attempt failed")

    with store.connect() as conn:
        reservation=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("reassigned-reservation-scope",canonical(["scene-a","scene-b"]))).fetchone()
        assert tuple(reservation)==("failed",newer_id)
    with pytest.raises(ValueError,match="different job"):
        store.retry(older_id)
    assert store.job(older_id)["state"]=="failed"
    assert store.job(newer_id)["state"]=="failed"
    with store.connect() as conn:
        reservation=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("reassigned-reservation-scope",canonical(["scene-a","scene-b"]))).fetchone()
        assert tuple(reservation)==("failed",newer_id)
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("reassigned-reservation-scope",)).fetchone()[0]==1

    store.retry(newer_id)
    assert store.job(newer_id)["state"]=="pending"
    with store.connect() as conn:
        reservation=conn.execute(
            "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
            ("reassigned-reservation-scope",canonical(["scene-a","scene-b"]))).fetchone()
        assert tuple(reservation)==("reserved",newer_id)


def test_missing_matrix_source_after_enqueue_never_marks_history_succeeded(tmp_path):
    store,job_id,row=_prepared(tmp_path,"missing-source-scope")
    Path(row[0][0].path).unlink()

    scheduler=Scheduler(store)
    deadline=time.monotonic()+25
    try:
        while time.monotonic()<deadline:
            scheduler.tick()
            job=store.job(job_id)
            if job["state"] in {"failed","blocked","canceled"} and not scheduler.active:
                break
            time.sleep(.04)
        job=store.job(job_id)
        assert job["state"] in {"failed","blocked"}
        assert job["result"] is None
        assert not scheduler.active
        with store.connect() as conn:
            reservation=conn.execute(
                "SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?",
                ("missing-source-scope",canonical(["scene-a","scene-b"]))).fetchone()
            assert tuple(reservation)==("failed",job_id)
        assert history(store,"missing-source-scope")==[]
    finally:
        scheduler.shutdown()


@pytest.mark.parametrize("payload",[
    {"matrix_scope":"","matrix_combination":canonical(["scene-a","scene-b"])},
    {"matrix_combination":canonical(["scene-a","scene-b"])},
])
def test_retry_refuses_incomplete_matrix_reservation_identity(tmp_path,payload):
    store=Store(tmp_path/"state.db")
    job_id=store.submit("render",payload)
    claimed=store.claim({"render"})
    assert claimed and claimed["id"]==job_id
    store.fail(job_id,"synthetic malformed Matrix identity")
    with pytest.raises(ValueError,match="missing its reservation identity"):
        store.retry(job_id)
    assert store.job(job_id)["state"]=="failed"
