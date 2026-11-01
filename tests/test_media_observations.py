from fractions import Fraction as Q
import json
import pytest
from fonesi_edit.media.probe import ProbeResult,ProbeError
from fonesi_edit.media.observations import normalize_probe


def probe(streams,format=None):return ProbeResult('a'*64,json.dumps({'streams':streams,'format':format or {}}),'/explicit/ffprobe',())
def video(index=3):return dict(index=index,codec_type='video',codec_name='h264',time_base='1/90000',start_pts=-3000,start_time='-0.033333',duration_ts=90000,duration='1.000000',width=720,height=576,sample_aspect_ratio='16:15',disposition={'attached_pic':0})


def test_exact_signed_stream_ticks_indices_and_container_summary_are_distinct():
    audio=dict(index=8,codec_type='audio',codec_name='aac',time_base='1/48000',start_pts=12000,duration_ts=48000,sample_rate='48000',channels=6,channel_layout='5.1(side)')
    result=normalize_probe(probe([audio,video()],{'duration':'2.000000'}))
    assert [x.index for x in result.streams]==[8,3]
    assert result.streams[1].start==Q(-1,30) and result.streams[1].sar==Q(16,15)
    assert result.streams[0].start==Q(1,4) and result.container_duration==2
    assert result.streams[0].channel_layout=='5.1(side)' and 'COMPOSITION_LAYOUT_UNRESOLVED' in result.streams[0].diagnostics
    assert not result.render_ready and 'START_TIME_SUMMARY_CONFLICT' not in result.streams[1].diagnostics


def test_unknowns_preserved_no_stereo_squarepixel_or_fake_duration():
    result=normalize_probe(probe([{'index':9,'codec_type':'audio','codec_name':'aac'},{'index':2,'codec_type':'data'}]))
    assert len(result.streams)==2 and result.streams[0].duration is None and result.streams[0].channels is None
    assert result.streams[1].kind=='data' and result.container_duration is None


def test_attached_picture_and_matrix_reflection_preserved_without_rotation_coercion():
    v=video();v['disposition']['attached_pic']=1
    v['side_data_list']=[{'side_data_type':'Display Matrix','rotation':-90,'displaymatrix':'\n00000000: -65536 0 0\n00000001: 0 65536 0\n00000002: 0 0 1073741824\n'}]
    stream=normalize_probe(probe([v])).streams[0]
    assert stream.display_matrix==(-65536,0,0,0,65536,0,0,0,1073741824)
    assert stream.rotation_degrees==-90 and stream.attached_picture
    assert 'ATTACHED_PICTURE_NOT_TIMELINE_VIDEO' in stream.diagnostics


@pytest.mark.parametrize('value',['1e1000000','NaN','1/0','0:1',True])
def test_invalid_sar_and_unknown_duration_not_invented(value):
    v=video();v['sample_aspect_ratio']=value;v.pop('duration_ts');v['duration']='N/A'
    stream=normalize_probe(probe([v])).streams[0]
    assert stream.sar is None and stream.duration is None


def test_tick_decimal_conflict_keeps_exact_observation_and_reports():
    v=video();v['start_time']='100.000000'
    stream=normalize_probe(probe([v])).streams[0]
    assert stream.start==Q(-1,30) and 'START_TIME_SUMMARY_CONFLICT' in stream.diagnostics


def test_duplicate_indices_and_nonfinite_or_duplicate_json_refused():
    with pytest.raises(ProbeError):normalize_probe(probe([video(),video()]))
    for raw in ('{"streams":[],"streams":[]}','{"streams":[],"x":1e999}'):
        with pytest.raises(ProbeError):normalize_probe(ProbeResult('a'*64,raw,'/explicit/ffprobe',()))


def test_cli_inspection_uses_explicit_probe_no_private_metadata(tmp_path,monkeypatch,capsys):
    from fonesi_edit.__main__ import main
    from fonesi_edit.media import probe as module
    calls=[]
    def inspect(path,tool):calls.append((path,tool));return probe([video()],{'duration':'1','tags':{'comment':'PRIVATE'}})
    monkeypatch.setattr(module,'inspect_media',inspect)
    assert main(['--inspect-media',str(tmp_path/'media'),'--ffprobe',str(tmp_path/'ffprobe')])==0
    out=capsys.readouterr();data=json.loads(out.out)
    assert len(calls)==1 and data['render_ready'] is False and 'PRIVATE' not in out.out
    assert data['streams'][0]['start']=={'num':-1,'den':30}


@pytest.mark.parametrize('args',[['--inspect-media','relative','--ffprobe','relative'],['--ffprobe','/tool'],['--inspect-media','/media']])
def test_cli_inspection_requires_explicit_mode_and_paths(args):
    from fonesi_edit.__main__ import main
    with pytest.raises(SystemExit) as caught:main(args)
    assert caught.value.code==2


def test_fresh_inspection_cli_imports_no_gui_or_storage(tmp_path):
    import os,sys,subprocess
    from pathlib import Path
    script='''import builtins,json,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.startswith(('PySide6','fonesi_edit.storage')):raise AssertionError('Unexpected GUI/storage import')
    return original(name,*args,**kwargs)
builtins.__import__=guarded
from fonesi_edit.media import probe
probe.inspect_media=lambda *args:probe.ProbeResult('a'*64,json.dumps({'streams':[{'index':0,'codec_type':'data'}]}),'/explicit',())
from fonesi_edit.__main__ import main
raise SystemExit(main(sys.argv[1:]))
'''
    before=list(tmp_path.iterdir())
    result=subprocess.run([sys.executable,'-c',script,'--inspect-media',str(tmp_path/'media'),'--ffprobe',str(tmp_path/'ffprobe')],capture_output=True,text=True,timeout=20,env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')})
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['render_ready'] is False and list(tmp_path.iterdir())==before


def test_fraction_summary_provenance_and_conflict_are_not_decimal_rounding():
    v=video();v['start_time']='1/3'
    stream=normalize_probe(probe([v])).streams[0]
    assert 'START_TIME_SUMMARY_CONFLICT' in stream.diagnostics
    v.pop('start_pts');stream=normalize_probe(probe([v])).streams[0]
    assert stream.start==Q(1,3) and stream.start_basis=='RATIONAL_SUMMARY'


def test_character_bound_precedes_encoding_oversized_probe():
    class Oversized(str):
        def encode(self,*args,**kwargs):raise AssertionError('Oversized metadata encoded')
    with pytest.raises(ProbeError):normalize_probe(ProbeResult('a'*64,Oversized('x'*(16*1024*1024+1)),'/tool',()))


@pytest.mark.parametrize('rotation',[None,'NaN'])
def test_raw_matrix_without_valid_rotation_summary_retains_unknown_provenance(rotation):
    v=video();v['side_data_list']=[{'side_data_type':'Display Matrix','rotation':rotation,'displaymatrix':'00000000: 65536 0 0\n00000001: 0 65536 0\n00000002: 0 0 1073741824'}]
    stream=normalize_probe(probe([v])).streams[0]
    assert stream.display_matrix is not None and stream.rotation_degrees is None
    assert stream.rotation_basis=='UNKNOWN' and 'ROTATION_SUMMARY_UNKNOWN' in stream.diagnostics
