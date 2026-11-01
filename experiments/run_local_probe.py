"""Reproducible P02 synthetic experiments. Not the Fonesi Edit application."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,statistics,subprocess,sys,time,shutil
from pathlib import Path

def run(argv, *, timeout=60, env=None):
    p=subprocess.run(argv,capture_output=True,timeout=timeout,env=env)
    if p.returncode:raise RuntimeError(f'process failed ({p.returncode}): {argv[0]}: {p.stderr.decode(errors="replace")[-4000:]}')
    return p.stdout

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--width',type=int,default=640);ap.add_argument('--height',type=int,default=360);args=ap.parse_args()
    if args.width<320 or args.height<180 or args.width%2 or args.height%2:ap.error('even dimensions at least320×180 required')
    root=args.output_dir.resolve();root.mkdir(parents=True,exist_ok=False) # never reuse/delete arbitrary existing output
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage,QPainter,QColor,QFont,QFontDatabase
    from PySide6.QtCore import QRectF,Qt,qVersion
    import numpy as np
    from PIL import Image
    started=time.time();app=QApplication([]);frames=root/'frames';frames.mkdir();families=QFontDatabase.families();font=next((f for f in families if 'Noto Sans CJK' in f),None)
    if font is None:raise RuntimeError('CJK corpus prerequisite missing; do not accept tofu fallback')
    scale=args.width/640;timings=[]
    for n in range(60):
        t=time.perf_counter();im=QImage(args.width,args.height,QImage.Format.Format_RGBA8888);im.fill(QColor('#213040'));p=QPainter(im);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setRenderHint(QPainter.RenderHint.TextAntialiasing);p.scale(scale,args.height/360)
        p.fillRect(QRectF(n*5,20,80,80),QColor(210,60,70,180));p.setPen(QColor('white'));p.setFont(QFont(font,22));p.drawText(QRectF(30,180,580,140),Qt.AlignmentFlag.AlignCenter,'Tiếng Việt có dấu — 中文测试\nClean synthetic P02 probe');p.save();p.translate(320,100);p.rotate(n*2);p.setBrush(QColor(240,200,40,180));p.drawRoundedRect(QRectF(-30,-15,60,30),8,8);p.restore();p.end();timings.append(time.perf_counter()-t)
        if not im.save(str(frames/f'frame{n:03}.png')):raise RuntimeError('PNG save failed')
    source=str(frames/'frame%03d.png');video=root/'raster.mp4';lossless=root/'raster-lossless.mkv'
    run(['ffmpeg','-v','error','-framerate','30','-i',source,'-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(video)])
    run(['ffmpeg','-v','error','-framerate','30','-i',source,'-c:v','ffv1','-pix_fmt','bgr0',str(lossless)])
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'])
    orig=np.array(Image.open(frames/'frame030.png').convert('RGB'),dtype=np.int16)
    def decoded(path):return np.frombuffer(run(['ffmpeg','-v','error','-i',str(path),'-vf',"select='eq(n,30)'",'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','-']),np.uint8).reshape(args.height,args.width,3).astype(np.int16)
    ll=decoded(lossless);lossy=decoded(video);error=np.abs(orig-lossy);mae=float(error.mean());p99=float(np.quantile(error,.99));exact=bool(np.array_equal(orig,ll));sentinel=bool(not np.array_equal(orig,np.roll(ll,3,axis=1)))
    if not exact or not sentinel or mae>3 or p99>15:raise RuntimeError(f'parity failed exact={exact} shifted={sentinel} mae={mae} p99={p99}')
    media=root/'two-audio-delayed.mkv'
    run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=320x180:r=30:d=3','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=3','-itsoffset','0.25','-f','lavfi','-i','sine=frequency=880:sample_rate=48000:duration=3','-map','0:v','-map','1:a','-map','2:a','-c:v','ffv1','-c:a','pcm_s16le',str(media)])
    mp=json.loads(run(['ffprobe','-v','error','-show_streams','-of','json',str(media)]));freq=[]
    for idx in [1,2]:
        pcm=np.frombuffer(run(['ffmpeg','-v','error','-i',str(media),'-map',f'0:{idx}','-f','f32le','-ac','1','-ar','48000','-']),np.float32)[:48000];freq.append(float(np.argmax(abs(np.fft.rfft(pcm)))*48000/len(pcm)))
    if freq!=[440.0,880.0] or mp['streams'][2]['start_time']!='0.250000':raise RuntimeError('stream selection/offset fixture failed')
    env={**os.environ,'QT_AUDIO_BACKEND':'pulseaudio'}
    audio_code='from PySide6.QtWidgets import QApplication; from PySide6.QtMultimedia import QMediaDevices; import json; a=QApplication([]); print(json.dumps({"outputs":len(QMediaDevices.audioOutputs()),"inputs":len(QMediaDevices.audioInputs())}))'
    audio=json.loads(run([sys.executable,'-c',audio_code],env=env,timeout=15))
    tool_hashes={name:{'path':shutil.which(name),'sha256':digest(shutil.which(name))} for name in ['ffmpeg','ffprobe']}
    font_file=None
    if shutil.which('fc-match'):
        font_file=run(['fc-match','-f','%{file}',font]).decode().strip()
    font_provenance={'file':font_file,'sha256':digest(font_file) if font_file and Path(font_file).is_file() else None,'distribution':'system font, not bundled'}
    commit=run(['git','rev-parse','HEAD']).decode().strip();ffmpeg=run(['ffmpeg','-version']).decode();ffprobe=run(['ffprobe','-version']).decode()
    report={'generation':'clean-2026-11-01','kind':'synthetic_toolchain_experiment_NOT_product_acceptance','code_commit':commit,'command':sys.argv,'environment':{'platform':platform.platform(),'python':sys.version,'qt':qVersion(),'cpu_count':os.cpu_count(),'font_family':font,'QT_QPA_PLATFORM':os.environ['QT_QPA_PLATFORM']},'tool_hashes':tool_hashes,'font_provenance':font_provenance,'ffmpeg_version':ffmpeg,'ffprobe_version':ffprobe,'frame_dimensions':[args.width,args.height],'frame_count':60,'raster_only_ms':{'p50':statistics.median(timings)*1000,'p95':sorted(timings)[56]*1000,'max':max(timings)*1000},'parity':{'frame_index':30,'lossless_exact':exact,'h264_mae_255':mae,'h264_p99_255':p99,'shift3px_rejected':sentinel},'media_duration':{s['codec_type']:s.get('duration') for s in probe['streams']},'stream_selection':{'indices':[1,2],'frequencies':freq,'second_start':'0.250000'},'headless_pulse_audio':audio,'elapsed_seconds':time.time()-started,'outputs':{p.name:digest(p) for p in [video,lossless,media]},'status':'PASS_SCOPED_EXPERIMENT','limits':['Not implemented CompositionPlan evaluator or application','Only synthetic shapes/text selected frame; not full effects or continuous playback','Rasters timings exclude decoding/PNG IO/encoding','Linux offscreen only; no Windows/GPU/Chrome/provider/physical audio acceptance','Pulse backend no-crash may report0devices; not audio playback PASS']}
    (root/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));app.quit()
if __name__=='__main__':main()
