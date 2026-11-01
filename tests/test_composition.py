from copy import deepcopy
import json,uuid
import pytest
from fonesi_edit.domain.composition import CompositionPlan,PlanError

BUILD='a'*64
@pytest.mark.parametrize('fixture',['empty_plan','multi_plan'])
def test_valid_models_roundtrip(fixture,request):
    data=request.getfixturevalue(fixture);p=CompositionPlan.parse(data)
    assert CompositionPlan.parse(p.canonical_json)==p
    assert p.to_dict()==data

def test_no_unchecked_constructor():
    with pytest.raises(TypeError):CompositionPlan('{}',())

def test_caller_and_returned_dict_cannot_mutate_snapshot(multi_plan):
    p=CompositionPlan.parse(multi_plan);before=p.canonical_json
    multi_plan['output']['width']=100
    p.to_dict()['output']['width']=200
    assert p.canonical_json==before
    with pytest.raises(AttributeError):p.canonical_json='{}'

@pytest.mark.parametrize('bad',['{"schema_version":1,"schema_version":1}','{"x":NaN}','{"x":Infinity}','\xff'])
def test_strict_json(bad):
    with pytest.raises(PlanError):CompositionPlan.parse(bad)

@pytest.mark.parametrize('change',[
 lambda p:p.update(cookie='secret'),
 lambda p:p['output'].update(fps=[0,1]),
 lambda p:p['output'].update(duration=[2,2]),
 lambda p:p['output'].update(width=1919),
 lambda p:p['assets'][0]['probe']['streams'][1].update(index=0),
 lambda p:p['assets'][0]['probe']['streams'][1].update(frame_pts=[[1,1],[0,1]]),
 lambda p:p['clips'][0].update(video_stream_index=3),
 lambda p:p['audio']['clips'][0].update(audio_stream_index=1),
 lambda p:p['audio']['clips'][0].update(source_out=[3,1]),
 lambda p:p['layers'][0]['content']['cues'][0].update(subtitle_stream_index=1),
 lambda p:p['layers'][0]['content']['cues'][0].update(sidecar_origin=[1,2]),
 lambda p:p['layers'][0]['content']['cues'][0].update(segment_ids=[str(uuid.uuid4())]),
 lambda p:p['layers'][0]['content']['cues'][0].update(time_basis='output'),
 lambda p:p['clips'][0]['crop'].update(width=[2,1]),
 lambda p:p['layers'][0]['transform'].update(opacity=[2,1]),
 lambda p:p['layers'][0]['style'].update(min_size_px=[100,1]),
 lambda p:p['fonts'][0].update(fallback_ids=[p['fonts'][0]['id']]),
 lambda p:p['layers'][0].update(id=p['clips'][0]['id']),
])
def test_invalid_semantics_fail_closed(multi_plan,change):
    change(multi_plan)
    with pytest.raises(PlanError):CompositionPlan.parse(multi_plan)

def test_declared_source_offsets_and_selected_video(multi_plan):
    p=CompositionPlan.parse(multi_plan);segment=next(iter(p.time_segments().values()))
    assert segment.stream_index==1
    assert segment.output_to_decoder_pts(0)==0

def test_moved_path_preserves_render_content_not_execution(multi_plan):
    a=CompositionPlan.parse(multi_plan);multi_plan['assets'][0]['path_ref']['path']='renamed/đường dẫn.mkv';multi_plan['fonts'][0]['path_ref']['path']='other/font.ttf';b=CompositionPlan.parse(multi_plan)
    assert a.render_content_digest(BUILD)==b.render_content_digest(BUILD)
    assert a.execution_digest({'tool':'one'})!=b.execution_digest({'tool':'one'})
    assert a.render_content_digest(BUILD)!=a.render_content_digest('b'*64)

def test_stream_selection_changes_render_digest(multi_plan):
    a=CompositionPlan.parse(multi_plan);multi_plan['clips'][0]['video_stream_index']=0;b=CompositionPlan.parse(multi_plan)
    assert a.render_content_digest(BUILD)!=b.render_content_digest(BUILD)

