from copy import deepcopy
import math
import pytest
from fonesi_edit.domain import Composition,Clip,Layer
from fonesi_edit.motion import transforms
from fonesi_edit.render import render_composition,reference_frame
from fonesi_edit.prototypes.media import create_fixture,probe


@pytest.mark.parametrize('preset',['fixed','left-right','right-left','top-bottom','bottom-top','diagonal','pingpong','bounce','corners','random','zoom','a-b'])
def test_motion_shared_expression_is_finite_reproducible_and_numeric(preset):
    layer=Layer(motion={'preset':preset,'speed':20,'duration':3,'repeat':True,'easing':'ease-in-out'})
    first=transforms(layer,320,180,123);second=transforms(layer,320,180,123)
    for key,value in first.items():
        assert value.ffmpeg()==second[key].ffmpeg()
        assert all(math.isfinite(value.value(t)) for t in (0,.5,3,10))


def test_real_multi_clip_alpha_mask_text_subtitle_audio_and_reuse(tmp_path):
    f=create_fixture(tmp_path/'media',duration=1)
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[
        Clip(str(f['source']),end=.5,subtitles=str(f['subtitles'])),Clip(str(f['source']),start=.5,end=1,speed=1)],layers=[
        Layer(kind='mask',x=.1,y=.7,width=.8,height=.15,style={'mode':'blur','radius':5}),
        Layer(kind='image',path=str(f['logo']),width=.15,height=.2,x=.8,y=.05),
        Layer(text='Fonesi Việt',style={'font_size':18,'color':'#ffffff','outline':1},keyframes={'x':[{'time':0,'value':.05},{'time':1,'value':.2}]})],
        audio=[{'path':str(f['source']),'volume':.1,'loop':True,'fade_out':.1}])
    output=tmp_path/'output.mp4'
    result=render_composition(c,output)
    assert result['validated'] and result['encoder']=='libx264'
    assert (probe(output).width,probe(output).height)==(320,180)
    assert render_composition(c,output)['reused']
    changed=deepcopy(c);changed.layers[-1].text='Different'
    with pytest.raises(FileExistsError):render_composition(changed,output)


def test_clip_crop_defaults_keep_legacy_project_payload_compatible():
    legacy = Composition.from_dict({"clips": [{"path": "legacy.mp4"}]})
    clip = legacy.clips[0]
    assert (clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height) == (0, 0, 1, 1)
    assert Composition.from_dict(legacy.to_dict()).clips[0].crop_width == 1


@pytest.mark.parametrize("values", [
    {"crop_x": -0.01},
    {"crop_y": 1.01},
    {"crop_width": 0},
    {"crop_height": -0.1},
    {"crop_x": 0.8, "crop_width": 0.3},
    {"crop_y": 0.8, "crop_height": 0.3},
    {"crop_x": float("nan")},
    {"crop_width": True},
])
def test_clip_crop_rejects_invalid_normalized_regions(values):
    with pytest.raises(ValueError, match="Crop region"):
        Composition(clips=[Clip("unused.mp4", **values)]).validate()


def test_crop_rect_pixels_uses_even_source_pixel_bounds():
    from fonesi_edit.render import crop_rect_pixels
    clip = Clip("unused.mp4", crop_x=0.25, crop_y=0.1,
                crop_width=0.5, crop_height=0.8)
    assert crop_rect_pixels(clip, 640, 360) == (320, 288, 160, 36)
    assert crop_rect_pixels(Clip("unused.mp4"), 640, 360) is None
    # Odd source dimensions are clamped to safe even boundaries.
    assert crop_rect_pixels(Clip("unused.mp4", crop_x=0.99, crop_y=0.99,
                                 crop_width=0.01, crop_height=0.01), 641, 361) == (2, 2, 638, 358)


def test_clip_crop_compiles_before_flip_rotation_and_renders(tmp_path):
    from fonesi_edit.render import compile_graph
    f = create_fixture(tmp_path / "media", duration=0.6)
    source = str(f["source"])
    clip = Clip(source, end=0.5, flip=True, rotation=90,
                crop_x=0.25, crop_y=0.1, crop_width=0.5, crop_height=0.8)
    composition = Composition(width=320, height=180, fps=25, encoder="cpu",
                              clips=[clip], mute_original=True)
    stage = tmp_path / "crop-stage"
    stage.mkdir()
    _, graph, _ = compile_graph(composition, stage)
    joined = ";".join(graph)
    crop_at = joined.index("crop=320:288:160:36")
    assert crop_at < joined.index("hflip") < joined.index("rotate=")
    output = tmp_path / "cropped.mp4"
    assert render_composition(composition, output)["validated"]
    assert (probe(output).width, probe(output).height) == (320, 180)


