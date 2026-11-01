"""No candidate execution: archive/control tests use owned sentinel ZIP bytes."""
import importlib.util
from pathlib import Path
import hashlib
import json
import zipfile
import pytest

spec = importlib.util.spec_from_file_location('candidate_harness', Path(__file__).parents[1]/'scripts/check_windows_ffmpeg.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def fixture(tmp_path, extra=None):
    path = tmp_path/'sentinel.zip'
    members = {'bin/ffmpeg.exe':b'NOT EXECUTABLE','bin/ffprobe.exe':b'ALSO NOT EXECUTABLE','LICENSE.txt':b'test notice'}
    with zipfile.ZipFile(path,'w') as z:
        for name,data in members.items():z.writestr('candidate/'+name,data)
        if extra:
            entry=zipfile.ZipInfo('placeholder')
            # Preserve deliberately malformed raw name; ZipInfo's constructor
            # otherwise normalizes backslashes on Windows before writing.
            entry.filename=entry.orig_filename='candidate/'+extra
            z.writestr(entry,b'foreign')
    pin = {'root':'candidate','size':path.stat().st_size,'sha256':h.digest(path),
           'members':{n:{'size':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in members.items()}}
    return path,pin


def test_exclusive_extraction_hash_and_no_execution(tmp_path,monkeypatch):
    archive,pin=fixture(tmp_path)
    monkeypatch.setattr(h,'native_cases',lambda *a:pytest.fail('Execution forbidden'))
    target=tmp_path/'owned'
    left,right=h.extract_candidate(archive,target,pin)
    assert left.read_bytes()==b'NOT EXECUTABLE' and right.read_bytes()==b'ALSO NOT EXECUTABLE'
    h.verify_members(target,pin)
    with pytest.raises(FileExistsError):h.extract_candidate(archive,target,pin)
    left.write_bytes(b'changed')
    with pytest.raises(ValueError):h.verify_members(target,pin)


@pytest.mark.parametrize('name',['../foreign','bin/CON.txt','bin/tool.','bin/tool ','bin/x:ads','bin\\x','bin/x\0hidden','BIN/FFMPEG.EXE'])
def test_unsafe_archive_refused_before_target_creation(tmp_path,name):
    archive,pin=fixture(tmp_path,name)
    target=tmp_path/'never'
    with pytest.raises(ValueError):h.extract_candidate(archive,target,pin)
    assert not target.exists()


def test_normalized_zipinfo_alias_cannot_hide_raw_backslash(tmp_path,monkeypatch):
    archive,pin=fixture(tmp_path,'bin\\x')
    original=zipfile.ZipInfo.__init__
    def normalized(self,*args,**kwargs):
        original(self,*args,**kwargs)
        self.filename=self.filename.replace('\\','/')
    monkeypatch.setattr(zipfile.ZipInfo,'__init__',normalized)
    with zipfile.ZipFile(archive) as z:
        entry=z.infolist()[-1]
        assert entry.filename=='candidate/bin/x' and entry.orig_filename=='candidate/bin\\x'
    with pytest.raises(ValueError):h.extract_candidate(archive,tmp_path/'never',pin)
    assert not (tmp_path/'never').exists()


def test_hash_and_member_pin_fail_closed(tmp_path):
    archive,pin=fixture(tmp_path)
    pin['sha256']='0'*64
    with pytest.raises(ValueError):h.extract_candidate(archive,tmp_path/'never',pin)
    assert not (tmp_path/'never').exists()
    pin['sha256']=h.digest(archive)
    pin['members']['bin/ffmpeg.exe']['sha256']='0'*64
    with pytest.raises(ValueError):h.extract_candidate(archive,tmp_path/'retained',pin)
    assert (tmp_path/'retained').exists()  # no destructive rollback/adoption


def test_explicit_execution_gate_precedes_archive_io(tmp_path,monkeypatch):
    monkeypatch.setattr(h.sys,'platform','win32')
    monkeypatch.setattr(h,'extract_candidate',lambda *a:pytest.fail('Must not extract'))
    with pytest.raises(SystemExit) as exc:
        h.main(['--archive',str(tmp_path/'missing'),'--work-dir',str(tmp_path/'work'),'--report',str(tmp_path/'report')])
    assert exc.value.code==2 and not (tmp_path/'report').exists()


def test_manifest_exact_reviewed_members():
    pin=json.loads(h.PIN.read_text())
    assert pin['asset_id']==695397553 and pin['sha256']=='5cef7bc48e513f3cee7c881e8b2999d835541edb1846c3e89443a67f8f8556ab'
    assert len(pin['members'])==10 and 'bin/ffplay.exe' not in pin['members']
    assert sum(n.endswith('.dll') for n in pin['members'])==7
