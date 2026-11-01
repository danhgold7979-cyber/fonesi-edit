"""Separate browser/auth/bridge/rights states, safe job refs and account cache scope."""
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import re
import uuid
from fonesi_edit.domain.composition import canonical

PLATFORMS=frozenset({'youtube','bilibili','tiktok','facebook','instagram','threads','x','douyin','xiaohongshu','kuaishou'})

class AccountError(ValueError):pass

class BrowserState(StrEnum):
    CLOSED='closed';OPEN='open';BUSY='busy';LOCKED='locked';MISSING='missing';INCOMPATIBLE='incompatible'

class WebState(StrEnum):
    UNKNOWN='unknown';SIGNED_OUT='signed_out';VALID='valid';EXPIRED='expired';VERIFY='verification_required';MISMATCH='identity_mismatch'

class BridgeState(StrEnum):
    UNKNOWN='unknown';READY='ready';UNAVAILABLE='unavailable'

class RightsState(StrEnum):
    UNKNOWN='unknown';ALLOWED='allowed';DENIED='denied'


def _uuid(value):
    try:
        if str(uuid.UUID(value))!=value:raise ValueError()
    except (ValueError,TypeError,AttributeError) as exc:raise AccountError('Canonical UUID required') from exc


def _label(value,name,optional=False):
    if optional and value is None:return
    if not isinstance(value,str) or not value.strip() or len(value)>200:
        raise AccountError(f'{name} must contain1..200characters')

