from hashlib import sha256
from pathlib import Path
import sqlite3
import uuid
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project,ProjectStore,PROJECTS_V1_SQL,PROJECT_V1_HASH,APPLICATION_ID
from fonesi_edit.storage.db_ownership import register_database,receipt_path,owns_database
from fonesi_edit.storage.restore import restore_project_backup,RestoreError,RestoreCanceled


@pytest.fixture
def migration_backup(tmp_path,empty_plan):
    path=tmp_path/'original.sqlite3';projects=[Project(str(uuid.uuid4()),'Dự án '+str(i),CompositionPlan.parse(empty_plan)) for i in range(2)]
    db=sqlite3.connect(path)
    db.execute(PROJECTS_V1_SQL);db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=1')
    for i,p in enumerate(projects):db.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(p.id,p.name,p.to_json(),i+3,1000.))
    db.commit();db.close();register_database(path,APPLICATION_ID,PROJECT_V1_HASH)
    with ProjectStore(path) as store:
        assert all(store.load(p.id).origin_base is None for p in projects)
        store.save(Project(projects[0].id,'Newer active state',projects[0].plan),expected_version=3)
    backup=next(tmp_path.glob('original.sqlite3.backup-*'))
    return path,backup,projects


def test_real_migration_backup_restore_reopens_all_original_rows(migration_backup,tmp_path):
    original,backup,projects=migration_backup;before=(original.read_bytes(),backup.read_bytes())
    folder=tmp_path/'Khôi phục 中文';folder.mkdir();target=folder/'projects.sqlite3'
    result=restore_project_backup(backup,target)
    assert result.project_count==2 and result.schema_version==1 and result.source_sha256==sha256(before[1]).hexdigest()
    assert target.read_bytes()==before[1]
    with ProjectStore(target) as restored:
        for i,p in enumerate(projects):
            row=restored.load(p.id);assert row.project.to_json()==p.to_json() and row.version==i+3 and row.origin_base is None
    assert (original.read_bytes(),backup.read_bytes())==before
    with ProjectStore(original) as live:assert live.load(projects[0].id).project.name=='Newer active state'


@pytest.mark.parametrize('kind',['target','receipt','-wal','-shm','-journal'])
def test_existing_destination_or_companion_never_modified(migration_backup,tmp_path,kind):
    _,backup,_=migration_backup;target=tmp_path/'restored.db'
    foreign=target if kind=='target' else receipt_path(target) if kind=='receipt' else target.with_name(target.name+kind)
    foreign.write_bytes(b'FOREIGN');before={p.name:p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    with pytest.raises(RestoreError) as caught:restore_project_backup(backup,target)
    assert not caught.value.destination_created
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}==before


@pytest.mark.parametrize('kind',['future','wal','corrupt_document'])
def test_unsupported_or_corrupt_backup_never_becomes_owned(migration_backup,tmp_path,kind):
    _,backup,_=migration_backup;db=sqlite3.connect(backup)
    if kind=='future':db.execute('PRAGMA user_version=999')
    elif kind=='wal':db.execute('PRAGMA journal_mode=WAL')
    else:db.execute("UPDATE projects SET document='{}'")
    db.commit();db.close();before=backup.read_bytes();target=tmp_path/'restored.db'
    with pytest.raises(RestoreError):restore_project_backup(backup,target)
    assert backup.read_bytes()==before and not receipt_path(target).exists()
    if kind in ('future','wal'):assert not target.exists()


def test_cancel_after_exclusive_creation_retains_unmarked_only(migration_backup,tmp_path):
    _,backup,_=migration_backup;before=backup.read_bytes();target=tmp_path/'restored.db';state={'cancel':False}
    def fault(stage):
        if stage=='after_create':state['cancel']=True
    with pytest.raises(RestoreCanceled) as caught:restore_project_backup(backup,target,cancel=lambda:state['cancel'],fault=fault)
    assert caught.value.destination_created and not caught.value.ownership_unknown
    assert target.exists() and not receipt_path(target).exists() and backup.read_bytes()==before


@pytest.mark.parametrize('boundary',['after_copy','after_validate','before_register','after_register'])
def test_fault_retains_destination_without_overwrite_or_retry(migration_backup,tmp_path,boundary):
    _,backup,_=migration_backup;target=tmp_path/'restored.db';before=backup.read_bytes();seen=[]
    def fault(stage):
        seen.append(stage)
        if stage==boundary:raise OSError('injected failure')
    with pytest.raises(RestoreError) as caught:restore_project_backup(backup,target,fault=fault)
    assert caught.value.destination_created and caught.value.ownership_unknown==(boundary=='after_register')
    assert backup.read_bytes()==before and seen.count(boundary)==1
    assert receipt_path(target).exists()==(boundary=='after_register')


def test_source_growth_stops_at_opened_bound(migration_backup,tmp_path):
    _,backup,_=migration_backup;target=tmp_path/'restored.db';once=[]
    def progress(copied,total):
        if not once:
            with backup.open('ab') as f:f.write(b'GROWTH')
            once.append(True)
    with pytest.raises(RestoreError):restore_project_backup(backup,target,progress=progress)
    assert target.exists() and not receipt_path(target).exists()


def test_document_bound_is_checked_before_parser(migration_backup,tmp_path,monkeypatch):
    import fonesi_edit.storage.restore as module
    _,backup,_=migration_backup;target=tmp_path/'restored.db'
    monkeypatch.setattr(module,'MAX_PROJECT_BYTES',128)
    monkeypatch.setattr(module.Project,'parse',lambda *a:pytest.fail('Oversized document must not reach parser'))
    with pytest.raises(RestoreError):restore_project_backup(backup,target)
    assert not receipt_path(target).exists()