def test_uuid_spelling_not_content_but_literal_text_is(multi_plan):
    a=CompositionPlan.parse(multi_plan);old=multi_plan['assets'][0]['id'];new=str(uuid.uuid4())
    for obj in [multi_plan['assets'][0],multi_plan['clips'][0],multi_plan['audio']['clips'][0],multi_plan['layers'][0]['content']['cues'][0]]:
        for k in ['id','asset_id']:
            if obj.get(k)==old:obj[k]=new
    b=CompositionPlan.parse(multi_plan);assert a.render_content_digest(BUILD)==b.render_content_digest(BUILD)
    cue=multi_plan['layers'][0]['content']['cues'][0];cue['text']=old;c=CompositionPlan.parse(multi_plan);cue['text']=new;d=CompositionPlan.parse(multi_plan)
    assert c.render_content_digest(BUILD)!=d.render_content_digest(BUILD)

def test_overlapping_clips_need_transition(multi_plan):
    duplicate=deepcopy(multi_plan['clips'][0]);duplicate['id']=str(uuid.uuid4());multi_plan['clips'].append(duplicate)
    with pytest.raises(PlanError,match='overlapping'):CompositionPlan.parse(multi_plan)

def test_relative_keyframe_time_not_amplitude(multi_plan):
    clip=multi_plan['clips'][0]['id'];multi_plan['layers'][0]['keyframes']=[{'property':'x','time':[1,2],'time_mode':'relative','reference_clip_id':clip,'value':[99,1],'easing':'linear'}]
    CompositionPlan.parse(multi_plan) # amplitude99 allowed; time1/2 maps1 second, not198seconds
    multi_plan['layers'][0]['keyframes'].append({'property':'x','time':[1,1],'time_mode':'absolute','reference_clip_id':None,'value':[0,1],'easing':'linear'})
    with pytest.raises(PlanError,match='Duplicate effective'):CompositionPlan.parse(multi_plan)

def test_duck_targets_are_explicit_not_master(multi_plan):
    aid=multi_plan['audio']['clips'][0]['id'];duck={'start':[0,1],'end':[1,1],'gain_db':[-12,1],'attack':[1,10],'release':[1,5],'envelope_hash':None,'target_audio_clip_ids':[aid],'sidechain_audio_clip_ids':[],'source_mode':'marked_intervals','threshold_db':[-30,1]};multi_plan['audio']['master']['ducking']=[duck]
    CompositionPlan.parse(multi_plan)
    duck['source_mode']='signal_envelope';duck['sidechain_audio_clip_ids']=[aid];duck['envelope_hash']='a'*64
    with pytest.raises(PlanError,match='duck targets'):CompositionPlan.parse(multi_plan)

def test_same_content_conflicting_probe_rejected(multi_plan):
    duplicate=deepcopy(multi_plan['assets'][0]);duplicate['id']=str(uuid.uuid4())
    duplicate['probe']['streams'][1]['sar']=[2,1]
    multi_plan['assets'].append(duplicate)
    with pytest.raises(PlanError,match='Conflicting metadata'):CompositionPlan.parse(multi_plan)

def test_same_font_face_conflicting_fallback_rejected(multi_plan):
    duplicate=deepcopy(multi_plan['fonts'][0]);duplicate['id']=str(uuid.uuid4())
    duplicate['fallback_ids']=[multi_plan['fonts'][0]['id']]
    multi_plan['fonts'].append(duplicate)
    with pytest.raises(PlanError,match='Conflicting metadata'):CompositionPlan.parse(multi_plan)

def test_large_shared_font_dag_linear_validation(multi_plan):
    # Fibonacci-style shared DAG was exponential under recursive traversal.
    fonts=[]
    for i in range(1000):
        font=deepcopy(multi_plan['fonts'][0]);font['id']=str(uuid.uuid4())
        font['sha256']=f'{i+1:064x}';font['path_ref']['asset_hash']=font['sha256']
        font['fallback_ids']=[f['id'] for f in fonts[-2:]]
        fonts.append(font)
    multi_plan['layers'][0]['style']['font_id']=fonts[-1]['id'];multi_plan['fonts']=fonts
    CompositionPlan.parse(multi_plan)
    fonts[0]['fallback_ids']=[fonts[-1]['id']]
    with pytest.raises(PlanError,match='cycle'):CompositionPlan.parse(multi_plan)

def test_deep_json_fails_with_controlled_error():
    with pytest.raises(PlanError):CompositionPlan.parse('['*2000+'0'+']'*2000)
