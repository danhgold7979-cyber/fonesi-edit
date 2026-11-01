from pathlib import Path
import sqlite3
import pytest
from fonesi_edit.dependencies.preferences import (
    ToolPreferences, PreferenceSnapshot, load_preferences, save_preferences,
    PreferencesError, PreferencesConflict, PreferencesUnknown, APPLICATION_ID, SQL)


def chosen(tmp_path):
    return ToolPreferences((str(tmp_path/'Công cụ'/'ffmpeg.exe'),'','','',''),str(tmp_path),False)


def test_missing_read_no_directory_and_unicode_roundtrip(tmp_path):
    path=tmp_path/'missing'/'tools.db'
    assert load_preferences(path)==PreferenceSnapshot(ToolPreferences())
    assert not path.parent.exists()
    path=tmp_path/'tools.db'; before=load_preferences(path); value=chosen(tmp_path)
    saved=save_preferences(path,value,before)
    assert saved.version==1 and saved.token and saved.value==value
    assert load_preferences(path)==saved
    cleared=save_preferences(path,ToolPreferences(),saved)
    assert cleared.version==2 and cleared.token==saved.token
    assert not (tmp_path/'Công cụ').exists() # paths are preferences, not executable access


def test_stale_and_recreated_store_do_not_mutate(tmp_path):
    path=tmp_path/'tools.db'; old=save_preferences(path,chosen(tmp_path),load_preferences(path))
    current=save_preferences(path,ToolPreferences(),old)
    with pytest.raises(PreferencesConflict):save_preferences(path,chosen(tmp_path),old)
    assert load_preferences(path)==current
    path.rename(tmp_path/'old.db'); path.with_name('tools.db.fonesi-owner').rename(tmp_path/'old.owner')
    fresh=save_preferences(path,chosen(tmp_path),load_preferences(path))
    assert fresh.version==old.version and fresh.token!=old.token
    with pytest.raises(PreferencesConflict):save_preferences(path,ToolPreferences(),old)
    assert load_preferences(path)==fresh


@pytest.mark.parametrize('kind',['empty','v0','future','receipt','wal','shm','journal','symlink'])
def test_foreign_preexisting_and_orphans_unchanged(tmp_path,kind):
    path=tmp_path/'tools.db'
    if kind=='empty':path.touch()
    elif kind in ('v0','future'):
        with sqlite3.connect(path) as db:db.execute('PRAGMA user_version='+('0' if kind=='v0' else '99'))
    elif kind=='symlink':
        target=tmp_path/'foreign';target.write_bytes(b'foreign')
        try:path.symlink_to(target)
        except OSError:pytest.skip('Link creation unavailable')
    else:path.with_name(path.name+('.fonesi-owner' if kind=='receipt' else '-'+kind)).write_bytes(b'FOREIGN')
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises((PreferencesError,FileExistsError)):load_preferences(path)
    with pytest.raises((PreferencesError,FileExistsError)):save_preferences(path,ToolPreferences(),PreferenceSnapshot(ToolPreferences()))
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


@pytest.mark.parametrize('value',['relative','bad\0path','/'+('x'*32769)])
def test_invalid_paths_rejected_before_store_creation(tmp_path,value):
    with pytest.raises(ValueError):ToolPreferences((value,'','','',''))
    assert not list(tmp_path.iterdir())


def test_commit_unknown_retains_durable_value_no_replay(tmp_path):
    path=tmp_path/'tools.db'; old=save_preferences(path,ToolPreferences(),load_preferences(path))
    def fault(stage):
        if stage=='after_commit':raise OSError('unknown storage detail')
    with pytest.raises(PreferencesUnknown):save_preferences(path,chosen(tmp_path),old,fault=fault)
    observed=load_preferences(path)
    assert observed.version==2 and observed.value==chosen(tmp_path)
    with pytest.raises(PreferencesConflict):save_preferences(path,chosen(tmp_path),old)
    assert load_preferences(path)==observed


def test_wal_header_refused_before_sqlite_and_without_sidecars(tmp_path,monkeypatch):
    import fonesi_edit.dependencies.preferences as module
    path=tmp_path/'tools.db';save_preferences(path,ToolPreferences(),load_preferences(path))
    with sqlite3.connect(path) as db:db.execute('PRAGMA journal_mode=WAL')
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.setattr(module.sqlite3,'connect',lambda *a,**k:pytest.fail('SQLite reached WAL input'))
    with pytest.raises(PreferencesError):load_preferences(path)
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


def test_embedded_nul_row_is_not_silently_truncated(tmp_path):
    path=tmp_path/'tools.db';save_preferences(path,ToolPreferences(),load_preferences(path))
    with sqlite3.connect(path) as db:db.execute('UPDATE preferences SET ffmpeg=?',(str(tmp_path)+'\0HIDDEN',))
    with pytest.raises(ValueError):load_preferences(path)


def test_cancel_before_any_creation(tmp_path):
    path=tmp_path/'tools.db'
    with pytest.raises(PreferencesError):save_preferences(path,ToolPreferences(),PreferenceSnapshot(ToolPreferences()),cancel=lambda:True)
    assert not list(tmp_path.iterdir())


def test_interrupted_constructor_closes_original_descriptor(tmp_path,monkeypatch):
    import os
    import fonesi_edit.dependencies.preferences as module
    seen=[];original=module._Connection.guard
    def interrupted(self):
        seen.append(self.fd);raise KeyboardInterrupt
    monkeypatch.setattr(module._Connection,'guard',interrupted)
    with pytest.raises(KeyboardInterrupt):save_preferences(tmp_path/'tools.db',ToolPreferences(),PreferenceSnapshot(ToolPreferences()))
    assert len(seen)==1
    with pytest.raises(OSError):os.fstat(seen[0])


def test_before_commit_failure_rolls_back_but_never_replays(tmp_path):
    path=tmp_path/'tools.db';old=save_preferences(path,ToolPreferences(),load_preferences(path));calls=[]
    def fault(stage):
        calls.append(stage)
        if stage=='before_commit':raise PermissionError('write denied')
    with pytest.raises(PreferencesUnknown):save_preferences(path,chosen(tmp_path),old,fault=fault)
    assert load_preferences(path)==old and calls==['before_commit']


def test_schema_changed_owned_store_never_mutated(tmp_path):
    path=tmp_path/'tools.db';save_preferences(path,ToolPreferences(),load_preferences(path))
    with sqlite3.connect(path) as db:db.execute('CREATE TABLE unrelated(x)')
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(PreferencesError):load_preferences(path)
    assert {p.name:p.read_bytes() for p in tmp_path.iterdir()}==before


def test_post_commit_other_writer_cannot_be_reported_as_own_save(tmp_path):
    path=tmp_path/'tools.db';old=save_preferences(path,ToolPreferences(),load_preferences(path))
    intended=chosen(tmp_path)
    other=ToolPreferences(('',str(tmp_path/'other-probe'),'','',''))
    outcomes=[]
    def intervening(stage):
        if stage=='after_commit':outcomes.append(save_preferences(path,other,load_preferences(path)))
    with pytest.raises(PreferencesUnknown):save_preferences(path,intended,old,fault=intervening)
    assert len(outcomes)==1 and load_preferences(path)==outcomes[0]
    assert outcomes[0].version==3 and outcomes[0].value==other
