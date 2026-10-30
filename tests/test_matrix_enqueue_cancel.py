"""P09-06: cancel-safe Matrix queue preflight and transactional reservation tests."""
from threading import Event

import pytest

from fonesi_edit.domain import Composition
from fonesi_edit.matrix import (
    Angle, MatrixEnqueueCancelled, enqueue_rows, history, combination,
)
from fonesi_edit.prototypes.media import create_fixture
from fonesi_edit.storage import Store


def _inputs(tmp_path):
    source=str(create_fixture(tmp_path/"media",duration=.5)["source"])
    rows=[
        [Angle(1,1,source,"a1"), Angle(2,1,source,"b1")],
        [Angle(1,2,source,"a2"), Angle(2,1,source,"b1")],
    ]
    store=Store(tmp_path/"state.db")
    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    return rows,store,preset


def test_cancelled_before_probe_does_not_insert_matrix_jobs(tmp_path):
    rows,store,preset=_inputs(tmp_path)
    token=Event();token.set()
    with pytest.raises(MatrixEnqueueCancelled,match="hủy"):
        enqueue_rows(store,"project",rows,preset,tmp_path/"out",cancel=token)
    assert store.jobs()==[]
    assert history(store,"project")==[]


def test_cancelled_during_preflight_does_not_open_reservation_transaction(tmp_path):
    rows,store,preset=_inputs(tmp_path)
    token=Event();progresses=[]
    def progress(value):
        progresses.append(value)
        if .3<=value<.7:
            token.set()
    with pytest.raises(MatrixEnqueueCancelled,match="hủy"):
        enqueue_rows(store,"project",rows,preset,tmp_path/"out",
                     progress=progress,cancel=token)
    assert progresses and progresses[0]==pytest.approx(.35)
    assert store.jobs()==[]
    assert history(store,"project")==[]


def test_cancel_during_second_stage_rolls_back_all_new_rows_and_preserves_old(tmp_path):
    rows,store,preset=_inputs(tmp_path)
    source=rows[0][0].path
    old_row=[Angle(1,1,source,"before-a"),Angle(2,1,source,"before-b")]
    before=enqueue_rows(store,"project",[old_row],preset,tmp_path/"out")
    token=Event();progresses=[]
    def progress(value):
        progresses.append(value)
        # First reservation and job INSERT have happened inside BEGIN IMMEDIATE;
        # the next cancel check must roll the entire transaction back.
        if .8<=value<.95:
            token.set()
    with pytest.raises(MatrixEnqueueCancelled,match="hủy"):
        enqueue_rows(store,"project",rows,preset,tmp_path/"out",
                     progress=progress,cancel=token)
    assert any(.8<=value<.95 for value in progresses)
    assert [job["id"] for job in store.jobs()]==before
    assert history(store,"project")==[["before-a","before-b"]]
    with store.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM matrix_history WHERE scope=?",
            ("project",)).fetchone()[0]==1
        assert conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE kind='render'").fetchone()[0]==1
    assert not (tmp_path/"out").exists()
