"""Bounded read-only executable candidate discovery. Existence is never readiness."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping,Callable,Sequence
import os
import stat
import time

TOOL_NAMES={'ffmpeg':('ffmpeg',),'ffprobe':('ffprobe',),'yt-dlp':('yt-dlp',),
            'gallery-dl':('gallery-dl',),'chrome':('chrome','google-chrome','google-chrome-stable')}
SOURCE_ORDER={'user':0,'managed':1,'bundled':2,'system':3,'extra':4}

@dataclass(frozen=True)
class Candidate:
    tool: str
    path: str
    source: str # Search-location classification, NOT ownership/trust proof.
    device: int
    inode: int
    size: int
    modified_ns: int
    link_or_reparse: bool
    readiness: str = 'UNCHECKED'

@dataclass(frozen=True)
class Selection:
    tool: str
    state: str
    candidate: Candidate|None

@dataclass(frozen=True)
class Discovery:
    status: str
    examined: int
    candidates: tuple[Candidate,...]
    selections: tuple[Selection,...]
    diagnostics: tuple[str,...]


def discover_tools(*,configured:Mapping[str,Path|str]|None=None,
                   managed_dirs:Sequence[Path|str]=(),bundled_dirs:Sequence[Path|str]=(),
                   system_dirs:Sequence[Path|str]=(),extra_dirs:Sequence[Path|str]=(),
                   cancel:Callable[[],bool]=lambda:False,max_checks:int=256,
                   timeout:float=3,clock:Callable[[],float]=time.monotonic,
                   windows:bool|None=None)->Discovery:
    if type(max_checks) is not int or not 1<=max_checks<=4096:raise ValueError('Invalid check budget')
    if type(timeout) not in (int,float) or not 0<timeout<=30:raise ValueError('Invalid time budget')
    configured=dict(configured or {})
    if not set(configured)<=set(TOOL_NAMES):raise ValueError('Unknown configured component')
    windows=os.name=='nt' if windows is None else windows
    # Bound input enumeration before constructing the candidate cross-product.
    groups=[]
    for source,dirs in (('managed',managed_dirs),('bundled',bundled_dirs),('system',system_dirs),('extra',extra_dirs)):
        if len(dirs)>128:raise ValueError('Too many search roots')
        for root in dirs:
            path=Path(root)
            if not path.is_absolute():raise ValueError('Search roots must be explicit absolute directories')
            groups.append((source,path))
    queue=[(tool,Path(path),'user') for tool,path in configured.items()]
    for source,root in groups:
        for tool,names in TOOL_NAMES.items():
            for name in names:
                queue.append((tool,root/(name+'.exe' if windows else name),source))
    candidates=[];diagnostics=[];seen=set();explicit={};examined=0;status='COMPLETE';deadline=clock()+timeout
    for tool,path,source in queue:
        if cancel():status='PARTIAL_CANCELED';break
        if examined>=max_checks or clock()>=deadline:status='PARTIAL_LIMIT';break
        examined+=1
        if not path.is_absolute():
            if source=='user':explicit[tool]='INVALID_EXPLICIT_PATH'
            diagnostics.append('NONABSOLUTE_CANDIDATE');continue
        try:
            named=path.lstat();info=path.stat()
            if not stat.S_ISREG(info.st_mode):raise ValueError('Not regular')
            linked=stat.S_ISLNK(named.st_mode) or bool(getattr(named,'st_file_attributes',0)&0x400)
            candidate=Candidate(tool,str(path),source,info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,linked)
        except (OSError,ValueError) as exc:
            if source=='user':explicit[tool]='INVALID_EXPLICIT_PATH'
            if isinstance(exc,OSError) and not isinstance(exc,(FileNotFoundError,NotADirectoryError)):
                status='PARTIAL_ERRORS';diagnostics.append('CANDIDATE_UNREADABLE')
            continue
        if source=='user':explicit[tool]=candidate
        key=(tool,info.st_dev,info.st_ino) if info.st_ino else (tool,str(path))
        if key not in seen:candidates.append(candidate);seen.add(key)
    candidates.sort(key=lambda x:SOURCE_ORDER[x.source]) # Stable declared-root/PATH order within class.
    selections=[]
    for tool in TOOL_NAMES:
        if tool in configured:
            result=explicit.get(tool)
            if isinstance(result,Candidate):selections.append(Selection(tool,'NEEDS_CHECK',result))
            else:selections.append(Selection(tool,result or 'NOT_EXAMINED',None))
        else:
            candidate=next((x for x in candidates if x.tool==tool),None)
            selections.append(Selection(tool,'NEEDS_CHECK' if candidate else 'MISSING' if status=='COMPLETE' else 'NOT_EXAMINED',candidate))
    return Discovery(status,examined,tuple(candidates),tuple(selections),tuple(sorted(set(diagnostics))))


def system_search_dirs(*,environment:Mapping[str,str]|None=None)->tuple[Path,...]:
    """Named directory candidates only; ignore relative/empty PATH entries, no cwd fallback."""
    environment=os.environ if environment is None else environment
    roots=[];seen=set();path_value=environment.get('PATH','')
    if len(path_value)>1024*1024:raise ValueError('PATH exceeds discovery budget')
    for entry in path_value.split(os.pathsep):
        if not entry:continue
        path=Path(entry)
        if path.is_absolute() and str(path) not in seen:roots.append(path);seen.add(str(path))
        if len(roots)>125:raise ValueError('PATH exceeds root budget; choose explicit directories')
    if os.name=='nt':
        for name in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            value=environment.get(name)
            if value and Path(value).is_absolute():
                roots.append(Path(value)/'Google'/'Chrome'/'Application')
    return tuple(roots)
