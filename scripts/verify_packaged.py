"""Run the desktop and independent workers from the frozen application."""
from pathlib import Path
import argparse
import json
import os
import subprocess
from datetime import datetime,timezone

parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
folder=(args.folder or root/'.local'/('packaged-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))).resolve()
executable=root/'dist/FonesiEdit'/('FonesiEdit.exe' if os.name=='nt' else 'FonesiEdit')
if not executable.is_file():raise SystemExit('Build FonesiEdit first')
env={**os.environ,'QT_QPA_PLATFORM':'offscreen'};env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
subprocess.run([str(executable),'--verify',str(folder)],env=env,check=True,timeout=150)
report=json.loads((folder/'proof.json').read_text(encoding='utf-8'))
if not report.get('passed') or not report.get('frozen'):raise SystemExit('Frozen proof did not pass')
if not report.get('bilingual_render_verified') or not report.get('rename_undo_verified'):raise SystemExit('Frozen subtitle/rename proof missing')
for name in ['ffmpeg','ffprobe']:
    tool=next(t for t in report['toolchain'] if t['name']==name)
    if not Path(tool['path']).is_relative_to(executable.parent):raise SystemExit('Proof used a system media tool instead of bundled '+name)
source=next(j['result']['output'] for j in report['jobs'] if j['kind']=='render')
subprocess.run([str(executable),'--smoke','--source',source,'--screenshot',str(folder/'desktop.png'),'--data-dir',str(folder/'ui-state')],env=env,check=True,timeout=40)
if not (folder/'desktop.png').is_file():raise SystemExit('UI evidence missing')
print('Frozen app + render/batch/matrix + video/image download over localhost + UI passed:',folder)
