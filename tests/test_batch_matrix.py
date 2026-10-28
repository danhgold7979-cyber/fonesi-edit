from pathlib import Path
import itertools
import pytest
from fonesi_edit.core.model import *
from fonesi_edit.core.storage import Store
from fonesi_edit.services.batch import *
from fonesi_edit.services.matrix import *


def test_scan_exclusions_and_symlink(tmp_path):
    for name in ['source/a.mp4','output/b.mp4','cache/c.mp4','Kênh edit/d.mp4']:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'x')
    (tmp_path/'loop').symlink_to(tmp_path,target_is_directory=True)
    assert [p.name for p in scan_folders([tmp_path])]==['a.mp4']


def test_duration_policies_no_implicit_concat():
    c=Clip('a',0,2*US)
    with pytest.raises(ValueError):fit_duration(c,5*US)
    with pytest.raises(ValueError):fit_duration(c,10*US,'speed')
    assert [x.time_map.duration for x in fit_duration(c,5*US,'loop')]==[2*US,2*US,US]
    assert sum(x.time_map.duration for x in fit_duration(c,5*US,'freeze'))==5*US
    assert fit_duration(c,US,'speed')[0].speed=='2'
    assert allocate_durations([2,3],5*US,overlap=US)==[3*US,3*US]


def test_batch_real_scan_plan_invalid_isolated(media,tmp_path):
    bad=tmp_path/'bad.mp4';bad.write_bytes(b'bad')
    plans=make_batch([media,bad],Project(width=320,height=180),tmp_path/'output')
    assert [p['status'] for p in plans]==['ready','invalid'];assert plans[0]['project']['clips'][0]['asset_id']==plans[0]['project']['assets'][0]['id']


def test_matrix_exhaustive_unique_small_oracle():
    result=generate([2,3],6,Rules(seed=42))
    assert result['status']=='complete';assert set(map(tuple,result['rows']))==set(itertools.product(range(2),range(3)))
    assert generate([2,3],7,Rules())['status']=='proven_impossible'


def test_matrix_strict_window_k_history_reproducible():
    r=Rules(window=1,different=2,seed=3)
    a=generate([3,3,3],7,r);b=generate([3,3,3],7,r)
    assert a['rows']==b['rows'];assert a['status']=='complete';assert validate_rows(a['rows'],r) is None
    assert generate([2,3],5,Rules(window=2))['status']=='proven_impossible'
    wrong=[a['rows'][0],a['rows'][0]];assert validate_rows(wrong,r)==1


def test_huge_matrix_bounded_and_cancel():
    result=generate([1000]*12,10,Rules(timeout=2));assert len(result['rows'])==10;assert result['theoretical']==1000**12
    assert generate([2,2],2,Rules(),cancel=lambda:True)['status']=='canceled'
    assert generate([3]*10,1000,Rules(timeout=0))['status']=='timeout'


def test_matrix_lock_and_reservation(tmp_path):
    result=generate([3,3],3,Rules(),locked={0:{0:2}});assert result['rows'][0][0]==2
    s=Store(tmp_path/'s.db');key=reserve(s,'p',['a','b'],'job')
    with pytest.raises(ValueError):reserve(s,'p',['a','b'],'other')
    with pytest.raises(ValueError):commit_history(s,'p',key,'job',{'path':'x'})
    commit_history(s,'p',key,'job',{'validated':True,'path':'out'})
    with pytest.raises(ValueError):reserve(s,'p',['a','b'],'new')
