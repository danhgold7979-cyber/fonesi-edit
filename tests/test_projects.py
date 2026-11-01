import json,sqlite3,uuid
from pathlib import Path
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project,ProjectStore,StorageError,ConflictError,NewerSchemaError,save_project_file,load_project_file

@pytest.fixture
def project(multi_plan):return Project(str(uuid.uuid4()),'Dự án 中文',CompositionPlan.parse(multi_plan))

def test_sqlite_roundtrip_cas_and_reopen(tmp_path,project):
    db=tmp_path/'thư mục'/'project.sqlite'
    with ProjectStore(db) as store:
        assert store.db.execute('PRAGMA foreign_keys').fetchone()==(1,)
        assert store.db.execute('PRAGMA journal_mode').fetchone()==('wal',)
        first=store.save(project);assert first.version==1
        with pytest.raises(ConflictError):store.save(project)
        second=store.save(project,expected_version=1);assert second.version==2
        with pytest.raises(ConflictError):store.save(project,expected_version=1)
        assert len(store.list_projects())==1
    with ProjectStore(db) as store:assert store.load(project.id)==second

def test_concurrent_store_cas(tmp_path,project):
    db=tmp_path/'db';a=ProjectStore(db);b=ProjectStore(db)
    try:
        a.save(project);b.save(project,expected_version=1)
        with pytest.raises(ConflictError):a.save(project,expected_version=1)
        assert a.load(project.id).version==2
    finally:a.close();b.close()

def test_project_commit_fault_rolls_back(tmp_path,project):
    def fault(point):
        if point=='before_project_commit':raise OSError('injected disk write fault')
    with ProjectStore(tmp_path/'db',fault=fault) as store:
        with pytest.raises(OSError):store.save(project)
        assert store.list_projects()==()

def test_migration_failure_is_transactional(tmp_path):
    db=tmp_path/'db'
    def fault(point):
        if point=='after_schema_creation':raise OSError('crash boundary')
    with pytest.raises(OSError):ProjectStore(db,fault=fault)
    with sqlite3.connect(db) as c:
        assert c.execute('PRAGMA user_version').fetchone()==(0,)
        assert c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()==[]
    before=db.read_bytes()
    with pytest.raises(StorageError,match='explicit recovery'):ProjectStore(db)
    assert db.read_bytes()==before
    assert not list(tmp_path.glob('db.backup-*'))

def test_newer_database_untouched(tmp_path):
    db=tmp_path/'future.sqlite'
    with sqlite3.connect(db) as c:c.execute('PRAGMA user_version=99');c.execute('CREATE TABLE future(secret TEXT)');c.execute("INSERT INTO future VALUES('sentinel')")
    before=db.read_bytes()
    with pytest.raises(NewerSchemaError):ProjectStore(db)
    assert db.read_bytes()==before

def test_unrelated_unversioned_database_untouched(tmp_path):
    db=tmp_path/'unrelated'
    with sqlite3.connect(db) as c:c.execute('CREATE TABLE unrelated(value TEXT)')
    before=db.read_bytes()
    with pytest.raises(StorageError,match='Unrecognized'):ProjectStore(db)
    assert db.read_bytes()==before

def test_file_save_no_overwrite_then_explicit_own_update(tmp_path,project):
    path=tmp_path/'Dự án 中文.fedit';digest=save_project_file(path,project)
    assert load_project_file(path)==(project,digest)
    with pytest.raises(ConflictError):save_project_file(path,project)
    updated=Project(project.id,'New',project.plan)
    new=save_project_file(path,updated,expected_digest=digest)
    assert load_project_file(path)==(updated,new)
    backup=list(tmp_path.glob('*.backup-*'));assert len(backup)==1
    assert load_project_file(backup[0])[0]==project

def test_foreign_existing_file_never_overwritten(tmp_path,project):
    p=tmp_path/'foreign';p.write_bytes(b'foreign bytes')
    with pytest.raises(ConflictError):save_project_file(p,project)
    assert p.read_bytes()==b'foreign bytes'

