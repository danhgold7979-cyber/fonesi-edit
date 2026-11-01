from fractions import Fraction as F
import pytest
from fonesi_edit.domain.timebase import rational,pair,half_up,frame_count,sample_index,TimeSegment,TimeValueError,resolve_cue,interpolate_keyframes

@pytest.mark.parametrize('value',[[True,1],[1,0],[2,4],[1,-1],[1.0,2],[1],[1,2,3],None])
def test_reject_bad_rationals(value):
    with pytest.raises(TimeValueError):rational(value)

def test_rational_boundaries_no_float_drift():
    assert rational([30000,1001])==F(30000,1001)
    assert pair(F(2,4))==[1,2]
    assert frame_count(F(1001,1000),F(30000,1001))==30
    assert frame_count(F(1),F(30000,1001))==30
    assert sample_index(F(1,3),48000)==16000
    assert half_up(F(1,2))==1 and half_up(F(-1,2))==0

def test_stream_origin_applied_once_and_half_open():
    s=TimeSegment('clip','asset',1,F(1,4),F(1),F(3),F(2),F(2))
    assert s.output_end==3
    assert s.output_to_decoder_pts(F(2))==F(5,4)
    assert s.output_to_decoder_pts(F(5,2))==F(9,4)
    with pytest.raises(TimeValueError):s.output_to_decoder_pts(F(3))
    assert s.asset_interval_to_output(F(0),F(2))==(F(2),F(19,8))
    assert s.asset_interval_to_output(F(4),F(5)) is None

def test_cue_stream_offset_repeated_asset(multi_plan):
    cue=multi_plan['layers'][0]['content']['cues'][0];asset=cue['asset_id'];a=TimeSegment('a',asset,1,F(0),F(0),F(2),F(0),F(1));b=TimeSegment('b',asset,1,F(0),F(0),F(2),F(3),F(2));cue['segment_ids']=['a','b']
    result=resolve_cue(cue,{'a':a,'b':b},F(1,10))
    assert [(r.segment_id,r.output_start,r.output_end) for r in result]==[('a',F(1,10),F(11,10)),('b',F(61,20),F(71,20))]
    assert cue['start']==[0,1] # non-destructive source cue

def test_sidecar_origin_replaces_embedded_offset(multi_plan):
    cue=multi_plan['layers'][0]['content']['cues'][0];cue.update(subtitle_stream_index=None,sidecar_origin=[1,2],segment_ids=['a'])
    s=TimeSegment('a',cue['asset_id'],0,F(0),F(0),F(2),F(0),F(1))
    assert resolve_cue(cue,{'a':s},F(99))[0].output_start==F(1,2)

@pytest.mark.parametrize('easing,expected',[('linear',F(1,4)),('ease_in',F(1,16)),('ease_out',F(7,16)),('ease_in_out',F(5,32))])
def test_interpolation_exact(easing,expected):
    points=[(F(0),F(0),easing),(F(1),F(1),'linear')]
    assert interpolate_keyframes(points,F(1,4))==expected
    assert interpolate_keyframes(points,F(-1))==0
    assert interpolate_keyframes(points,F(2))==1

def test_duplicate_keyframe_effective_time_rejected():
    with pytest.raises(TimeValueError):interpolate_keyframes([(F(1),F(0),'linear'),(F(1),F(3),'linear')],F(1))

@pytest.mark.parametrize('bad',[0.5,True,float('nan'),float('inf')])
def test_direct_time_interfaces_never_admit_float_or_bool(bad):
    from fonesi_edit.domain.timebase import pair,half_up,frame_count,sample_index,TimeSegment,interpolate_keyframes
    for action in [lambda:pair(bad),lambda:half_up(bad),lambda:frame_count(bad,24),
                   lambda:sample_index(bad,48000),
                   lambda:TimeSegment('clip','asset',0,bad,0,1,0,1),
                   lambda:interpolate_keyframes([(0,0,'linear'),(1,1,'linear')],bad)]:
        with pytest.raises(TimeValueError):action()
