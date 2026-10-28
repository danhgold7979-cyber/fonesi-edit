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


@pytest.mark.parametrize('kwargs',[
    {'policy':'unknown'},
    {'allocation':'unknown'},
    {'allocation':'weights'},
    {'policy':'loop','target':2},
    {'policy':'freeze','target':2},
])
def test_duration_policy_rejects_unsupported_or_silent_fallback(kwargs):
    composition=Composition(clips=[Clip('synthetic.mp4',end=4)])
    options=dict(kwargs)
    target=options.pop('target',5)
    with pytest.raises(ValueError):
        fit_duration(composition,target,**options)
    assert composition.clips[0].speed==1
    assert composition.clips[0].end==4


@pytest.mark.parametrize('policy',['loop','freeze'])
def test_multiple_clips_never_silently_convert_loop_or_freeze_to_speed(policy):
    composition=Composition(clips=[Clip('one.mp4',end=2),Clip('two.mp4',end=2)])
    with pytest.raises(ValueError,match='exactly one clip'):
        fit_duration(composition,6,policy=policy)
    assert [clip.speed for clip in composition.clips]==[1,1]


def test_batch_main_audio_mapping_by_name_is_correct_and_renders_real_audio(tmp_path):
    from shutil import copyfile
    media=create_fixture(tmp_path/'channel/videos',duration=.5)
    first=Path(media['source'])
    second=first.with_name('clip2.mp4')
    copyfile(first,second)
    audio_folder=tmp_path/'audio'
    audio_folder.mkdir()
    copyfile(first,audio_folder/first.name)
    copyfile(second,audio_folder/second.name)
    groups={str(tmp_path/'channel'):[str(first),str(second)]}
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',seed=11,
                       audio=[{'path':'music.ogg','mode':'music','volume':.2}])
    before=preset.to_dict()
    plans=batch_plan(groups,preset,audio_mode='by_name',audio_folder=audio_folder)
    assert len(plans)==2
    for plan in plans:
        assert Path(plan['audio_source']).stem==Path(plan['source']).stem
        c=Composition.from_dict(plan['composition'])
        assert c.audio[0]['mode']=='main'
        assert c.audio[0]['path']==plan['audio_source']
        assert c.audio[1]['mode']=='music'
        assert c.clips[0].path==str(Path(plan['source']).resolve())
    assert preset.to_dict()==before
    # Avoid missing "music.ogg" in the real compositor proof; this track is
    # tested above as preserved metadata, and actual audio binding below.
    real=Composition.from_dict(plans[0]['composition'])
    real.audio=[real.audio[0]]
    out=tmp_path/'verified.mp4'
    result=render_composition(real,out)
    assert result['validated'] and probe(out).audio_codec


def test_batch_audio_ordered_and_seeded_random_are_deterministic(tmp_path):
    from shutil import copyfile
    media=create_fixture(tmp_path/'channel/videos',duration=.5)
    a=Path(media['source']);b=a.with_name('clip2.mp4');copyfile(a,b)
    groups={str(tmp_path/'channel'):[str(b),str(a)]}
    sounds=tmp_path/'sounds';sounds.mkdir()
    copyfile(a,sounds/'audio1.mp4');copyfile(a,sounds/'audio2.mp4')
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',seed=123)
    ordered=batch_plan(groups,preset,audio_mode='ordered',audio_folder=sounds)
    assert [Path(plan['audio_source']).name for plan in ordered]==['audio1.mp4','audio2.mp4']
    first=batch_plan(groups,preset,audio_mode='random',audio_folder=sounds)
    second=batch_plan(groups,preset,audio_mode='random',audio_folder=sounds)
    assert first==second
    assert all(Path(plan['audio_source']).parent==sounds for plan in first)
    assert [Path(plan['audio_source']).name for plan in first]


def test_batch_audio_mapping_rejects_missing_ambiguous_and_unsupported_modes(tmp_path):
    from shutil import copyfile
    media=create_fixture(tmp_path/'channel/videos',duration=.5)
    video=Path(media['source'])
    groups={str(tmp_path/'channel'):[str(video)]}
    preset=Composition(width=320,height=180,fps=25,encoder='cpu')
    with pytest.raises(ValueError,match='Unknown audio assignment mode'):
        batch_plan(groups,preset,audio_mode='silent_fallback')
    with pytest.raises(ValueError,match='Chọn thư mục'):
        batch_plan(groups,preset,audio_mode='by_name')
    folder=tmp_path/'sounds';folder.mkdir()
    copyfile(video,folder/'unrelated.mp4')
    with pytest.raises(ValueError,match='đúng một audio'):
        batch_plan(groups,preset,audio_mode='by_name',audio_folder=folder)
    with pytest.raises(ValueError,match='số audio bằng số video'):
        batch_plan(groups,preset,audio_mode='ordered',audio_folder=folder/'not-here') if False else \
            batch_plan({str(tmp_path/'channel'):[str(video),str(video)]},
                       preset,audio_mode='ordered',audio_folder=folder)
    copyfile(video,folder/'same.mp4')
    (folder/'unrelated.mp4').unlink()
    copyfile(video,folder/'same.mov')
    with pytest.raises(ValueError,match='đúng một audio'):
        batch_plan({str(tmp_path/'channel'):[str(folder/'same.mp4')]},
                   preset,audio_mode='by_name',audio_folder=folder)
    (folder/'bad.wav').write_bytes(b'not a valid sound')
    with pytest.raises(ValueError,match='không có track hợp lệ'):
        batch_plan(groups,preset,audio_mode='random',audio_folder=folder)
