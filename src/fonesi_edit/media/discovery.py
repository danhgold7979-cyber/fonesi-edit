"""Bounded read-only local discovery, excluding output/cache/staging namespaces.

Uses standard os.scandir and the existing tested directory-pin capability; no new
native adapter or recursive symlink following. Results are candidates, NOT decoded
media validation or authority to render/publish. Network/OS I/O has no hard deadline.
"""
from contextlib import ExitStack
from dataclasses import dataclass
import os
from pathlib import Path
import stat

from fonesi_edit.artifacts.filesystem import Destination,PublicationError


class DiscoveryError(RuntimeError):pass


@dataclass(frozen=True)
class ScanResult:
    paths: tuple[Path,...]
    examined: int
    excluded: int
    status: str


# Candidate extensions only; actual probe/decode remains mandatory.
MEDIA_EXTENSIONS=frozenset({'.mp4','.mkv','.mov','.webm','.avi','.m4v','.mp3','.wav','.m4a','.aac','.flac','.ogg','.opus','.jpg','.jpeg','.png','.webp','.bmp'})


def scan_media(root,*,excluded_roots=(),excluded_file_ids=(),extensions=None,cancel=lambda:False,
               max_entries=100000,max_results=10000,max_depth=64):
    if (type(max_entries) is not int or not 1<=max_entries<=1000000 or
        type(max_results) is not int or not 1<=max_results<=100000 or
        type(max_depth) is not int or not 1<=max_depth<=64):
        raise DiscoveryError('Bounded scan limits required')
    if type(excluded_roots) is not tuple or len(excluded_roots)>128:
        raise DiscoveryError('Explicit bounded output/cache roots required')
    if (type(excluded_file_ids) is not tuple or len(excluded_file_ids)>100000 or
        any(type(x) is not tuple or len(x)!=2 or any(type(n) is not int or n<0 for n in x) for x in excluded_file_ids)):
        raise DiscoveryError('Bounded physical artifact identities required')
    if extensions is not None and (type(extensions) is not frozenset or len(extensions)>128 or
        any(type(x) is not str or not x.startswith('.') or not 2<=len(x)<=16 or not x[1:].isascii() or not x[1:].isalnum() or x!=x.lower() for x in extensions)):
        raise DiscoveryError('Explicit bounded lowercase extension filter required')
    blocked_files=set(excluded_file_ids);found=[];seen_files=set();seen_dirs=set()
    examined=0;excluded=0;status='COMPLETE'
    def under(path,parent):return path==parent or parent in path.parents
    try:
        with ExitStack() as stack:
            source=stack.enter_context(Destination(root))
            blocked=[stack.enter_context(Destination(path)) for path in excluded_roots]
            blocked_ids={item.identity for item in blocked}
            if any(under(source.root,item.root) or source.identity==item.identity for item in blocked):
                raise DiscoveryError('Source root overlaps an excluded output/cache root')
            def check():
                nonlocal status
                if cancel():status='PARTIAL_CANCELED';return False
                source._check()
                for item in blocked:item._check()
                return True
            def walk(directory,depth):
                nonlocal examined,excluded,status
                if not check():return
                if directory.identity in seen_dirs:excluded+=1;return
                seen_dirs.add(directory.identity)
                with os.scandir(directory.fd if directory.fd is not None else directory.root) as entries:
                    for entry in entries:
                        if not check():return
                        directory._check()
                        if examined>=max_entries:status='PARTIAL_LIMIT';return
                        examined+=1
                        info=entry.stat(follow_symlinks=False);identity=(info.st_dev,info.st_ino)
                        path=directory.root/entry.name
                        if (stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400 or
                            entry.name.startswith('.fonesi-stage-') or identity in blocked_files or
                            any(under(path,item.root) for item in blocked)):
                            excluded+=1;continue
                        if stat.S_ISDIR(info.st_mode):
                            if identity in blocked_ids:excluded+=1;continue
                            if depth>=max_depth:status='PARTIAL_LIMIT';return
                            with Destination(path) as child:
                                if child.identity!=identity:raise DiscoveryError('Directory changed during discovery')
                                walk(child,depth+1)
                            if status!='COMPLETE':return
                        elif stat.S_ISREG(info.st_mode) and (extensions is None or path.suffix.lower() in extensions):
                            if not info.st_ino:raise DiscoveryError('Source filesystem lacks physical identity')
                            if identity in seen_files:excluded+=1;continue
                            if len(found)>=max_results:status='PARTIAL_LIMIT';return
                            seen_files.add(identity);found.append(path)
                directory._check()
            walk(source,0)
            check() # cancellation/identity at return boundary, not only entry boundaries
    except DiscoveryError:raise
    except (OSError,PublicationError) as exc:
        raise DiscoveryError('Source or exclusion namespace unavailable or changed; no files modified') from exc
    return ScanResult(tuple(sorted(found)),examined,excluded,status)
