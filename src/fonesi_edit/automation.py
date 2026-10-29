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
        if not executable:
            _GPU['data']=None
            return
        result=subprocess.run([executable,'--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2)
        if result.returncode:
            _GPU['data']=None
            return
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
    if profile not in {'quiet','balanced','max'}:
        raise ValueError('Unknown resource profile; choose quiet, balanced or max')
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


def submit_many_once(store, kind, requests):
    """Atomically enqueue a bounded list of idempotent jobs.

    Each request is (payload, stable_key). All validation happens before the
    first write. Existing keys are reused only with exactly the same kind and
    canonical snapshot; an unrelated or changed job never silently replaces
    the requested work. One SQL error rolls back the *whole* batch.
    """
    if kind not in {'render', 'scan', 'download', 'translate'}:
        raise ValueError('Loại job hàng loạt không hợp lệ')
    if not isinstance(requests, (list, tuple)) or len(requests) > 500:
        raise ValueError('Chỉ enqueue tối đa 500 job đồng bộ một lần')
    tool_paths = store.setting('tool_paths', {})
    prepared = []
    identities = set()
    for item in requests:
        if (not isinstance(item, (tuple, list)) or len(item) != 2
                or not isinstance(item[0], dict) or type(item[1]) is not str
                or not 1 <= len(item[1]) <= 4096):
            raise ValueError('Snapshot hoặc khóa idempotent hàng loạt không hợp lệ')
        payload, key = item
        job_id = hashlib.sha256(key.encode()).hexdigest()[:32]
        if job_id in identities:
            raise ValueError('Khóa job bị trùng trong cùng nhóm đồng bộ')
        identities.add(job_id)
        encoded = canonical(checked_payload({**payload, '_tools': tool_paths}))
        prepared.append((job_id, encoded))
    created = existing = 0
    with store.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        for job_id, encoded in prepared:
            row = conn.execute('SELECT kind,payload FROM jobs WHERE id=?', (job_id,)).fetchone()
            if row is not None:
                if row['kind'] != kind or row['payload'] != encoded:
                    raise ValueError(
                        'Khóa job đồng bộ đã tồn tại với loại hoặc snapshot khác; '
                        'không ghi đè hoặc đổi tài khoản')
                existing += 1
                continue
            now = time.time()
            conn.execute(
                "INSERT INTO jobs(id,kind,state,payload,created,updated,depends_on) "
                "VALUES(?,?,'pending',?,?,?,?)",
                (job_id, kind, encoded, now, now, canonical([])))
            created += 1
    return {'ids': [job_id for job_id, _ in prepared],
            'created': created, 'existing': existing}


class Automation:
    def __init__(self,store):self.store=store;self.stop_event=Event();self.thread=None;self.errors=[];self.seen={}
    def start(self):
        self.thread=Thread(target=self.loop,daemon=True);self.thread.start()
    def stop(self):self.stop_event.set()
    def loop(self):
        while not self.stop_event.wait(3):
            try:self.tick()
            except Exception as exc:
                from .worker import sanitize_error_message
                self.errors=(self.errors+[sanitize_error_message(exc,limit=400)])[-20:]
    def tick(self):
        self.watch();self.completed_scheduled_scans();self.schedules();self.completed_downloads()
    def watch(self):
        watches=self.store.setting('watches',[])
        for watch in watches:
            root=Path(watch['folder'])
            if not root.is_dir():continue
            for current,dirs,files in root.walk(follow_symlinks=False):
                dirs[:]=[d for d in dirs if not d.startswith('.') and not d.lower().endswith(' edit') and d.lower() not in {'cache','profiles','browser-profiles','videos edit','quality-upgrades'}]
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
    def completed_scheduled_scans(self):
        """Safely reconcile a successful scheduled scan before the next period.

        The active pointer and processed receipt persist across app restarts.
        If history is unsafe or a job failed, neither progress nor schedule
        replacement is recorded; Queue retry/manual correction is required.
        """
        from .sync import selectable_sync_indices, plan_new_only_sync, sync_media_identity
        with self.store.connect() as conn:
            schedule_ids=[row['id'] for row in conn.execute('SELECT id FROM schedules')]
        processed=[]
        for schedule_id in schedule_ids:
            active=self.store.cached('schedule-active:'+schedule_id)
            if not isinstance(active,dict) or not active.get('job'):
                continue
            scan=self.store.job(active['job'])
            if (scan['kind']!='scan' or scan['state']!='succeeded'
                    or (scan.get('payload') or {}).get('sync_schedule_id')!=schedule_id):
                continue
            marker='schedule-synced:'+scan['id']
            if self.store.cached(marker):
                continue
            result=scan.get('result')
            if not isinstance(result,dict) or not isinstance(result.get('items'),list):
                raise ValueError('Scan theo lịch chưa có danh sách kết quả hợp lệ; chưa đồng bộ')
            indices=selectable_sync_indices(result['items'])
            # Reuse the same validated snapshot/account/URL checks as manual sync.
            if indices:
                from .downloads import selected_download_payloads
                selected=selected_download_payloads(scan,indices)
                history=self.store.download_jobs_for_urls([p['url'] for p in selected])
                plan=plan_new_only_sync(scan,indices,history)
            else:
                plan={'payloads':[],'already_valid':0,'already_queued':0,'total':0}
            batch=[]
            for request in plan['payloads']:
                payload={key:value for key,value in request.items()
                         if key not in {'sync_schedule_id','sync_schedule_slot'}}
                batch.append((payload,sync_media_identity(payload)))
            posted=submit_many_once(self.store,'download',batch)
            receipt={'scan_job':scan['id'],'count':plan['total'],
                     'new_jobs':posted['created'],'reused_jobs':posted['existing'],
                     'already_valid':plan['already_valid'],
                     'already_queued':plan['already_queued'],
                     'complete':result.get('complete')}
            # Marker is written only after the batch transaction succeeded.
            # On crash before this write, the stable key prevents duplicates.
            self.store.cache(marker,receipt)
            processed.append(receipt)
        return processed

    def schedules(self):
        """Run bounded scan-first schedules; never repeatedly download a channel."""
        with self.store.connect() as conn:
            rows=[dict(r) for r in conn.execute(
                'SELECT * FROM schedules WHERE next_run<=?',(time.time(),))]
        scheduled=[]
        for row in rows:
            data=json.loads(row['data'])
            if not isinstance(data,dict) or data.get('mode','scan_new_only')!='scan_new_only':
                raise ValueError('Chỉ hỗ trợ lịch quét rồi đồng bộ mục mới')
            base=data.get('payload')
            if not isinstance(base,dict) or base.get('download_mode','media')!='media':
                raise ValueError('Lịch chỉ được quét nguồn media thông thường')
            limit=base.get('limit',0)
            if type(limit) is not int or limit<0:
                raise ValueError('Giới hạn quét theo lịch không hợp lệ')
            interval=data.get('interval')
            if type(interval) not in {int,float} or not 60<=interval<=6_000_000:
                raise ValueError('Khoảng lịch đồng bộ phải là số giây hợp lệ')
            existing=self.store.cached('schedule-active:'+row['id'])
            if isinstance(existing,dict) and existing.get('job'):
                previous=self.store.job(existing['job'])
                if previous['kind']=='scan':
                    # Failed/canceled scans stay blocked pending explicit retry;
                    # succeeded scans must be reconciled before the next cycle.
                    if (previous['state']!='succeeded'
                            or not self.store.cached('schedule-synced:'+previous['id'])):
                        continue
                elif previous['state'] in {'pending','running','blocked'}:
                    # Legacy direct-download schedule already running.
                    continue
            slot=int(row['next_run'])
            scan_payload={**base,'limit':100 if limit==0 else min(200,limit),
                          'sync_schedule_id':row['id'],'sync_schedule_slot':slot}
            key=f'schedule-scan:{row["id"]}:{slot}'
            job_id=submit_once(self.store,'scan',scan_payload,key)
            self.store.cache('schedule-active:'+row['id'],{'job':job_id})
            now=time.time()
            with self.store.connect() as conn:
                conn.execute('UPDATE schedules SET last_run=?,next_run=? WHERE id=?',
                             (now,now+max(60,interval),row['id']))
            scheduled.append(job_id)
        return scheduled

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
