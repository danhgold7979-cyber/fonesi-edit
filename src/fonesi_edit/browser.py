"""Chrome profile metadata and user-consented session handoff (never Chrome DB decryption)."""
from pathlib import Path
from http.cookiejar import Cookie, CookieJar
import ctypes
import hashlib
import json
import os
import secrets
import time

from .domain import identifier,canonical
from .prototypes.browser import PLATFORMS,Profile,open_login

DOMAINS={'YouTube':['youtube.com','google.com'],'Facebook':['facebook.com'],'TikTok':['tiktok.com'],
 'Instagram':['instagram.com'],'Threads':['threads.com','threads.net','instagram.com'],'X':['x.com','twitter.com'],
 'Bilibili':['bilibili.com'],'Douyin':['douyin.com'],'Xiaohongshu':['xiaohongshu.com'],'Kuaishou':['kuaishou.com']}


def protect(data: bytes, decrypt=False) -> bytes:
    if os.name!='nt':
        raise PermissionError('Session persistence requires Windows DPAPI; no plaintext fallback')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    target=Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    crypt.CryptProtectData.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype=crypt.CryptUnprotectData.restype=wintypes.BOOL
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    if decrypt:
        ok=crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target))
    else:
        ok=crypt.CryptProtectData(ctypes.byref(source),'Fonesi session',None,None,None,1,ctypes.byref(target))
    if not ok:raise PermissionError('Windows could not protect/unprotect this user session')
    try:return ctypes.string_at(target.data,target.size)
    finally:kernel.LocalFree(target.data)


def create_profile(store,label):
    if not label.strip() or len(label)>80:raise ValueError('Tên hồ sơ cần 1–80 ký tự')
    key=identifier();folder=store.path.parent/'browser-profiles'/key
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'fonesi-profile.json').write_text(json.dumps({'id':key,'label':label,'owner':'fonesi-p02'}),encoding='utf-8')
    with store.connect() as c:c.execute('INSERT INTO profiles VALUES(?,?,?)',(key,label.strip(),str(folder)))
    return key


def profiles(store):
    with store.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM profiles ORDER BY label')]


def rename_profile(store,key,label):
    if not label.strip() or len(label)>80:raise ValueError('Tên hồ sơ cần 1–80 ký tự')
    with store.connect() as c:
        row=c.execute('SELECT path FROM profiles WHERE id=?',(key,)).fetchone()
        if not row:raise ValueError('Unknown profile')
        from .domain import atomic_json
        marker=Path(row['path'])/'fonesi-profile.json';data=json.loads(marker.read_text(encoding='utf-8'));data['label']=label.strip();atomic_json(marker,data)
        c.execute('UPDATE profiles SET label=? WHERE id=?',(label.strip(),key))


def forget_session(store,binding_id):
    with store.connect() as c:
        c.execute('DELETE FROM secrets WHERE key=?',('session:'+binding_id,))
        c.execute("UPDATE bindings SET status='login_required',checked=? WHERE id=?",(time.time(),binding_id))


def revoke_pairing(store,profile_id):
    """Revoke every pending or active bridge for one profile atomically."""
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        rows=c.execute("SELECT key,value FROM settings WHERE key LIKE 'bridge:%' OR key LIKE 'pair:%'").fetchall()
        for row in rows:
            try:
                data=json.loads(row['value'])
            except (TypeError,ValueError,json.JSONDecodeError):
                continue
            if isinstance(data,dict) and data.get('profile_id')==profile_id:
                c.execute('DELETE FROM settings WHERE key=?',(row['key'],))

def bindings(store):
    with store.connect() as c:
        return [dict(r) for r in c.execute('SELECT bindings.*,profiles.label FROM bindings JOIN profiles ON profiles.id=bindings.profile_id ORDER BY platform,label')]


def bind(store,profile_id,platform):
    if platform not in DOMAINS:raise ValueError('Unknown platform')
    with store.connect() as c:
        if not c.execute('SELECT 1 FROM profiles WHERE id=?',(profile_id,)).fetchone():raise ValueError('Unknown profile')
        row=c.execute('SELECT id FROM bindings WHERE profile_id=? AND platform=?',(profile_id,platform)).fetchone()
        if row:return row[0]
        key=identifier();c.execute('INSERT INTO bindings(id,profile_id,platform) VALUES(?,?,?)',(key,profile_id,platform));return key


def login(store,profile_id,platform,chrome=None):
    with store.connect() as c:row=c.execute('SELECT * FROM profiles WHERE id=?',(profile_id,)).fetchone()
    if not row:raise ValueError('Unknown profile')
    bind(store,profile_id,platform)
    return open_login(Profile(row['id'],row['label'],Path(row['path'])),platform,chrome)


