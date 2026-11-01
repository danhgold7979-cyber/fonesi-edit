"""Python process stand-ins for pair/Qt routing, not FFmpeg capability evidence."""
import sys,time,threading
from pathlib import Path
from hashlib import sha256
import pytest
from fonesi_edit.dependencies.retirement import PairRetirement
from fonesi_edit.dependencies.fixture import materialize_fixture,SHA256,SIZE,EXPECTED
from fonesi_edit.dependencies.checks import ToolPin,check_pair,ToolCheckError,ToolCheckCanceled
from fonesi_edit.jobs.process import run_owned,ProcessError,ProcessCanceled
from fonesi_edit.media.validation import MediaValidation
from fonesi_edit.ui import tool_pair as ui
import fonesi_edit.dependencies.checks as checks


def spin(app,predicate):
    end=time.monotonic()+8
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()


def install_standins(monkeypatch,*,unknown_decode=False,mismatch=False):
    versions=[]
    def owned(args,**kwargs):
        if args[-1]=='-version':
            component=('ffmpeg','ffprobe')[len(versions)];versions.append(component)
            data=(component+' version 8.1.3 Copyright\nlibavutil 60. 26.103 / 60. 26.103\nlibavcodec 62. 28.103 / 62. 28.103\nlibavformat 62. 12.103 / 62. 12.103\n').encode()
            if mismatch and component=='ffprobe':data=data.replace(b'8.1.3',b'9.0.0')
        else:data=bytes(768)
        return run_owned([sys.executable,'-c',f'import sys;sys.stdout.buffer.write({data!r})'],**kwargs)
    def validation(path,probe,decoder,expected,*,_lifecycle,cancel,timeout):
        with _lifecycle.validation_body():
            _lifecycle.run(run_owned,[sys.executable,'-c','print("probe")'],cancel=cancel,timeout=5)
            if unknown_decode:
                def unknown(*a,**k):raise ProcessError('PRIVATE retirement unknown')
                try:_lifecycle.run(unknown,[])
                except ProcessError:raise ToolCheckError('sanitized') from None
            _lifecycle.run(run_owned,[sys.executable,'-c','print("decode")'],cancel=cancel,timeout=5)
        return MediaValidation(SHA256,EXPECTED)
    monkeypatch.setattr(checks,'run_owned',owned);monkeypatch.setattr(checks,'validate_media',validation)


def pins():
    path=Path(sys.executable).resolve();digest=sha256(path.read_bytes()).hexdigest()
    return ToolPin('ffmpeg',path,digest),ToolPin('ffprobe',path,digest)


def test_five_actual_owned_standins_complete_only_exact_operation(tmp_path,monkeypatch):
    install_standins(monkeypatch);fixture=materialize_fixture(tmp_path);op=object();receipt=PairRetirement(op)
    result=check_pair(*pins(),fixture,SHA256,EXPECTED,_retirement=receipt)
    assert result.fixture_sha256==SHA256 and receipt.complete_for(op) and len(receipt.mechanisms)==5
    assert not receipt.complete_for(object())
    with pytest.raises(RuntimeError):
        with receipt.check_body():pass
    assert not receipt.confirmed_for(op)


def test_sanitized_unknown_second_media_attempt_stays_unknown(tmp_path,monkeypatch):
    install_standins(monkeypatch,unknown_decode=True);fixture=materialize_fixture(tmp_path)
    op=object();receipt=PairRetirement(op)
    with pytest.raises(ToolCheckError):check_pair(*pins(),fixture,SHA256,EXPECTED,_retirement=receipt)
    assert not receipt.confirmed_for(op) and receipt.mechanisms[-1] is None
    assert len(receipt.mechanisms)==4


def test_unentered_empty_wrong_order_receipts_never_complete():
    op=object();receipt=PairRetirement(op);assert not receipt.confirmed_for(op)
    with receipt.check_body():pass
    assert receipt.confirmed_for(op) and not receipt.complete_for(op)
    other=PairRetirement(op)
    with pytest.raises(RuntimeError):
        with other.check_body():
            with other.stage('media'):pass
    assert not other.confirmed_for(op)


def test_fixture_exact_exclusive_and_never_adopts_or_cleans(tmp_path):
    left=materialize_fixture(tmp_path);left.write_bytes(b'foreign after creation')
    right=materialize_fixture(tmp_path)
    assert left!=right and left.read_bytes()==b'foreign after creation'
    assert len(right.read_bytes())==SIZE and sha256(right.read_bytes()).hexdigest()==SHA256


