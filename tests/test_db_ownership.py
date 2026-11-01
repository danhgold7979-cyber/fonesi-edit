from pathlib import Path
import shutil
import sqlite3
import pytest
from fonesi_edit.storage.db_ownership import owns_database,register_database,receipt_path,DatabaseOwnershipError


def database(path):
    db=sqlite3.connect(path);db.execute('PRAGMA application_id=12345');db.close()


def test_receipt_identity_and_header_required(tmp_path):
    path=tmp_path/'db';database(path)
    assert not owns_database(path,12345,'a'*64)
    register_database(path,12345,'a'*64)
    assert owns_database(path,12345,'a'*64)
    assert not owns_database(path,12346,'a'*64)
    assert not owns_database(path,12345,'b'*64)
    replacement=tmp_path/'copy';shutil.copy2(path,replacement);replacement.replace(path)
    assert not owns_database(path,12345,'a'*64)

def test_foreign_receipt_never_overwritten(tmp_path):
    path=tmp_path/'db';database(path);receipt=receipt_path(path);receipt.write_bytes(b'foreign')
    with pytest.raises(DatabaseOwnershipError):register_database(path,12345,'a'*64)
    assert receipt.read_bytes()==b'foreign'
