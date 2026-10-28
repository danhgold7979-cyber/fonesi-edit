from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import subprocess
import pytest
from fonesi_edit.core.model import *
from fonesi_edit.core.paths import content_hash
from fonesi_edit.services.media import inspect_asset,validate_media
from fonesi_edit.services.render import render_project,reference_frame,atempo
from fonesi_edit.services.composition import paint_frame,text_image


def project_for(media):
    a=inspect_asset(media)
    return Project(width=320,height=180,assets=[a],clips=[Clip(a.id,0,a.duration)],settings={'burn_subtitles':True,'hardware':'cpu'})


def test_real_render_text_mask_motion_sub_and_no_clobber(media,tmp_path):
    p=project_for(media);before=content_hash(media)
    p.layers=[Layer(kind='mask',name='Che',x=.1,y=.1,width=.25,height=.2,end=p.duration,z=0,style={'mask_mode':'blur','blur_radius':5}),
              Layer(name='Tiêu đề',text='Tiếng Việt',x=.1,y=.1,width=.7,height=.25,end=p.duration,z=1,style={'font_size':24,'fill':'#ffffff','stroke_width':1,'overflow':'shrink'},keyframes={'x':[Keyframe(0,.1),Keyframe(p.duration,.2)]})]
    p.cues=[Cue(0,p.duration,'Phụ đề mẫu')]
    out=tmp_path/'kết quả.mp4';result=render_project(p,out)
    assert result['validated'];assert Path(result['path']).exists();assert out.with_suffix('.srt').exists()
    assert content_hash(media)==before
    other=render_project(p,out);assert other['path']!=str(out)
    assert validate_media(Path(other['path']),duration=p.duration,audio=True)['validated']


def test_reference_export_frame_parity(media,tmp_path):
    p=project_for(media);p.layers=[Layer(text='Fonesi',x=.1,y=.1,width=.8,height=.3,end=p.duration,style={'font_size':28,'fill':'#ffcc33','overflow':'shrink'})]
    out=tmp_path/'out.mp4';render_project(p,out)
    ref=tmp_path/'ref.png';reference_frame(p,400000,ref)
    actual=tmp_path/'actual.png';subprocess.run(['ffmpeg','-v','error','-ss','0.4','-i',str(out),'-frames:v','1',str(actual)],check=True)
    with Image.open(ref) as a,Image.open(actual) as b:
        rms=ImageStat.Stat(ImageChops.difference(a.convert('RGB'),b.convert('RGB'))).rms
    assert max(rms)<12,rms

@pytest.mark.parametrize('fit',['fit','crop','blur'])
def test_transform_modes_render(media,tmp_path,fit):
    p=project_for(media);p.width=180;p.height=320;p.clips[0].fit=fit;p.clips[0].speed='2'
    result=render_project(p,tmp_path/(fit+'.mp4'));assert abs(result['duration']-600000)<150000


def test_unsupported_properties_and_text_overflow_are_not_silent(media,tmp_path):
    p=project_for(media);p.layers=[Layer(text='long '*100,width=.1,height=.1,end=p.duration)]
    with pytest.raises(ValueError,match='overflow'):render_project(p,tmp_path/'out.mp4')
    p.layers=[];p.settings['hardware']='gpu'
    with pytest.raises(ValueError,match='GPU required'):render_project(p,tmp_path/'out.mp4')
