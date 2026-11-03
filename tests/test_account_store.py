from dataclasses import replace
import json
import sqlite3
import uuid
import pytest
from fonesi_edit.accounts.models import BrowserProfile,Binding,BrowserState,WebState,SourceAccess,AccountReference,RightsState
from fonesi_edit.accounts.store import AccountStore,AccountStoreError,APPLICATION_ID,TABLES


def profile():return BrowserProfile(str(uuid.uuid4()),'Hồ sơ A','#3355aa',str(uuid.uuid4()),'linked',BrowserState.CLOSED)


def test_profile_binding_defaults_roundtrip_last_known_observations(tmp_path):
    path=tmp_path/'accounts.db';p=profile();b=Binding(str(uuid.uuid4()),p.id,'youtube','channel-A',web=WebState.VALID,web_checked_at=100)
    with AccountStore(path) as store:
        saved_p=store.save(p,observed_at=100);saved_b=store.save(b,observed_at=100)
        store.set_default('youtube',b.id,expected_version=saved_b.version)
    with AccountStore(path) as store:
        assert store.profile(p.id)==saved_p and store.binding(b.id)==saved_b
        assert store.default('youtube')==saved_b and store.default('facebook') is None
        assert store.binding(b.id).observed_at==100 # no invented freshness at reopen


def test_multiple_channels_share_one_signed_in_identity_and_unlink_preserves_browser(tmp_path):
    chrome=tmp_path/'Chrome';chrome.mkdir();sentinel=chrome/'Cookies';sentinel.write_bytes(b'foreign-browser-sentinel')
    path=tmp_path/'accounts.db'
    with AccountStore(path) as store:
        p=profile();store.save(p,observed_at=1)
        binding=Binding(str(uuid.uuid4()),p.id,'youtube','signed-in-account-A');store.save(binding,observed_at=1)
        scope=AccountReference(binding.id,p.id,'youtube',binding.identity,1).cache_scope()
        for channel in ('channel-A','channel-B'):
            store.save_access(binding.id,SourceAccess(channel,scope,RightsState.ALLOWED,1),expected_binding_version=1,observed_at=1)
        assert store.db.execute('SELECT count(*) FROM profiles').fetchone()[0]==1
        assert store.db.execute('SELECT count(*) FROM bindings').fetchone()[0]==1
    with AccountStore(path) as store:
        assert store.source_access(binding.id,'channel-A').value.account_scope==scope
        assert store.source_access(binding.id,'channel-B').value.account_scope==scope
        store.set_default('youtube',binding.id,expected_version=1)
        store.unlink_binding(binding.id,expected_version=1)
        assert store.default('youtube') is None and store.db.execute('SELECT count(*) FROM access').fetchone()[0]==0
        assert store.profile(p.id).value==p
    assert sentinel.read_bytes()==b'foreign-browser-sentinel'


def test_stale_cas_and_identity_generation_prevent_silent_rebinding(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        b=Binding(str(uuid.uuid4()),p.id,'facebook','identity-A');store.save(b,observed_at=2)
        with pytest.raises(AccountStoreError):store.save(replace(b,identity='B'),observed_at=3,expected_version=1)
        newer=store.save(replace(b,identity='B',generation=2),observed_at=3,expected_version=1)
        with pytest.raises(AccountStoreError):store.save(b,observed_at=4,expected_version=1)
        with pytest.raises(AccountStoreError):store.unlink_binding(b.id,expected_version=1)
        assert store.binding(b.id)==newer


def test_defaults_platform_identity_and_timestamp_constraints(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=10);b=Binding(str(uuid.uuid4()),p.id,'youtube','A')
        store.save(b,observed_at=10)
        with pytest.raises(AccountStoreError):store.set_default('facebook',b.id,expected_version=1)
        with pytest.raises(AccountStoreError):store.set_default('youtube',b.id,expected_version=True)
        with pytest.raises(AccountStoreError):store.save(b,observed_at=9,expected_version=1)
        with pytest.raises(AccountStoreError):store.save(replace(b,web_checked_at=30),observed_at=20,expected_version=1)
        assert store.default('facebook') is None


def test_unknown_secret_fields_refused_before_persistence(tmp_path):
    path=tmp_path/'accounts.db'
    with AccountStore(path) as store:
        with pytest.raises(AccountStoreError):store.save({'password':'SECRET_SENTINEL'},observed_at=1)
        assert store.db.execute('SELECT count(*) FROM profiles').fetchone()[0]==0
    assert b'SECRET_SENTINEL' not in path.read_bytes()


@pytest.mark.parametrize('kind',['foreign','future','malformed'])
def test_foreign_future_malformed_store_never_mutated(tmp_path,kind):
    path=tmp_path/'account.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE foreign_data(secret)')
        if kind!='foreign':db.execute(f'PRAGMA application_id={APPLICATION_ID}')
        db.execute('PRAGMA user_version='+('99' if kind=='future' else '1'))
    before=path.read_bytes()
    with pytest.raises(AccountStoreError):AccountStore(path)
    assert path.read_bytes()==before
    assert not (tmp_path/'account.db-wal').exists()