def pairing_code(store,profile_id):
    with store.connect() as c:
        # Code issuance and profile revocation share one writer lock. A code
        # created before revocation is visible to the revocation sweep.
        c.execute('BEGIN IMMEDIATE')
        if not c.execute('SELECT 1 FROM profiles WHERE id=?',(profile_id,)).fetchone():
            raise ValueError('Unknown profile')
        code=secrets.token_urlsafe(18)
        key='pair:'+hashlib.sha256(code.encode()).hexdigest()
        value=canonical({'profile_id':profile_id,'expires':time.time()+300})
        c.execute(
            'INSERT INTO settings(key,value) VALUES(?,?) '
            'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            (key,value))
    return code

def pair(store,code):
    key='pair:'+hashlib.sha256(code.encode()).hexdigest()
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone();data=json.loads(row[0]) if row else None
        if not data or data['expires']<time.time():raise PermissionError('Pairing code expired/invalid')
        token=secrets.token_urlsafe(32)
        c.execute('INSERT INTO settings VALUES(?,?)',('bridge:'+hashlib.sha256(token.encode()).hexdigest(),canonical({'profile_id':data['profile_id']})))
        c.execute('DELETE FROM settings WHERE key=?',(key,))
    return token


def cookie_identity(platform,cookies):
    name={'Facebook':'c_user','Instagram':'ds_user_id','Bilibili':'DedeUserID','X':'twid'}.get(platform)
    value=next((c['value'] for c in cookies if c.get('name')==name),None)
    if platform=='X' and value:value=value.removeprefix('u=')
    return value


def receive_session(store,token,platform,cookies):
    if not isinstance(token,str) or not token or platform not in DOMAINS:
        raise PermissionError('Bridge is not paired')
    bridge_key='bridge:'+hashlib.sha256(token.encode()).hexdigest()
    with store.connect() as c:
        # Pairing revocation uses this same writer lock. Whichever operation
        # acquires it first completes before the other can inspect or mutate state.
        c.execute('BEGIN IMMEDIATE')
        bridge_row=c.execute('SELECT value FROM settings WHERE key=?',(bridge_key,)).fetchone()
        try:
            pairing=json.loads(bridge_row['value']) if bridge_row else None
        except (TypeError,ValueError,json.JSONDecodeError):
            pairing=None
        if not isinstance(pairing,dict) or not isinstance(pairing.get('profile_id'),str):
            raise PermissionError('Bridge is not paired')
        if not isinstance(cookies,list) or len(cookies)>1000 or any(not isinstance(item,dict) for item in cookies):
            raise ValueError('Invalid cookie snapshot')
        allowed=[]
        for cookie in cookies:
            domain=cookie.get('domain','').lstrip('.').lower()
            if not any(domain==d or domain.endswith('.'+d) for d in DOMAINS[platform]):continue
            if cookie.get('partitionKey'):continue  # Do not pretend CHIPS context transfers to arbitrary HTTP requests.
            allowed.append({k:cookie[k] for k in ('name','value','domain','path','secure','expirationDate') if k in cookie})
        if not allowed:raise PermissionError('No transferable session cookies for this platform')
        identity=cookie_identity(platform,allowed)
        profile_id=pairing['profile_id']
        if not c.execute('SELECT 1 FROM profiles WHERE id=?',(profile_id,)).fetchone():
            raise PermissionError('Bridge profile is unavailable')
        binding=c.execute(
            'SELECT id,identity FROM bindings WHERE profile_id=? AND platform=?',
            (profile_id,platform)).fetchone()
        if binding:
            binding_id=binding['id']
            old=binding['identity']
        else:
            binding_id=identifier()
            c.execute(
                'INSERT INTO bindings(id,profile_id,platform) VALUES(?,?,?)',
                (binding_id,profile_id,platform))
            old=None
        # Re-check under the writer lock so concurrent handoffs cannot silently
        # replace a different account after both read an empty identity.
        if old and identity and old!=identity:
            raise PermissionError('Account mismatch; old jobs keep the original account')
        if platform in {'Facebook','Instagram','Bilibili','X'} and not identity:
            c.execute("UPDATE bindings SET status='login_required',checked=? WHERE id=?",
                      (time.time(),binding_id))
            return {'binding_id':binding_id,'status':'login_required','connector_verified':False}
        encrypted=protect(canonical({'cookies':allowed,'captured':time.time()}).encode())
        c.execute('INSERT INTO secrets VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                  ('session:'+binding_id,encrypted))
        c.execute('UPDATE bindings SET identity=?,status=?,checked=? WHERE id=?',
                  (identity,'available' if identity else 'identity_unverified',time.time(),binding_id))
    return {'binding_id':binding_id,'status':'available' if identity else 'identity_unverified','connector_verified':False}

def cookie_jar(store,binding_id,expected_identity=None):
    with store.connect() as c:
        row=c.execute('SELECT * FROM bindings WHERE id=?',(binding_id,)).fetchone()
        secret=c.execute('SELECT value FROM secrets WHERE key=?',('session:'+binding_id,)).fetchone()
    if not row or not secret:raise PermissionError('Chưa nhận phiên từ Chrome; cần đăng nhập và gửi phiên qua bridge')
    if row['status']=='login_required':raise PermissionError('Phiên đã đăng xuất; đăng nhập lại đúng tài khoản')
    if expected_identity and row['identity']!=expected_identity:raise PermissionError('Account mismatch')
    snapshot=json.loads(protect(bytes(secret[0]),decrypt=True));jar=CookieJar()
    for item in snapshot['cookies']:
        expires=item.get('expirationDate')
        if expires and expires<time.time():continue
        jar.set_cookie(Cookie(0,item['name'],item['value'],None,False,item['domain'],True,item['domain'].startswith('.'),
            item.get('path','/'),True,bool(item.get('secure')),int(expires) if expires else None,not bool(expires),None,None,{},False))
    if not len(jar):
        key='session:'+binding_id
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            current=c.execute('SELECT value FROM secrets WHERE key=?',(key,)).fetchone()
            # An explicit relogin may race this read. Remove only the exact
            # expired snapshot used above; never delete a newer session.
            if current and bytes(current['value'])==bytes(secret['value']):
                c.execute('DELETE FROM secrets WHERE key=?',(key,))
                c.execute(
                    "UPDATE bindings SET status='login_required',checked=? "
                    "WHERE id=? AND identity IS ?",
                    (time.time(),binding_id,row['identity']))
        raise PermissionError('Session expired; login again in the same profile')
    return jar
