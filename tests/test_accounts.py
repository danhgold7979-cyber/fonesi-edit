from dataclasses import replace
import uuid
import pytest
from fonesi_edit.accounts.models import *

def ident():return str(uuid.uuid4())

def profile():return BrowserProfile(ident(),'Chrome A','#aabbcc',ident(),'managed')

def binding(p,platform='facebook',identity='auth-A'):
    return Binding(ident(),p.id,platform,identity,web=WebState.VALID,bridge=BridgeState.READY,web_checked_at=100,bridge_checked_at=100)

def preflight(c,ref,source='source-one',rights=RightsState.ALLOWED):
    return c.check_auth_rights(ref,source_id=source,access=SourceAccess(source,ref.cache_scope(),rights,100),now=100,max_age=300)

def test_multiple_platforms_one_profile_and_alternate_profile():
    c=Catalog();a=profile();b=replace(profile(),label='Chrome B');c.add_profile(a);c.add_profile(b)
    fa=binding(a);ta=binding(a,'tiktok');fb=binding(b,identity='auth-B')
    for item in [fa,ta,fb]:c.bind(item)
    with pytest.raises(AccountError,match='alternate identity'):c.bind(binding(a,identity='auth-C'))
    assert c.snapshot(fa.id).cache_scope()!=c.snapshot(fb.id).cache_scope()
    assert c.snapshot(fa.id).cache_scope()!=c.snapshot(ta.id).cache_scope()

def test_pages_channels_not_auth_identity():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p,'youtube');c.bind(b)
    ref=c.snapshot(b.id)
    # Two source IDs are caller source selection, never substituted for auth identity.
    for source in ['channel-one','channel-two']:
        assert preflight(c,ref,source).identity=='auth-A'
        assert source!=ref.expected_identity

@pytest.mark.parametrize('field,value,message',[
    ('web',WebState.EXPIRED,'Website'),('bridge',BridgeState.UNAVAILABLE,'bridge')])
def test_independent_axes_not_all_auth_expired(field,value,message):
    c=Catalog();p=profile();c.add_profile(p);b=replace(binding(p),**{field:value});c.bind(b)
    with pytest.raises(AccountError,match=message):preflight(c,c.snapshot(b.id))
    if field!='web':assert b.web==WebState.VALID

def test_unlink_not_delete_profile_or_public_fallback():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p);c.bind(b);c.set_default(b.id);ref=c.snapshot(b.id)
    c.unlink(b.id);assert c.default('facebook') is None
    with pytest.raises(AccountError,match='no automatic fallback'):preflight(c,ref)
    c.bind(binding(p)) # profile retained without any browser data operations

def test_snapshot_no_credentials_and_identity_mismatch():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p);c.bind(b);ref=c.snapshot(b.id)
    assert AccountReference.parse(ref.to_dict())==ref
    for field in ['password','cookie','bearer_token','user_data_dir']:
        data=ref.to_dict();data[field]='SECRET_SENTINEL'
        with pytest.raises(AccountError):AccountReference.parse(data)
    with pytest.raises(AccountError,match='mismatch'):preflight(c,replace(ref,expected_identity='other'))
    with pytest.raises(AccountError,match='generation'):preflight(c,replace(ref,generation=2))

def test_unknown_identity_not_ready():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p,identity=None);c.bind(b)
    with pytest.raises(AccountError,match='Verify account identity'):c.snapshot(b.id)


def test_source_rights_are_not_global_for_auth_account():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p);c.bind(b);ref=c.snapshot(b.id)
    allowed=SourceAccess('page-one',ref.cache_scope(),RightsState.ALLOWED,100)
    denied=SourceAccess('page-two',ref.cache_scope(),RightsState.DENIED,100)
    assert allowed.cache_key()!=denied.cache_key()
    assert c.check_auth_rights(ref,source_id='page-one',access=allowed,now=100,max_age=300)==b
    with pytest.raises(AccountError,match='rights'):c.check_auth_rights(ref,source_id='page-two',access=denied,now=100,max_age=300)
    with pytest.raises(AccountError,match='scope mismatch'):c.check_auth_rights(ref,source_id='page-two',access=allowed,now=100,max_age=300)
    wrong=replace(allowed,account_scope='0'*64)
    with pytest.raises(AccountError,match='scope mismatch'):c.check_auth_rights(ref,source_id='page-one',access=wrong,now=100,max_age=300)


def test_same_identity_refresh_old_job_new_rights_scope():
    c=Catalog();p=profile();c.add_profile(p);b=replace(binding(p),generation=2);c.bind(b)
    current=c.snapshot(b.id);old=replace(current,generation=1)
    fresh=SourceAccess('page',current.cache_scope(),RightsState.ALLOWED,100)
    assert c.check_auth_rights(old,source_id='page',access=fresh,now=100,max_age=10)==b
    with pytest.raises(AccountError,match='scope mismatch'):
        c.check_auth_rights(old,source_id='page',access=replace(fresh,account_scope=old.cache_scope()),now=100,max_age=10)
    with pytest.raises(AccountError,match='stale'):
        c.check_auth_rights(current,source_id='page',access=fresh,now=1000,max_age=10)
    with pytest.raises(AccountError,match='stale'):
        c.check_auth_rights(current,source_id='page',access=replace(fresh,checked_at=None),now=100,max_age=10)

@pytest.mark.parametrize('change',[{'platform':[]},{'generation':True},{'web':'valid'},{'web_checked_at':float('inf')}])
def test_bad_binding_types_rejected(change):
    with pytest.raises(AccountError):replace(binding(profile()),**change)


@pytest.mark.parametrize('field,stamp',[('web_checked_at',None),('web_checked_at',101),('bridge_checked_at',0),('bridge_checked_at',101)])
def test_each_account_check_freshness_independent(field,stamp):
    c=Catalog();p=profile();c.add_profile(p);b=replace(binding(p),**{field:stamp});c.bind(b)
    ref=c.snapshot(b.id);access=SourceAccess('page',ref.cache_scope(),RightsState.ALLOWED,100)
    with pytest.raises(AccountError,match='stale'):
        c.check_auth_rights(ref,source_id='page',access=access,now=100,max_age=10)

@pytest.mark.parametrize('state',[BrowserState.MISSING,BrowserState.INCOMPATIBLE])
def test_missing_browser_configuration_blocks_check(state):
    c=Catalog();p=replace(profile(),state=state);c.add_profile(p);b=binding(p);c.bind(b)
    with pytest.raises(AccountError,match='Browser configuration'):preflight(c,c.snapshot(b.id))

def test_future_source_rights_never_ready():
    c=Catalog();p=profile();c.add_profile(p);b=binding(p);c.bind(b);ref=c.snapshot(b.id)
    future=SourceAccess('page',ref.cache_scope(),RightsState.ALLOWED,101)
    with pytest.raises(AccountError,match='stale'):
        c.check_auth_rights(ref,source_id='page',access=future,now=100,max_age=10)
