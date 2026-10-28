"""Reproducible source-driven build on the current OS; never cross-claims Windows."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import json
import hashlib
from importlib.metadata import version


def isolate_linux_media(target,executables):
    """Keep Qt's LGPL codec libraries out of the independent FFmpeg process."""
    tools=target/'_internal/tools';private=tools/'lib';binary=tools/'bin';private.mkdir(exist_ok=True);binary.mkdir(exist_ok=True)
    for source in executables:
        source=Path(source);name=source.name;shutil.copyfile(source,binary/name);(binary/name).chmod(0o755)
        dependencies=subprocess.run(['ldd',str(source)],check=True,capture_output=True,text=True).stdout.splitlines()
        for line in dependencies:
            if 'not found' in line:raise RuntimeError('Unresolved FFmpeg dependency: '+line)
            if ' => /' not in line:continue
            library=Path(line.split(' => ',1)[1].split(' (',1)[0].strip())
            if library.name in {'libc.so.6','libm.so.6','libpthread.so.0','libdl.so.2','librt.so.1'}:continue
            shutil.copyfile(library,private/library.name)
        launcher=tools/name;launcher.unlink(missing_ok=True)
        launcher.write_text('#!/bin/sh\nbase=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexport LD_LIBRARY_PATH="$base/lib${LD_LIBRARY_PATH_ORIG:+:$LD_LIBRARY_PATH_ORIG}"\nexec "$base/bin/'+name+'" "$@"\n',encoding='utf-8');launcher.chmod(0o755)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-host',action='store_true');parser.add_argument('--ffmpeg-dir',type=Path);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];os.chdir(root)
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if args.ffmpeg_dir:
        ffmpeg=str(args.ffmpeg_dir/('ffmpeg.exe' if os.name=='nt' else 'ffmpeg'));ffprobe=str(args.ffmpeg_dir/('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    elif os.name=='nt' and ffmpeg and Path(ffmpeg).stat().st_size<1024*1024:
        # Chocolatey PATH may point at a shim, which would break on a clean PC.
        package=Path(os.environ.get('ChocolateyInstall','C:/ProgramData/chocolatey'))/'lib/ffmpeg'
        candidates=[p for p in package.rglob('ffmpeg.exe') if p.stat().st_size>1024*1024 and (p.parent/'ffprobe.exe').is_file()]
        if len(candidates)!=1:raise SystemExit('Choose actual FFmpeg binaries using --ffmpeg-dir; do not bundle Chocolatey shims')
        ffmpeg=str(candidates[0]);ffprobe=str(candidates[0].parent/'ffprobe.exe')
    if not ffmpeg or not ffprobe:raise SystemExit('Build needs verified FFmpeg and ffprobe in PATH')
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','FonesiEdit','--paths','src',
        '--add-binary',ffmpeg+':tools','--add-binary',ffprobe+':tools','--add-data','extension:extension',
        '--collect-submodules','yt_dlp.extractor','--collect-all','yt_dlp_ejs','--collect-submodules','gallery_dl.extractor',
        '--collect-submodules','gallery_dl.downloader','--collect-submodules','pysubs2.formats']
    if os.name=='nt':command+=['--windowed','--manifest','packaging/windows.manifest']
    command+=['scripts/app_entry.py'];subprocess.run(command,check=True)
    target=root/'dist/FonesiEdit'
    if sys.platform.startswith('linux'):isolate_linux_media(target,[ffmpeg,ffprobe])
    shutil.copyfile(root/'docs/USER_GUIDE.md',target/'USER_GUIDE.md')
    shutil.copytree(root/'docs',target/'docs',dirs_exist_ok=True)
    guide=(target/'USER_GUIDE.md').read_text(encoding='utf-8').replace('](IMPLEMENTATION_COVERAGE.md)','](docs/IMPLEMENTATION_COVERAGE.md)')
    (target/'USER_GUIDE.md').write_text(guide,encoding='utf-8')
    shutil.copyfile(root/'packaging/THIRD_PARTY_NOTICES.md',target/'THIRD_PARTY_NOTICES.md')
    inventory={name:version(name) for name in ['fonesi-edit','PySide6','yt-dlp','gallery-dl','pysubs2','psutil','fonttools','pyinstaller']}
    inventory['lock_sha256']=hashlib.sha256((root/'uv.lock').read_bytes()).hexdigest()
    inventory['media_sha256']={Path(path).name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in (ffmpeg,ffprobe)}
    inventory['source_sha256']={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((root/'src').rglob('*.py'))}
    (target/'build-info.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    with (target/'ffmpeg-build.txt').open('w',encoding='utf-8') as stream:subprocess.run([ffmpeg,'-version'],stdout=stream,stderr=stream,check=True)
    if args.native_host:
        subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--console','--name','fonesi-native-host',
            '--paths','src','--add-data','extension:extension','scripts/native_host_entry.py'],check=True)
        host=root/'dist'/('fonesi-native-host.exe' if os.name=='nt' else 'fonesi-native-host');shutil.copyfile(host,target/host.name)
    print(target)


if __name__=='__main__':main()
