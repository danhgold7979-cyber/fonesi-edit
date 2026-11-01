"""Owned explicit paths, not executable trust, activation or job authority."""
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import sqlite3

from fonesi_edit.jobs.ownership import identity, regular
from fonesi_edit.storage.db_ownership import (owns_database, register_database,
                                             receipt_path, ownership_token)
from .discovery import TOOL_NAMES

APPLICATION_ID = 0x46455450
VERSION = 1
LIMIT = 32768
COLUMNS = (*TOOL_NAMES, 'extra')
# SQL identifiers are fixed and quoted (two tool names contain hyphens).
SQL = 'CREATE TABLE preferences (singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL CHECK(version>0), ' + ', '.join(
    f'"{key}" TEXT NOT NULL CHECK(length(CAST("{key}" AS BLOB))<={LIMIT})' for key in COLUMNS
) + ', include_system INTEGER NOT NULL CHECK(include_system IN (0,1)))'
SCHEMA_HASH = sha256(SQL.encode()).hexdigest()

class PreferencesError(RuntimeError): pass
class PreferencesConflict(PreferencesError): pass
class PreferencesUnknown(PreferencesError): pass

@dataclass(frozen=True)
class ToolPreferences:
    paths: tuple[str, ...] = ('', '', '', '', '')
    extra: str = ''
    include_system: bool = True

    def __post_init__(self):
        if type(self.paths) is not tuple or len(self.paths) != len(TOOL_NAMES) or type(self.include_system) is not bool:
            raise ValueError('Exact tool preference fields required')
        for value in (*self.paths, self.extra):
            if (type(value) is not str or len(value) > LIMIT or '\0' in value or
                len(value.encode('utf-8')) > LIMIT or (value and not Path(value).is_absolute())):
                raise ValueError('Bounded absolute path or empty preference required')

@dataclass(frozen=True)
class PreferenceSnapshot:
    value: ToolPreferences
    version: int = 0
    token: str | None = None


def _companions(path):
    return (receipt_path(path), *(path.with_name(path.name+s) for s in ('-wal','-shm','-journal')))

def _present(path):
    try: path.lstat(); return True
    except FileNotFoundError: return False

def _matches(db):
    return list(db.execute("SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name")) == [('table','preferences',SQL)]

