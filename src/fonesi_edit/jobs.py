"""Persistent subprocess scheduler; UI calls tick without waiting on workers."""
from pathlib import Path
import os
import subprocess
import sys

from .storage import Store


class Scheduler:
    def __init__(self, store: Store, parallel=1):
        self.store, self.parallel = store, max(1, parallel)
        self.active = {}
        self.paused = False
        self.store.recover()

    def tick(self):
        for job_id, (process, log) in list(self.active.items()):
            if process.poll() is None:
                if self.store.job(job_id)["cancel_requested"]:
                    # Worker reads cancellation from SQLite and tears down FFmpeg first.
                    continue
            else:
                log.close()
                if self.store.job(job_id)["state"] == "running":
                    self.store.fail(job_id, f"Worker exited without a result ({process.returncode})")
                del self.active[job_id]
        from .automation import metrics,recommended_parallel
        sample=metrics(self.store.path.parent)
        capacity=min(self.parallel,recommended_parallel(sample,self.store.setting('resource_profile','balanced')))
        limits=self.store.setting('job_limits',{'render':1,'download':2,'scan':2,'translate':1})
        counts={kind:sum(self.store.job(key)['kind']==kind for key in self.active) for kind in limits}
        allowed={kind for kind,limit in limits.items() if counts[kind]<max(1,int(limit))}
        while not self.paused and len(self.active) < capacity and allowed:
            job = self.store.claim(allowed)
            if not job:
                break
            logs = self.store.path.parent / "logs"
            logs.mkdir(exist_ok=True)
            log = (logs / (job["id"] + ".log")).open("ab")
            args = [sys.executable, "--worker"] if getattr(sys, "frozen", False) else [sys.executable, "-m", "fonesi_edit.worker"]
            args += ["--db", str(self.store.path), "--job", job["id"]]
            try:
                process = subprocess.Popen(args, stdout=log, stderr=log, start_new_session=os.name != "nt")
            except OSError as exc:
                log.close()
                self.store.fail(job["id"], type(exc).__name__)
                continue
            self.active[job["id"]] = process, log
            kind=job['kind'];counts[kind]=counts.get(kind,0)+1
            if counts[kind]>=limits.get(kind,1):allowed.discard(kind)

    def shutdown(self):
        self.paused = True
        for job_id in list(self.active):
            self.store.cancel(job_id)
