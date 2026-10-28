import time
from pathlib import Path
from fonesi_edit.core.model import Project,Clip
from fonesi_edit.services.media import inspect_asset,validate_media
from fonesi_edit.services.preview import build_proxy,waveform,proxy_key
from fonesi_edit.ui.playback import Playback


def test_proxy_waveform_and_qt_video_frame(media,tmp_path,qapp):
    a=inspect_asset(media);p=Project(width=320,height=180,assets=[a],clips=[Clip(a.id,0,a.duration)])
    target=tmp_path/'proxy.mp4';build_proxy(p,target)
    assert validate_media(target,duration=p.duration,audio=True)['validated']
    wave=waveform(target,100);assert 1<=len(wave)<=100;assert max(x['max'] for x in wave)>0
    frames=[];player=Playback();player.frame.connect(frames.append);player.load(target);player.toggle();deadline=time.monotonic()+10
    while time.monotonic()<deadline and not frames:qapp.processEvents();time.sleep(.02)
    player.stop();assert frames and frames[0].size==(320,180)
    old=proxy_key(p);p.settings['bilingual']=True;assert proxy_key(p)==old