@dataclass(frozen=True)
class BrowserProfile:
    id:str
    label:str
    color:str
    installation_id:str
    ownership:str
    state:BrowserState=BrowserState.CLOSED

    def __post_init__(self):
        _uuid(self.id);_uuid(self.installation_id);_label(self.label,'Profile label')
        if not isinstance(self.color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',self.color):raise AccountError('RGB profile color required')
        if self.ownership not in {'managed','linked'}:raise AccountError('Unknown profile ownership')
        if not isinstance(self.state,BrowserState):raise AccountError('Typed browser state required')
        # Paths/version/check timestamps belong to installation/profile persistence,
        # never to account job references; this pure model does not invent checks.

@dataclass(frozen=True)
class Binding:
    id:str
    profile_id:str
    platform:str
    identity:str|None
    display_name:str|None=None
    web:WebState=WebState.UNKNOWN
    bridge:BridgeState=BridgeState.UNKNOWN
    generation:int=1
    web_checked_at:int|None=None
    bridge_checked_at:int|None=None

    def __post_init__(self):
        _uuid(self.id);_uuid(self.profile_id)
        if not isinstance(self.platform,str) or self.platform not in PLATFORMS:raise AccountError('Unknown platform')
        _label(self.identity,'Identity',True);_label(self.display_name,'Display name',True)
        if not isinstance(self.web,WebState) or not isinstance(self.bridge,BridgeState):
            raise AccountError('Typed independent status axes required')
        if type(self.generation) is not int or self.generation<1:raise AccountError('Positive generation required')
        for checked in [self.web_checked_at,self.bridge_checked_at]:
            if checked is not None and (type(checked) is not int or checked<0):raise AccountError('Invalid check timestamp')

@dataclass(frozen=True)
class AccountReference:
    binding_id:str
    profile_id:str
    platform:str
    expected_identity:str
    generation:int

    def __post_init__(self):
        _uuid(self.binding_id);_uuid(self.profile_id);_label(self.expected_identity,'Expected identity')
        if not isinstance(self.platform,str) or self.platform not in PLATFORMS or type(self.generation) is not int or self.generation<1:
            raise AccountError('Invalid account reference')

    def to_dict(self):
        # Closed export allowlist: never serialize profile objects/session material.
        return {'binding_id':self.binding_id,'profile_id':self.profile_id,'platform':self.platform,
                'expected_identity':self.expected_identity,'generation':self.generation}

    @classmethod
    def parse(cls,value):
        if not isinstance(value,dict) or set(value)!={'binding_id','profile_id','platform','expected_identity','generation'}:
            raise AccountError('Unknown/secret account reference fields forbidden')
        return cls(**value)

    def cache_scope(self):
        return sha256(canonical(self.to_dict()).encode()).hexdigest()

@dataclass(frozen=True)
class SourceAccess:
    source_id:str
    account_scope:str
    rights:RightsState=RightsState.UNKNOWN
    checked_at:int|None=None

    def __post_init__(self):
        _label(self.source_id,'Source ID')
        if not isinstance(self.account_scope,str) or not re.fullmatch(r'[a-f0-9]{64}',self.account_scope):raise AccountError('Account scope hash required')
        if not isinstance(self.rights,RightsState):raise AccountError('Typed source rights required')
        if self.checked_at is not None and (type(self.checked_at) is not int or self.checked_at<0):raise AccountError('Invalid rights check timestamp')

    def cache_key(self):
        return sha256(canonical({'source_id':self.source_id,'account_scope':self.account_scope}).encode()).hexdigest()


class Catalog:
    """In-memory domain catalog only. Persistence/check evidence remains separate."""
    def __init__(self):
        self._profiles={};self._bindings={};self._defaults={}

    def add_profile(self,profile:BrowserProfile):
        if not isinstance(profile,BrowserProfile):raise AccountError('Typed profile required')
        if profile.id in self._profiles:raise AccountError('Profile already exists')
        self._profiles[profile.id]=profile

    def bind(self,binding:Binding):
        if not isinstance(binding,Binding):raise AccountError('Typed binding required')
        if binding.profile_id not in self._profiles:raise AccountError('Unknown profile')
        if binding.id in self._bindings:raise AccountError('Binding already exists')
        if any(b.profile_id==binding.profile_id and b.platform==binding.platform for b in self._bindings.values()):
            raise AccountError('Platform already bound in this profile; alternate identity needs another profile')
        self._bindings[binding.id]=binding

    def set_default(self,binding_id):
        binding=self._bindings[binding_id]
        self._defaults[binding.platform]=binding_id

    def default(self,platform):
        return self._bindings.get(self._defaults.get(platform))

    def unlink(self,binding_id):
        binding=self._bindings.pop(binding_id)
        if self._defaults.get(binding.platform)==binding_id:self._defaults.pop(binding.platform)
        # Mapping removal only. Never delete/log out/profile-close or touch Chrome.
        return binding

    def snapshot(self,binding_id):
        binding=self._bindings[binding_id]
        if binding.identity is None:raise AccountError('Verify account identity before authenticated snapshot')
        return AccountReference(binding.id,binding.profile_id,binding.platform,binding.identity,binding.generation)

    def check_auth_rights(self,reference:AccountReference,*,source_id:str,access:SourceAccess,now:int,max_age:int):
        """Partial auth/rights check only, NOT permission to acquire a browser profile.

        Admission must independently verify profile lease, busy/locked capability,
        connector compatibility and rate-limit policy before any browser operation.
        """
        if not isinstance(reference,AccountReference):raise AccountError('Typed account reference required')
        if type(now) is not int or type(max_age) is not int or now<0 or max_age<0:raise AccountError('Explicit nonnegative check time/freshness policy required')
        binding=self._bindings.get(reference.binding_id)
        if binding is None:raise AccountError('Selected account was unlinked; no automatic fallback')
        if (binding.profile_id,binding.platform,binding.identity)!=(reference.profile_id,reference.platform,reference.expected_identity):
            raise AccountError('Account identity mismatch; old job cannot silently rebind')
        if binding.generation<reference.generation:raise AccountError('Account reference generation is newer than known check')
        profile=self._profiles[binding.profile_id]
        if profile.state in {BrowserState.MISSING,BrowserState.INCOMPATIBLE}:raise AccountError('Browser configuration unavailable')
        if binding.web!=WebState.VALID:raise AccountError(f'Website session: {binding.web}')
        if binding.bridge!=BridgeState.READY:raise AccountError(f'Connector bridge: {binding.bridge}')
        for checked in [binding.web_checked_at,binding.bridge_checked_at]:
            if checked is None or not 0<=now-checked<=max_age:raise AccountError('Account check is stale or unverified')
        # Same-identity session refresh may satisfy an old job, but old cached rights cannot.
        current_scope=self.snapshot(binding.id).cache_scope()
        if not isinstance(access,SourceAccess) or access.source_id!=source_id or access.account_scope!=current_scope:
            raise AccountError('Source/account access scope mismatch')
        if access.checked_at is None or not 0<=now-access.checked_at<=max_age:raise AccountError('Source rights check is stale or unverified')
        if access.rights!=RightsState.ALLOWED:raise AccountError(f'Source rights: {access.rights}')
        return binding
