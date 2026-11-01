import json
import os
from pathlib import Path
import sys
import pytest
from fonesi_edit.dependencies.discovery import discover_tools,system_search_dirs


def executable(root,name,content=b'never executed'):
    root.mkdir(exist_ok=True)
    leaf=name+'.exe' if os.name=='nt' and name in {'ffmpeg','ffprobe','yt-dlp','gallery-dl','chrome'} else name
    path=root/leaf;path.write_bytes(content);return path


def selected(report,tool):return next(x for x in report.selections if x.tool==tool)


def test_explicit_invalid_never_falls_back(tmp_path):
    system=tmp_path/'system';executable(system,'ffmpeg')
    result=discover_tools(configured={'ffmpeg':tmp_path/'missing'},system_dirs=[system])
    assert selected(result,'ffmpeg').state=='INVALID_EXPLICIT_PATH'
    assert selected(result,'ffmpeg').candidate is None
    assert any(x.tool=='ffmpeg' for x in result.candidates)


def test_auto_source_order_is_not_trust_or_execution(tmp_path):
    managed=tmp_path/'managed';bundled=tmp_path/'bundled';system=tmp_path/'system'
    paths=[executable(root,'ffmpeg') for root in (managed,bundled,system)]
    result=discover_tools(managed_dirs=[managed],bundled_dirs=[bundled],system_dirs=[system])
    pick=selected(result,'ffmpeg')
    assert pick.candidate.path==str(paths[0]) and pick.state=='NEEDS_CHECK'
    assert all(x.read_bytes()==b'never executed' for x in paths)
    assert {x.readiness for x in result.candidates}=={'UNCHECKED'}


def test_explicit_unicode_path_overrides_automatic_order(tmp_path):
    user=executable(tmp_path/'Tiếng Việt 中文','my custom tool');managed=tmp_path/'managed';executable(managed,'ffmpeg')
    result=discover_tools(configured={'ffmpeg':user},managed_dirs=[managed])
    assert selected(result,'ffmpeg').candidate.path==str(user)
    assert selected(result,'ffmpeg').candidate.source=='user'


def test_partial_limit_and_cancel_never_report_complete_missing(tmp_path):
    root=tmp_path/'tools';root.mkdir()
    limited=discover_tools(system_dirs=[root],max_checks=1)
    canceled=discover_tools(system_dirs=[root],cancel=lambda:True)
    assert limited.status=='PARTIAL_LIMIT' and limited.examined==1
    assert canceled.status=='PARTIAL_CANCELED' and canceled.examined==0
    assert all(x.state=='NOT_EXAMINED' for x in limited.selections+canceled.selections)


def test_unreadable_is_partial_not_missing(tmp_path,monkeypatch):
    root=tmp_path/'tools';root.mkdir();real=Path.lstat
    def denied(self,*args,**kwargs):
        if self.stem=='ffmpeg':raise PermissionError('denied')
        return real(self,*args,**kwargs)
    monkeypatch.setattr(Path,'lstat',denied)
    report=discover_tools(system_dirs=[root])
    assert report.status=='PARTIAL_ERRORS' and selected(report,'ffmpeg').state=='NOT_EXAMINED'


def test_path_discovery_never_adds_cwd_or_changes_environment(tmp_path):
    before=dict(os.environ);env={'PATH':os.pathsep.join(['',str(tmp_path),'relative',str(tmp_path)])}
    assert system_search_dirs(environment=env)==(tmp_path,)
    assert dict(os.environ)==before
    with pytest.raises(ValueError):system_search_dirs(environment={'PATH':os.pathsep.join(str(tmp_path/str(i)) for i in range(126))})


def test_symlink_is_only_unverified_candidate(tmp_path):
    target=executable(tmp_path/'external','target');root=tmp_path/'tools';root.mkdir()
    leaf='ffmpeg.exe' if os.name=='nt' else 'ffmpeg'
    try:(root/leaf).symlink_to(target)
    except OSError:pytest.skip('Symlink unavailable')
    candidate=selected(discover_tools(system_dirs=[root]),'ffmpeg').candidate
    assert candidate.link_or_reparse and candidate.readiness=='UNCHECKED'
    assert target.read_bytes()==b'never executed'


def test_headless_scan_reports_metadata_without_qt_or_data_init(tmp_path,monkeypatch,capsys):
    from fonesi_edit.__main__ import main
    root=tmp_path/'tools';executable(root,'ffmpeg');monkeypatch.setenv('PATH',str(root))
    data=tmp_path/'unused'
    assert main(['--scan-tools','--data-dir',str(data)])==0
    report=json.loads(capsys.readouterr().out)
    assert report['status']=='COMPLETE' and not data.exists()
    assert next(x for x in report['selections'] if x['tool']=='ffmpeg')['state']=='NEEDS_CHECK'
    # Import baseline may include Qt from other tests; no GUI is created by this path.
    assert not list(tmp_path.rglob('*.sqlite3'))


def test_invalid_tool_options_refused_before_data_creation(tmp_path,monkeypatch,capsys):
    from fonesi_edit.__main__ import main
    monkeypatch.setenv('PATH','')
    assert main(['--scan-tools','--tool-path','ffmpeg=relative'])==0
    assert selected(discover_tools(configured={'ffmpeg':'relative'}),'ffmpeg').state=='INVALID_EXPLICIT_PATH'
    assert main(['--scan-tools','--tool-path','unknown=/tmp/tool'])==2
    with pytest.raises(SystemExit):main(['--tool-dir',str(tmp_path)])


def test_declared_path_order_and_elapsed_budget(tmp_path):
    first=tmp_path/'z-first';second=tmp_path/'a-second'
    chosen=executable(first,'ffmpeg');executable(second,'ffmpeg')
    assert selected(discover_tools(system_dirs=[first,second]),'ffmpeg').candidate.path==str(chosen)
    ticks=iter([0,4])
    report=discover_tools(system_dirs=[first],timeout=3,clock=lambda:next(ticks))
    assert report.status=='PARTIAL_LIMIT' and report.examined==0


def test_fresh_process_scan_imports_no_gui_or_storage(tmp_path):
    import subprocess
    script="""
import builtins,sys
real=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.startswith(('PySide6','fonesi_edit.storage')):raise AssertionError('Forbidden initialization '+name)
    return real(name,*args,**kwargs)
builtins.__import__=guarded
from fonesi_edit.__main__ import main
raise SystemExit(main(['--scan-tools','--tool-path','chrome='+sys.argv[1]]))
"""
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path/'missing-chrome')],env={**{k:v for k,v in os.environ.items() if k.upper() not in {'PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'}},'PATH':str(tmp_path),**{key:str(tmp_path) for key in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA')}},capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    payload=json.loads(result.stdout)
    assert payload['status']=='COMPLETE'
    # Host-installed tools may be discovered; existence never grants readiness.
    assert all(c['readiness']=='UNCHECKED' for c in payload['candidates'])
    chrome=next(s for s in payload['selections'] if s['tool']=='chrome')
    assert chrome['state']=='INVALID_EXPLICIT_PATH' and chrome['candidate'] is None
    assert all(s['state'] in {'MISSING','NEEDS_CHECK','INVALID_EXPLICIT_PATH'} for s in payload['selections'])


def test_windows_named_executable_metadata_without_execution(tmp_path):
    root=tmp_path/'windows tools';root.mkdir();candidate=root/'ffmpeg.exe';candidate.write_bytes(b'not executed')
    report=discover_tools(system_dirs=[root],windows=True)
    assert selected(report,'ffmpeg').candidate.path==str(candidate)
    assert selected(report,'ffmpeg').state=='NEEDS_CHECK'