def configure(panel):
    path=str(Path(sys.executable).resolve())
    panel.ffmpeg.setText(path);panel.ffprobe.setText(path);panel.trust.setChecked(True)


def test_actual_gui_pair_observation_and_either_path_resets_trust(qt_app,tmp_path,monkeypatch):
    install_standins(monkeypatch);panel=ui.PairCheckPanel(tmp_path);configure(panel)
    assert panel.start_button.isEnabled();panel.start();spin(qt_app,lambda:not panel.busy)
    output=panel.output.toPlainText();assert '8.1.3' in output and SHA256 in output and 'KHÔNG cấp lease' in output
    assert not panel.revoked and len(list(tmp_path.glob('pair-selftest-*/fixture.mp4')))==1
    panel.ffprobe.setText(str(tmp_path/'different'));assert not panel.trust.isChecked() and not panel.output.toPlainText()
    panel.trust.setChecked(True);panel.ffmpeg.setText(str(tmp_path/'different2'));assert not panel.trust.isChecked()
    panel.close()


def test_stale_input_cannot_discard_unknown_safety_latch(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event()
    def unknown(*a,_retirement,**kwargs):
        with _retirement.check_body():
            with _retirement.stage('versions'):
                entered.set();release.wait(3);raise ToolCheckError('PRIVATE delegated uncertainty')
    monkeypatch.setattr(ui,'check_pair',unknown)
    panel=ui.PairCheckPanel(tmp_path);configure(panel);panel.start();spin(qt_app,entered.is_set)
    panel.ffmpeg.setText(str(tmp_path/'new'));release.set();spin(qt_app,lambda:not panel.busy)
    assert panel.revoked and not panel.start_button.isEnabled() and 'PRIVATE' not in panel.message.text()
    panel.trust.setChecked(True);panel.start();assert panel.worker is None
    panel.close()


def test_actual_started_child_cancel_confirms_only_retirement(qt_app,tmp_path,monkeypatch):
    ready=threading.Event()
    def canceled(*a,_retirement,cancel,**kwargs):
        try:
            with _retirement.check_body():
                with _retirement.stage('versions') as scope:
                    with scope.validation_body():
                        scope.run(run_owned,[sys.executable,'-c','import time;print("READY",flush=True);time.sleep(30)'],
                            cancel=cancel,timeout=5,on_stdout=lambda b:ready.set())
        except ProcessCanceled:raise ToolCheckCanceled('canceled') from None
    monkeypatch.setattr(ui,'check_pair',canceled)
    panel=ui.PairCheckPanel(tmp_path);configure(panel);panel.start();spin(qt_app,ready.is_set)
    worker=panel.worker;panel.request_stop();assert panel.busy
    spin(qt_app,lambda:not panel.busy)
    assert worker.retired and worker.outcome=='CANCELED' and len(worker.mechanisms)==1
    assert not panel.revoked and not panel.output.toPlainText() and not panel.start_button.isEnabled()
    panel.close()


def test_fake_success_without_actual_receipt_is_not_accepted(qt_app,tmp_path,monkeypatch):
    monkeypatch.setattr(ui,'check_pair',lambda *a,**k:object())
    panel=ui.PairCheckPanel(tmp_path);configure(panel);panel.start();spin(qt_app,lambda:not panel.busy)
    assert panel.revoked and not panel.output.toPlainText()
    panel.close()


def test_known_retired_mismatched_pair_allows_manual_retry_not_readiness(qt_app,tmp_path,monkeypatch):
    install_standins(monkeypatch,mismatch=True)
    panel=ui.PairCheckPanel(tmp_path);configure(panel);panel.start();worker=panel.worker
    spin(qt_app,lambda:not panel.busy)
    assert worker.retired and worker.outcome=='REFUSED' and len(worker.mechanisms)==2
    assert not panel.revoked and panel.start_button.isEnabled() and not panel.output.toPlainText()
    panel.close()


def test_invalid_packaged_fixture_refuses_before_directory_or_decode(tmp_path,monkeypatch):
    import fonesi_edit.dependencies.fixture as fixture
    monkeypatch.setattr(fixture,'DATA',b'A'*4097)
    monkeypatch.setattr(fixture.base64,'b64decode',lambda *a,**k:pytest.fail('Oversized decode entered'))
    with pytest.raises(ValueError):fixture.materialize_fixture(tmp_path)
    assert list(tmp_path.iterdir())==[]
