from pathlib import Path
import pytest
from fonesi_edit.fileio import read_bounded


def test_actual_read_bounded_without_stat(monkeypatch):
    class Source:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self, size):
            assert size == 11
            return b'x'*11
    monkeypatch.setattr(Path,'open',lambda *a,**k:Source())
    with pytest.raises(ValueError,match='exceeds'):read_bounded('growing',10)


def test_exact_boundary(tmp_path):
    path=tmp_path/'file';path.write_bytes(b'x'*10)
    assert read_bounded(path,10)==b'x'*10
