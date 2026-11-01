import json,sqlite3
from pathlib import Path
import pytest
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.schema import JOBS_SQL,APPLICATION_ID,VERSION,TABLES,V1_HASH,matches
from fonesi_edit.storage.db_ownership import register_database,receipt_path


def legacy(path):
    db=sqlite3.connect(path,isolation_level=None)
    db.execute(JOBS_SQL);db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=1')
    db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',('job','request','{"seed":42}','hash','pending',1,0,None,None,0))
    db.close();register_database(path,APPLICATION_ID,V1_HASH)


def test_populated_v1_upgrade_preserves_snapshot_and_receipt(tmp_path):
    p=tmp_path/'jobs.db';legacy(p);receipt=receipt_path(p).read_bytes()
    with_repo=JobRepository(p)
    try:
        assert with_repo.get('job').snapshot_json=='{"seed":42}'
        assert with_repo.db.execute('PRAGMA user_version').fetchone()[0]==2
        assert matches(with_repo.db,2)
        assert with_repo.db.execute('PRAGMA foreign_keys').fetchone()[0]==1
    finally:with_repo.close()
    assert receipt_path(p).read_bytes()==receipt # known lineage retained, no receipt rewrite gap
    backup=next(tmp_path.glob('jobs.db.backup-*'))
    with sqlite3.connect(f'file:{backup}?mode=ro',uri=True) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==1
        assert db.execute('SELECT snapshot_json FROM jobs').fetchone()[0]=='{"seed":42}'
        assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    r=JobRepository(p);assert r.get('job').request_key=='request';r.close()
    assert len(list(tmp_path.glob('jobs.db.backup-*')))==1


@pytest.mark.parametrize('boundary',['after_migration_backup','after_create_coordinator_epochs','after_create_artifact_sets','after_create_publications','after_create_artifacts','after_create_completion_history','before_migration_commit'])
def test_v1_migration_fault_rolls_back_all_new_records(tmp_path,boundary):
    p=tmp_path/'jobs.db';legacy(p);receipt=receipt_path(p).read_bytes()
    def fault(stage):
        if stage==boundary:raise OSError('injected migration failure')
    with pytest.raises(OSError):JobRepository(p,migration_fault=fault)
    with sqlite3.connect(p) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==1
        assert matches(db,1)
        assert db.execute('SELECT snapshot_json FROM jobs').fetchone()[0]=='{"seed":42}'
    assert receipt_path(p).read_bytes()==receipt
    r=JobRepository(p);assert matches(r.db,2);r.close()


def test_future_jobs_schema_unchanged(tmp_path):
    p=tmp_path/'future.db';db=sqlite3.connect(p);db.executescript(f'PRAGMA application_id={APPLICATION_ID};PRAGMA user_version=99;CREATE TABLE future(x);');db.close();before=p.read_bytes()
    with pytest.raises(JobConflict):JobRepository(p)
    assert p.read_bytes()==before and not list(tmp_path.glob('*.backup-*'))


def test_foreign_empty_application_identity_unchanged(tmp_path):
    p=tmp_path/'foreign.db';db=sqlite3.connect(p);db.execute('PRAGMA application_id=123456');db.close();before=p.read_bytes()
    with pytest.raises(JobConflict):JobRepository(p)
    assert p.read_bytes()==before


def test_extra_trigger_not_a_known_schema(tmp_path):
    p=tmp_path/'jobs.db';legacy(p)
    db=sqlite3.connect(p);db.execute('CREATE TRIGGER surprise AFTER INSERT ON jobs BEGIN DELETE FROM jobs; END');db.close();before=p.read_bytes()
    with pytest.raises(JobConflict,match='schema'):JobRepository(p)
    assert p.read_bytes()==before and not list(tmp_path.glob('*.backup-*'))


def test_committed_schema_with_legacy_receipt_reopens(tmp_path):
    p=tmp_path/'jobs.db';legacy(p)
    # Model crash after SQL migration commit but before any later startup steps.
    from fonesi_edit.jobs.schema import migrate
    db=sqlite3.connect(p,isolation_level=None);migrate(db,p,1);db.close()
    assert json.loads(receipt_path(p).read_text())['schema_hash']==V1_HASH
    r=JobRepository(p);assert r.get('job').snapshot_hash=='hash';r.close()


def test_foreign_receipt_blocks_before_migration(tmp_path):
    p=tmp_path/'jobs.db';legacy(p);receipt_path(p).write_bytes(b'FOREIGN');before=p.read_bytes()
    with pytest.raises(JobConflict,match='receipt'):JobRepository(p)
    assert p.read_bytes()==before and receipt_path(p).read_bytes()==b'FOREIGN'
    assert not list(tmp_path.glob('*.backup-*'))


def test_quoted_literal_case_change_is_not_equivalent_schema(tmp_path):
    p=tmp_path/'jobs.db';db=sqlite3.connect(p)
    for name,sql in TABLES.items():
        db.execute(sql.replace("'prepared'","'PREPARED'") if name=='artifact_sets' else sql)
    db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=2');db.close()
    before=p.read_bytes()
    with pytest.raises(JobConflict,match='schema'):JobRepository(p)
    assert p.read_bytes()==before


def test_missing_receipt_adoption_is_explicit(tmp_path):
    p=tmp_path/'jobs.db';legacy(p);receipt_path(p).unlink();before=p.read_bytes()
    with pytest.raises(JobConflict,match='adoption'):JobRepository(p)
    assert p.read_bytes()==before and not receipt_path(p).exists()
    r=JobRepository(p,adopt_unmarked=True);assert r.get('job').request_key=='request';r.close()
    assert receipt_path(p).exists()


def test_concurrent_application_identity_change_stops_migration(tmp_path):
    from fonesi_edit.jobs.schema import migrate
    p=tmp_path/'jobs.db';legacy(p);db=sqlite3.connect(p,isolation_level=None)
    def changed(stage):
        if stage=='after_migration_backup':db.execute('PRAGMA application_id=12345')
    with pytest.raises(sqlite3.DatabaseError,match='Concurrent'):
        migrate(db,p,1,fault=changed)
    assert db.execute('PRAGMA user_version').fetchone()[0]==1 and matches(db,1)
    db.close()
