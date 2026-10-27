from copy import deepcopy
from pathlib import Path
from threading import Thread,Event
import hashlib
import json
import os
import time
import shutil
import subprocess
import csv

import psutil
from .batch import batch_plan,VIDEO_EXTENSIONS
from .domain import Composition,canonical,checked_payload

_GPU={'data':None,'checked':0,'busy':False}

def update_gpu():
    try:
        executable=shutil.which('nvidia-smi')
        if not executable:return
        result=subprocess.run([executable,'--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2)
        if result.returncode:return
        rows=list(csv.reader(result.stdout.splitlines()))
        _GPU['data']=[{'name':r[0].strip(),'percent':float(r[1]),'used_mib':float(r[2]),'total_mib':float(r[3]),'temperature':float(r[4])} for r in rows if len(r)==5]
    except (OSError,ValueError,subprocess.TimeoutExpired):_GPU['data']=None
    finally:_GPU['checked']=time.time();_GPU['busy']=False


def metrics(path):
    ram=psutil.virtual_memory();disk=psutil.disk_usage(str(path))
    if not _GPU['busy'] and time.time()-_GPU['checked']>3:
        _GPU['busy']=True;Thread(target=update_gpu,daemon=True).start()
    return {'cpu_percent':psutil.cpu_percent(interval=None),'cores':psutil.cpu_count() or 1,'ram_available':ram.available,'ram_total':ram.total,
        'disk_free':disk.free,'gpu':_GPU['data'],'vram':None,'sampled':time.time()}


def recommended_parallel(data,profile='balanced'):
    if data['ram_available']<1024**3 or data['disk_free']<256*1024**2 or data.get('cpu_percent',0)>=97:return 0
    cap=1 if profile=='quiet' else 2 if profile=='balanced' else max(1,data['cores']-1)
    return max(1,min(cap,max(1,int(data['ram_available']/(2*1024**3))),max(1,data['cores']//2)))


def submit_once(store,kind,payload,key,depends_on=()):
    payload=checked_payload({**payload,'_tools':store.setting('tool_paths',{})})
    job_id=hashlib.sha256(key.encode()).hexdigest()[:32]
    with store.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT id FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row:return row[0]
        now=time.time()
        conn.execute("INSERT INTO jobs(id,kind,state,payload,created,updated,depends_on) VALUES(?,?,'pending',?,?,?,?)",(job_id,kind,canonical(payload),now,now,canonical(list(depends_on))))
    return job_id


class Automation:
    def __init__(self,store):self.store=store;self.stop_event=Event();self.thread=None;self.errors=[];self.seen={}
    def start(self):
        self.thread=Thread(target=self.loop,daemon=True);self.thread.start()
    def stop(self):self.stop_event.set()
    def loop(self):
        while not self.stop_event.wait(3):
            try:self.tick()
            except Exception as exc:self.errors=(self.errors+[str(exc)[-400:]])[-20:]
    def tick(self):
        self.watch();self.schedules();self.completed_downloads()
    def watch(self):
        watches=self.store.setting('watches',[])
        for watch in watches:
            root=Path(watch['folder'])
            if not root.is_dir():continue
            for current,dirs,files in root.walk(follow_symlinks=False):
                dirs[:]=[d for d in dirs if not d.startswith('.') and not d.lower().endswith(' edit') and d.lower() not in {'cache','profiles','browser-profiles','videos edit'}]
                for name in files:
                    path=current/name
                    if path.suffix.lower() not in VIDEO_EXTENSIONS or path.is_symlink():continue
                    stat=path.stat();stamp=(stat.st_size,stat.st_mtime_ns);key=str(path)
                    previous=self.seen.get(key);self.seen[key]=stamp
                    if previous!=stamp:continue
                    digest=hashlib.sha256(canonical([key,stamp,watch['preset']]).encode()).hexdigest()
                    if self.store.cached('watch:'+digest):continue
                    plans=batch_plan({str(current.parent if current.name=='videos' else current):[str(path)]},Composition.from_dict(watch['preset']))
                    for plan in plans:submit_once(self.store,'render',plan,'watch:'+digest)
                    self.store.cache('watch:'+digest,{'enqueued':True})
    def schedules(self):
        with self.store.connect() as conn:rows=[dict(r) for r in conn.execute('SELECT * FROM schedules WHERE next_run<=?',(time.time(),))]
        for row in rows:
            data=json.loads(row['data']);slot=int(row['next_run']);key=f'schedule:{row["id"]}:{slot}'
            existing=self.store.cached('schedule-active:'+row['id'])
            if existing and self.store.job(existing['job'])['state'] in {'pending','running','blocked'}:continue
            job=submit_once(self.store,'download',data['payload'],key)
            self.store.cache('schedule-active:'+row['id'],{'job':job})
            with self.store.connect() as conn:conn.execute('UPDATE schedules SET last_run=?,next_run=? WHERE id=?',(time.time(),time.time()+max(60,data['interval']),row['id']))
    def completed_downloads(self):
        for job in self.store.jobs(limit=2000):
            if job['kind']!='download' or job['state']!='succeeded' or not job['payload'].get('workflow'):continue
            workflow=job['payload']['workflow']
            for item in job['result'].get('files',[]):
                if item.get('kind')!='video':continue
                path=Path(item['path']);channel=path.parent.parent if path.parent.name=='videos' else path.parent
                plans=batch_plan({str(channel):[str(path)]},Composition.from_dict(workflow['preset']))
                for plan in plans:
                    deps=[job['id']];c=Composition.from_dict(plan['composition'])
                    language=workflow.get('language','vi')
                    refs=[(clip,'subtitles') for clip in c.clips if clip.subtitles]+[(layer,'path') for layer in c.layers if layer.kind=='subtitle' and layer.path and layer.style.get('subtitle_role')!='source']
                    for ref,field in refs:
                        source=Path(getattr(ref,field));existing_language=source.stem.split('.')[-1]
                        if workflow.get('translate') and not (existing_language==language or existing_language.startswith(language+'-')):
                            output=source.with_name(source.stem+'.'+language+'.srt')
                            translation=submit_once(self.store,'translate',{'source':str(source),'output':str(output),'source_language':'auto','target_language':language,'config':workflow.get('translation',{})},job['id']+':translate:'+str(source),[job['id']])
                            if translation not in deps:deps.append(translation)
                            setattr(ref,field,str(output))
                    plan['composition']=c.to_dict();submit_once(self.store,'render',plan,job['id']+':render:'+str(path),deps)
