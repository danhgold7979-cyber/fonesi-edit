from pathlib import Path
import pytest
from fonesi_edit.batch import scan_folders,fit_duration,batch_plan
from fonesi_edit.domain import Composition,Clip,Layer
from fonesi_edit.prototypes.media import create_fixture,probe
from fonesi_edit.render import render_composition


def test_duration_keeps_scenes_with_bounds_and_reports_infeasible():
    c=Composition(clips=[Clip('a',end=4),Clip('b',end=6)],transition=.2)
    result=fit_duration(c,7,minimum=.5,maximum=2,allocation='equal')
    assert len(result.clips)==2
    assert abs(sum((x.end-x.start)/x.speed for x in result.clips)-.2-7)<.001
    assert all(.5<=x.speed<=2 for x in result.clips)
    with pytest.raises(ValueError):fit_duration(c,1,minimum=.5,maximum=2)
    assert c.clips[0].speed==1


def test_scan_ignores_outputs_and_preserves_parent_folders(tmp_path):
    for name in ['A/videos/a.mp4','A edit/videos/out.mp4','.cache/skip.mp4','B/videos/b.mp4']:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
    groups=scan_folders(tmp_path)
    assert set(Path(p).name for p in groups)=={'A','B'}
    assert (tmp_path/'A edit/videos/out.mp4').exists()


@pytest.mark.parametrize('policy',['loop','freeze'])
def test_explicit_extension_policy_produces_real_target_duration(tmp_path,policy):
    files=create_fixture(tmp_path/'media',duration=.5)
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(files['source']),end=.5)])
    fitted=fit_duration(c,1.5,policy=policy)
    result=render_composition(fitted,tmp_path/'result.mp4')
    assert abs(probe(Path(result['output'])).duration-1.5)<.15


def test_subtitle_preset_rebinds_each_source_and_each_loop_without_stale_cues(tmp_path):
    files=create_fixture(tmp_path/'channel/videos',duration=.5);source=files['source'];sidecar=source.with_suffix('.srt')
    sidecar.write_text('1\n00:00:00,000 --> 00:00:00,400\nĐúng video\n',encoding='utf-8')
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',duration_target=1,layers=[Layer(kind='subtitle',path=str(tmp_path/'wrong.srt'),style={'font_size':18},x=.2,y=.7)])
    plan=batch_plan({str(tmp_path/'channel'):[str(source)]},preset,policy='loop')[0]
    actual=Composition.from_dict(plan['composition']);assert len(actual.layers)==len(actual.clips)==2
    assert batch_plan({str(tmp_path/'channel'):[str(source)]},preset,policy='loop')[0]['composition']==plan['composition']
    assert all(layer.path==str(sidecar) and layer.clip_ids==[clip.id] and layer.x==.2 for layer,clip in zip(actual.layers,actual.clips))
    assert render_composition(actual,Path(plan['output']))['validated']
    assert preset.layers[0].path.endswith('wrong.srt')


def test_batch_video_settings_survive_new_clip_creation_and_seeded_random_render(tmp_path):
    from fonesi_edit.render import compile_graph
    files=create_fixture(tmp_path/'channel/videos',duration=1);source=files['source']
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',fit='blur',seed=42,adjustments={'batch_video':{'speed':2,'trim_head':.1,'trim_tail':.1,'flip':True,'random_flip':0,'random_rotate':True,'rotation_min':2,'rotation_max':4,'random_zoom':True,'zoom_min':1,'zoom_max':1.1}})
    first=batch_plan({str(tmp_path/'channel'):[str(source)]},preset)[0];second=batch_plan({str(tmp_path/'channel'):[str(source)]},preset)[0]
    assert first['composition']==second['composition']
    c=Composition.from_dict(first['composition']);clip=c.clips[0];assert clip.flip and clip.speed==2 and 2<=clip.rotation<=4
    stage=tmp_path/'graph';stage.mkdir();_,graph,duration=compile_graph(c,stage)
    assert 'hflip' in graph and 'rotate=' in graph and '[zoom0]' in graph and abs(duration-.4)<.001
    assert render_composition(c,Path(first['output']))['validated']


def test_bilingual_source_target_files_are_bound_independently(tmp_path):
    from fonesi_edit.subtitles import Caption,write_captions
    files=create_fixture(tmp_path/'channel/videos',duration=.5);path=files['source']
    source=path.with_name(path.stem+'.zh.srt');target=path.with_name(path.stem+'.vi.srt')
    write_captions(source,[Caption(0,400,'Original')]);write_captions(target,[Caption(0,400,'Bản dịch')])
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',adjustments={'bilingual_subtitles':True})
    first=batch_plan({str(tmp_path/'channel'):[str(path)]},preset)[0];second=batch_plan({str(tmp_path/'channel'):[str(path)]},preset)[0]
    assert first==second
    c=Composition.from_dict(first['composition']);roles={l.style['subtitle_role']:l for l in c.layers}
    assert roles['source'].path==str(source) and roles['target'].path==str(target)
    assert roles['source'].y!=roles['target'].y
    assert render_composition(c,Path(first['output']))['validated']
