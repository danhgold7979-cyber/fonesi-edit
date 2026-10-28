from pathlib import Path
import json
import time
from fonesi_edit.core.jobs import Scheduler
from fonesi_edit.core.storage import Store


def test_real_worker_process_validation_and_pause(media,tmp_path):
    s=Store(tmp_path/'state.db');j=s.enqueue('inspect',{'path':str(media)})
    scheduler=Scheduler(s);scheduler.paused=True;scheduler.tick();assert s.get(j)['state']=='pending'
    scheduler.paused=False;deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        scheduler.tick()
        if s.get(j)['state'] in {'succeeded','failed','blocked_configuration'}:break
        time.sleep(.05)
    row=s.get(j);assert row['state']=='succeeded',row
    assert json.loads(row['result'])['validated']
    assert s.get(j)['attempt']==1
    scheduler.tick();assert not scheduler.children
