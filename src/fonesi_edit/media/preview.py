"""Bounded still-frame preview extraction; never a render or playback claim."""
from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import os
from pathlib import Path,PureWindowsPath
import stat
from threading import RLock

from fonesi_edit.jobs.process import run_owned,ProcessError,ProcessCanceled
from .probe import fingerprint,ProbeError,ProbeCanceled


class PreviewError(RuntimeError):
    pass


class PreviewCanceled(PreviewError):
    pass


@dataclass(frozen=True)
class PreviewFrame:
    png:bytes
    source_sha256:str
    tool_sha256:str
    stream_index:int
    decoder_time:Fraction
    width:int
    height:int
    cache_hit:bool=False


_SOURCE_HASHES=OrderedDict()
_FRAME_CACHE=OrderedDict()
_CACHE_LOCK=RLock()
_SOURCE_HASH_LIMIT=128
_FRAME_CACHE_LIMIT=64
_FRAME_CACHE_BYTES=48*1024*1024
_FRAME_CACHE_SIZE=0
_MAX_PNG_BYTES=8*1024*1024
_MAX_SOURCE_BYTES=32*1024**3
_MAX_TOOL_BYTES=1024**3


def _signature(path:Path):
    info=path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise PreviewError('Source/tool must be a regular non-reparse file')
    if info.st_size<1:return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def _regular_tree(path:Path):
    if not path.is_absolute():raise PreviewError('Absolute path required')
    current=Path(path.anchor)
    for part in path.parts[1:]:
        current=current/part
        _signature(current)
    return path


def resolve_asset_path(asset:dict,project_base:Path|str)->Path:
    if type(asset) is not dict or type(asset.get('path_ref')) is not dict:
        raise PreviewError('Typed composition asset path required')
    ref=asset['path_ref'];base=ref.get('base');value=ref.get('path')
    if type(value) is not str or not value or '\0' in value or len(value)>32768:
        raise PreviewError('Bounded asset path required')
    windows=PureWindowsPath(value)
    if base=='project':
        if windows.drive or windows.root or Path(value).is_absolute():
            raise PreviewError('Project-relative asset path is ambiguous')
        root=Path(project_base).absolute()
        candidate=root/value
        try:
            resolved=candidate.resolve(strict=True)
            resolved.relative_to(root.resolve(strict=True))
        except (OSError,ValueError):
            raise PreviewError('Project-relative asset escapes its project folder or is missing') from None
    elif base=='absolute':
        candidate=Path(value)
        if not candidate.is_absolute():raise PreviewError('Absolute asset path required')
    else:raise PreviewError('Unknown asset path base')
    _regular_tree(candidate)
    return candidate


def _hash_pinned(path:Path,*,tool:bool,cancel):
    global _SOURCE_HASHES
    signature=_signature(path)
    limit=_MAX_TOOL_BYTES if tool else _MAX_SOURCE_BYTES
    if signature[2]>limit:raise PreviewError('Source/tool exceeds preview input size bound')
    key=(str(path),signature)
    with _CACHE_LOCK:
        cached=_SOURCE_HASHES.get(key)
        if cached is not None:
            _SOURCE_HASHES.move_to_end(key)
            return cached,signature
    try:digest=fingerprint(path,cancel)
    except ProbeCanceled as exc:raise PreviewCanceled('Preview canceled while fingerprinting') from exc
    except ProbeError as exc:raise PreviewError('Cannot fingerprint preview input') from exc
    if _signature(path)!=signature:raise PreviewError('Preview input changed while fingerprinting')
    with _CACHE_LOCK:
        _SOURCE_HASHES[key]=digest
        _SOURCE_HASHES.move_to_end(key)
        while len(_SOURCE_HASHES)>_SOURCE_HASH_LIMIT:_SOURCE_HASHES.popitem(last=False)
    return digest,signature


def _png_dimensions(data:bytes):
    if type(data) is not bytes or not 33<=len(data)<=_MAX_PNG_BYTES or data[:8]!=b'\x89PNG\r\n\x1a\n':
        raise PreviewError('Decoder did not return a bounded PNG frame')
    if data[12:16]!=b'IHDR':raise PreviewError('PNG frame has no leading IHDR')
    width=int.from_bytes(data[16:20],'big');height=int.from_bytes(data[20:24],'big')
    if not (1<=width<=1280 and 1<=height<=720):raise PreviewError('PNG frame dimensions exceed preview bounds')
    if data[24] not in (8,16) or data[25] not in (0,2,3,4,6):raise PreviewError('Unsupported PNG sample layout')
    return width,height


def _timestamp(value:Fraction):
    if type(value) is not Fraction or value<0:raise PreviewError('Nonnegative exact decoder timestamp required')
    scale=10**9
    ticks=(value.numerator*scale*2+value.denominator)//(2*value.denominator)
    whole,fraction=divmod(ticks,scale)
    return f'{whole}.{fraction:09d}'


