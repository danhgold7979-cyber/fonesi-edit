from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import shutil
import pytest
from fonesi_edit.media.validation import ExpectedStream,validate_media,MediaValidationError
from fonesi_edit.media.probe import ProbeResult,ProbeCanceled
from fonesi_edit.jobs.process import ProcessResult,ProcessError,run_owned
import fonesi_edit.media.validation as validation

VIDEO=ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25))
AUDIO=ExpectedStream(1,'audio','aac',F(0),F(1),F(1,25),sample_rate=48000,channels=1)

@pytest.fixture
def mock_validation(tmp_path,monkeypatch):
    source=tmp_path/'output';source.write_bytes(b'unchanged')
    tool=tmp_path/'tool';tool.write_bytes(b'fake');tool.chmod(0o700)
    streams=[{'index':0,'codec_type':'video','codec_name':'h264','start_time':'0','duration':'1','width':64,'height':48,'avg_frame_rate':'25/1'}]
    def probe(*a,**k):return ProbeResult('digest',json.dumps({'streams':streams}),str(tool),())
    monkeypatch.setattr(validation,'inspect_media',probe)
    monkeypatch.setattr(validation,'fingerprint',lambda *a:'digest')
    return source,tool,streams


def test_exact_mapping_and_owned_decode_flags(mock_validation,monkeypatch):
    source,tool,streams=mock_validation
    def decode(args,**kwargs):
        assert args[args.index('-map')+1]=='0:0'
        assert args[-3:]==['-f','null','-'] and '-c' not in args
        assert '-xerror' in args and args[args.index('-max_error_rate')+1]=='0'
        assert args[args.index('-protocol_whitelist')+1]=='file,pipe'
        return ProcessResult(0,b'',b'')
    monkeypatch.setattr(validation,'run_owned',decode)
    result=validate_media(source,tool,tool,(VIDEO,))
    assert result.sha256=='digest' and result.policy=='probe-and-full-decode-v1'
    assert source.read_bytes()==b'unchanged'


@pytest.mark.parametrize('field,value',[('duration','2'),('duration',None),('codec_name','hevc'),('width',65),('width',64.0),('avg_frame_rate','0/0'),('start_time','1')])
def test_metadata_mismatch_never_decodes(mock_validation,monkeypatch,field,value):
    source,tool,streams=mock_validation;streams[0][field]=value
    monkeypatch.setattr(validation,'run_owned',lambda *a,**k:pytest.fail('Mismatched metadata decoded'))
    with pytest.raises(MediaValidationError):validate_media(source,tool,tool,(VIDEO,))


def test_missing_extra_tracks_fail(mock_validation,monkeypatch):
    source,tool,streams=mock_validation;streams.append({'index':1,'codec_type':'audio'})
    with pytest.raises(MediaValidationError,match='track set'):validate_media(source,tool,tool,(VIDEO,))


@pytest.mark.parametrize('failure',['decode','timeout','changed','cancel'])
def test_failed_decode_changed_bytes_and_cancel_never_accept(mock_validation,monkeypatch,failure):
    source,tool,_=mock_validation
    def decode(*a,**k):
        if failure=='timeout':raise ProcessError('SECRET tool stderr')
        if failure=='cancel':raise ProbeCanceled('SECRET')
        return ProcessResult(7 if failure=='decode' else 0,b'',b'SECRET')
    monkeypatch.setattr(validation,'run_owned',decode)
    if failure=='changed':monkeypatch.setattr(validation,'fingerprint',lambda *a:'different')
    with pytest.raises((MediaValidationError,ProbeCanceled)) as result:validate_media(source,tool,tool,(VIDEO,))
    assert 'SECRET' not in str(result.value)


def test_expectation_requires_exact_bounded_values():
    for changes in ({'duration':1.0},{'tolerance':F(1)},{'index':True},{'frame_rate':None},{'channels':1}):
        with pytest.raises(ValueError):replace(VIDEO,**changes)


def test_actual_local_ffmpeg_probe_full_decode_and_corrupt_rejection(tmp_path):
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:pytest.skip('Explicit FFmpeg/ffprobe unavailable; actual target gate open')
    path=tmp_path/'Kiểm tra 中文.mp4'
    generated=run_owned([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','color=c=red:s=64x48:r=25:d=1',
                         '-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=1','-c:v','libx264',
                         '-pix_fmt','yuv420p','-c:a','aac','-t','1',str(path)],timeout=30)
    assert generated.returncode==0
    before=path.read_bytes()
    result=validate_media(path,ffprobe,ffmpeg,(VIDEO,AUDIO),timeout=30)
    assert result.streams==(VIDEO,AUDIO) and path.read_bytes()==before
    with pytest.raises(MediaValidationError):validate_media(path,ffprobe,ffmpeg,(replace(VIDEO,width=128),AUDIO),timeout=30)
    damaged=tmp_path/'damaged.mp4';damaged.write_bytes(before[:len(before)//2])
    with pytest.raises(MediaValidationError):validate_media(damaged,ffprobe,ffmpeg,(VIDEO,AUDIO),timeout=30)


@pytest.mark.parametrize('value',['1e10000','1e999999999999999999999','1E-10000','9'*81,'NaN',True,1.0])
def test_metadata_exponent_and_complexity_rejected_before_fraction(value,monkeypatch):
    monkeypatch.setattr(validation,'Fraction',lambda *a:pytest.fail('Unbounded metadata reached Fraction'))
    with pytest.raises(MediaValidationError):validation._number(value)


@pytest.mark.parametrize('value,expected',[('0.125',F(1,8)),('30000/1001',F(30000,1001)),('-0.25',F(-1,4)),(48000,F(48000))])
def test_fixed_decimal_and_rational_metadata(value,expected):
    assert validation._number(value)==expected
