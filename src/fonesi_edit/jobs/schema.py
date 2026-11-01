"""Exact reviewed SQLite signatures and one transactional jobs upgrade."""
from hashlib import sha256
import os
from pathlib import Path
import sqlite3
import uuid

APPLICATION_ID=1178946122
VERSION=2
JOBS_SQL='CREATE TABLE jobs(\n                        id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,\n                        snapshot_json TEXT NOT NULL, snapshot_hash TEXT NOT NULL,\n                        state TEXT NOT NULL, version INTEGER NOT NULL,\n                        attempt INTEGER NOT NULL, lease_token TEXT,\n                        lease_deadline REAL, cancel_requested INTEGER NOT NULL)'
TABLES={
    'jobs':JOBS_SQL,
    'coordinator_epochs':'''CREATE TABLE coordinator_epochs (
        epoch INTEGER PRIMARY KEY AUTOINCREMENT, owner_uuid TEXT UNIQUE NOT NULL)''',
    'artifact_sets':'''CREATE TABLE artifact_sets (
        id TEXT PRIMARY KEY, job_id TEXT UNIQUE NOT NULL REFERENCES jobs(id),
        snapshot_hash TEXT NOT NULL, attempt INTEGER NOT NULL, lease_token TEXT NOT NULL,
        coordinator_epoch INTEGER NOT NULL REFERENCES coordinator_epochs(epoch),
        roles_json TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('prepared','claimed','committed','conflict')),
        version INTEGER NOT NULL CHECK(version>0))''',
    'publications':'''CREATE TABLE publications (
        id TEXT PRIMARY KEY, set_id TEXT NOT NULL REFERENCES artifact_sets(id),
        role TEXT NOT NULL, destination_root TEXT NOT NULL, final_name TEXT NOT NULL,
        staging_receipt_json TEXT NOT NULL, validation_json TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('prepared','claimed','committed','conflict','unknown')),
        version INTEGER NOT NULL CHECK(version>0), UNIQUE(set_id,role),
        UNIQUE(destination_root,final_name))''',
    'artifacts':'''CREATE TABLE artifacts (
        publication_id TEXT PRIMARY KEY REFERENCES publications(id),
        final_identity_json TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL CHECK(size>=0),
        verified_at REAL NOT NULL)''',
    'completion_history':'''CREATE TABLE completion_history (
        set_id TEXT PRIMARY KEY REFERENCES artifact_sets(id), job_id TEXT UNIQUE NOT NULL REFERENCES jobs(id),
        snapshot_hash TEXT NOT NULL, completed_at REAL NOT NULL)''',
}

def normalize(sql):return ''.join(sql.lower().split())
V1_HASH=sha256(normalize(JOBS_SQL).encode()).hexdigest()
V2_HASH=sha256('\0'.join(k+':'+TABLES[k].strip() for k in sorted(TABLES)).encode()).hexdigest()
KNOWN_LINEAGE_HASHES=(V1_HASH,V2_HASH)


def matches(db,version):
    expected={'jobs':JOBS_SQL} if version==1 else TABLES if version==2 else {}
    if db.execute("SELECT name FROM sqlite_master WHERE type!='table' AND name NOT LIKE 'sqlite_%'").fetchone():return False
    actual=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    return {k:v.strip() for k,v in actual.items()}=={k:v.strip() for k,v in expected.items()}


def backup(db,path):
    target=path.with_name(path.name+'.backup-'+uuid.uuid4().hex)
    # Reserve exclusively; SQLite never opens a preexisting foreign backup name.
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    copy=sqlite3.connect(target)
    try:
        db.backup(copy)
        if copy.execute('PRAGMA quick_check').fetchone()[0]!='ok':
            raise sqlite3.DatabaseError('Jobs migration backup failed validation')
    finally:copy.close()
    with target.open('r+b') as stream:os.fsync(stream.fileno())
    return target


def migrate(db,path,version,*,fault=lambda stage:None):
    """Caller checks identity/exact known schema before entry. No retry of mutations."""
    saved=backup(db,path) if version==1 else None
    fault('after_migration_backup')
    db.execute('BEGIN IMMEDIATE')
    try:
        if (db.execute('PRAGMA user_version').fetchone()[0]!=version or
            db.execute('PRAGMA application_id').fetchone()[0] not in ((0,APPLICATION_ID) if version==0 else (APPLICATION_ID,)) or
            not matches(db,version)):
            raise sqlite3.DatabaseError('Concurrent schema change; migration not replayed')
        for name,sql in TABLES.items():
            if name=='jobs' and version==1:continue
            db.execute(sql);fault('after_create_'+name)
        db.execute(f'PRAGMA application_id={APPLICATION_ID}')
        db.execute(f'PRAGMA user_version={VERSION}')
        fault('before_migration_commit')
        db.execute('COMMIT')
    except BaseException:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    return saved
