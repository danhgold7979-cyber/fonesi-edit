"""Opt-in app-open scheduling, stable-file detection and owned cache cleanup."""
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import time
import psutil
from ..core.model import digest
from ..core.paths import contained,content_hash
from .batch import scan_folders


@dataclass
class ResourcePolicy:
    reserve_ram:int=512*1024**2
    reserve_disk:int=512*1024**2
    render_limit:int=1
    download_limit:int=2
    inspect_limit:int=2

    def admission(self,root:Path,required_disk=0):
        metrics=measure(root)
        if metrics['available_ram'] is not None and metrics['available_ram']<self.reserve_ram:return False,'RAM below configured reserve'
        if metrics['free_disk'] is not None and metrics['free_disk']-required_disk<self.reserve_disk:return False,'Disk below configured reserve'
        return True,'ready'


def measure(root):
    result={'cpu_percent':None,'available_ram':None,'free_disk':None,'gpu_percent':None,'vram_free':None,'temperature':None}
    try:result.update(cpu_percent=psutil.cpu_percent(),available_ram=psutil.virtual_memory().available,free_disk=shutil.disk_usage(root).free)
    except (OSError,RuntimeError):pass
    return result


class StableWatcher:
    def __init__(self,roots,exclude=(),stable_seconds=2):self.roots=roots;self.exclude=exclude;self.stable_seconds=stable_seconds;self.seen={};self.emitted={}
    def poll(self,now=None):
        now=time.monotonic() if now is None else now;ready=[];present=set()
        for path in scan_folders(self.roots,self.exclude):
            present.add(path)
            try:stat=path.stat()
            except OSError:continue
            signature=(stat.st_size,stat.st_mtime_ns)
            old=self.seen.get(path)
            if not old or old[0]!=signature:self.seen[path]=(signature,now);continue
            if now-old[1]>=self.stable_seconds and self.emitted.get(path)!=signature:
                ready.append(path);self.emitted[path]=signature
        for path in set(self.seen)-present:self.seen.pop(path,None);self.emitted.pop(path,None)
        return ready


class Schedule:
    def __init__(self,store):self.store=store
    def add(self,identity,interval_seconds,config,missed='once'):
        if interval_seconds<10 or missed not in {'once','skip'}:raise ValueError('Invalid schedule')
        self.store.put('schedule',identity,{'interval':interval_seconds,'next':time.time()+interval_seconds,'config':config,'missed':missed,'running':None,'enabled':True})
    def due(self,now=None):
        now=now or time.time();result=[]
        for key,item in self.store.objects('schedule').items():
            if not item['enabled'] or item.get('running') or item['next']>now:continue
            elapsed=now-item['next'];item['next']=now+item['interval']
            if item['missed']=='skip' and elapsed>item['interval']:self.store.put('schedule',key,item);continue
            item['running']='reserved';self.store.put('schedule',key,item);result.append((key,item['config']))
        return result
    def finish(self,identity):
        item=self.store.objects('schedule')[identity];item['running']=None;self.store.put('schedule',identity,item)


def workflow_jobs(store,items:list[dict],mode='batch'):
    if mode not in {'batch','rolling'}:raise ValueError('Unknown workflow mode')
    downloads=[store.enqueue('download',x['download'],dedupe_key='download:'+digest(x['download'])) for x in items]
    # Render snapshots explicitly refer to expected stable input; validation step handles missing/failed download.
    downstream=[]
    for i,item in enumerate(items):
        if not item.get('render'):continue
        deps=[(j,True) for j in downloads] if mode=='batch' else [(downloads[i],False)]
        downstream.append(store.enqueue('render',item['render'],dependencies=deps,dedupe_key='render:'+digest(item['render'])))
    return downloads,downstream


def cleanup_cache(root:Path,max_bytes:int,leased=()):
    root=Path(root).resolve();marker=root/'.fonesi-cache'
    if not marker.is_file() or marker.read_text()!='owned-cache-v1':raise ValueError('Refuse cleanup without owned-cache marker')
    leases={Path(p).resolve() for p in leased};files=[]
    for p in root.rglob('*'):
        if p==marker or not p.is_file() or p.is_symlink() or not contained(p,root):continue
        files.append((p.stat().st_mtime,p.stat().st_size,p))
    total=sum(size for _,size,_ in files);removed=[]
    for _,size,p in sorted(files):
        if total<=max_bytes:break
        if p.resolve() in leases:continue
        p.unlink();total-=size;removed.append(str(p))
    return removed
