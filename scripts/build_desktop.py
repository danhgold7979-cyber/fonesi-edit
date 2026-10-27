"""Reproducible source-driven build on the current OS; never cross-claims Windows."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-host',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];os.chdir(root)
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:raise SystemExit('Build needs verified FFmpeg and ffprobe in PATH')
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','FonesiEdit','--paths','src',
        '--add-binary',ffmpeg+':tools','--add-binary',ffprobe+':tools','--add-data','extension:extension',
        '--collect-submodules','yt_dlp.extractor','--collect-all','yt_dlp_ejs','--collect-submodules','gallery_dl.extractor',
        '--collect-submodules','gallery_dl.downloader','--collect-submodules','pysubs2.formats']
    if os.name=='nt':command+=['--windowed','--manifest','packaging/windows.manifest']
    command+=['scripts/app_entry.py'];subprocess.run(command,check=True)
    target=root/'dist/FonesiEdit'
    shutil.copyfile(root/'docs/USER_GUIDE.md',target/'USER_GUIDE.md')
    shutil.copyfile(root/'packaging/THIRD_PARTY_NOTICES.md',target/'THIRD_PARTY_NOTICES.md')
    with (target/'ffmpeg-build.txt').open('w',encoding='utf-8') as stream:subprocess.run([ffmpeg,'-version'],stdout=stream,stderr=stream,check=True)
    if args.native_host:
        subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--console','--name','fonesi-native-host',
            '--paths','src','--add-data','extension:extension','scripts/native_host_entry.py'],check=True)
        host=root/'dist'/('fonesi-native-host.exe' if os.name=='nt' else 'fonesi-native-host');shutil.copyfile(host,target/host.name)
    print(target)


if __name__=='__main__':main()
