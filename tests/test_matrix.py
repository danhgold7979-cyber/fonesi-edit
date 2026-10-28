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


def test_duplicate_history_does_not_understate_remaining_matrix_capacity():
    source=scenes([2,2])
    seen=[source[0][0].hash,source[1][0].hash]
    old_history=[seen[:],seen[:]]
    result=generate(source,3,seed=7,history=old_history)
    assert result['complete'] and len(result['rows'])==3
    assert len({combination(row) for row in result['rows']})==3
    assert all([a.hash for a in row]!=seen for row in result['rows'])
    assert old_history==[seen,seen]


def test_locked_matrix_row_scene_indices_are_validated_and_strings_normalized():
    source=scenes([2,2])
    result=generate(source,1,locks={'0':{'1':source[1][1].hash}})
    assert result['complete']
    assert result['rows'][0][1].hash==source[1][1].hash
    for locks in (
        {1:{0:source[0][0].hash}},
        {-1:{0:source[0][0].hash}},
        {0:{2:source[0][0].hash}},
        {0:{-1:source[0][0].hash}},
        {0:{0:'unknown-hash'}},
        {'not-an-index':{0:source[0][0].hash}},
    ):
        with pytest.raises(ValueError,match='Locked|locked'):
            generate(source,1,locks=locks)



def test_regenerate_one_row_preserves_locked_cell_and_forward_wk():
    from fonesi_edit.matrix import regenerate_row, matrix_rows_valid
    source = scenes([4, 4])
    rows = generate(source, 4, seed=8, window=1, different=2)['rows']
    before = [[angle.hash for angle in row] for row in rows]
    locks = {0: rows[1][0].hash}
    result = regenerate_row(source, rows, 1, seed=11, window=1, different=2,
                            locks=locks, seconds=3)
    updated = [list(row) for row in rows]
    updated[1] = result['row']
    assert result['row'][0].hash == locks[0]
    assert result['row'][1].hash != rows[1][1].hash
    assert [[a.hash for a in row] for row in rows] == before
    assert [a.hash for a in updated[0]] == before[0]
    assert [a.hash for a in updated[2]] == before[2]
    assert [a.hash for a in updated[3]] == before[3]
    assert matrix_rows_valid(updated, [], 1, 2)
    assert [a.hash for a in regenerate_row(source, rows, 1, seed=11,
        window=1, different=2, locks=locks, seconds=3)['row']] == [
        a.hash for a in result['row']]


def test_regenerate_row_checks_later_rows_not_only_previous():
    from fonesi_edit.matrix import regenerate_row, matrix_rows_valid
    source = scenes([3])
    rows = [[source[0][0]], [source[0][1]], [source[0][2]]]
    assert matrix_rows_valid(rows, [], window=1, different=0)
    # No alternative exists: replacing middle with either neighbor would
    # break W=1 of the middle or *following* row.
    with pytest.raises(ValueError, match='Không có góc thay thế'):
        regenerate_row(source, rows, 1, seed=1, window=1, seconds=2)
    assert [row[0].hash for row in rows] == [a.hash for a in source[0]]


def test_regenerate_row_rejects_locked_and_historical_combinations_without_changes():
    from fonesi_edit.matrix import regenerate_row
    source=scenes([2,2])
    rows=[[source[0][0],source[1][0]]]
    historical=[[source[0][0].hash,source[1][1].hash],
                [source[0][1].hash,source[1][0].hash]]
    locked={0:rows[0][0].hash}
    with pytest.raises(ValueError,match='Không có góc thay thế'):
        regenerate_row(source,rows,0,locks=locked,history=historical,seconds=2)
    with pytest.raises(ValueError,match='All angles'):
        regenerate_row(source,rows,0,locks={0:rows[0][0].hash,1:rows[0][1].hash})
    with pytest.raises(ValueError,match='Locked angle'):
        regenerate_row(source,rows,0,locks={0:source[0][1].hash})
    assert rows[0][0]==source[0][0]