def test_other_project_identity_rejected_even_matching_digest(tmp_path,project):
    p=tmp_path/'p';digest=save_project_file(p,project);different=Project(str(uuid.uuid4()),'Other',project.plan)
    with pytest.raises(ConflictError):save_project_file(p,different,expected_digest=digest)
    assert load_project_file(p)[0]==project

@pytest.mark.parametrize('point',['after_staging','after_backup'])
def test_save_failure_retains_previous_project(tmp_path,project,point):
    p=tmp_path/'p';digest=save_project_file(p,project);original=p.read_bytes()
    def fault(p):
        if p==point:raise OSError('injected')
    with pytest.raises(OSError):save_project_file(p,Project(project.id,'Changed',project.plan),expected_digest=digest,fault=fault)
    assert p.read_bytes()==original
    assert not list(tmp_path.glob('.*staging-*'))

def test_new_file_publish_race_no_replace(tmp_path,project):
    p=tmp_path/'new'
    def fault(point):
        if point=='after_staging':p.write_bytes(b'foreign racer')
    with pytest.raises(FileExistsError):save_project_file(p,project,fault=fault)
    assert p.read_bytes()==b'foreign racer'

@pytest.mark.parametrize('mutate',[
 lambda p:p.update(schema_version=2),
 lambda p:p.update(schema_version=True),
 lambda p:p.update(cookie='secret'),
 lambda p:p.update(name=''),
 lambda p:p.update(project_id='not-uuid'),
])
def test_invalid_project_envelope_rejected(project,mutate):
    raw=json.loads(project.to_json());mutate(raw)
    with pytest.raises(StorageError):Project.parse(json.dumps(raw))

def test_duplicate_project_json_rejected(project):
    with pytest.raises(StorageError,match='Duplicate'):Project.parse('{"name":"one","name":"two"}')

def test_closed_store_rejected(tmp_path,project):
    s=ProjectStore(tmp_path/'db');s.close()
    with pytest.raises(StorageError):s.load(project.id)

def test_foreign_version_one_database_unchanged(tmp_path):
    import sqlite3
    path=tmp_path/'foreign-one.db';db=sqlite3.connect(path)
    db.executescript('CREATE TABLE other(x);PRAGMA user_version=1;');db.close()
    before=path.read_bytes()
    with pytest.raises(StorageError,match='Foreign database'):ProjectStore(path)
    assert path.read_bytes()==before

def test_matching_identity_malformed_schema_unchanged(tmp_path):
    import sqlite3
    from fonesi_edit.storage.projects import APPLICATION_ID
    path=tmp_path/'corrupt.db';db=sqlite3.connect(path)
    db.executescript(f'CREATE TABLE projects(id TEXT);PRAGMA user_version=1;PRAGMA application_id={APPLICATION_ID};');db.close()
    before=path.read_bytes()
    with pytest.raises(StorageError,match='schema'):ProjectStore(path)
    assert path.read_bytes()==before

def test_foreign_adjacent_lock_file_untouched(tmp_path,empty_plan):
    path=tmp_path/'project.json';lock=tmp_path/'project.json.fonesi-lock';lock.write_bytes(b'')
    p=Project(str(uuid.uuid4()),'new',CompositionPlan.parse(empty_plan))
    with pytest.raises(StorageError,match='foreign'):save_project_file(path,p)
    assert lock.read_bytes()==b'' and not path.exists()

def test_symlink_adjacent_lock_cannot_modify_target(tmp_path,empty_plan):
    path=tmp_path/'project.json';foreign=tmp_path/'foreign';foreign.write_bytes(b'')
    lock=tmp_path/'project.json.fonesi-lock'
    try:lock.symlink_to(foreign)
    except OSError:pytest.skip('Symlink creation unavailable on this target')
    p=Project(str(uuid.uuid4()),'new',CompositionPlan.parse(empty_plan))
    with pytest.raises(StorageError,match='symlink'):save_project_file(path,p)
    assert foreign.read_bytes()==b'' and not path.exists()
