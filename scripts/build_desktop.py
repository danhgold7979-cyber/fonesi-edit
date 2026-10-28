"""Frozen developer build; target-platform acceptance is a separate mandatory proof."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import re
import ssl
import hashlib
import sys

parser=argparse.ArgumentParser();parser.add_argument('--without-media-tools',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parents[1];os.chdir(root)
source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src').rglob('*.py')}
source_manifest={'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),'source_hashes':source_hashes,'lock_sha256':hashlib.sha256((root/'uv.lock').read_bytes()).hexdigest()}
(root/'.local').mkdir(exist_ok=True);source_manifest_file=root/'.local/build-source-manifest.json';source_manifest_file.write_text(json.dumps(source_manifest,indent=2))
cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--name','FonesiEdit','--onedir','--paths','src',
     '--collect-all','yt_dlp','--collect-all','gallery_dl','--collect-all','fontTools','--collect-data','certifi',
     '--hidden-import','PySide6.QtMultimedia','--copy-metadata','yt-dlp','--copy-metadata','gallery-dl',
     '--copy-metadata','pysubs2','--copy-metadata','PySide6','--copy-metadata','psutil','--copy-metadata','fonttools','--copy-metadata','Pillow',
     '--add-data',f'packaging{os.pathsep}packaging']
cmd+=['--add-data',f'{source_manifest_file}{os.pathsep}metadata','--add-data',f'src{os.pathsep}source']
# Preserve any stdlib TLS policy adjunct shipped by the execution runtime; never disable verification.
tls_adjunct=Path(ssl.__file__).parent/'codex-rejected-cas.pem'
if tls_adjunct.is_file():cmd+=['--add-data',f'{tls_adjunct}{os.pathsep}.']
if not args.without_media_tools:
    for name in ['ffmpeg','ffprobe']:
        path=shutil.which(name)
        if not path:raise SystemExit('Missing '+name+'; explicitly choose --without-media-tools only for non-release developer build')
        cmd+=['--add-binary',f'{path}{os.pathsep}media/bin']
        if sys.platform.startswith('linux'):
            linked=subprocess.check_output(['ldd',path],text=True)
            libraries=set(re.findall(r'=> (/[^ ]+)',linked))
            for library in sorted(libraries):cmd+=['--add-data',f'{library}{os.pathsep}media/lib']
        elif os.name=='nt':
            for library in Path(path).parent.glob('*.dll'):cmd+=['--add-data',f'{library}{os.pathsep}media/bin']
if os.name=='nt':cmd+=['--manifest','packaging/windows.manifest']
cmd+=['scripts/app_entry.py'];subprocess.run(cmd,check=True)
manifest={'os':platform.platform(),'python':platform.python_version(),'pyinstaller':importlib.metadata.version('pyinstaller'),
          'commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'media_tools_bundled':not args.without_media_tools,
          'source_manifest':source_manifest,'acceptance':'Build only; run packaged --verify and real Windows acceptance before release'}
if shutil.which('ffmpeg'):Path('dist/FonesiEdit/ffmpeg-build.txt').write_text(subprocess.check_output([shutil.which('ffmpeg'),'-version'],text=True))
Path('dist/FonesiEdit/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
