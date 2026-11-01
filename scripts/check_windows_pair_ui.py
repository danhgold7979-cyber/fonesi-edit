"""Actual selected-pair GUI gate, only the separately approved pinned candidate."""
import argparse,json,platform,sys,time
from pathlib import Path
from check_windows_ffmpeg import PIN,extract_candidate,verify_members


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--work-dir',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--execute-reviewed-candidate',action='store_true')
    args=parser.parse_args(argv)
    if sys.platform!='win32' or not args.execute_reviewed_candidate:
        parser.error('Explicit reviewed Windows candidate execution required')
    if not all(p.is_absolute() for p in (args.archive,args.work_dir,args.report)):
        parser.error('Absolute owned paths required')
    pin=json.loads(PIN.read_text());report={'status':'FAIL','scope':'Actual selected pair Qt gate, not installer/lease/fullcodec/GPU',
        'platform':platform.platform(),'python':platform.python_version(),'archive_sha256':pin['sha256'],'cases':[]}
    with args.report.open('x',encoding='utf8') as stream:
        try:
            args.work_dir.mkdir(mode=0o700)
            target=args.work_dir/'candidate';ffmpeg,ffprobe=extract_candidate(args.archive,target,pin)
            verify_members(target,pin)
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QCoreApplication,QEvent
            from shiboken6 import delete
            from fonesi_edit.ui.tool_pair import PairCheckPanel
            import os
            app=QApplication([]);panel=PairCheckPanel(args.work_dir);previous=Path.cwd()
            try:
                os.chdir(target/'bin')  # Controlled private CWD as in native CPU gate.
                def wait():
                    deadline=time.monotonic()+100
                    while panel.busy and time.monotonic()<deadline:
                        app.processEvents();time.sleep(.005)
                    if panel.busy:
                        panel.request_stop()
                        deadline=time.monotonic()+25
                        while panel.busy and time.monotonic()<deadline:
                            app.processEvents();time.sleep(.005)
                        raise AssertionError('Pair UI exceeded test observation window')
                panel.ffmpeg.setText(str(ffmpeg));panel.ffprobe.setText(str(ffprobe))
                assert not panel.start_button.isEnabled()
                panel.trust.setChecked(True);panel.start();worker=panel.worker;wait()
                assert worker.outcome=='OBSERVED' and worker.retired and not panel.revoked
                assert worker.mechanisms==('WINDOWS_JOB_EMPTY',)*5
                result=worker.result
                assert result.ffmpeg.path==ffmpeg and result.ffprobe.path==ffprobe
                assert result.ffmpeg.sha256==pin['members']['bin/ffmpeg.exe']['sha256']
                assert result.ffprobe.sha256==pin['members']['bin/ffprobe.exe']['sha256']
                assert result.ffmpeg_version.version in panel.output.toPlainText()
                assert result.fixture_sha256 in panel.output.toPlainText()
                report['cases'].append({'name':'actual-selected-pair-through-Qt','version':result.ffmpeg_version.version,
                    'fixture_sha256':result.fixture_sha256,'mechanisms':worker.mechanisms,
                    'ffmpeg_sha256':result.ffmpeg.sha256,'ffprobe_sha256':result.ffprobe.sha256})
                # Both binaries remain trusted exact pins, but their assigned roles
                # are wrong. No substitution of the previously good pair allowed.
                panel.ffmpeg.setText(str(ffprobe));panel.ffprobe.setText(str(ffmpeg))
                assert not panel.trust.isChecked() and not panel.output.toPlainText()
                panel.trust.setChecked(True);panel.start();worker=panel.worker;wait()
                assert worker.outcome=='REFUSED' and worker.retired and not panel.revoked
                assert worker.mechanisms==('WINDOWS_JOB_EMPTY',)
                assert not panel.output.toPlainText()
                report['cases'].append({'name':'actual-wrong-selected-role-refused-no-fallback','mechanisms':worker.mechanisms})
                verify_members(target,pin);report['members']=pin['members'];report['status']='PASS'
            finally:
                os.chdir(previous)
                panel.request_stop()
                while panel.busy:app.processEvents();time.sleep(.005)
                panel.close();delete(panel);QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
        except BaseException as exc:
            report['failure_type']=type(exc).__name__;raise
        finally:json.dump(report,stream,indent=2)
    return 0


if __name__=='__main__':raise SystemExit(main())