def test_crossfade_speed_crop_and_reference_use_real_export(tmp_path):
    f=create_fixture(tmp_path/'media',duration=1)
    c=Composition(width=180,height=320,fps=25,encoder='cpu',fit='crop',transition=.1,
        clips=[Clip(str(f['source']),end=1,speed=2),Clip(str(f['source']),end=.5)],mute_original=True)
    result=render_composition(c,tmp_path/'out.mp4')
    assert abs(probe(tmp_path/'out.mp4').duration-.9)<.15
    frame=reference_frame(c,tmp_path/'reference',second=.2)
    assert frame.is_file() and frame.stat().st_size>1000


def test_dynamic_rotated_feathered_mask_and_ducking_normalization(tmp_path):
    f=create_fixture(tmp_path/'media',duration=.5)
    mask=Layer(kind='mask',x=.1,y=.2,width=.4,height=.3,rotation=20,style={'mode':'mosaic','radius':3,'corner_radius':8,'feather':3},keyframes={'x':[{'time':0,'value':.1},{'time':.5,'value':.3}]})
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(f['source']),end=.5)],layers=[mask],
        audio=[{'path':str(f['source']),'mode':'main','volume':.5},{'path':str(f['source']),'mode':'music','loop':True,'volume':.1}],adjustments={'ducking':True,'normalize':True})
    result=render_composition(c,tmp_path/'dynamic.mp4')
    assert result['validated']


def test_draggable_subtitle_layer_maps_source_trim_speed_and_output_time(tmp_path):
    from fonesi_edit.render import compile_graph
    f=create_fixture(tmp_path/'media',duration=1)
    sub=tmp_path/'timed.srt';sub.write_text('1\n00:00:00,200 --> 00:00:00,800\nĐúng thời gian\n',encoding='utf-8')
    clip=Clip(str(f['source']),start=.2,end=1,speed=2)
    layer=Layer(kind='subtitle',path=str(sub),clip_ids=[clip.id],x=.2,y=.5,style={'font_size':18})
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[clip],layers=[layer])
    stage=tmp_path/'graph';stage.mkdir();compile_graph(comp,stage)
    import pysubs2
    cue=pysubs2.load(str(stage/'layer-0.ass'))[0]
    assert cue.start==0 and cue.end==300
    assert render_composition(comp,tmp_path/'subtitle.mp4')['validated']


def test_solo_track_excludes_original_audio_in_actual_output(tmp_path):
    import subprocess
    from fonesi_edit.prototypes.tools import locate_tool
    from array import array
    f=create_fixture(tmp_path/'media',duration=.5)
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(f['source']),end=.5)],audio=[{'path':str(f['source']),'mode':'music','solo':True,'volume':0}])
    output=tmp_path/'solo.mp4';render_composition(comp,output)
    data=subprocess.run([locate_tool('ffmpeg'),'-v','error','-i',str(output),'-vn','-f','s16le','-'],capture_output=True,check=True).stdout
    samples=array('h');samples.frombytes(data)
    assert samples and max(abs(value) for value in samples)==0


@pytest.mark.parametrize('bad_gain',[float('nan'),float('inf'),-1,5])
def test_clip_gain_rejects_nonfinite_and_out_of_bounds(bad_gain):
    with pytest.raises(ValueError,match='rotation/volume'):
        Composition(clips=[Clip('synthetic.mp4',volume=bad_gain)]).validate()


@pytest.mark.parametrize('changes',[
    {'width':320.0},
    {'height':True},
    {'fps':30.5},
    {'fps':True},
    {'width':321},
])
def test_output_geometry_requires_even_integer_dimensions_and_integer_fps(changes):
    values={'width':320,'height':180,'fps':25,**changes}
    with pytest.raises(ValueError):
        Composition(**values).validate()
    Composition(width=320,height=180,fps=25).validate()



