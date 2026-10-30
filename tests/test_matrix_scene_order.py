"""P09 scene ordering: immutable assets, transposed locks/history and enqueue safety."""
from copy import deepcopy
from pathlib import Path

import pytest

from fonesi_edit.domain import Composition
from fonesi_edit.matrix import (
    Angle, combination, enqueue_rows, history, matrix_rows_valid,
    normalize_matrix_history, reorder_matrix_scenes, row_composition,
    scene_directories,
)
from fonesi_edit.prototypes.media import create_fixture, probe
from fonesi_edit.render import render_composition
from fonesi_edit.storage import Store


def scenes():
    return [
        [Angle(1, j + 1, f"synthetic/C1/{j}.mp4", f"a{j}") for j in range(3)],
        [Angle(2, j + 1, f"synthetic/C2/{j}.mp4", f"b{j}") for j in range(3)],
        [Angle(3, j + 1, f"synthetic/C3/{j}.mp4", f"c{j}") for j in range(3)],
    ]


def test_scene_order_transposes_rows_history_and_locks_without_mutating_inputs():
    original = scenes()
    rows = [
        [original[0][1], original[1][1], original[2][1]],
        [original[0][2], original[1][2], original[2][2]],
    ]
    previous = [["a0", "b0", "c0"]]
    locked = {(0, 1), (1, 3)}
    before = deepcopy((original, rows, previous, locked))
    result = reorder_matrix_scenes(
        original, rows, locked, previous, [2, 0, 1], window=1, different=3
    )
    assert [[a.hash for a in row] for row in result["rows"]] == [
        ["c1", "a1", "b1"], ["c2", "a2", "b2"]
    ]
    assert result["history"] == [["c0", "a0", "b0"]]
    assert result["locked"] == {(0, 2), (1, 1)}
    assert [[a.scene for a in group] for group in result["scenes"]] == [
        [1] * 3, [2] * 3, [3] * 3
    ]
    assert [a.path for group in result["scenes"] for a in group] == [
        a.path for i in (2, 0, 1) for a in original[i]
    ]
    assert matrix_rows_valid(result["rows"], result["history"], 1, 3)
    assert (original, rows, previous, locked) == before
    assert scene_directories(result["scenes"]) == [
        str(Path("synthetic/C3").resolve()),
        str(Path("synthetic/C1").resolve()),
        str(Path("synthetic/C2").resolve()),
    ]


@pytest.mark.parametrize("order", [[], [0], [0, 0, 2], [0, 1, 3], [False, 1, 2], [2, -1, 0]])
def test_scene_order_refuses_invalid_permutations_without_partial_mutation(order):
    original = scenes()
    rows = [[group[0] for group in original]]
    snapshot = deepcopy((original, rows))
    with pytest.raises(ValueError, match="permutation"):
        reorder_matrix_scenes(original, rows, set(), [], order)
    assert (original, rows) == snapshot


def test_scene_order_refuses_mismatched_rows_locked_cells_and_history():
    original = scenes()
    rows = [[group[1] for group in original]]
    before = deepcopy((original, rows))
    with pytest.raises(ValueError, match="source scenes"):
        reorder_matrix_scenes(
            original, [[original[1][1], original[0][1], original[2][1]]],
            set(), [], [1, 0, 2])
    with pytest.raises(ValueError, match="locked"):
        reorder_matrix_scenes(original, rows, {(0, 4)}, [], [1, 0, 2])
    with pytest.raises(ValueError, match="history"):
        reorder_matrix_scenes(original, rows, set(), [["b0", "a0", "c0"]], [1, 0, 2])
    assert (original, rows) == before


def test_history_reprojects_previous_saved_orders_and_refuses_ambiguous_identity():
    original=scenes()
    ordered = reorder_matrix_scenes(original, [], set(), [], [2, 0, 1])["scenes"]
    source = [["b0", "c1", "a2"], ["a0", "b1", "c2"]]
    expected = [["c1", "a2", "b0"], ["c2", "a0", "b1"]]
    assert normalize_matrix_history(ordered, source)==expected
    assert source==[["b0", "c1", "a2"], ["a0", "b1", "c2"]]
    with pytest.raises(ValueError, match="unique source scene"):
        normalize_matrix_history(ordered, [["a0", "b0", "missing"]])
    with pytest.raises(ValueError, match="scene count"):
        normalize_matrix_history(ordered, [["a0"]])
    ambiguous = [
        [Angle(1, 1, "fixture/C1/1.mp4", "same")],
        [Angle(2, 1, "fixture/C2/1.mp4", "same")],
    ]
    with pytest.raises(ValueError, match="unique source scene"):
        normalize_matrix_history(ambiguous, [["same", "same"]])


def test_duplicate_after_reordering_is_rejected_inside_atomic_enqueue(tmp_path):
    first=create_fixture(tmp_path/"one", duration=.5)["source"]
    second=create_fixture(tmp_path/"two", duration=.5)["source"]
    original=[[Angle(1, 1, str(first), "a")], [Angle(2, 1, str(second), "b")]]
    store=Store(tmp_path/"state.db")
    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    original_job=enqueue_rows(store,"ordered-scope",
                              [[original[0][0],original[1][0]]],preset,tmp_path/"out")
    prior=history(store,"ordered-scope")
    assert prior==[["a","b"]]
    moved=reorder_matrix_scenes(original, [[original[0][0],original[1][0]]],
                                set(), [], [1,0])
    with pytest.raises(ValueError,match="Tổ hợp đã được dùng"):
        enqueue_rows(store,"ordered-scope",moved["rows"],preset,tmp_path/"out",
                     scene_order=moved["scenes"])
    assert len(store.jobs())==1
    assert store.jobs()[0]["id"]==original_job[0]
    assert history(store,"ordered-scope")==prior
    assert not (tmp_path/"out").exists()
    assert first.is_file() and second.is_file()


def test_moved_rows_define_real_composition_clip_order_and_source_bytes(tmp_path):
    import hashlib
    first=create_fixture(tmp_path/"one",duration=.5)["source"]
    second=create_fixture(tmp_path/"two",duration=.5)["source"]
    originals = {str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in (first,second)}
    old=[[Angle(1, 1, str(first), "a")], [Angle(2, 1, str(second), "b")]]
    moved=reorder_matrix_scenes(old,[[old[0][0],old[1][0]]],set(),[],[1,0])
    comp=row_composition(moved["rows"][0],Composition(width=320,height=180,
                                                      fps=25,encoder="cpu"))
    assert [clip.path for clip in comp.clips]==[str(second.resolve()),str(first.resolve())]
    assert [clip.id for clip in comp.clips]==[
        __import__("hashlib").sha256(f"{i}:{digest}".encode()).hexdigest()[:32]
        for i,digest in ((1,"b"),(2,"a"))
    ]
    result=render_composition(comp,tmp_path/"reordered.mp4")
    assert result["validated"]
    assert abs(probe(tmp_path/"reordered.mp4").duration-1)<.15
    assert originals=={str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in (first,second)}
