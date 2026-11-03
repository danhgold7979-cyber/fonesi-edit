import hashlib
import struct
import zlib
from fractions import Fraction
from pathlib import Path

import pytest

from fonesi_edit.media import preview as module
from fonesi_edit.jobs.process import ProcessResult,ProcessError,ProcessCanceled


def _chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)


def _png(width=16,height=9):
    raw=b''.join(b'\x00'+bytes((24,48,72,255))*width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n'+_chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+
            _chunk(b'IDAT',zlib.compress(raw))+_chunk(b'IEND',b''))


@pytest.fixture
def inputs(tmp_path):
    source=tmp_path/'source.mp4';source.write_bytes(b'video source bytes')
    ffmpeg=tmp_path/'ffmpeg';ffmpeg.write_bytes(b'explicit fake executable');ffmpeg.chmod(0o700)
    module.clear_preview_cache()
    return source,ffmpeg,hashlib.sha256(source.read_bytes()).hexdigest()


def test_explicit_stream_timestamp_and_cache_hit_are_content_bound(inputs,monkeypatch):
    source,ffmpeg,digest=inputs;calls=[]
    def run(args,**kwargs):
        calls.append((args,kwargs))
        return ProcessResult(0,_png(),b'')
    monkeypatch.setattr(module,'run_owned',run)
    first=module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,
        stream_index=7,decoder_time=Fraction(3,2))
    second=module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,
        stream_index=7,decoder_time=Fraction(3,2))
    assert len(calls)==1
    assert first.cache_hit is False and second.cache_hit is True
    assert first.png==second.png and (first.width,first.height)==(16,9)
    args=calls[0][0]
    assert args[args.index('-ss')+1]=='1.500000000'
    assert args[args.index('-map')+1]=='0:7'
    assert args[args.index('-frames:v')+1]=='1'
    assert args[-1]=='pipe:1'
    assert calls[0][1]['max_output_bytes']==8*1024*1024


def test_source_mutation_invalidates_hash_and_refuses_stale_project_asset(inputs,monkeypatch):
    source,ffmpeg,digest=inputs
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:ProcessResult(0,_png(),b''))
    module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    source.write_bytes(b'changed source bytes')
    with pytest.raises(module.PreviewError,match='content no longer matches'):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))


def test_tool_change_invalidates_cache_and_uses_new_tool_hash(inputs,monkeypatch):
    source,ffmpeg,digest=inputs;calls=[]
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(calls.append(a) or ProcessResult(0,_png(),b'')))
    first=module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    ffmpeg.write_bytes(b'changed executable')
    second=module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    assert len(calls)==2
    assert first.tool_sha256!=second.tool_sha256
    assert second.cache_hit is False


def test_project_relative_asset_resolves_inside_project_only(tmp_path):
    root=tmp_path/'project';root.mkdir()
    media=root/'clip.mp4';media.write_bytes(b'clip')
    asset={'path_ref':{'base':'project','path':'clip.mp4'}}
    assert module.resolve_asset_path(asset,root)==media
    asset['path_ref']['path']='../outside.mp4'
    with pytest.raises(module.PreviewError):
        module.resolve_asset_path(asset,root)


def test_absolute_asset_requires_regular_non_symlink_file(tmp_path):
    source=tmp_path/'clip.mp4';source.write_bytes(b'clip')
    asset={'path_ref':{'base':'absolute','path':str(source)}}
    assert module.resolve_asset_path(asset,tmp_path)==source
    link=tmp_path/'link.mp4'
    try:link.symlink_to(source)
    except (OSError,NotImplementedError):pytest.skip('Symlink creation unavailable')
    asset['path_ref']['path']=str(link)
    with pytest.raises(module.PreviewError,match='symlinks or reparse'):
        module.resolve_asset_path(asset,tmp_path)


@pytest.mark.parametrize('timestamp,expected',[
    (Fraction(-1,50),'-0.020000000'),
    (Fraction(0),'0.000000000'),
    (Fraction(3,2),'1.500000000'),
])
def test_timestamp_contract_preserves_exact_signed_stream_time(timestamp,expected):
    assert module._timestamp(timestamp)==expected


def test_decoder_failure_and_cancellation_never_cache_a_frame(inputs,monkeypatch):
    source,ffmpeg,digest=inputs
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:ProcessResult(1,b'',b'private decoder stderr'))
    with pytest.raises(module.PreviewError,match='did not produce'):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(_ for _ in ()).throw(ProcessCanceled('private cancellation')))
    with pytest.raises(module.PreviewCanceled):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    assert not module._FRAME_CACHE


