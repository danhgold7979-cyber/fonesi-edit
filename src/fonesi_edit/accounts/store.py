"""Owned versioned account metadata, never browser credentials or live authority."""
from contextlib import contextmanager
from dataclasses import asdict,dataclass,fields
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import stat

from fonesi_edit.domain.composition import canonical
from fonesi_edit.storage.sqlite_open import open_versioned
from fonesi_edit.storage.db_ownership import owns_database,register_database,receipt_path
from .models import BrowserProfile,Binding,BrowserState,WebState,BridgeState,PLATFORMS,SourceAccess,AccountReference,RightsState

APPLICATION_ID=0x46454143
VERSION=1
TABLES={
 'profiles':"CREATE TABLE profiles(id TEXT PRIMARY KEY, payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB))<=8192), version INTEGER NOT NULL CHECK(typeof(version)='integer' AND version>0), observed_at INTEGER NOT NULL CHECK(observed_at>=0))",
 'bindings':"CREATE TABLE bindings(id TEXT PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id), platform TEXT NOT NULL, payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB))<=8192), version INTEGER NOT NULL CHECK(typeof(version)='integer' AND version>0), observed_at INTEGER NOT NULL CHECK(observed_at>=0), UNIQUE(profile_id,platform))",
 'access':"CREATE TABLE access(binding_id TEXT NOT NULL REFERENCES bindings(id) ON DELETE CASCADE, source_id TEXT NOT NULL, account_scope TEXT NOT NULL, payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB))<=8192), version INTEGER NOT NULL CHECK(typeof(version)='integer' AND version>0), observed_at INTEGER NOT NULL CHECK(observed_at>=0), PRIMARY KEY(binding_id,source_id,account_scope))",
 'defaults':"CREATE TABLE defaults(platform TEXT PRIMARY KEY, binding_id TEXT NOT NULL REFERENCES bindings(id) ON DELETE CASCADE)"
}
SCHEMA_HASH=sha256(canonical(TABLES).encode()).hexdigest()

class AccountStoreError(RuntimeError):pass

@dataclass(frozen=True)
class Observation:
    value: BrowserProfile|Binding|SourceAccess
    version: int
    observed_at: int
    # Persisted status is historical observation, not fresh auth/browser permission.


