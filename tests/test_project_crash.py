"""Actual owned-child termination at persistence boundaries, not monkeypatch-only faults."""
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import time
import uuid
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project,ProjectStore,save_project_file,load_project_file


def terminate_at_marker(code,marker):
    child=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if child.poll() is not None:
                out,err=child.communicate()
                raise AssertionError(f'Child exited before crash boundary: {child.returncode} {out!r} {err!r}')
            try:
                if marker.read_text()=='READY':break
            except OSError:pass
            time.sleep(.01)
        else:raise AssertionError('Child never reached crash boundary')
        child.kill() # exact created Popen handle only, never searched PID/process name
        child.wait(timeout=5)
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
        child.stdout.close();child.stderr.close()

@pytest.mark.parametrize('boundary,new_visible', [('after_staging',False),('after_backup',False),('after_publish',True)])
def test_project_file_kill_atomicity_and_lock_release(tmp_path,empty_plan,boundary,new_visible):
    path=tmp_path/'dự án.json';marker=tmp_path/'ready'
    project=Project(str(uuid.uuid4()),'old',CompositionPlan.parse(empty_plan))
    save_project_file(path,project)
    code=f'''from dataclasses import replace
from pathlib import Path
import time
from fonesi_edit.storage.projects import load_project_file,save_project_file
p,d=load_project_file({str(path)!r})
def fault(stage):
 if stage=={boundary!r}:
  Path({str(marker)!r}).write_text('READY')
  time.sleep(30)
save_project_file({str(path)!r},replace(p,name='new'),expected_digest=d,fault=fault)
'''
    terminate_at_marker(code,marker)
    actual,digest=load_project_file(path)
    assert actual.name==('new' if new_visible else 'old')
    assert actual.id==project.id and actual.plan==project.plan
    # OS released dead owner's advisory lock; no lockfile deletion/workaround.
    save_project_file(path,replace(actual,name='after-restart'),expected_digest=digest)
    assert load_project_file(path)[0].name=='after-restart'


def test_sqlite_kill_before_commit_preserves_previous(tmp_path,empty_plan):
    path=tmp_path/'projects.db';marker=tmp_path/'ready'
    project=Project(str(uuid.uuid4()),'old',CompositionPlan.parse(empty_plan))
    with ProjectStore(path) as store:store.save(project)
    code=f'''from dataclasses import replace
from pathlib import Path
import time
from fonesi_edit.storage.projects import ProjectStore
def fault(stage):
 if stage=='before_project_commit':
  Path({str(marker)!r}).write_text('READY')
  time.sleep(30)
with ProjectStore({str(path)!r},fault=fault) as store:
 row=store.load({project.id!r})
 store.save(replace(row.project,name='uncommitted'),expected_version=row.version)
'''
    terminate_at_marker(code,marker)
    with ProjectStore(path) as store:
        actual=store.load(project.id)
        assert actual.project.name=='old' and actual.version==1
        assert store.save(replace(project,name='recovered'),expected_version=1).version==2
