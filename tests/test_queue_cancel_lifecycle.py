"""Real selected UI cancel to owned retirement/cleanup; Python decoder stand-in."""
from contextlib import ExitStack
from fractions import Fraction as F
import os
import sys
import threading
import time
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.inbox import CoordinatorInbox
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.publication import PublicationSession
from fonesi_edit.jobs.process import run_owned
from fonesi_edit.media.validation import ExpectedStream
from fonesi_edit.media.probe import ProbeCanceled
from fonesi_edit.artifacts.filesystem import PublicationError
from fonesi_edit.ui.queue import QueuePage
from test_retirement_lifecycle import install_python_probe
from test_queue_view import wait_for,queue


def test_selected_ui_cancel_retires_descendant_then_cleans_only_owned_stage(tmp_path,empty_plan,qt_app,monkeypatch):
    source=tmp_path/'source.bin';original=b'Python lifecycle fixture; NOT media codec evidence';source.write_bytes(original)
    root=tmp_path/'output';root.mkdir();foreign=root/'foreign.tmp';foreign.write_bytes(b'FOREIGN')
    marker=tmp_path/'child-status';release=tmp_path/'release-child';ready=threading.Event();shared={};errors=[];observations=[]
    install_python_probe(monkeypatch,observations)
    child=f'import pathlib,time;p=pathlib.Path({str(marker)!r});r=pathlib.Path({str(release)!r});p.write_text("ready");\\nwhile not r.exists():time.sleep(.01)\\np.write_text("SURVIVED")'
    parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(10)'
    def decoder(args,**kwargs):
        observations.append(kwargs['_retirement']);return run_owned([sys.executable,'-c',parent],**kwargs)
    monkeypatch.setattr('fonesi_edit.media.validation.run_owned',decoder)
    def runner():
        try:
            with ExitStack() as stack:
                repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
                empty_plan['output'].update(width=64,height=48,fps=[25,1],video_codec='h264')
                expected=ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25))
                outputs=RequiredOutputs((RequiredOutput('media','media',str(root),'final.mp4',expected_streams=(expected,)),))
                job=repo.submit('actual-ui-cancel',CompositionPlan.parse(empty_plan),0,outputs=outputs)
                owner=stack.enter_context(CoordinatorOwnership(repo));inbox=stack.enter_context(CoordinatorInbox(owner))
                job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
                session=stack.enter_context(PublicationSession(repo,owner,job))
                shared.update(inbox=inbox,job_id=job.id);ready.set()
                def cancel():
                    inbox.drain();return repo.get(job.id).cancel_requested
                with pytest.raises(ProbeCanceled):session.stage_media('media',source,sys.executable,sys.executable,cancel=cancel,timeout=8)
                assert not session._quiescence_unknown and all(o.mechanism in {'WINDOWS_JOB_EMPTY','POSIX_GROUP_RETIRED'} for o in observations)
                current=repo.get(job.id);assert current.state=='validating' and current.cancel_requested
                repo.worker_transition(current,current.lease_token,'canceled');inbox.notify_changed()
                if os.name=='nt':assert session.cleanup_canceled()==1
                else:
                    with pytest.raises(PublicationError,match='unavailable'):session.cleanup_canceled()
                shared['final_state']=repo.get(job.id).state
                assert repo.db.execute('SELECT count(*) FROM artifacts').fetchone()[0]==0
                assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
        except BaseException as exc:errors.append(exc);ready.set()
    thread=threading.Thread(target=runner);thread.start();page=None
    try:
        assert ready.wait(5) and not errors
        page=QueuePage(tmp_path/'jobs.db',inbox=shared['inbox']);page.show();page.refresh()
        wait_for(qt_app,lambda:not page.busy and marker.exists())
        assert page.table.item(0,1).text()=='validating'
        page.table.selectRow(0);page.action_buttons['cancel'].click()
        wait_for(qt_app,lambda:not page.busy and page.table.item(0,1).text()=='canceled')
        thread.join(3);assert not thread.is_alive() and not errors
        wait_for(qt_app,lambda:not page.progress_timer.isActive())
        assert shared['final_state']=='canceled' and len(observations)==2
        # Release a descendant only after the owned stage worker has
        # confirmed retirement. A surviving child must then report itself.
        release.write_text('release')
        deadline=time.monotonic()+2
        while marker.read_text()=='ready' and time.monotonic()<deadline:time.sleep(.01)
        assert marker.read_text()=='ready'
        assert source.read_bytes()==original and foreign.read_bytes()==b'FOREIGN' and not (root/'final.mp4').exists()
        assert bool(list(root.glob('.fonesi-stage-*')))==(os.name!='nt')
    finally:
        if page is not None:
            page.request_stop();wait_for(qt_app,lambda:not page.busy);page.close();page.deleteLater();qt_app.processEvents()
        if 'inbox' in shared:shared['inbox'].close()
        thread.join(10)


def test_close_is_not_terminal_refresh_until_admitted_command_finishes(queue,monkeypatch):
    import fonesi_edit.jobs.inbox as module
    from test_coordinator_inbox import request
    repo,jobs=queue;real=module._apply_owned
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        future=inbox.submit(request(repo,jobs[0],'pause'))
        def during(*args,**kwargs):
            inbox.close()
            assert inbox.state()==(1,False) # Admission still owns an unfinished operation.
            return real(*args,**kwargs)
        monkeypatch.setattr(module,'_apply_owned',during)
        assert inbox.drain()==1 and future.result().state=='paused'
        assert inbox.state()==(2,True)


def test_busy_ui_does_not_drop_transition_or_final_close_refresh(queue,qt_app):
    from fonesi_edit.jobs.view import read_queue
    repo,jobs=queue
    with CoordinatorOwnership(repo) as owner, CoordinatorInbox(owner) as inbox:
        page=QueuePage(repo.path,inbox=inbox);page.show_snapshot(read_queue(repo.path))
        index=next(i for i in range(page.table.rowCount()) if page.table.item(i,0).text()==jobs[0].id)
        repo.pause(jobs[0]);inbox.notify_changed()
        page.commander=object() # Explicit busy barrier; no fake production executor.
        page.poll_progress();assert page.table.item(index,1).text()=='pending'
        page.commander=None;page.poll_progress()
        # Another durable transition while the asynchronous snapshot may be reading.
        repo.request_cancel(repo.get(jobs[0].id));inbox.close()
        wait_for(qt_app,lambda:not page.busy and page.table.item(index,1).text()=='canceled')
        wait_for(qt_app,lambda:not page.progress_timer.isActive())
        assert not page.busy and inbox.state()[1]
        page.request_stop();page.close();page.deleteLater();qt_app.processEvents()
