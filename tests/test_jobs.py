from pathlib import Path
import json
import time
from fonesi_edit.core.jobs import Scheduler
from fonesi_edit.core.storage import Store


def test_real_worker_process_validation_and_pause(media,tmp_path):
    s=Store(tmp_path/'state.db');j=s.enqueue('inspect',{'path':str(media)})
    scheduler=Scheduler(s);scheduler.paused=True;scheduler.tick();assert s.get(j)['state']=='pending'
    scheduler.paused=False;deadline=time.monotonic()+20
    terminal={'succeeded','succeeded_with_warnings','failed','canceled','blocked_configuration'}
    while time.monotonic()<deadline:
        scheduler.tick()
        row=s.get(j)
        # The worker commits its terminal state just before interpreter shutdown.
        # Wait for the parent to observe process exit and reap the child as well.
        if row['state'] in terminal and j not in scheduler.children:break
        time.sleep(.05)
    row=s.get(j);assert row['state']=='succeeded',row
    assert json.loads(row['result'])['validated']
    assert s.get(j)['attempt']==1
    assert not scheduler.children
