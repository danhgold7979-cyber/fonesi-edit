from pathlib import Path
from urllib.parse import urlparse
import subprocess
from ..core.model import uid
from ..core.paths import contained
from .tools import inspect_tool

PLATFORMS={
 'YouTube':('youtube.com','https://www.youtube.com/'), 'Bilibili':('bilibili.com','https://www.bilibili.com/'),
 'TikTok':('tiktok.com','https://www.tiktok.com/login'), 'Facebook':('facebook.com','https://www.facebook.com/login/'),
 'Instagram':('instagram.com','https://www.instagram.com/accounts/login/'), 'Threads':('threads.net','https://www.threads.net/'),
 'X':('x.com','https://x.com/i/flow/login'), 'Douyin':('douyin.com','https://www.douyin.com/'),
 'Xiaohongshu':('xiaohongshu.com','https://www.xiaohongshu.com/'), 'Kuaishou':('kuaishou.com','https://www.kuaishou.com/')}

class BrowserManager:
    def __init__(self,root:Path,store):self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True);self.store=store;self.running={}
    def create_profile(self,name):
        identity=uid();path=self.root/identity;path.mkdir()
        self.store.put('browser_profile',identity,{'id':identity,'name':name,'path':str(path),'ownership':'app_managed'})
        return identity
    def bind(self,platform,profile_id,identity=''):
        if platform not in PLATFORMS:raise ValueError('Unknown platform')
        if profile_id not in self.store.objects('browser_profile'):raise ValueError('Unknown profile')
        bindings=self.store.objects('account_binding')
        if any(b['platform']==platform and b['profile_id']==profile_id for b in bindings.values()):raise ValueError('One identity per platform/profile; use another profile for another account')
        key=uid();self.store.put('account_binding',key,{'id':key,'platform':platform,'profile_id':profile_id,'identity':identity,'web_state':'unchecked','bridge_state':'unverified','source_state':'unchecked','default':not any(b['platform']==platform for b in bindings.values())});return key
    def open(self,chrome,profile_id,platform):
        status=inspect_tool('chrome',chrome)
        if status.state!='ready':raise ValueError(status.error or status.state)
        profile=self.store.objects('browser_profile')[profile_id];path=Path(profile['path'])
        if not contained(path,self.root):raise ValueError('Only app-managed isolated profiles are supported')
        if any((path/x).exists() for x in ['SingletonLock','lockfile']):raise ValueError('Profile is open/locked; existing lock is not removed')
        if profile_id in self.running and self.running[profile_id].poll() is None:raise ValueError('Profile is already open in a managed Chrome process')
        proc=subprocess.Popen([chrome,'--user-data-dir='+str(path),'--no-first-run',PLATFORMS[platform][1]],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.running[profile_id]=proc;return proc.pid
    def preflight(self,binding_id,expected_identity=None):
        if not binding_id:return {'public':True,'ready':True}
        binding=self.store.objects('account_binding').get(binding_id)
        if not binding:raise ValueError('Selected account binding no longer exists; no public fallback')
        if expected_identity and binding['identity']!=expected_identity:raise ValueError('Account identity mismatch; job remains assigned to original account')
        if binding['web_state']!='verified':raise ValueError('Website login not verified; open the selected Chrome profile')
        if binding['bridge_state']!='verified':raise ValueError('Connector session handoff has not been verified for this account/Chrome/OS')
        if binding['source_state']!='verified':raise ValueError('Source access rights not verified')
        return {'ready':True,'profile_id':binding['profile_id'],'identity':binding['identity']}
    def unlink(self,binding_id):
        with self.store.connection() as db:db.execute("DELETE FROM objects WHERE namespace='account_binding' AND id=?",(binding_id,))
        # Deliberately does not log out or remove Chrome data.
