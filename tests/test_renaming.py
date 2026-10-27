from pathlib import Path
import json
import pytest
from fonesi_edit.domain import fingerprint
from fonesi_edit.matrix import Angle
from fonesi_edit.renaming import scene_rename_plan,apply_rename,undo_rename,recover_rename


def make_scene(tmp_path):
    root=tmp_path/'scenes';folder=root/'scene one';folder.mkdir(parents=True)
    first=folder/'shot a.mp4';second=folder/'shot b.mp4';first.write_bytes(b'original one');second.write_bytes(b'original two')
    first.with_suffix('.srt').write_text('caption')
    return root,[[Angle(1,1,str(first),fingerprint(first)),Angle(1,2,str(second),fingerprint(second))]]


def test_rename_and_undo_preserve_source_bytes_timestamps_and_sidecar(tmp_path):
    root,scenes=make_scene(tmp_path);plan=scene_rename_plan(scenes);stamps={op['source']:Path(op['source']).stat().st_mtime_ns for op in plan}
    result=apply_rename(root,plan)
    for op in plan:assert not Path(op['source']).exists() and fingerprint(Path(op['target']))==op['sha256'] and Path(op['target']).stat().st_mtime_ns==stamps[op['source']]
    assert (root/'scene one/C1G1.srt').read_text()=='caption'
    undo_rename(result['journal'])
    for op in plan:assert fingerprint(Path(op['source']))==op['sha256'] and not Path(op['target']).exists()
    with pytest.raises(ValueError):undo_rename(result['journal'])


def test_collision_and_cancel_never_lose_or_overwrite_source(tmp_path):
    root,scenes=make_scene(tmp_path);plan=scene_rename_plan(scenes);occupied=Path(plan[0]['target']);occupied.write_bytes(b'do not replace')
    with pytest.raises(FileExistsError):apply_rename(root,plan)
    assert occupied.read_bytes()==b'do not replace';occupied.unlink()
    class Cancel:
        count=0
        def is_set(self):self.count+=1;return self.count==2
    with pytest.raises(RuntimeError):apply_rename(root,plan,Cancel())
    assert all(fingerprint(Path(op['source']))==op['sha256'] for op in plan)


def test_incomplete_journal_recovers_a_move_even_before_state_was_saved(tmp_path):
    root,scenes=make_scene(tmp_path);source=Path(scenes[0][0].path);temp=source.with_name('.partial-rename');digest=fingerprint(source);source.rename(temp)
    journal=root/'unfinished.json';journal.write_text(json.dumps({'root':str(root),'state':'prepared','operations':[{'source':str(source),'temporary':str(temp),'target':str(source.with_name('C1G1.mp4')),'sha256':digest,'state':'source'}]}))
    recover_rename(journal);assert source.is_file() and fingerprint(source)==digest and not temp.exists()


def test_two_stage_rename_and_undo_handle_existing_name_cycles(tmp_path):
    root=tmp_path/'scene';root.mkdir();a=root/'C1G1.mp4';b=root/'C1G2.mp4';a.write_bytes(b'angle A');b.write_bytes(b'angle B')
    plan=[{'source':str(a),'target':str(b),'sha256':fingerprint(a)},{'source':str(b),'target':str(a),'sha256':fingerprint(b)}]
    result=apply_rename(root,plan);assert a.read_bytes()==b'angle B' and b.read_bytes()==b'angle A'
    undo_rename(result['journal']);assert a.read_bytes()==b'angle A' and b.read_bytes()==b'angle B'
