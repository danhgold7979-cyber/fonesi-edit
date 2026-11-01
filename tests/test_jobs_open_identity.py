import os
from pathlib import Path
import shutil
import sqlite3
import pytest
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.storage.db_ownership import receipt_path
from fonesi_edit.domain.composition import CompositionPlan


@pytest.mark.parametrize('empty_sqlite',[False,True])
def test_default_unmarked_empty_refuses_before_sqlite(tmp_path,monkeypatch,empty_sqlite):
    import fonesi_edit.jobs.repository as module
    path=tmp_path/'db'
    if empty_sqlite:
        with sqlite3.connect(path) as db:db.execute('PRAGMA user_version=0')
    else:path.touch()
    before=path.read_bytes()
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('Foreign store opened'))
    with pytest.raises(JobConflict,match='before SQLite'):JobRepository(path)
    assert path.read_bytes()==before and not receipt_path(path).exists()


def test_leaf_symlink_not_resolved_into_owned_database(tmp_path):
    target=tmp_path/'target';repo=JobRepository(target);repo.close()
    alias=tmp_path/'alias'
    try:alias.symlink_to(target)
    except OSError:pytest.skip('Symlink unavailable')
    before=target.read_bytes()
    with pytest.raises(JobConflict,match='non-reparse'):JobRepository(alias)
    assert target.read_bytes()==before


def test_identity_restore_does_not_revive_repository(tmp_path):
    path=tmp_path/'db';moved=tmp_path/'original';repo=JobRepository(path)
    try:
        try:path.rename(moved)
        except PermissionError:
            repo.guard_database();return # Actual Windows pin-denied branch, not injected mutation.
        shutil.copyfile(moved,path)
        with pytest.raises(JobConflict,match='identity'):repo.guard_database()
        path.unlink();moved.rename(path)
        with pytest.raises(JobConflict,match='revoked'):repo.guard_database()
    finally:repo.close()


def test_submit_postcommit_error_not_masked_or_replayed(tmp_path,empty_plan):
    repo=JobRepository(tmp_path/'db');original=repo.db
    class LostReturn:
        @property
        def in_transaction(self):return original.in_transaction
        def execute(self,sql,*args):
            result=original.execute(sql,*args)
            if sql=='COMMIT':raise OSError('lost after submission commit')
            return result
    repo.db=LostReturn()
    try:
        with pytest.raises(OSError,match='lost after submission commit'):
            repo.submit('one',CompositionPlan.parse(empty_plan),0)
        assert original.execute('SELECT count(*) FROM jobs').fetchone()[0]==1
        assert not original.in_transaction
    finally:repo.db=original;repo.close()


def test_open_policy_rejects_truthy_nonboolean_adoption(tmp_path):
    with pytest.raises(JobConflict):JobRepository(tmp_path/'db',adopt_unmarked='yes')
    assert not (tmp_path/'db').exists()


def test_explicit_adoption_cannot_override_foreign_receipt(tmp_path,monkeypatch):
    import fonesi_edit.jobs.repository as module
    path=tmp_path/'db';repo=JobRepository(path);repo.close()
    receipt_path(path).write_bytes(b'foreign');before=path.read_bytes()
    monkeypatch.setattr(module,'open_versioned',lambda *a,**k:pytest.fail('Foreign marked database opened'))
    with pytest.raises(JobConflict):JobRepository(path,adopt_unmarked=True)
    assert path.read_bytes()==before and receipt_path(path).read_bytes()==b'foreign'
