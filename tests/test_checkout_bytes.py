from pathlib import Path
import subprocess


def test_canonical_specs_unchanged_even_with_autocrlf(tmp_path):
    root=Path(__file__).resolve().parents[1]
    paths=['docs/PRODUCT_REQUIREMENTS.md','docs/EDITOR_SPEC.md','docs/SETTINGS_AND_BROWSER_SPEC.md']
    subprocess.run(['git','-c','core.autocrlf=true','checkout-index','--prefix='+tmp_path.as_posix()+'/',*paths],cwd=root,check=True)
    for path in paths:
        committed=subprocess.check_output(['git','show','HEAD:'+path],cwd=root)
        assert (tmp_path/path).read_bytes()==committed
