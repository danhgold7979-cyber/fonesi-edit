import json,hashlib
from fractions import Fraction as Q
import pytest
from fonesi_edit.media import frames as module
from fonesi_edit.media.probe import ProbeResult,ProbeError,ProbeCanceled
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.jobs.process import ProcessResult,ProcessError,ProcessCanceled


@pytest.fixture
def context(tmp_path):
    source=tmp_path/'media';source.write_bytes(b'owned media');tool=tmp_path/'ffprobe';tool.write_bytes(b'owned test stand-in');tool.chmod(0o700)
    stream={'index':3,'codec_type':'video','codec_name':'h264','time_base':'1/1000','start_pts':-100,'duration_ts':1000,'disposition':{'attached_pic':0}}
    obs=normalize_probe(ProbeResult(hashlib.sha256(source.read_bytes()).hexdigest(),json.dumps({'streams':[stream]}),str(tool),()))
    return source,tool,obs,stream


def output(stream,frames,code=0,stderr=b''):return ProcessResult(code,json.dumps({'streams':[stream],'frames':frames}).encode(),stderr)
def frame(pts):return {'stream_index':3,'pts':pts,'best_effort_timestamp':pts+1,'duration':40,'pkt_duration':50}


def test_signed_repeated_discontinuous_pts_preserved_and_exact_binding(context,monkeypatch):
    source,tool,obs,stream=context;calls=[]
    def run(args,**kwargs):calls.append(args);return output(stream,[frame(-100),frame(-60),frame(-60),frame(-90)])
    monkeypatch.setattr(module,'run_owned',run)
    result=module.observe_frames(source,tool,obs,3)
    assert [x.pts for x in result.frames]==[-100,-60,-60,-90]
    assert [x.best_effort_timestamp for x in result.frames]==[-99,-59,-59,-89]
    assert result.time_base==Q(1,1000) and result.start_pts==-100 and not result.render_ready
    assert 'NONINCREASING_PTS_PRESERVED' in result.frames[2].diagnostics and 'DURATION_FIELDS_DIFFER' in result.frames[0].diagnostics
    assert result.source_sha256==obs.sha256 and result.tool_sha256==hashlib.sha256(tool.read_bytes()).hexdigest()
    assert calls[0][calls[0].index('-select_streams')+1]=='3' and '-read_intervals' not in calls[0]


@pytest.mark.parametrize('kind',['cap','nonzero','stderr'])
def test_incomplete_observations_never_claim_eof(context,monkeypatch,kind):
    source,tool,obs,stream=context
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:output(stream,[frame(0),frame(40)],code=2 if kind=='nonzero' else 0,stderr=b'PRIVATE DECODE ERROR' if kind=='stderr' else b''))
    result=module.observe_frames(source,tool,obs,3,max_frames=1 if kind=='cap' else 100)
    assert result.status=='INCOMPLETE' and not result.render_ready
    assert len(result.frames)==(1 if kind=='cap' else 2) and 'PRIVATE' not in str(result)


@pytest.mark.parametrize('kind',['stream','timebase','start','frameindex','source','tool'])
def test_binding_mismatch_never_returns_frame_map(context,monkeypatch,kind):
    source,tool,obs,stream=context;rows=[frame(0)]
    def run(*a,**k):
        if kind=='stream':stream['index']=0
        elif kind=='timebase':stream['time_base']='1/90000'
        elif kind=='start':stream['start_pts']=0
        elif kind=='frameindex':rows[0]['stream_index']=0
        elif kind=='source':source.write_bytes(b'changed')
        elif kind=='tool':tool.write_bytes(b'changed')
        return output(stream,rows)
    monkeypatch.setattr(module,'run_owned',run)
    with pytest.raises(ProbeError):module.observe_frames(source,tool,obs,3)


