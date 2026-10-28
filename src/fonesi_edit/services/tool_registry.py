"""Reviewed artifact pin. A successful install still needs target workflow acceptance."""
import hashlib,json,os,platform
from .tools import ToolManager

WINDOWS_FFMPEG={
    'name':'ffmpeg','version':'9.0.2','os':'Windows','architecture':'x86_64',
    'url':'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip',
    'sha256':'60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba',
    'archive':'zip','executable':'ffmpeg-9.0.2-essentials_build/bin/ffmpeg.exe',
    'required_capabilities':['scale','overlay','subtitles'],'max_bytes':160*1024**2,'max_unpacked_bytes':600*1024**2,
    'source_page':'https://www.gyan.dev/ffmpeg/builds/',
    'checksum_source':'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip.sha256',
    'reviewed':'2026-10-28','target_acceptance':'pending actual Windows proof'}
# The artifact SHA above is a committed trust pin, not downloaded dynamically at install time.
MANIFEST_SHA=hashlib.sha256(json.dumps(WINDOWS_FFMPEG,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def install_windows_ffmpeg(manager:ToolManager,cancel=lambda:False,progress=lambda *a:None):
    if platform.system()!='Windows' or platform.machine().lower() not in {'amd64','x86_64'}:raise ValueError('Pinned package is Windows x64 only; current OS is not compatible')
    key='ffmpeg:'+WINDOWS_FFMPEG['version'];existing=manager.store.objects('tool_installation').get(key)
    if existing:
        from .tools import inspect_tool
        if inspect_tool('ffmpeg',existing['path'],WINDOWS_FFMPEG['required_capabilities']).state!='ready':raise ValueError('Existing installation failed validation; repair requires a separate staged version')
        executable=existing['path']
    else:executable=manager.install(WINDOWS_FFMPEG,trusted_manifest_hash=MANIFEST_SHA,cancel=cancel,progress=progress)
    from pathlib import Path
    from .tools import inspect_tool
    probe=Path(executable).with_name('ffprobe.exe')
    if inspect_tool('ffprobe',str(probe)).state!='ready':raise ValueError('FFprobe validation failed; do not mark bundle ready')
    manager.store.put('tool_override','ffmpeg',{'path':executable});manager.store.put('tool_override','ffprobe',{'path':str(probe)})
    return {'ffmpeg':executable,'ffprobe':str(probe)}
