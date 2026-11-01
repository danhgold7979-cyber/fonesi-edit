from dataclasses import replace
import json
import pytest
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.domain.composition import CompositionPlan,canonical


def output(role='video',name='Kết quả 中文.mp4'):
    return RequiredOutput(role,'media','C:/Videos edit',name)


def test_manifest_is_closed_immutable_and_order_canonical():
    a=output();b=RequiredOutput('sub','subtitle','C:/Videos edit','Caption.srt')
    manifest=RequiredOutputs((a,b));other=RequiredOutputs((b,a))
    assert manifest.to_dict()==other.to_dict()
    changed=manifest.to_dict();changed['required'].clear()
    assert len(manifest.items)==2
    with pytest.raises(AttributeError):a.role='omitted'
    with pytest.raises(ValueError):RequiredOutputs((a,a))
    with pytest.raises(ValueError):RequiredOutputs((a,replace(a,role='other')))
    with pytest.raises(ValueError):RequiredOutputs([])


@pytest.mark.parametrize('changes',[
 {'role':'../video'},{'kind':'anything'},{'destination_root':'relative'},
 {'destination_root':'C:/root/../elsewhere'},{'destination_root':'//server/share'},
 {'final_name':'../source.mp4'},{'final_name':'CON.txt'},{'final_name':'ads:stream'},
])
def test_invalid_manifest_is_rejected_before_io(changes):
    with pytest.raises((ValueError,RuntimeError)):replace(output(),**changes)


def test_v1_exact_snapshot_preserved_and_v2_required_roles_reopen(tmp_path,empty_plan):
    path=tmp_path/'jobs.db';plan=CompositionPlan.parse(empty_plan)
    a=output();b=RequiredOutput('subtitle','subtitle','C:/Videos edit','Caption.srt')
    outputs=RequiredOutputs((a,b))
    repo=JobRepository(path)
    try:
        old=repo.submit('old',plan,42)
        assert old.snapshot_json==canonical({'version':1,'composition':plan.to_dict(),'seed':42})
        new=repo.submit('new',plan,42,outputs=outputs)
        assert json.loads(new.snapshot_json)['outputs']==outputs.to_dict()
        assert json.loads(new.snapshot_json)['version']==2
        assert repo.submit('new',plan,42,outputs=RequiredOutputs((b,a)))==new
        for changed in (None,RequiredOutputs((a,)),RequiredOutputs((replace(a,final_name='different.mp4'),b))):
            with pytest.raises(JobConflict):repo.submit('new',plan,42,outputs=changed)
    finally:repo.close()
    repo=JobRepository(path)
    try:
        assert repo.get(old.id)==old and repo.get(new.id)==new
        with pytest.raises(ValueError):repo.submit('bad',plan,42,outputs={'validated':True})
    finally:repo.close()
