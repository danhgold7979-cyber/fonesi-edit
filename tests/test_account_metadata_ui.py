"""Read-only Settings profile/account metadata panel; no browser or credential access."""
import threading
import time

from fonesi_edit.accounts.models import (
    BrowserProfile, Binding, BrowserState, WebState, BridgeState,
)
from fonesi_edit.accounts.store import AccountStore
from fonesi_edit.ui.account_metadata import AccountMetadataPanel


def spin(app,predicate,seconds=5):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:
        app.processEvents()
        time.sleep(.005)
    assert predicate()
    app.processEvents()


def _seed(path):
    profile=BrowserProfile(
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','Hồ sơ A','#3355aa',
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','linked',BrowserState.CLOSED,
    )
    binding=Binding(
        'cccccccc-cccc-4ccc-8ccc-cccccccccccc',profile.id,'youtube','identity-A',
        display_name='Kênh A',web=WebState.VALID,bridge=BridgeState.READY,
        web_checked_at=150,bridge_checked_at=160,
    )
    with AccountStore(path) as store:
        store.save(profile,observed_at=100)
        saved=store.save(binding,observed_at=200)
        store.set_default('youtube',binding.id,expected_version=saved.version)
    return profile,binding


def test_first_open_missing_store_does_not_create_database_or_parent(qt_app,tmp_path):
    directory=tmp_path/'not-created'
    path=directory/'accounts.sqlite3'
    panel=AccountMetadataPanel(path)
    panel.first_open()
    spin(qt_app,lambda:not panel.busy)
    assert not directory.exists()
    assert not path.exists()
    assert 'không tạo' in panel.status.text().lower()
    panel.close()


def test_panel_renders_only_last_known_metadata_without_mutating_store(qt_app,tmp_path):
    path=tmp_path/'accounts.sqlite3'
    profile,binding=_seed(path)
    before=path.read_bytes()
    receipt=path.with_name(path.name+'.fonesi-owner').read_bytes()
    panel=AccountMetadataPanel(path)
    panel.first_open()
    spin(qt_app,lambda:not panel.busy)
    assert panel.profile_table.rowCount()==1
    assert panel.binding_table.rowCount()==1
    assert panel.profile_table.item(0,0).text()==profile.label
    assert panel.profile_table.item(0,3).text()=='closed'
    assert panel.binding_table.item(0,0).text()=='youtube'
    assert panel.binding_table.item(0,1).text()=='Kênh A'
    assert panel.binding_table.item(0,5).text()=='Có'
    assert 'last-known' in panel.status.text()
    assert path.read_bytes()==before
    assert path.with_name(path.name+'.fonesi-owner').read_bytes()==receipt
    panel.close()


def test_panel_refuses_foreign_store_and_keeps_it_unchanged(qt_app,tmp_path):
    path=tmp_path/'foreign.db'
    path.write_bytes(b'foreign-account-store-sentinel')
    before=path.read_bytes()
    panel=AccountMetadataPanel(path)
    panel.first_open()
    spin(qt_app,lambda:not panel.busy)
    assert 'không thể đọc' in panel.status.text().lower()
    assert path.read_bytes()==before
    assert not path.with_name(path.name+'.fonesi-owner').exists()
    assert panel.refresh_button.isEnabled()
    panel.close()


def test_close_waits_for_account_snapshot_worker_retirement(qt_app,tmp_path,monkeypatch):
    entered=threading.Event()
    release=threading.Event()
    real=AccountStore.read_snapshot
    def held(path,**kwargs):
        entered.set()
        release.wait(3)
        return real(path,**kwargs)
    monkeypatch.setattr(AccountStore,'read_snapshot',staticmethod(held))
    panel=AccountMetadataPanel(tmp_path/'missing'/'accounts.sqlite3')
    panel.refresh()
    spin(qt_app,entered.is_set)
    panel.request_stop()
    assert panel.busy and not panel.refresh_button.isEnabled()
    release.set()
    spin(qt_app,lambda:not panel.busy)
    assert 'dừng' in panel.status.text().lower()
    panel.close()
