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
    assert 'asplit=' in graph and graph.count('acrossfade=d=0.1')>=2
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