def test_regenerate_row_cancel_and_bad_index_do_not_mutate_rows():
    from threading import Event
    from fonesi_edit.matrix import regenerate_row
    source=scenes([2,3])
    rows=[[source[0][0],source[1][0]]]
    event=Event();event.set()
    with pytest.raises(RuntimeError,match='Canceled'):
        regenerate_row(source,rows,0,seconds=1,cancel=event)
    with pytest.raises(ValueError,match='row index'):
        regenerate_row(source,rows,-1)
    with pytest.raises(ValueError,match='time budget'):
        regenerate_row(source,rows,0,seconds=0)
    assert rows==[[source[0][0],source[1][0]]]



def test_planned_angle_usage_includes_unselected_zero_count_angles():
    from fonesi_edit.matrix import angle_usage
    source=scenes([3,2])
    rows=[[source[0][0],source[1][1]],[source[0][0],source[1][0]]]
    usage=angle_usage(source,rows)
    assert [(item['angle'],item['uses']) for item in usage[0]]==[(1,2),(2,0),(3,0)]
    assert [(item['angle'],item['uses']) for item in usage[1]]==[(1,1),(2,1)]
    assert all(item['hash']==source[i][j].hash for i,group in enumerate(usage)
               for j,item in enumerate(group))
    assert sum(item['uses'] for item in usage[0])==len(rows)
    with pytest.raises(ValueError,match='row length'):
        angle_usage(source,[[source[0][0]]])
    with pytest.raises(ValueError,match='absent'):
        angle_usage(source,[[Angle(1,4,'/invalid','unknown'),source[1][0]]])


def test_matrix_audio_duration_weights_follow_real_ffprobe_and_snapshot(tmp_path):
    from fonesi_edit.matrix import row_composition
    from fonesi_edit.domain import Composition
    fixture=create_fixture(tmp_path/'media',duration=1)
    clip=str(fixture['source'])
    row=[Angle(1,1,clip,'scene-one'),Angle(2,1,clip,'scene-two')]
    preset=Composition(width=320,height=180,fps=25,encoder='cpu')
    before=preset.to_dict()
    comp=row_composition(row,preset,clip,allocation='weights',
                         minimum=.1,maximum=10,weights=[1,3])
    lengths=[(c.end-c.start)/c.speed for c in comp.clips]
    assert len(lengths)==2
    assert abs(lengths[0]/lengths[1]-1/3)<.01
    assert abs(sum(lengths)-1)<.03
    assert comp.audio[0]['mode']=='main'
    assert preset.to_dict()==before
    store=Store(tmp_path/'state.db')
    jobs=enqueue_rows(store,'weights-test',[row],preset,tmp_path/'out',clip,
                      'weights',minimum=.1,maximum=10,weights=[1,3])
    queued=store.job(jobs[0])['payload']['composition']['clips']
    queued_lengths=[(c['end']-c['start'])/c['speed'] for c in queued]
    assert abs(queued_lengths[0]/queued_lengths[1]-1/3)<.01
    with pytest.raises(ValueError,match='Manual duration weights'):
        row_composition(row,preset,clip,allocation='weights')


def test_matrix_manual_scene_durations_without_audio_and_explicit_audio_mismatch(tmp_path):
    from fonesi_edit.matrix import row_composition
    fixture=create_fixture(tmp_path/'media',duration=1)
    source=str(fixture['source'])
    angles=[Angle(1,1,source,'clip-a'),Angle(2,1,source,'clip-b')]
    preset=Composition(width=320,height=180,fps=25,encoder='cpu')
    comp=row_composition(angles,preset,allocation='manual',
                         minimum=.1,maximum=10,manual_durations=[.25,.75])
    actual=[(clip.end-clip.start)/clip.speed for clip in comp.clips]
    assert all(abs(a-b)<.002 for a,b in zip(actual,[.25,.75]))
    assert abs(comp.duration_target-1)<.002
    with pytest.raises(ValueError,match='sum to target'):
        row_composition(angles,preset,source,allocation='manual',
                        minimum=.1,maximum=10,manual_durations=[.2,.3])
    with pytest.raises(ValueError,match='Weighted scenes require'):
        row_composition(angles,preset,allocation='weights',weights=[1,2])