class _Connection:
    """Cooperating private namespace; no concurrent external journal-mode changes."""
    def __init__(self, path, *, create=False):
        self.path=Path(path); self.fd=None; self.db=None; self.revoked=False; self.created=False
        if not self.path.is_absolute(): raise PreferencesError('Explicit preference store path required')
        try:
            if create:
                if any(_present(p) for p in _companions(self.path)):
                    raise PreferencesConflict('Existing preference companions; no adoption')
                self.fd=os.open(self.path, os.O_RDONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0), 0o600)
                self.created=True
            else:
                if not regular(self.path.lstat()): raise PreferencesError('Regular non-reparse store required')
                self.fd=os.open(self.path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
            self.original=identity(os.fstat(self.fd)); self.guard()
            if not create:
                self.header_guard()
                if not owns_database(self.path,APPLICATION_ID,SCHEMA_HASH):
                    raise PreferencesError('Unmarked or foreign preferences refused')
            # Read-only mode cannot create the main file; rollback header preflight
            # prevents WAL sidecars during reads. Writer never changes journal mode.
            self.db=sqlite3.connect(self.path.as_uri()+('?mode=rw' if create else '?mode=ro'),uri=True,
                                   timeout=.25,isolation_level=None)
            self.guard()
            if create:
                if list(self.db.execute('SELECT name FROM sqlite_master')) or self.db.execute('PRAGMA user_version').fetchone()[0] or self.db.execute('PRAGMA application_id').fetchone()[0]:
                    raise PreferencesError('Fresh store changed before initialization')
                self.db.execute('PRAGMA synchronous=FULL')
            else: self.schema_guard()
        except BaseException: self.close(); raise

    def guard(self):
        if self.fd is None or self.revoked: raise PreferencesError('Preference continuity revoked')
        try:
            named=self.path.lstat(); opened=os.fstat(self.fd)
            if not regular(named) or not regular(opened) or identity(named)!=self.original or identity(opened)!=self.original:
                raise PreferencesError('Preference store identity changed')
        except BaseException: self.revoked=True; raise

    def header_guard(self):
        self.guard(); os.lseek(self.fd,0,os.SEEK_SET); header=os.read(self.fd,100)
        if (len(header)!=100 or header[:16]!=b'SQLite format 3\0' or header[18:20]!=b'\1\1' or
            any(_present(p) for p in _companions(self.path)[1:])):
            raise PreferencesError('Unsupported journal/header or recovery needed; left unchanged')
        self.guard()

    def schema_guard(self):
        self.guard()
        if (self.db.execute('PRAGMA user_version').fetchone()[0]!=VERSION or
            self.db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or not _matches(self.db)):
            raise PreferencesError('Unsupported preference schema; left unchanged')
        self.guard()

    def snapshot(self):
        self.schema_guard()
        cols=','.join(f"typeof(\"{c}\"),coalesce(substr(CAST(\"{c}\" AS BLOB),1,{LIMIT+1}),X'')" for c in COLUMNS)
        rows=self.db.execute(f'SELECT singleton,version,{cols},include_system,typeof(include_system) FROM preferences LIMIT 2').fetchall()
        if len(rows)!=1: raise PreferencesError('Exactly one preference snapshot required')
        row=rows[0]
        if row[0]!=1 or type(row[1]) is not int or not 1<=row[1]<2**63 or row[-1]!='integer' or row[-2] not in (0,1):
            raise PreferencesError('Invalid preference version/flags')
        values=[]
        for i in range(2,14,2):
            if row[i]!='text' or type(row[i+1]) is not bytes or len(row[i+1])>LIMIT:
                raise PreferencesError('Invalid bounded preference path')
            values.append(row[i+1].decode('utf-8',errors='strict'))
        value=ToolPreferences(tuple(values[:5]),values[5],bool(row[-2]))
        token=ownership_token(self.path,APPLICATION_ID,SCHEMA_HASH); self.guard()
        return PreferenceSnapshot(value,row[1],token)

    def close(self):
        self.revoked=True
        try:
            if self.db is not None: self.db.close()
        finally:
            self.db=None; fd,self.fd=self.fd,None
            if fd is not None: os.close(fd)


def load_preferences(path, *, cancel=lambda:False):
    path=Path(path)
    if not path.is_absolute(): raise PreferencesError('Explicit preference store path required')
    if cancel(): raise PreferencesError('Preference read canceled')
    if not _present(path):
        if any(_present(p) for p in _companions(path)): raise PreferencesError('Orphan preference companions; no reset')
        return PreferenceSnapshot(ToolPreferences())
    connection=_Connection(path)
    try:
        if cancel(): raise PreferencesError('Preference read canceled')
        result=connection.snapshot(); connection.header_guard()
        if cancel(): raise PreferencesError('Preference read canceled')
        return result
    finally: connection.close()


def save_preferences(path, value, expected, *, cancel=lambda:False, fault=lambda _:None):
    if type(value) is not ToolPreferences or type(expected) is not PreferenceSnapshot:
        raise ValueError('Typed preferences and captured snapshot required')
    if type(expected.version) is not int or not 0<=expected.version<2**63-1 or ((expected.version==0)!=(expected.token is None)):
        raise ValueError('Valid preference CAS required')
    if cancel(): raise PreferencesError('Preference save canceled before mutation')
    connection=None; entered=False
    try:
        if expected.version==0:
            connection=_Connection(path,create=True)
        else:
            connection=_Connection(path)
            # Validate the old read-only connection before reopening writable.
            if connection.snapshot()!=expected: raise PreferencesConflict('Preferences changed; reload')
            connection.db.close(); connection.db=None; connection.guard(); connection.header_guard()
            connection.db=sqlite3.connect(connection.path.as_uri()+'?mode=rw',uri=True,timeout=.25,isolation_level=None)
            connection.schema_guard(); connection.db.execute('PRAGMA synchronous=FULL')
        if cancel(): raise PreferencesError('Preference save canceled before transaction')
        entered=True; connection.db.execute('BEGIN IMMEDIATE'); connection.guard()
        if connection.created:
            if list(connection.db.execute('SELECT name FROM sqlite_master')) or connection.db.execute('PRAGMA user_version').fetchone()[0] or connection.db.execute('PRAGMA application_id').fetchone()[0]:
                raise PreferencesConflict('Fresh preference store changed')
            connection.db.execute(SQL)
            connection.db.execute(f'PRAGMA application_id={APPLICATION_ID}')
            connection.db.execute(f'PRAGMA user_version={VERSION}')
        elif connection.snapshot()!=expected: raise PreferencesConflict('Preferences changed; reload')
        version=expected.version+1
        connection.db.execute('INSERT OR REPLACE INTO preferences VALUES(?,?,?,?,?,?,?,?,?)',
                              (1,version,*value.paths,value.extra,int(value.include_system)))
        connection.guard(); fault('before_commit'); connection.db.execute('COMMIT'); fault('after_commit')
        connection.guard(); connection.header_guard(); connection.schema_guard()
        register_database(connection.path,APPLICATION_ID,SCHEMA_HASH)
        result=connection.snapshot()
        if (result.version!=version or result.value!=value or
            (expected.token is not None and result.token!=expected.token)):
            raise PreferencesUnknown('Post-commit preference readback differs; reconcile without replay')
        fault('before_close'); connection.close(); connection=None
        return result
    except BaseException as exc:
        # No retry, deletion or optimistic claim of rollback after any write entry.
        if entered: raise PreferencesUnknown('Preference save outcome requires reload') from exc
        raise
    finally:
        if connection is not None:
            try: connection.close()
            except BaseException as exc:
                raise PreferencesUnknown('Preference save close outcome requires reconciliation') from exc