def test_effect_boundary_rechecks_target_hash(migration_backup,tmp_path):
    _,backup,_=migration_backup;target=tmp_path/'restored.db'
    def fault(stage):
        if stage=='before_register':
            with target.open('r+b') as f:f.seek(200);f.write(b'CHANGED')
    with pytest.raises(RestoreError):restore_project_backup(backup,target,fault=fault)
    assert not receipt_path(target).exists()


def test_cli_real_backup_headless_fresh_process(migration_backup,tmp_path):
    import subprocess,sys,os
    original,backup,projects=migration_backup;before=(original.read_bytes(),backup.read_bytes())
    target=tmp_path/'cli-restored.db'
    script='''import builtins,sys
real=builtins.__import__
def guarded(name,*args,**kwargs):
    if name.startswith('PySide6'):raise AssertionError('Qt imported by restore')
    return real(name,*args,**kwargs)
builtins.__import__=guarded
from fonesi_edit.__main__ import main
raise SystemExit(main(sys.argv[1:]))
'''
    result=subprocess.run([sys.executable,'-c',script,'--restore-project-store',str(backup),
                           '--restore-destination',str(target)],capture_output=True,text=True,timeout=20,
                          env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')})
    assert result.returncode==0,result.stderr
    assert 'Restored 2 project(s)' in result.stdout and projects[0].name not in result.stdout
    assert (original.read_bytes(),backup.read_bytes())==before
    with ProjectStore(target) as restored:assert restored.load(projects[1].id).version==4


@pytest.mark.parametrize('options',[
    ['--restore-project-store','backup'],['--restore-destination','target'],['--restore-timeout','2'],
    ['--restore-project-store','backup','--restore-destination','target','--data-dir','unused'],
    ['--restore-project-store','backup','--restore-destination','target','--subtitle-format','srt'],
])
def test_cli_restore_options_refused_before_io(options):
    from fonesi_edit.__main__ import main
    with pytest.raises(SystemExit) as caught:main(options)
    assert caught.value.code==2


def test_cli_restore_foreign_target_and_bad_timeout_are_sanitized(migration_backup,tmp_path,capsys):
    from fonesi_edit.__main__ import main
    _,backup,_=migration_backup;target=tmp_path/'PRIVATE-target.db';target.write_bytes(b'FOREIGN')
    args=['--restore-project-store',str(backup),'--restore-destination',str(target)]
    assert main(args)==2 and target.read_bytes()==b'FOREIGN'
    for timeout in ('nan','inf','0','3601'):
        assert main(args+['--restore-timeout',timeout])==2
    output=capsys.readouterr();assert 'PRIVATE' not in output.err and not output.out


def test_current_schema_backup_preserves_explicit_origin(migration_backup,tmp_path):
    original,_,projects=migration_backup;origin=tmp_path/'original-media';origin.mkdir()
    with ProjectStore(original) as store:
        current=store.load(projects[0].id)
        store.save(current.project,expected_version=current.version,origin_base=str(origin))
        backup=store._backup()
    # Prepare an explicitly offline rollback-format v2 fixture. A backup copied
    # from a WAL-mode current store is intentionally unsupported by this importer.
    with sqlite3.connect(backup) as db:assert db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
    target=tmp_path/'current-restored.db'
    result=restore_project_backup(backup,target)
    assert result.schema_version==2
    with ProjectStore(target) as restored:
        assert restored.load(projects[0].id).origin_base==str(origin)


@pytest.mark.parametrize('field',['id','name','origin_base'])
def test_embedded_nul_metadata_cannot_validate_truncated_prefix(migration_backup,tmp_path,field):
    _,backup,_=migration_backup
    with sqlite3.connect(backup) as db:
        if field=='origin_base':
            db.execute('ALTER TABLE projects ADD COLUMN origin_base TEXT');db.execute('PRAGMA user_version=2')
            db.execute('UPDATE projects SET origin_base=?',(str(tmp_path)+'\0HIDDEN',))
        else:db.execute(f'UPDATE projects SET {field}={field} || char(0) || ?',('HIDDEN',))
    target=tmp_path/'bad-text.db'
    with pytest.raises(RestoreError):restore_project_backup(backup,target)
    assert not receipt_path(target).exists()


def test_complete_supported_uuid_and_name_spelling_roundtrips(migration_backup,tmp_path):
    _,backup,projects=migration_backup
    p=Project('urn:uuid:'+projects[0].id,'Valid\0full name 中文',projects[0].plan)
    with sqlite3.connect(backup) as db:
        db.execute('DELETE FROM projects');db.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(p.id,p.name,p.to_json(),7,1000.))
    target=tmp_path/'supported-text.db';restore_project_backup(backup,target)
    with ProjectStore(target) as store:assert store.load(p.id).project.to_json()==p.to_json()


@pytest.mark.parametrize('field',['id','name','origin_base'])
def test_blob_metadata_not_silently_adopted_as_text(migration_backup,tmp_path,field):
    _,backup,_=migration_backup
    with sqlite3.connect(backup) as db:
        if field=='origin_base':
            db.execute('ALTER TABLE projects ADD COLUMN origin_base TEXT');db.execute('PRAGMA user_version=2')
            db.execute('UPDATE projects SET origin_base=?',(str(tmp_path).encode(),))
        else:db.execute(f'UPDATE projects SET {field}=CAST({field} AS BLOB)')
    target=tmp_path/'blob-metadata.db'
    with pytest.raises(RestoreError):restore_project_backup(backup,target)
    assert not receipt_path(target).exists()
