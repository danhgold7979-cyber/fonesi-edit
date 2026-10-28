"""A bounded subprocess scheduler; the desktop never runs heavy jobs on its UI thread."""
from pathlib import Path
import json
import os
import subprocess
import sys
import threading
import time
from .model import uid
from .process import Cancelled, redact
from .storage import Store


def worker_command(db: Path, job_id: str, owner: str) -> list[str]:
    if getattr(sys,'frozen',False):
        return [sys.executable,'--worker',str(db),job_id,owner]
    return [sys.executable,'-m','fonesi_edit.app','--worker',str(db),job_id,owner]


class Scheduler:
    def __init__(self, store: Store, limit=1):
        self.store=store;self.limit=limit;self.paused=False;self.children={}
        self.store.recover()

    def tick(self):
        for jid,proc in list(self.children.items()):
            if proc.poll() is not None:
                del self.children[jid]
                row=self.store.get(jid)
                if row['state'] in {'running','validating'}:
                    self.store.finish(jid,row['owner'],'failed',error=f'Worker exited unexpectedly ({proc.returncode}); stage can be retried')
        if self.paused:return
        while len(self.children)<self.limit:
            owner=uid();row=self.store.claim(owner)
            if row is None:break
            try:
                proc=subprocess.Popen(worker_command(self.store.path,row['id'],owner),stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                self.children[row['id']]=proc
            except OSError as exc:
                self.store.finish(row['id'],owner,'failed',error=redact(str(exc)))

    def shutdown(self, cancel=False):
        self.paused=True
        if cancel:
            for jid in self.children:self.store.cancel(jid)


def execute_job(db: Path, job_id: str, owner: str):
    store=Store(db);row=store.get(job_id)
    if row['owner']!=owner or row['state']!='running':raise RuntimeError('Worker does not own job')
    stopped=threading.Event()
    def heartbeat():
        while not stopped.wait(3):store.heartbeat(job_id,owner)
    thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
    cancel=lambda:bool(store.get(job_id)['cancel_requested'])
    progress=lambda stage,value,message='':store.update_progress(job_id,owner,stage,value,message)
    try:
        snapshot=json.loads(row['snapshot'])
        for name,path in snapshot.get('tools',{}).items():
            if path:os.environ['FONESI_'+name.upper()+'_PATH']=path
        if row['kind']=='inspect':
            from ..services.media import validate_media
            progress('validating',None,'Kiểm tra giải mã media')
            result=validate_media(Path(snapshot['path']),cancel=cancel)
            result['path']=snapshot['path']
        elif row['kind']=='render':
            from ..services.render import render_project
            from .model import Project
            result=render_project(Project.from_dict(snapshot['project']),Path(snapshot['output']),cancel=cancel,progress=progress)
        elif row['kind']=='download':
            from ..services.downloads import download
            result=download(snapshot,cancel=cancel,progress=progress)
        else:
            raise ValueError('Unknown job type: '+row['kind'])
        if cancel():raise Cancelled('Canceled before completion')
        if snapshot.get('matrix'):
            from ..services.matrix import commit_history
            commit_history(store,snapshot['matrix']['project_id'],snapshot['matrix']['key'],job_id,result)
        store.finish(job_id,owner,'succeeded_with_warnings' if result.get('warnings') else 'succeeded',result=result)
    except Cancelled as exc:
        store.finish(job_id,owner,'canceled',error=str(exc))
    except (FileNotFoundError,PermissionError) as exc:
        store.finish(job_id,owner,'blocked_configuration',error=redact(str(exc)))
    except Exception as exc:
        store.finish(job_id,owner,'failed',error=redact(f'{type(exc).__name__}: {exc}'))
    finally:
        stopped.set();thread.join(timeout=1)
