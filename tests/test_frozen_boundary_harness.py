"""Harness unit checks; not frozen-binary execution evidence."""
import importlib.util
from pathlib import Path
import pytest
from fonesi_edit.jobs.process import ProcessResult

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen_boundary_harness',ROOT/'scripts/check_frozen_boundaries.py')
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)


def test_packaged_notice_exact_bytes_required(tmp_path):
    expected=tmp_path/'MIT';expected.write_bytes(b'Exact MIT\n')
    target=tmp_path/'bundle/_internal/fonesi_edit/licenses/pysubs2-LICENSE.txt';target.parent.mkdir(parents=True);target.write_bytes(expected.read_bytes())
    assert len(harness.verify_license(tmp_path/'bundle',expected))==64
    target.write_bytes(b'changed')
    with pytest.raises(AssertionError):harness.verify_license(tmp_path/'bundle',expected)


def test_case_uses_owned_bounded_runner_and_expected_status(monkeypatch,tmp_path):
    calls=[]
    def run(args,**kwargs):calls.append((args,kwargs));return ProcessResult(0,b'expected output',b'')
    monkeypatch.setattr(harness,'run_owned',run)
    result=harness.run_case(tmp_path/'app',['--version'],0,contains='expected')
    assert result['actual_returncode']==0 and calls[0][1]=={'timeout':30,'max_output_bytes':256*1024}
    with pytest.raises(AssertionError):harness.run_case(tmp_path/'app',[],2)
    with pytest.raises(AssertionError):harness.run_case(tmp_path/'app',[],0,contains='missing')


def test_existing_evidence_never_overwritten(tmp_path):
    report=tmp_path/'report.json';report.write_bytes(b'prior evidence')
    with pytest.raises(AssertionError):harness.main(['--binary',str(tmp_path/'missing'),'--report',str(report)])
    assert report.read_bytes()==b'prior evidence'