@pytest.mark.parametrize(('placement','extra','expected'),[
    ('absolute',{'offset':.4},.4),
    ('percent',{'position_pct':50,'offset':.1},.65),
    ('video_end',{'offset':.2},.9),
    ('scene_start',{'scene_index':2,'offset':.1},.4),
    ('scene_end',{'scene_index':1,'offset':.1},.3),
])
def test_sfx_placement_anchors_follow_real_clip_timing(placement,extra,expected,tmp_path):
    from fonesi_edit.render import compile_graph,audio_timeline_offset
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    c=Composition(width=320,height=180,fps=25,encoder='cpu',transition=.1,
                  mute_original=True,clips=[
                      Clip(source,end=.8,speed=2),
                      Clip(source,end=.8)],
                  audio=[{'path':source,'mode':'sfx','placement':placement,**extra}])
    stage=tmp_path/'graph';stage.mkdir()
    args,graph,total=compile_graph(c,stage)
    assert abs(total-1.1)<1e-6
    assert f'adelay={round(expected*1000)}:all=1' in graph
    ranges={c.clips[0].id:(0,.4),c.clips[1].id:(.3,.8)}
    assert abs(audio_timeline_offset(c.audio[0],total,c.clips,ranges)-expected)<1e-6


@pytest.mark.parametrize('invalid',[
    {'placement':'unsupported'},
    {'placement':'percent'},
    {'placement':'percent','position_pct':-1},
    {'placement':'percent','position_pct':101},
    {'placement':'percent','position_pct':float('nan')},
    {'placement':'percent','position_pct':True},
    {'placement':'scene_start'},
    {'placement':'scene_start','scene_index':0},
    {'placement':'scene_end','scene_index':2},
    {'placement':'scene_start','scene_index':1.5},
])
def test_invalid_sfx_placement_is_rejected_in_domain(invalid):
    c=Composition(clips=[Clip('unused.mp4',end=1)],audio=[
        {'path':'unused.mp4','mode':'sfx',**invalid}])
    with pytest.raises(ValueError,match='SFX'):
        c.validate()
    with pytest.raises(ValueError,match='Relative placement'):
        Composition(clips=[Clip('a.mp4',end=1)],audio=[
            {'path':'b.wav','mode':'music','placement':'video_end'}]).validate()


def test_sfx_anchor_rejects_out_of_range_onset_without_silent_fallback(tmp_path):
    from fonesi_edit.render import compile_graph
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    for placement,extra in [
        ('video_end',{'offset':0}),
        ('video_end',{'offset':2}),
        ('percent',{'position_pct':100}),
        ('scene_start',{'scene_index':1,'offset':2}),
        ('scene_end',{'scene_index':1,'offset':2}),
    ]:
        c=Composition(width=320,height=180,fps=25,encoder='cpu',
            clips=[Clip(source,end=1)],audio=[
                {'path':source,'mode':'sfx','placement':placement,**extra}])
        folder=tmp_path/(placement+str(len(extra))+'_'+str(extra.get('offset',0)).replace('-','n'))
        folder.mkdir(exist_ok=True)
        with pytest.raises(ValueError,match='outside the output timeline'):
            compile_graph(c,folder)


def test_exported_sfx_is_audible_only_after_percent_anchor(tmp_path):
    from array import array
    import subprocess
    from fonesi_edit.prototypes.tools import locate_tool
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    c=Composition(width=320,height=180,fps=25,encoder='cpu',
        clips=[Clip(source,end=1)],mute_original=True,audio=[
            {'path':source,'mode':'sfx','volume':1,'placement':'percent',
             'position_pct':50,'offset':0}])
    out=tmp_path/'sfx-at-half.mp4'
    assert render_composition(c,out)['validated']
    result=subprocess.run([locate_tool('ffmpeg'),'-v','error','-i',str(out),
                           '-vn','-ac','1','-ar','48000','-f','s16le','-'],
                          capture_output=True,check=True)
    samples=array('h');samples.frombytes(result.stdout)
    assert len(samples)>40000
    assert max(abs(value) for value in samples[4800:14400])<20
    assert max(abs(value) for value in samples[30000:42000])>100



@pytest.mark.parametrize('track',[
    {'mode':'music','loop':True,'loop_crossfade':-1},
    {'mode':'music','loop':True,'loop_crossfade':float('nan')},
    {'mode':'music','loop':True,'loop_crossfade':11},
    {'mode':'music','loop':False,'loop_crossfade':.1},
    {'mode':'main','loop':True,'loop_crossfade':.1},
    {'mode':'sfx','loop':True,'loop_crossfade':.1},
])
def test_music_loop_crossfade_invalid_inputs_are_rejected(track):
    comp=Composition(clips=[Clip('unused.mp4',end=1)],
        audio=[{'path':'unused.mp4',**track}])
    with pytest.raises(ValueError,match='crossfade'):
        comp.validate()


