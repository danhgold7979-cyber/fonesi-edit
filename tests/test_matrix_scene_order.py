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


def _choices_for(scenes):
    from fonesi_edit.matrix import scene_directories
    return {folder:{"enabled":True,"angles":[angle.hash for angle in scene],"pin":None}
            for folder,scene in zip(scene_directories(scenes),scenes)}


def test_explicit_scene_and_angle_selection_preserves_original_g_hash_and_files():
    from fonesi_edit.matrix import select_matrix_scenes,scene_manifest
    original=scenes()
    untouched=deepcopy(original)
    choices=_choices_for(original)
    keys=list(choices)
    choices[keys[0]]["angles"]=["a1"]
    choices[keys[1]]["enabled"]=False
    choices[keys[2]]["angles"]=["c0","c2"]
    choices[keys[2]]["pin"]="c2"
    result=select_matrix_scenes(original,choices)
    assert len(result["scenes"])==2
    assert [[(a.scene,a.index,a.hash) for a in group] for group in result["scenes"]]==[
        [(1,2,"a1")],[(2,1,"c0"),(2,3,"c2")]
    ]
    assert result["pins"]=={1:"c2"}
    assert result["folders"]==[keys[0],keys[2]]
    assert original==untouched
    assert scene_manifest(original)==scene_manifest(untouched)


@pytest.mark.parametrize("mutation,match",[
    (lambda c,k:c.pop(k[1]),"match all scanned"),
    (lambda c,k:c[k[0]].update(enabled=1),"Invalid scene"),
    (lambda c,k:c[k[0]].update(angles="a0"),"Invalid scene"),
    (lambda c,k:c[k[0]].update(angles=["a0","a0"]),"unique"),
    (lambda c,k:c[k[0]].update(angles=["missing"]),"no longer exists"),
    (lambda c,k:c[k[0]].update(angles=[]),"at least one"),
    (lambda c,k:c[k[0]].update(angles=["a0"],pin="a1"),"Pinned angle"),
    (lambda c,k:[c[key].update(enabled=False) for key in k],"At least one"),
])
def test_explicit_selection_rejects_invalid_snapshots_without_mutation(mutation,match):
    from fonesi_edit.matrix import select_matrix_scenes
    original=scenes()
    before=deepcopy(original)
    choices=_choices_for(original)
    mutation(choices,list(choices))
    with pytest.raises(ValueError,match=match):
        select_matrix_scenes(original,choices)
    assert original==before


def test_global_scene_pin_merges_locks_and_exposes_w_capacity_conflicts():
    from fonesi_edit.matrix import scene_generation_locks,generate
    original=scenes()
    pins={1:"b1"}
    locks=scene_generation_locks(original,pins,2,0,{0:{0:"a2"}})
    assert locks=={0:{0:"a2",1:"b1"},1:{1:"b1"}}
    rows=generate(original,2,seed=3,locks=locks)["rows"]
    assert len(rows)==2 and all(row[1].hash=="b1" for row in rows)
    assert rows[0][0].hash=="a2"
    for kwargs,message in [
        ({"window":1},"W>0"),
        ({"locks":{0:{1:"b2"}}},"xung đột"),
        ({"pins":{1:"missing"}},"does not belong"),
    ]:
        options={"scenes":original,"pins":pins,"count":2}
        options.update(kwargs)
        with pytest.raises(ValueError,match=message):
            scene_generation_locks(**options)
    with pytest.raises(ValueError,match="không đủ"):
        scene_generation_locks(original,{0:"a0",1:"b0",2:"c0"},2)


def test_project_full_legacy_history_safely_projects_only_known_excluded_scenes():
    from fonesi_edit.matrix import select_matrix_scenes
    full=scenes()
    choices=_choices_for(full)
    keys=list(choices)
    choices[keys[1]]["enabled"]=False
    selected=select_matrix_scenes(full,choices)["scenes"]
    old=[["c1","a0","b2"],["a1","b0","c2"]]
    assert normalize_matrix_history(selected,old,all_scenes=full)==[
        ["a0","c1"],["a1","c2"]]
    assert old==[["c1","a0","b2"],["a1","b0","c2"]]
    for unsafe,message in [
        ([["a1","b1","not-an-angle"]],"unique source scene"),
        ([["a1","b1","b0","c1"]],"incompatible scene count"),
    ]:
        with pytest.raises(ValueError,match=message):
            normalize_matrix_history(selected,unsafe,all_scenes=full)
    with pytest.raises(ValueError,match="incompatible scene count"):
        normalize_matrix_history(selected,old)