def _matches(db,version):
    if db.execute("SELECT 1 FROM sqlite_master WHERE type!='table' AND name NOT LIKE 'sqlite_%'").fetchone():return False
    actual=dict(db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
    return actual==(TABLES if version==VERSION else {})


def _decode(table,payload):
    try:
        if type(payload) is not str or len(payload.encode())>8192:raise ValueError
        def pairs(items):
            result={}
            for key,value in items:
                if key in result:raise ValueError('Duplicate account key')
                result[key]=value
            return result
        raw=json.loads(payload,object_pairs_hook=pairs)
        expected={field.name for field in fields(BrowserProfile if table=='profiles' else SourceAccess if table=='access' else Binding)}
        if type(raw) is not dict or set(raw)!=expected:raise ValueError('Unexpected account fields')
        if table=='profiles':raw['state']=BrowserState(raw['state']);return BrowserProfile(**raw)
        if table=='access':raw['rights']=RightsState(raw['rights']);return SourceAccess(**raw)
        raw['web']=WebState(raw['web']);raw['bridge']=BridgeState(raw['bridge']);return Binding(**raw)
    except (ValueError,TypeError,KeyError) as exc:raise AccountStoreError('Invalid bounded account observation') from exc


class AccountStore:
    def __init__(self,path):
        self.path=Path(path).absolute();self.db=None;self.fd=None
        self.path.parent.mkdir(parents=True,exist_ok=True)
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
        created=False
        try:
            try:
                self.fd=os.open(self.path,flags|os.O_CREAT|os.O_EXCL,0o600);created=True
            except FileExistsError:
                info=self.path.lstat()
                if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:raise AccountStoreError('Account database must be regular/non-reparse')
                self.fd=os.open(self.path,flags)
            info=os.fstat(self.fd);self.identity=(info.st_dev,info.st_ino);self.guard()
            if not created and not owns_database(self.path,APPLICATION_ID,SCHEMA_HASH):
                raise AccountStoreError('Preexisting unmarked/foreign account store is never silently adopted')
            connect=lambda path,**kwargs:sqlite3.connect(Path(path).as_uri()+'?mode=rw',uri=True,**kwargs)
            self.db,version=open_versioned(self.path,connect=connect,owned=lambda:owns_database(self.path,APPLICATION_ID,SCHEMA_HASH))
            self.guard()
            appid=self.db.execute('PRAGMA application_id').fetchone()[0]
            if version not in (0,VERSION) or appid not in ((0,APPLICATION_ID) if version==0 else (APPLICATION_ID,)) or not _matches(self.db,version):
                raise AccountStoreError('Foreign/newer/corrupt account store; no migration performed')
            marker=receipt_path(self.path)
            if marker.exists() or marker.is_symlink():
                if not owns_database(self.path,APPLICATION_ID,SCHEMA_HASH):raise AccountStoreError('Account ownership receipt invalid')
            elif version:raise AccountStoreError('Existing account store has no ownership receipt')
            if version==0:
                self.db.execute('BEGIN IMMEDIATE')
                try:
                    self.guard()
                    if (self.db.execute('PRAGMA user_version').fetchone()[0]!=0 or
                        self.db.execute('PRAGMA application_id').fetchone()[0] not in (0,APPLICATION_ID) or not _matches(self.db,0)):
                        raise AccountStoreError('Concurrent account initialization; not replayed')
                    for sql in TABLES.values():self.db.execute(sql)
                    self.db.execute(f'PRAGMA application_id={APPLICATION_ID}');self.db.execute(f'PRAGMA user_version={VERSION}')
                    self.db.execute('COMMIT')
                except BaseException:
                    if self.db.in_transaction:self.db.execute('ROLLBACK')
                    raise
            self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL');self.db.execute('PRAGMA busy_timeout=5000')
            register_database(self.path,APPLICATION_ID,SCHEMA_HASH)
        except BaseException:self.close();raise

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):
        try:
            if self.db is not None:self.db.close()
        finally:
            self.db=None
            if self.fd is not None:os.close(self.fd);self.fd=None
    def guard(self):
        if self.fd is None:raise AccountStoreError('Account store closed')
        named=self.path.lstat();opened=os.fstat(self.fd)
        if (not stat.S_ISREG(named.st_mode) or getattr(named,'st_file_attributes',0)&0x400 or not opened.st_ino or
            self.identity!=(named.st_dev,named.st_ino) or self.identity!=(opened.st_dev,opened.st_ino)):
            raise AccountStoreError('Account database identity changed')
    @contextmanager
    def transaction(self):
        self.guard();self.db.execute('BEGIN IMMEDIATE')
        try:
            self.guard();yield;self.guard();self.db.execute('COMMIT')
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise

    def _get(self,table,key):
        self.guard()
        extra=",profile_id,platform" if table=='bindings' else ''
        row=self.db.execute(f'SELECT substr(payload,1,8193),version,observed_at{extra} FROM {table} WHERE id=?',(key,)).fetchone()
        if row is None:raise KeyError(key)
        value=_decode(table,row[0])
        if (value.id!=key or type(row[1]) is not int or row[1]<1 or type(row[2]) is not int or row[2]<0 or
            (table=='bindings' and (value.profile_id,value.platform)!=(row[3],row[4]))):
            raise AccountStoreError('Account row identity/version mismatch')
        return Observation(value,row[1],row[2])
    def profile(self,key):return self._get('profiles',key)
    def binding(self,key):return self._get('bindings',key)

    def save(self,value,*,observed_at,expected_version=None):
        table='profiles' if type(value) is BrowserProfile else 'bindings' if type(value) is Binding else None
        if table is None:raise AccountStoreError('Typed allowlisted profile/binding required')
        if type(observed_at) is not int or not 0<=observed_at<=2**63-1:raise AccountStoreError('Observation timestamp required')
        if expected_version is not None and (type(expected_version) is not int or not 1<=expected_version<2**63-1):raise AccountStoreError('Expected version invalid')
        payload=canonical(asdict(value));value=_decode(table,payload)
        if isinstance(value,Binding) and any(t is not None and t>observed_at for t in (value.web_checked_at,value.bridge_checked_at)):
            raise AccountStoreError('Check timestamps exceed recorded observation')
        with self.transaction():
            try:current=self._get(table,value.id)
            except KeyError:current=None
            if (current is None and expected_version is not None) or (current is not None and current.version!=expected_version):
                raise AccountStoreError('Stale account observation; refresh before save')
            if current is not None:
                if observed_at<current.observed_at:raise AccountStoreError('Older observation cannot replace newer data')
                if table=='profiles' and (current.value.installation_id,current.value.ownership)!=(value.installation_id,value.ownership):
                    raise AccountStoreError('Profile installation/ownership identity is immutable; use a new profile ID')
                if table=='bindings':
                    old=current.value;changed=(old.profile_id,old.platform,old.identity)!=(value.profile_id,value.platform,value.identity)
                    if value.generation<old.generation+int(changed):raise AccountStoreError('Identity change must advance binding generation')
            version=1 if current is None else current.version+1
            if table=='profiles':
                if current is None:self.db.execute('INSERT INTO profiles VALUES(?,?,?,?)',(value.id,payload,version,observed_at))
                else:self.db.execute('UPDATE profiles SET payload=?,version=?,observed_at=? WHERE id=?',(payload,version,observed_at,value.id))
            else:
                if current is None:self.db.execute('INSERT INTO bindings VALUES(?,?,?,?,?,?)',(value.id,value.profile_id,value.platform,payload,version,observed_at))
                else:
                    if value.platform!=current.value.platform:self.db.execute('DELETE FROM defaults WHERE binding_id=?',(value.id,))
                    self.db.execute('UPDATE bindings SET profile_id=?,platform=?,payload=?,version=?,observed_at=? WHERE id=?',(value.profile_id,value.platform,payload,version,observed_at,value.id))
        return Observation(value,version,observed_at)

    def set_default(self,platform,binding_id,*,expected_version,expected_default=None):
        if type(platform) is not str or platform not in PLATFORMS:raise AccountStoreError('Unknown platform')
        if type(expected_version) is not int or expected_version<1:raise AccountStoreError('Expected binding version required')
        with self.transaction():
            old=self.db.execute('SELECT binding_id FROM defaults WHERE platform=?',(platform,)).fetchone()
            if (None if old is None else old[0])!=expected_default:raise AccountStoreError('Default selection changed; refresh first')
            record=self.binding(binding_id)
            if record.version!=expected_version or record.value.platform!=platform:raise AccountStoreError('Default binding changed or platform mismatch')
            self.db.execute('INSERT INTO defaults VALUES(?,?) ON CONFLICT(platform) DO UPDATE SET binding_id=excluded.binding_id',(platform,binding_id))
    def default(self,platform):
        if type(platform) is not str or platform not in PLATFORMS:raise AccountStoreError('Unknown platform')
        self.guard();row=self.db.execute('SELECT binding_id FROM defaults WHERE platform=?',(platform,)).fetchone()
        if row is None:return None
        record=self.binding(row[0])
        if record.value.platform!=platform:raise AccountStoreError('Default platform identity mismatch')
        return record
    def unlink_binding(self,key,*,expected_version):
        if type(expected_version) is not int or expected_version<1:raise AccountStoreError('Expected binding version required')
        with self.transaction():
            current=self.binding(key)
            if current.version!=expected_version:raise AccountStoreError('Binding changed before unlink')
            self.db.execute('DELETE FROM bindings WHERE id=?',(key,))
        # No browser profile directory, cookies or user files are ever touched.


    def _scope(self,binding):
        if binding.identity is None:raise AccountStoreError('Account identity must be recorded before scoped source access')
        return AccountReference(binding.id,binding.profile_id,binding.platform,binding.identity,binding.generation).cache_scope()

    def source_access(self,binding_id,source_id):
        binding=self.binding(binding_id);scope=self._scope(binding.value)
        row=self.db.execute('SELECT substr(payload,1,8193),version,observed_at FROM access WHERE binding_id=? AND source_id=? AND account_scope=?',
                            (binding_id,source_id,scope)).fetchone()
        if row is None:raise KeyError(source_id)
        value=_decode('access',row[0])
        if (value.source_id!=source_id or value.account_scope!=scope or type(row[1]) is not int or row[1]<1 or
            type(row[2]) is not int or row[2]<0):raise AccountStoreError('Source-access identity/version mismatch')
        return Observation(value,row[1],row[2])

    def save_access(self,binding_id,value,*,expected_binding_version,observed_at,expected_version=None):
        if type(value) is not SourceAccess:raise AccountStoreError('Typed source access required')
        if type(expected_binding_version) is not int or expected_binding_version<1:raise AccountStoreError('Expected binding version required')
        if type(observed_at) is not int or not 0<=observed_at<=2**63-1:raise AccountStoreError('Observation timestamp required')
        if expected_version is not None and (type(expected_version) is not int or not 1<=expected_version<2**63-1):raise AccountStoreError('Expected access version invalid')
        payload=canonical(asdict(value));value=_decode('access',payload)
        if value.checked_at is not None and value.checked_at>observed_at:raise AccountStoreError('Rights check exceeds observation time')
        with self.transaction():
            binding=self.binding(binding_id)
            if binding.version!=expected_binding_version or value.account_scope!=self._scope(binding.value):
                raise AccountStoreError('Source access belongs to a different/stale account scope')
            try:current=self.source_access(binding_id,value.source_id)
            except KeyError:current=None
            if (current is None and expected_version is not None) or (current is not None and current.version!=expected_version):
                raise AccountStoreError('Stale source-access observation')
            if current is not None and observed_at<current.observed_at:raise AccountStoreError('Older source-access observation')
            version=1 if current is None else current.version+1
            if current is None:self.db.execute('INSERT INTO access VALUES(?,?,?,?,?,?)',(binding_id,value.source_id,value.account_scope,payload,version,observed_at))
            else:self.db.execute('UPDATE access SET payload=?,version=?,observed_at=? WHERE binding_id=? AND source_id=? AND account_scope=?',
                                 (payload,version,observed_at,binding_id,value.source_id,value.account_scope))
        return Observation(value,version,observed_at)
