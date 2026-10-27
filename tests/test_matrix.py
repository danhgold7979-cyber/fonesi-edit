from pathlib import Path
import time
import pytest
from fonesi_edit.domain import Composition
from fonesi_edit.matrix import Angle,generate,combination,valid_against,enqueue_rows,history
from fonesi_edit.storage import Store
from fonesi_edit.jobs import Scheduler
from fonesi_edit.prototypes.media import create_fixture


def scenes(sizes):return [[Angle(i+1,j+1,f'{i}/{j}.mp4',f'hash-{i}-{j}') for j in range(n)] for i,n in enumerate(sizes)]


def test_small_space_complete_unique_and_reproducible():
    source=scenes([2,3]);a=generate(source,6,seed=1);b=generate(source,6,seed=1)
    assert a['complete'] and len({combination(row) for row in a['rows']})==6
    assert [combination(r) for r in a['rows']]==[combination(r) for r in b['rows']]
    with pytest.raises(ValueError):generate(source,7)


def test_window_difference_and_locks_are_not_relaxed():
    source=scenes([3,3]);plan=generate(source,3,seed=4,window=1,different=2)
    assert plan['complete']
    previous=[]
    for row in plan['rows']:
        assert valid_against(row,previous,1,2)
        previous.append([a.hash for a in row])
    locked=generate(source,1,locks={0:{0:source[0][2].hash}})
    assert locked['rows'][0][0].index==3


def test_reservation_atomic_and_worker_commits_validated_output(tmp_path):
    files=create_fixture(tmp_path/'media',duration=.5);path=str(files['source'])
    rows=[[Angle(1,1,path,'a'),Angle(2,1,path,'b')]]
    store=Store(tmp_path/'state.db');preset=Composition(width=320,height=180,encoder='cpu')
    ids=enqueue_rows(store,'project',rows,preset,tmp_path/'out')
    assert history(store,'project')==[['a','b']]
    with pytest.raises(ValueError):enqueue_rows(store,'project',rows,preset,tmp_path/'out')
    scheduler=Scheduler(store);deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        scheduler.tick()
        if not scheduler.active and store.job(ids[0])['state'] in {'failed','succeeded'}:break
        time.sleep(.05)
    assert store.job(ids[0])['state']=='succeeded',store.job(ids[0])['error']
    with store.connect() as c:assert c.execute('SELECT state FROM matrix_history').fetchone()[0]=='succeeded'


def test_final_reservation_rechecks_current_history_window_atomically(tmp_path):
    f=create_fixture(tmp_path/'media',duration=.5);path=str(f['source']);store=Store(tmp_path/'state.db');preset=Composition(width=320,height=180,encoder='cpu')
    first=[Angle(1,1,path,'a'),Angle(2,1,path,'b')]
    second=[Angle(1,1,path,'a'),Angle(2,2,path,'c')]
    enqueue_rows(store,'project',[first],preset,tmp_path/'out')
    with pytest.raises(ValueError,match='W/K'):enqueue_rows(store,'project',[second],preset,tmp_path/'out',window=1,different=2)
    assert len(store.jobs())==1 and history(store,'project')==[['a','b']]
    assert Path(store.jobs()[0]['payload']['output']).name.startswith('video_000001_')
