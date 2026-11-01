"""Project session storage must not silently adopt or mutate unrelated files."""
import shutil
import sqlite3
import pytest
from fonesi_edit.storage.projects import ProjectStore,StorageError
from fonesi_edit.storage.db_ownership import receipt_path


@pytest.mark.parametrize('sqlite_empty',[False,True])
def test_unmarked_empty_store_is_untouched(tmp_path,sqlite_empty):
    path=tmp_path/'db'
    if sqlite_empty:
        with sqlite3.connect(path) as db:db.execute('PRAGMA user_version=0')
    else:path.touch()
    original=path.read_bytes()
    with pytest.raises(StorageError,match='explicit recovery'):ProjectStore(path)
    assert path.read_bytes()==original
    assert not receipt_path(path).exists()
    assert not path.with_name('db-wal').exists()


def test_invalid_existing_receipt_refused_before_sqlite(tmp_path,monkeypatch):
    import fonesi_edit.storage.projects as module
    path=tmp_path/'db'
    with ProjectStore(path):pass
    receipt_path(path).write_bytes(b'FOREIGN')
    before=path.read_bytes()
    def forbidden(*args,**kwargs):raise AssertionError('SQLite must not open foreign receipt')
    monkeypatch.setattr(module,'open_versioned',forbidden)
    with pytest.raises(StorageError):ProjectStore(path)
    assert path.read_bytes()==before and receipt_path(path).read_bytes()==b'FOREIGN'


def test_exact_schema_rejects_extra_trigger_without_mutation(tmp_path):
    path=tmp_path/'db'
    with ProjectStore(path):pass
    with sqlite3.connect(path) as db:
        db.execute('CREATE TRIGGER foreign_trigger AFTER INSERT ON projects BEGIN DELETE FROM projects; END')
    before=path.read_bytes()
    with pytest.raises(StorageError,match='schema'):ProjectStore(path)
    assert path.read_bytes()==before


def test_original_opened_identity_and_revocation(tmp_path):
    path=tmp_path/'db';moved=tmp_path/'original'
    with ProjectStore(path) as store:
        try:path.rename(moved)
        except PermissionError:
            assert store.list_projects()==() # Windows may pin the original name.
            return
        shutil.copyfile(moved,path)
        with pytest.raises(StorageError,match='identity'):store.list_projects()
        path.unlink();moved.rename(path)
        with pytest.raises(StorageError,match='revoked'):store.list_projects()


def test_completed_commit_error_preserved_without_invalid_rollback(tmp_path):
    path=tmp_path/'db'
    with ProjectStore(path) as store:
        original=store.db
        class LoseCommitReturn:
            @property
            def in_transaction(self):return original.in_transaction
            def execute(self,sql,*args):
                result=original.execute(sql,*args)
                if sql=='COMMIT':raise OSError('lost after commit')
                return result
        store.db=LoseCommitReturn()
        try:
            with pytest.raises(OSError,match='lost after commit'):
                with store.transaction():pass
            assert not original.in_transaction
        finally:store.db=original


def test_interrupted_initialization_closes_original_descriptor(tmp_path,monkeypatch):
    import os
    import fonesi_edit.storage.projects as module
    path=tmp_path/'db';opened=[];real=os.open
    def capture(target,*args,**kwargs):
        fd=real(target,*args,**kwargs)
        if target==path:opened.append(fd)
        return fd
    monkeypatch.setattr(module.os,'open',capture)
    def fault(point):
        if point=='before_migration':raise KeyboardInterrupt('interrupted initialization')
    with pytest.raises(KeyboardInterrupt):ProjectStore(path,fault=fault)
    assert len(opened)==1
    with pytest.raises(OSError):os.fstat(opened[0])
    assert path.read_bytes()==b'' and not receipt_path(path).exists()
    with pytest.raises(StorageError,match='explicit recovery'):ProjectStore(path)


def test_unusable_zero_identity_refused(tmp_path,monkeypatch):
    import os
    import fonesi_edit.storage.projects as module
    real=os.fstat
    def unusable(fd):
        info=real(fd)
        class Unusable:
            st_ino=0
            def __getattr__(self,name):return getattr(info,name)
        return Unusable()
    monkeypatch.setattr(module.os,'fstat',unusable)
    with pytest.raises(StorageError,match='identity'):ProjectStore(tmp_path/'db')
    assert not receipt_path(tmp_path/'db').exists()


def test_identity_rechecked_before_wal_configuration(tmp_path,monkeypatch):
    import fonesi_edit.storage.projects as module
    path=tmp_path/'db'
    with ProjectStore(path):pass
    real=module.open_versioned;queries=[];moved=False;pin_denied=False
    class Connection:
        def __init__(self,db):self.db=db
        def execute(self,sql,*args):
            nonlocal moved,pin_denied
            queries.append(sql)
            result=self.db.execute(sql,*args)
            if sql=='PRAGMA foreign_keys=ON':
                try:path.rename(tmp_path/'original')
                except PermissionError:pin_denied=True
                else:shutil.copyfile(tmp_path/'original',path);moved=True
            return result
        def close(self):self.db.close()
    def wrap(*args,**kwargs):
        db,version=real(*args,**kwargs)
        return Connection(db),version
    monkeypatch.setattr(module,'open_versioned',wrap)
    try:
        store=ProjectStore(path)
    except StorageError:
        assert moved and 'PRAGMA journal_mode=WAL' not in queries
    else:
        store.close()
        assert pin_denied and not moved