def test_subset_enqueue_does_not_reuse_project_reserved_full_scene_history(tmp_path):
    from fonesi_edit.matrix import select_matrix_scenes
    source=[
        create_fixture(tmp_path/"C1",duration=.5)["source"],
        create_fixture(tmp_path/"C2",duration=.5)["source"],
        create_fixture(tmp_path/"C3",duration=.5)["source"],
    ]
    full=[[Angle(i+1,1,str(path),f"content-hash-{i}")]
          for i,path in enumerate(source)]
    store=Store(tmp_path/"state.db")
    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    whole=[[group[0] for group in full]]
    original_jobs=enqueue_rows(store,"same-project",whole,preset,tmp_path/"out")
    assert len(original_jobs)==1
    persisted=history(store,"same-project")
    choices=_choices_for(full)
    keys=list(choices)
    choices[keys[2]]["enabled"]=False
    subset=select_matrix_scenes(full,choices)["scenes"]
    assert [angle.hash for angle in subset[0]]==["content-hash-0"]
    with pytest.raises(ValueError,match="Tổ hợp đã được dùng"):
        enqueue_rows(store,"same-project",[[scene[0] for scene in subset]],preset,
                     tmp_path/"out",scene_order=subset,all_scenes=full)
    assert [job["id"] for job in store.jobs()]==original_jobs
    assert history(store,"same-project")==persisted
    assert all(path.is_file() for path in source)
    assert not (tmp_path/"out").exists()


def test_known_shorter_subset_history_does_not_block_return_to_full_matrix():
    from fonesi_edit.matrix import select_matrix_scenes,generate
    full=scenes()
    choices=_choices_for(full)
    choices[list(choices)[1]]["enabled"]=False
    short=select_matrix_scenes(full,choices)["scenes"]
    original=[["a0","b0","c0"],["a1","b1","c1"]]
    short_record=["a2","c2"]
    # Full -> subset: complete historic rows project, so used pairs cannot
    # be reused even when the removed B angle differs.
    projected=normalize_matrix_history(short,original,all_scenes=full)
    assert projected==[["a0","c0"],["a1","c1"]]
    # Subset -> full: a render missing B is a different composition, not
    # a false duplicate or reason to permanently lock the user's project.
    restored=normalize_matrix_history(full,[*original,short_record],all_scenes=full)
    assert restored==original
    assert len(generate(full,1,seed=4,history=restored)["rows"])==1
    # Malformed, removed or cross-scene ambiguous hashes are never skipped.
    with pytest.raises(ValueError,match="unique source scene"):
        normalize_matrix_history(full,[*original,["a2","missing"]],all_scenes=full)


def test_source_filtered_matrix_renders_without_modifying_original_files(tmp_path):
    from fonesi_edit.matrix import scan_scenes,select_matrix_scenes
    import hashlib
    root=tmp_path/"source-corpus"
    videos=[create_fixture(root/f"C{number}",duration=.5)["source"]
            for number in (1,2,3)]
    before={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in videos}
    full=scan_scenes(root)
    choices=_choices_for(full)
    choices[list(choices)[1]]["enabled"]=False
    chosen=select_matrix_scenes(full,choices)["scenes"]
    assert len(chosen)==2 and [row[0].scene for row in chosen]==[1,2]
    comp=row_composition([scene[0] for scene in chosen],
                         Composition(width=320,height=180,fps=25,encoder="cpu"))
    assert [clip.path for clip in comp.clips]==[str(videos[0].resolve()),
                                                str(videos[2].resolve())]
    assert render_composition(comp,tmp_path/"filtered-output.mp4")["validated"]
    assert abs(probe(tmp_path/"filtered-output.mp4").duration-1)<.15
    assert before=={str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in videos}


def test_full_subset_full_project_matrix_history_does_not_lock_selected_scene_sets(tmp_path):
    from fonesi_edit.matrix import select_matrix_scenes
    root=tmp_path/"source"
    source_a=create_fixture(root/"C1",duration=.5)["source"]
    source_a2=create_fixture(root/"C1-alt",duration=.75)["source"]
    # Reuse a root collection of three explicit scene folders below.
    b=create_fixture(root/"C2",duration=.5)["source"]
    c=create_fixture(root/"C3",duration=.5)["source"]
    full=[
        [Angle(1,1,str(source_a),"a0"),Angle(1,2,str(source_a2),"a1")],
        [Angle(2,1,str(b),"b0")],
        [Angle(3,1,str(c),"c0")],
    ]
    store=Store(tmp_path/"state.db")
    preset=Composition(width=320,height=180,fps=25,encoder="cpu")
    whole=[[scene[0] for scene in full]]
    one=enqueue_rows(store,"project",whole,preset,tmp_path/"out",scene_order=full,
                     all_scenes=full)
    choices=_choices_for(full)
    choices[list(choices)[1]]["enabled"]=False
    selected=select_matrix_scenes(full,choices)["scenes"]
    fresh_short=[[selected[0][1],selected[1][0]]]
    two=enqueue_rows(store,"project",fresh_short,preset,tmp_path/"out",
                     scene_order=selected,all_scenes=full)
    assert len(two)==1
    # A different full composition remains valid; the old shorter render
    # cannot be mistaken for a complete 3-scene tuple.
    old=history(store,"project")
    full_previous=normalize_matrix_history(full,old,all_scenes=full)
    assert full_previous==[["a0","b0","c0"]]
    full_new=[[full[0][1],full[1][0],full[2][0]]]
    three=enqueue_rows(store,"project",full_new,preset,tmp_path/"out",
                       scene_order=full,all_scenes=full)
    assert len(three)==1
    assert len(store.jobs())==3
    assert all(video.is_file() for video in (source_a,source_a2,b,c))
    assert not (tmp_path/"out").exists()