def test_invalid_stream_time_and_png_dimensions_fail_closed(inputs,monkeypatch):
    source,ffmpeg,digest=inputs
    with pytest.raises(module.PreviewError):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=-1,decoder_time=Fraction(0))
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:ProcessResult(0,_png(2048,1000),b''))
    with pytest.raises(module.PreviewError,match='dimensions exceed'):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))


def test_reparse_or_missing_source_refused_before_process_launch(inputs,monkeypatch):
    source,ffmpeg,digest=inputs;calls=[]
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(calls.append(a) or ProcessResult(0,_png(),b'')))
    with pytest.raises(module.PreviewError):
        module.extract_preview_frame(source.parent/'missing.mp4',ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))
    assert not calls

def test_empty_source_and_empty_ffmpeg_are_refused(inputs):
    source,ffmpeg,digest=inputs
    source.write_bytes(b'')
    with pytest.raises(module.PreviewError,match='Empty source/tool'):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,stream_index=0,decoder_time=Fraction(0))

def test_unknown_process_retirement_is_not_reported_as_ordinary_decoder_failure(inputs,monkeypatch):
    source,ffmpeg,digest=inputs
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(_ for _ in ()).throw(
        ProcessError('All-descendant retirement unconfirmed: job remains active')))
    with pytest.raises(module.PreviewRetirementUnknown,match='do not retry or close'):
        module.extract_preview_frame(source,ffmpeg,expected_sha256=digest,
            stream_index=0,decoder_time=Fraction(0))

def test_audio_waveform_extracts_bounded_float32_bins_and_reuses_cache(inputs,monkeypatch):
    source,ffmpeg,digest=inputs;calls=[]
    pcm=struct.pack('<4f',-1.0,-0.5,0.5,1.0)
    def run(args,**kwargs):
        calls.append((args,kwargs))
        return ProcessResult(0,pcm,b'')
    monkeypatch.setattr(module,'run_owned',run)
    first=module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
        stream_index=3,decoder_start=Fraction(-1,50),duration=Fraction(1,2),bucket_count=2)
    second=module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
        stream_index=3,decoder_start=Fraction(-1,50),duration=Fraction(1,2),bucket_count=2)
    assert len(calls)==1
    assert first.peaks==((-1.0,-0.5),(0.5,1.0))
    assert first.sample_count==4 and first.sample_rate==8000
    assert first.cache_hit is False and second.cache_hit is True
    args=calls[0][0]
    assert args[args.index('-ss')+1]=='-0.020000000'
    assert args[args.index('-map')+1]=='0:3'
    assert args[args.index('-t')+1]=='0.500000000'
    assert args[args.index('-ac')+1]=='1' and args[args.index('-ar')+1]=='8000'
    assert calls[0][1]['max_output_bytes']==2*1024*1024
    assert source.read_bytes()==b'video source bytes'


@pytest.mark.parametrize('pcm',[
    b'abc',
    struct.pack('<2f',0.0,float('nan')),
    struct.pack('<2f',0.0,float('inf')),
])
def test_audio_waveform_rejects_malformed_or_nonfinite_pcm(inputs,monkeypatch,pcm):
    source,ffmpeg,digest=inputs
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:ProcessResult(0,pcm,b''))
    with pytest.raises(module.PreviewError):
        module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
            stream_index=1,decoder_start=Fraction(0),duration=Fraction(1),bucket_count=32)


def test_audio_waveform_rejects_duration_and_sample_bounds_before_launch(inputs,monkeypatch):
    source,ffmpeg,digest=inputs;calls=[]
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(calls.append(a) or ProcessResult(0,struct.pack('<f',0),b'')))
    with pytest.raises(module.PreviewError,match='bounded waveform'):
        module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
            stream_index=0,decoder_start=Fraction(0),duration=Fraction(61),bucket_count=32)
    assert not calls


def test_audio_waveform_process_cancellation_and_unknown_retirement_are_distinct(inputs,monkeypatch):
    source,ffmpeg,digest=inputs
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(_ for _ in ()).throw(ProcessCanceled('cancel')))
    with pytest.raises(module.PreviewCanceled):
        module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
            stream_index=0,decoder_start=Fraction(0),duration=Fraction(1),bucket_count=32)
    monkeypatch.setattr(module,'run_owned',lambda *a,**k:(_ for _ in ()).throw(
        ProcessError('Job quiescence query failed; process retirement unconfirmed')))
    with pytest.raises(module.PreviewRetirementUnknown):
        module.extract_audio_waveform(source,ffmpeg,expected_sha256=digest,
            stream_index=0,decoder_start=Fraction(0),duration=Fraction(1),bucket_count=32)
