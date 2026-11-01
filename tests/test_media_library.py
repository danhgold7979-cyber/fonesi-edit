from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json,uuid
import pytest
from fonesi_edit.media.probe import ProbeResult
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.domain.media_library import (MediaLibrary,MediaRecord,MediaPath,MediaLibraryError,
    MediaLibraryConflict,observation_from_dict,validate_observation)


def observation(content=b'media',raw=None):
    raw=raw or {'streams':[{'index':3,'codec_type':'video','codec_name':'mpeg4','time_base':'1/1000',
        'start_pts':-20,'duration_ts':1000,'width':32,'height':24,'sample_aspect_ratio':'4:3',
        'disposition':{'attached_pic':0}}],'format':{'duration':'1'}}
    return normalize_probe(ProbeResult(sha256(content).hexdigest(),json.dumps(raw),'fixture-not-executed',()))


def record(path='media.bin',content=b'media',*,raw=None,id=None):
    digest=sha256(content).hexdigest()
    return MediaRecord(id or str(uuid.uuid4()),digest,len(content),MediaPath('project',path,digest),'OBSERVED',observation(content,raw))


def test_unresolved_no_audio_signed_time_and_unknown_tracks_roundtrip():
    raw={'streams':[{'index':7,'codec_type':'audio','time_base':'1/48000','start_pts':-1024,'duration_ts':48000},
                    {'index':2,'codec_type':'video','disposition':{'attached_pic':1}},
                    {'index':9,'codec_type':'data'}]}
    item=record(raw=raw);parsed=MediaLibrary.from_dict(MediaLibrary((item,)).to_dict()).items[0]
    assert parsed==item and [s.index for s in parsed.observation.streams]==[7,2,9]
    assert parsed.observation.streams[0].start==Fraction(-1024,48000)
    assert parsed.observation.streams[1].attached_picture and parsed.observation.streams[1].width is None
    assert parsed.observation.render_ready is False
    no_audio=record();assert 'NO_AUDIO_TRACK' in no_audio.observation.diagnostics


def test_large_derived_tick_rationals_roundtrip_not_rejected_by_reader():
    raw={'streams':[{'index':0,'codec_type':'video','time_base':f'{2**127+1}/1',
                    'start_pts':-(2**63),'duration_ts':2**63-1}]}
    item=record(raw=raw);assert item.observation.streams[0].start.numerator.bit_length()>128
    assert MediaLibrary.from_dict(MediaLibrary((item,)).to_dict()).items[0]==item


def test_raw_reflected_matrix_and_unknown_summary_preserved():
    raw={'streams':[{'index':0,'codec_type':'video','side_data_list':[{'side_data_type':'Display Matrix',
        'displaymatrix':'00000000: -65536 0 0\n00000001: 0 65536 0\n00000002: 0 0 1073741824'}]}]}
    item=record(raw=raw);copy=MediaLibrary.from_dict(MediaLibrary((item,)).to_dict()).items[0]
    stream=copy.observation.streams[0];assert stream.display_matrix[0]==-65536 and stream.rotation_degrees is None
    assert stream.rotation_basis=='UNKNOWN' and 'ROTATION_SUMMARY_UNKNOWN' in stream.diagnostics


def test_duplicate_identity_policy_noop_or_explicit_conflict():
    item=record();library=MediaLibrary((item,))
    same,new_id,changed=library.add(replace(item,id=str(uuid.uuid4())))
    assert same is library and new_id==item.id and not changed
    for candidate in (replace(item,path_ref=replace(item.path_ref,path='moved.bin')),
                      replace(item,size_bytes=item.size_bytes+1),
                      replace(item,observation_state='NOT_PROBED',observation=None)):
        with pytest.raises(MediaLibraryConflict):library.add(candidate)
    different=record(content=b'other',id=item.id)
    with pytest.raises(MediaLibraryConflict):library.add(different)
    with pytest.raises(MediaLibraryError):MediaLibrary((item,replace(item,id=str(uuid.uuid4()))))


def test_unprobed_records_are_not_fabricated_observations():
    item=record();unknown=replace(item,observation_state='PROBE_UNAVAILABLE',observation=None)
    assert MediaLibrary.from_dict(MediaLibrary((unknown,)).to_dict()).items[0]==unknown
    with pytest.raises(MediaLibraryError):replace(item,observation_state='NOT_PROBED')


@pytest.mark.parametrize('change',[
    lambda x:replace(x,render_ready=True),lambda x:replace(x,render_ready=0),
    lambda x:replace(x,sha256='wrong'),lambda x:replace(x,streams=list(x.streams)),
    lambda x:replace(x,streams=(replace(x.streams[0],start=Fraction(1)),)),
    lambda x:replace(x,streams=(replace(x.streams[0],start_basis='DECIMAL_SUMMARY'),)),
    lambda x:replace(x,streams=(replace(x.streams[0],time_base=Fraction(1,2**257)),)),
    lambda x:replace(x,streams=(replace(x.streams[0],diagnostics=()),)),
    lambda x:replace(x,diagnostics=()),
])
def test_typed_dataclass_does_not_bypass_semantic_validation(change):
    with pytest.raises(MediaLibraryError):validate_observation(change(observation()))


@pytest.mark.parametrize('path',['/absolute','C:\\absolute','C:relative','\\root','bad\0name'])
def test_relative_path_ambiguity_rejected_but_parent_relative_valid(path):
    with pytest.raises(MediaLibraryError):MediaPath('project',path,'a'*64)
    assert MediaPath('project','../legitimate.bin','a'*64).base=='project'


def test_reader_rejects_noncanonical_rational_unknown_keys_hash_mismatch():
    item=record();raw=item.to_dict();raw['observation']['streams'][0]['time_base']={'num':2,'den':2000}
    with pytest.raises(MediaLibraryError):MediaRecord.from_dict(raw)
    raw=item.to_dict();raw['credential']='secret'
    with pytest.raises(MediaLibraryError):MediaRecord.from_dict(raw)
    raw=item.to_dict();raw['path_ref']['asset_hash']='b'*64
    with pytest.raises(MediaLibraryError):MediaRecord.from_dict(raw)


@pytest.mark.parametrize('field,value',[('display_matrix',[0]*10),('diagnostics',['CODEC_UNKNOWN']*100)])
def test_reader_rejects_oversized_observation_arrays(field,value):
    raw=observation().to_dict();raw['streams'][0][field]=value
    with pytest.raises(MediaLibraryError):observation_from_dict(raw)


def test_typed_path_revalidated_at_library_boundary():
    item=record();object.__setattr__(item.path_ref,'path','/ambiguous')
    with pytest.raises(MediaLibraryError):MediaLibrary((item,))


@pytest.mark.parametrize('reverse',[False,True])
def test_duplicate_content_cannot_hide_another_existing_uuid(reverse):
    first=record(content=b'first');second=record(content=b'second')
    items=(second,first) if reverse else (first,second)
    with pytest.raises(MediaLibraryConflict):MediaLibrary(items).add(replace(first,id=second.id))
