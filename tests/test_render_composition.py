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