@pytest.mark.parametrize('failure',[ProcessCanceled('private'),ProcessError('retirement unknown')])
def test_failed_owned_process_never_fabricates_partial_json(context,monkeypatch,failure):
    source,tool,obs,_=context
    def run(*a,**k):raise failure
    monkeypatch.setattr(module,'run_owned',run)
    with pytest.raises(ProbeError) as caught:module.observe_frames(source,tool,obs,3)
    assert 'private' not in str(caught.value) and caught.value.__cause__ is failure


def test_unknown_timestamps_remain_unknown_and_empty_scan_not_readiness(context,monkeypatch):
    source,tool,obs,stream=context
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:output(stream,[{'stream_index':3,'best_effort_timestamp':-5}]))
    result=module.observe_frames(source,tool,obs,3)
    assert result.frames[0].pts is None and result.frames[0].duration is None and result.frames[0].best_effort_timestamp==-5


def test_truncated_json_and_prelaunch_cancel_refuse(context,monkeypatch):
    source,tool,obs,_=context;calls=[]
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(calls.append(1) or ProcessResult(0,b'{"frames":[',b'')))
    with pytest.raises(ProbeCanceled):module.observe_frames(source,tool,obs,3,cancel=lambda:True)
    assert not calls
    with pytest.raises(ProbeError):module.observe_frames(source,tool,obs,3)


@pytest.mark.parametrize('args',[['--frame-stream','0'],['--inspect-media','/x','--ffprobe','/tool','--frame-limit','2'],['--inspect-media','/x','--ffprobe','/tool','--frame-stream','-1']])
def test_cli_frame_options_refuse_before_tool_execution(args):
    from fonesi_edit.__main__ import main
    with pytest.raises(SystemExit) as caught:main(args)
    assert caught.value.code==2


def test_nonregular_input_refused_before_hash_or_launch(context,monkeypatch,tmp_path):
    source,tool,obs,_=context
    def forbidden(*a,**k):raise AssertionError('Nonregular input reached hash/launch')
    monkeypatch.setattr(module,'fingerprint',forbidden);monkeypatch.setattr(module,'run_owned',forbidden)
    with pytest.raises(ProbeError):module.observe_frames(tmp_path,tool,obs,3)


def test_cli_incomplete_frame_scan_has_distinct_exit_three(context,monkeypatch,capsys):
    from fonesi_edit.__main__ import main
    from fonesi_edit.media import probe as probe_module
    source,tool,obs,stream=context
    monkeypatch.setattr(probe_module,'inspect_media',lambda *a:ProbeResult(obs.sha256,json.dumps({'streams':[stream]}),str(tool),()))
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:output(stream,[frame(0),frame(40)]))
    assert main(['--inspect-media',str(source),'--ffprobe',str(tool),'--frame-stream','3','--frame-limit','1'])==3
    result=json.loads(capsys.readouterr().out)
    assert result['frame_scan']['status']=='INCOMPLETE' and len(result['frame_scan']['frames'])==1


@pytest.mark.parametrize('unknown',[False,True])
def test_frame_invocation_records_actual_retirement_or_unknown(context,monkeypatch,unknown):
    import sys
    from fonesi_edit.media.retirement import ValidationLifecycle
    from fonesi_edit.jobs.process import run_owned as actual_runner
    source,tool,obs,stream=context;operation=object();lifecycle=ValidationLifecycle(operation)
    def runner(args,**kwargs):
        if unknown:raise ProcessError('Injected unconfirmed frame retirement')
        payload=json.dumps({'streams':[stream],'frames':[frame(0)]})
        return actual_runner([sys.executable,'-c',f'print({payload!r})'],**kwargs)
    monkeypatch.setattr(module,'run_owned',runner)
    if unknown:
        with pytest.raises(ProbeError):
            with lifecycle.validation_body():module.observe_frames(source,tool,obs,3,_lifecycle=lifecycle)
        assert not lifecycle.confirmed_for(operation) and lifecycle.mechanisms==(None,)
    else:
        with lifecycle.validation_body():result=module.observe_frames(source,tool,obs,3,_lifecycle=lifecycle)
        assert result.status=='OBSERVED_EOF' and lifecycle.confirmed_for(operation) and len(lifecycle.mechanisms)==1