def test_music_loop_crossfade_compiles_and_exports_real_audio(tmp_path):
    from pathlib import Path
    from fonesi_edit.render import compile_graph
    source=str(create_fixture(tmp_path/'fixture',duration=.6)['source'])
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',mute_original=True,
        clips=[Clip(source,end=.5) for _ in range(4)],
        audio=[{'path':source,'mode':'music','loop':True,'loop_crossfade':.1,
                'volume':.3,'fade_in':.03,'fade_out':.05}])
    args,graph,total=compile_graph(comp,tmp_path/'stage')
    assert abs(total-2)<.01
    assert 'asplit=' not in graph and graph.count('acrossfade=d=0.1')>=2
    assert args.count(source)>len(comp.clips)+1  # Separate music inputs per repeat
    assert 'adelay=0:all=1' in graph
    assert '-stream_loop' not in args
    result=render_composition(comp,tmp_path/'with-crossfade.mp4')
    assert result['validated']
    media=probe(Path(result['output']))
    assert media.audio_codec is not None and abs(media.duration-2)<.15
    invalid=deepcopy(comp)
    invalid.audio[0]['loop_crossfade']=.35  # Too long for a ~.6 s segment.
    with pytest.raises(ValueError,match='dài hơn hai lần'):
        compile_graph(invalid,tmp_path/'invalid')



@pytest.mark.parametrize('track',[
    {'mode':'sfx','repeat_count':0},
    {'mode':'sfx','repeat_count':33},
    {'mode':'sfx','repeat_count':2.5,'repeat_interval':.1},
    {'mode':'sfx','repeat_count':True},
    {'mode':'sfx','repeat_count':2,'repeat_interval':0},
    {'mode':'sfx','repeat_count':2,'repeat_interval':-1},
    {'mode':'sfx','repeat_count':2,'repeat_interval':float('nan')},
    {'mode':'sfx','repeat_count':1,'repeat_interval':.2},
    {'mode':'music','repeat_count':2,'repeat_interval':.2},
    {'mode':'main','repeat_count':2,'repeat_interval':.2},
    {'mode':'sfx','loop':True,'repeat_count':2,'repeat_interval':.2},
])
def test_repeated_sfx_invalid_configuration_is_rejected(track):
    composition=Composition(clips=[Clip('unused.mp4',end=1)],
        audio=[{'path':'sfx.wav',**track}])
    with pytest.raises(ValueError,match='SFX repeat'):
        composition.validate()


def test_sfx_repeat_anchors_render_two_audible_events_without_leaking_outside(tmp_path):
    from array import array
    import subprocess
    from fonesi_edit.render import compile_graph
    from fonesi_edit.prototypes.tools import locate_tool
    source=str(create_fixture(tmp_path/'media',duration=1)['source'])
    composition=Composition(width=320,height=180,fps=25,encoder='cpu',
        clips=[Clip(source,end=1)],mute_original=True,audio=[{
            'path':source,'mode':'sfx','placement':'percent','position_pct':20,
            'repeat_count':2,'repeat_interval':.4,'trim_end':.12,'volume':1}])
    args,graph,total=compile_graph(composition,tmp_path/'graph')
    assert abs(total-1)<.01
    assert 'adelay=200:all=1' in graph and 'adelay=600:all=1' in graph
    assert 'amix=inputs=2:normalize=0:duration=longest[sfxrepeated0]' in graph
    assert args.count(source)==3  # Video input plus two independent SFX inputs.
    result=render_composition(composition,tmp_path/'two-sfx.mp4')
    assert result['validated']
    decoded=subprocess.run([locate_tool('ffmpeg'),'-v','error',
        '-i',str(tmp_path/'two-sfx.mp4'),'-vn','-ac','1','-ar','48000',
        '-f','s16le','-'],capture_output=True,check=True).stdout
    samples=array('h');samples.frombytes(decoded)
    assert len(samples)>43000
    def peak(start,end):
        return max(abs(sample) for sample in samples[round(start*48000):round(end*48000)])
    assert peak(.05,.12)<20 and peak(.40,.50)<20
    assert peak(.23,.30)>100 and peak(.63,.70)>100
    invalid=deepcopy(composition);invalid.audio[0]['repeat_interval']=.81
    with pytest.raises(ValueError,match='outside the output timeline'):
        compile_graph(invalid,tmp_path/'invalid')
