"""Focused P02 experiment ownership regressions, not product tests."""
import json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def invoke(script,*args):
    return subprocess.run([sys.executable,str(ROOT/'experiments'/script),*map(str,args)],capture_output=True,timeout=20,env={**os.environ,'QT_QPA_PLATFORM':'offscreen'})

def test_frozen_probe_never_overwrites_foreign_report(tmp_path):
    report=tmp_path/'report.json';report.write_bytes(b'foreign sentinel')
    result=invoke('frozen_probe.py','--report',report)
    assert result.returncode != 0
    assert report.read_bytes()==b'foreign sentinel'

def test_frozen_probe_owns_new_report(tmp_path):
    report=tmp_path/'new.json';result=invoke('frozen_probe.py','--report',report)
    assert result.returncode==0,result.stderr.decode()
    assert json.loads(report.read_text())['visible'] is True
    assert json.loads(report.read_text())['frozen'] is False

def test_raster_probe_rejects_existing_directory_without_mutation(tmp_path):
    sentinel=tmp_path/'source';sentinel.write_bytes(b'keep')
    result=invoke('run_local_probe.py','--output-dir',tmp_path)
    assert result.returncode != 0
    assert list(tmp_path.iterdir())==[sentinel]
    assert sentinel.read_bytes()==b'keep'
