"""P01 schema design checks, not domain evaluator or media acceptance."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]
schema=json.loads((ROOT/'docs/schemas/composition-v1.schema.json').read_text())
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema,format_checker=FormatChecker())
example=json.loads((ROOT/'docs/schemas/examples/empty-composition.json').read_text())
assert not list(validator.iter_errors(example)), list(validator.iter_errors(example))
assert 'video_stream_index' in schema['$defs']['clip']['required']
assert 'audio_stream_index' in schema['$defs']['audio_clip']['required']
assert {'time_basis','asset_id','source_track_id','segment_ids'} <= set(schema['$defs']['cue']['required'])
assert 'keyframe.time*clip_output_duration' in schema['$defs']['keyframe']['$comment']
assert {'target_audio_clip_ids','sidechain_audio_clip_ids','source_mode','threshold_db'} <= set(schema['$defs']['audio']['properties']['master']['properties']['ducking']['items']['required'])
multi=json.loads((ROOT/'docs/schemas/examples/multi-stream-composition.json').read_text())
assert not list(validator.iter_errors(multi)), list(validator.iter_errors(multi))
assert 'subtitle_stream' in schema['$defs']
assert set(schema['$defs']['probe']['properties']) == {'duration','streams'}
cases=[]
for key in schema['required']:
    bad=deepcopy(example);del bad[key];cases.append(('missing_'+key,bad))
bad=deepcopy(example);bad['mystery']=1;cases.append(('unknown_root',bad))
bad=deepcopy(example);bad['output']['fps']=[30,0];cases.append(('zero_denominator',bad))
bad=deepcopy(example);bad['output']['fps']=[True,1];cases.append(('bool_not_integer',bad))
bad=deepcopy(example);bad['output']['fps']=[30,1,99];cases.append(('rational_arity',bad))
bad=deepcopy(example);bad['output']['video_codec']='imaginary';cases.append(('unknown_codec',bad))
bad=deepcopy(example);bad['id']='not-uuid';cases.append(('invalid_uuid',bad))
bad=deepcopy(multi);bad['assets'][0]['probe']['streams'][2]['width']=640;cases.append(('audio_cannot_borrow_video_geometry',bad))
bad=deepcopy(multi);del bad['assets'][0]['probe']['streams'][4]['subtitle_format'];cases.append(('subtitle_requires_format',bad))
for name,bad in cases:
    assert list(validator.iter_errors(bad)), f'negative sentinel did not fail: {name}'
print(json.dumps({'schema_dialect':'2020-12','valid_examples':2,'rejected_invalid_examples':len(cases),'structural_design':'PASS','semantic_R01_R15':'NOT_IMPLEMENTED','runtime_acceptance':'NOT_RUN'},indent=2))