def _cache_key(source_hash,tool_hash,stream_index,decoder_time,max_width,max_height):
    return (source_hash,tool_hash,stream_index,decoder_time,max_width,max_height,'png-v1')


def clear_preview_cache():
    global _FRAME_CACHE_SIZE
    with _CACHE_LOCK:
        _SOURCE_HASHES.clear();_FRAME_CACHE.clear();_FRAME_CACHE_SIZE=0


def extract_preview_frame(source:Path|str,ffmpeg:Path|str,*,expected_sha256:str,
                          stream_index:int,decoder_time:Fraction,cancel=lambda:False,
                          timeout:float=20,max_width:int=1280,max_height:int=720)->PreviewFrame:
    """Extract one explicit stream frame into bounded memory; no disk/cache writes.

    Decoder time is absolute stream timestamp (stream_start + stream-relative time).
    This is a still-frame convenience preview; it does not certify PTS parity,
    audio synchronization, codec support, full decode validity or export readiness.
    """
    global _FRAME_CACHE_SIZE
    source=Path(source);ffmpeg=Path(ffmpeg)
    if (not source.is_absolute() or not ffmpeg.is_absolute() or
        type(expected_sha256) is not str or len(expected_sha256)!=64 or
        any(ch not in '0123456789abcdef' for ch in expected_sha256) or
        type(stream_index) is not int or not 0<=stream_index<=2**31-1 or
        type(decoder_time) is not Fraction or
        type(timeout) not in (int,float) or not 0<timeout<=120 or
        type(max_width) is not int or not 1<=max_width<=1280 or
        type(max_height) is not int or not 1<=max_height<=720):
        raise PreviewError('Explicit bounded still-preview inputs required')
    if cancel():raise PreviewCanceled('Preview canceled before input inspection')
    _regular_tree(source);_regular_tree(ffmpeg)
    if not os.access(ffmpeg,os.X_OK):raise PreviewError('Explicit FFmpeg executable is not executable')
    source_hash,source_signature=_hash_pinned(source,tool=False,cancel=cancel)
    if source_hash!=expected_sha256:raise PreviewError('Source content no longer matches the project asset hash')
    tool_hash,tool_signature=_hash_pinned(ffmpeg,tool=True,cancel=cancel)
    key=_cache_key(source_hash,tool_hash,stream_index,decoder_time,max_width,max_height)
    with _CACHE_LOCK:
        cached=_FRAME_CACHE.get(key)
        if cached is not None:
            _FRAME_CACHE.move_to_end(key)
            if _signature(source)==source_signature and _signature(ffmpeg)==tool_signature:
                return PreviewFrame(cached.png,source_hash,tool_hash,stream_index,decoder_time,
                                    cached.width,cached.height,True)
            _FRAME_CACHE.pop(key,None);_FRAME_CACHE_SIZE-=len(cached.png)
    if cancel():raise PreviewCanceled('Preview canceled before decoder launch')
    args=[str(ffmpeg),'-nostdin','-hide_banner','-loglevel','error',
          '-protocol_whitelist','file,pipe','-i',str(source),
          '-ss',_timestamp(decoder_time),'-map',f'0:{stream_index}',
          '-an','-sn','-dn','-frames:v','1','-threads','1',
          '-vf',f'scale=w={max_width}:h={max_height}:force_original_aspect_ratio=decrease',
          '-f','image2pipe','-vcodec','png','pipe:1']
    try:result=run_owned(args,cancel=cancel,timeout=timeout,max_output_bytes=_MAX_PNG_BYTES)
    except ProcessCanceled as exc:raise PreviewCanceled('Preview decoder canceled; owned process retired') from exc
    except (ProcessError,OSError) as exc:raise PreviewError('Preview decoder failed or retirement was not confirmed') from exc
    if cancel():raise PreviewCanceled('Preview canceled after decoder retirement')
    if result.returncode!=0:raise PreviewError('FFmpeg did not produce a preview frame')
    if _signature(source)!=source_signature or _signature(ffmpeg)!=tool_signature:
        raise PreviewError('Source or FFmpeg changed during preview extraction')
    width,height=_png_dimensions(result.stdout)
    frame=PreviewFrame(result.stdout,source_hash,tool_hash,stream_index,decoder_time,width,height,False)
    with _CACHE_LOCK:
        _FRAME_CACHE[key]=frame;_FRAME_CACHE.move_to_end(key);_FRAME_CACHE_SIZE+=len(frame.png)
        while _FRAME_CACHE and (_FRAME_CACHE_SIZE>_FRAME_CACHE_BYTES or len(_FRAME_CACHE)>_FRAME_CACHE_LIMIT):
            _,removed=_FRAME_CACHE.popitem(last=False);_FRAME_CACHE_SIZE-=len(removed.png)
    return frame
