import importlib.util
from pathlib import Path
import subprocess
import pytest

spec=importlib.util.spec_from_file_location('ci_identity',Path(__file__).resolve().parents[1]/'scripts/ci_identity.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_exact_source():
    sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert module.verify(sha)['source_sha']==sha

def test_wrong_source_fails_closed():
    with pytest.raises(RuntimeError,match='Wrong CI checkout'):module.verify('0'*40)