def test_binding_requires_existing_profile_and_cascading_default_removal_is_atomic(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();b=Binding(str(uuid.uuid4()),p.id,'youtube','A')
        with pytest.raises(sqlite3.IntegrityError):store.save(b,observed_at=1)
        assert store.db.execute('SELECT count(*) FROM bindings').fetchone()[0]==0
        store.save(p,observed_at=1);store.save(b,observed_at=1)
        store.set_default('youtube',b.id,expected_version=1)
        with pytest.raises(AccountStoreError):store.unlink_binding(b.id,expected_version=2)
        assert store.default('youtube').value==b


def test_corrupt_payload_identity_and_unknown_fields_not_accepted(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        raw=json.loads(store.db.execute('SELECT payload FROM profiles').fetchone()[0]);raw['password']='secret'
        store.db.execute('UPDATE profiles SET payload=?',(json.dumps(raw),))
        with pytest.raises(AccountStoreError):store.profile(p.id)
        raw.pop('password');raw['id']=str(uuid.uuid4());store.db.execute('UPDATE profiles SET payload=?',(json.dumps(raw),))
        with pytest.raises(AccountStoreError):store.profile(p.id)


def test_profile_identity_cannot_silently_retarget_existing_bindings(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        with pytest.raises(AccountStoreError):store.save(replace(p,installation_id=str(uuid.uuid4())),observed_at=2,expected_version=1)
        changed=store.save(replace(p,label='Nhãn mới',color='#aa5533'),observed_at=2,expected_version=1)
        assert changed.value.installation_id==p.installation_id


def test_default_selection_cas_and_corrupt_platform_refusal(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        other=profile();store.save(other,observed_at=1)
        a=Binding(str(uuid.uuid4()),p.id,'youtube','A');b=replace(a,id=str(uuid.uuid4()),profile_id=other.id,identity='B')
        store.save(a,observed_at=1);store.save(b,observed_at=1)
        store.set_default('youtube',a.id,expected_version=1)
        with pytest.raises(AccountStoreError):store.set_default('youtube',b.id,expected_version=1)
        store.set_default('youtube',b.id,expected_version=1,expected_default=a.id)
        assert store.default('youtube').value.id==b.id
        store.db.execute("INSERT INTO defaults VALUES('facebook',?)",(b.id,))
        with pytest.raises(AccountStoreError):store.default('facebook')


@pytest.mark.parametrize('empty_sqlite',[False,True])
def test_preexisting_unmarked_empty_store_never_adopted(tmp_path,empty_sqlite):
    path=tmp_path/'foreign-empty.db'
    if empty_sqlite:
        with sqlite3.connect(path) as db:db.execute('PRAGMA user_version=0')
    else:path.write_bytes(b'')
    before=path.read_bytes()
    with pytest.raises(AccountStoreError,match='never silently adopted'):AccountStore(path)
    assert path.read_bytes()==before
    assert not (tmp_path/'foreign-empty.db.fonesi-owner').exists()
    assert not (tmp_path/'foreign-empty.db-wal').exists()


def test_one_identity_per_profile_platform_enforced_on_insert_and_update(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        a=Binding(str(uuid.uuid4()),p.id,'youtube','account-A');store.save(a,observed_at=1)
        with pytest.raises(sqlite3.IntegrityError):store.save(replace(a,id=str(uuid.uuid4()),identity='account-B'),observed_at=1)
        other=Binding(str(uuid.uuid4()),p.id,'facebook','account-C');store.save(other,observed_at=1)
        with pytest.raises(sqlite3.IntegrityError):store.save(replace(other,platform='youtube',generation=2),observed_at=2,expected_version=1)
        assert store.binding(other.id).value.platform=='facebook'


def test_source_rights_cannot_cross_identity_generation_or_account(tmp_path):
    with AccountStore(tmp_path/'accounts.db') as store:
        p=profile();store.save(p,observed_at=1)
        b=Binding(str(uuid.uuid4()),p.id,'youtube','account-A');store.save(b,observed_at=1)
        scope=AccountReference(b.id,p.id,b.platform,b.identity,b.generation).cache_scope()
        access=SourceAccess('channel-A',scope,RightsState.ALLOWED,1)
        store.save_access(b.id,access,expected_binding_version=1,observed_at=1)
        b2=replace(b,identity='account-B',generation=2);store.save(b2,expected_version=1,observed_at=2)
        with pytest.raises(KeyError):store.source_access(b.id,'channel-A')
        with pytest.raises(AccountStoreError):store.save_access(b.id,access,expected_binding_version=2,observed_at=2)
        assert store.db.execute('SELECT count(*) FROM access').fetchone()[0]==1 # old observation retained, never used as current



def test_read_snapshot_missing_store_never_creates_path_or_receipt(tmp_path):
    directory=tmp_path/'not-created'
    path=directory/'accounts.sqlite3'
    assert AccountStore.read_snapshot(path) is None
    assert not directory.exists()
    assert not path.exists()
    assert not path.with_name(path.name+'.fonesi-owner').exists()


def test_read_snapshot_is_bounded_typed_and_does_not_mutate_owned_store(tmp_path):
    path=tmp_path/'accounts.sqlite3'
    p=profile()
    b=Binding(str(uuid.uuid4()),p.id,'youtube','identity-A',display_name='Kênh A',
              web=WebState.VALID,web_checked_at=150)
    with AccountStore(path) as store:
        store.save(p,observed_at=100)
        saved=store.save(b,observed_at=200)
        store.set_default('youtube',b.id,expected_version=saved.version)
    before=path.read_bytes()
    receipt=path.with_name(path.name+'.fonesi-owner').read_bytes()
    names={x.name for x in tmp_path.iterdir()}
    snapshot=AccountStore.read_snapshot(path,profile_limit=1,binding_limit=1)
    assert snapshot is not None
    assert snapshot.profile_total==1 and len(snapshot.profiles)==1
    assert snapshot.binding_total==1 and len(snapshot.bindings)==1
    assert snapshot.profiles[0].value==p
    assert snapshot.bindings[0].value==b
    assert snapshot.defaults==(('youtube',b.id),)
    assert path.read_bytes()==before
    assert path.with_name(path.name+'.fonesi-owner').read_bytes()==receipt
    assert {x.name for x in tmp_path.iterdir()}==names


def test_read_snapshot_refuses_active_wal_without_modifying_store(tmp_path):
    path=tmp_path/'accounts.sqlite3'
    store=AccountStore(path)
    try:
        p=profile();store.save(p,observed_at=1)
        wal=path.with_name(path.name+'-wal')
        assert wal.exists()
        before=path.read_bytes();wal_before=wal.read_bytes()
        with pytest.raises(AccountStoreError,match='busy'):
            AccountStore.read_snapshot(path)
        assert path.read_bytes()==before and wal.read_bytes()==wal_before
    finally:
        store.close()


def test_read_snapshot_refuses_unowned_file_without_adoption_or_mutation(tmp_path):
    path=tmp_path/'foreign.db';path.write_bytes(b'foreign-account-store-sentinel')
    before=path.read_bytes()
    with pytest.raises(AccountStoreError,match='regular|unowned|foreign'):
        AccountStore.read_snapshot(path)
    assert path.read_bytes()==before
    assert not path.with_name(path.name+'.fonesi-owner').exists()
