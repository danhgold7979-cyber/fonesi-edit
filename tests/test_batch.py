from pathlib import Path
import pytest
from fonesi_edit.batch import scan_folders,fit_duration,batch_plan
from fonesi_edit.domain import Composition,Clip
from fonesi_edit.prototypes.media import create_fixture,probe
from fonesi_edit.render import render_composition


def test_duration_keeps_scenes_with_bounds_and_reports_infeasible():
    c=Composition(clips=[Clip('a',end=4),Clip('b',end=6)],transition=.2)
    result=fit_duration(c,7,minimum=.5,maximum=2,allocation='equal')
    assert len(result.clips)==2
    assert abs(sum((x.end-x.start)/x.speed for x in result.clips)-.2-7)<.001
    assert all(.5<=x.speed<=2 for x in result.clips)
    with pytest.raises(ValueError):fit_duration(c,1,minimum=.5,maximum=2)
    assert c.clips[0].speed==1


def test_scan_ignores_outputs_and_preserves_parent_folders(tmp_path):
    for name in ['A/videos/a.mp4','A edit/videos/out.mp4','.cache/skip.mp4','B/videos/b.mp4']:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
    groups=scan_folders(tmp_path)
    assert set(Path(p).name for p in groups)=={'A','B'}
    assert (tmp_path/'A edit/videos/out.mp4').exists()


@pytest.mark.parametrize('policy',['loop','freeze'])
def test_explicit_extension_policy_produces_real_target_duration(tmp_path,policy):
    files=create_fixture(tmp_path/'media',duration=.5)
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(files['source']),end=.5)])
    fitted=fit_duration(c,1.5,policy=policy)
    result=render_composition(fitted,tmp_path/'result.mp4')
    assert abs(probe(Path(result['output'])).duration-1.5)<.15
