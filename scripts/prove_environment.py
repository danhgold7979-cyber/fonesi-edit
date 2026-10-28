"""Record measured local prerequisites, never infer target-platform acceptance."""
from pathlib import Path
import importlib.metadata as metadata
import json
import os
import platform
import subprocess
import tempfile
import time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication, QLabel
app=QApplication.instance() or QApplication([])
label=QLabel('Fonesi — tiếng Việt / 中文'); label.show(); app.processEvents()
report={'os':platform.platform(),'python':platform.python_version(),'qt_smoke':label.isVisible(),
        'packages':{p:metadata.version(p) for p in ['PySide6','pysubs2','psutil','fonttools','Pillow','yt-dlp','gallery-dl','pytest','pyinstaller']},
        'external':{k:'NOT RUN' for k in ['Windows','Chrome real sessions','GPU','live social download','configured translation']}}
with tempfile.TemporaryDirectory(prefix='fonesi-kiểm-中文-') as d:
 p=Path(d)/'mẫu.mp4'; start=time.monotonic()
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=25','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1','-c:v','libx264','-c:a','aac',str(p)],check=True)
 report['cpu_encode_seconds']=time.monotonic()-start
 report['probe']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
 subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
 report['decode']='PASS'
report['ffmpeg']=subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]
report['ffprobe']=subprocess.check_output(['ffprobe','-version'],text=True).splitlines()[0]
out=Path('docs/rebuild/evidence/environment.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='probe'},ensure_ascii=False,indent=2))
