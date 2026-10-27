"""Length-framed native messaging endpoint, paired by a short-lived user code."""
from pathlib import Path
import hashlib
import json
import os
import struct
import sys

from .browser import pair,receive_session
from .paths import data_directory,resource_directory
from .storage import Store


def extension_id():
    import base64
    manifest=json.loads((resource_directory('extension')/'manifest.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256(base64.b64decode(manifest['key'])).hexdigest()[:32]
    return ''.join(chr(ord('a')+int(n,16)) for n in digest)


def handle(store,message):
    if message.get('type')=='pair':return {'token':pair(store,str(message.get('code','')))}
    if message.get('type')=='snapshot':
        return receive_session(store,str(message.get('token','')),message.get('platform'),message.get('cookies'))
    raise ValueError('Unknown bridge message')


def register_host(executable:Path,data=None):
    if os.name!='nt':raise PermissionError('Native host registration is Windows-only')
    if not executable.is_file() or executable.suffix.lower()!='.exe':raise ValueError('Choose the packaged fonesi-native-host.exe')
    root=Path(data or data_directory()).resolve();root.mkdir(parents=True,exist_ok=True)
    path=root/'native-host.json'
    path.write_text(json.dumps({'name':'com.fonesi.bridge','description':'Fonesi user-consented Chrome session bridge',
        'path':str(executable.resolve()),'type':'stdio','allowed_origins':['chrome-extension://'+extension_id()+'/']},indent=2),encoding='utf-8')
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,r'Software\Google\Chrome\NativeMessagingHosts\com.fonesi.bridge') as key:
        winreg.SetValueEx(key,'',0,winreg.REG_SZ,str(path))
        winreg.SetValueEx(key,'DataDirectory',0,winreg.REG_SZ,str(root))
    return path


def main():
    origin='chrome-extension://'+extension_id()+'/'
    if origin not in sys.argv[1:]:return 2
    root=data_directory()
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Google\Chrome\NativeMessagingHosts\com.fonesi.bridge') as key:root=Path(winreg.QueryValueEx(key,'DataDirectory')[0])
        except FileNotFoundError:pass
    store=Store(root/'state.db')
    incoming,outgoing=sys.stdin.buffer,sys.stdout.buffer
    while True:
        header=incoming.read(4)
        if not header:return 0
        if len(header)!=4:return 2
        length=struct.unpack('<I',header)[0]
        if not 0<length<=1024*1024:return 2
        raw=incoming.read(length)
        if len(raw)!=length:return 2
        try:reply={'ok':True,'result':handle(store,json.loads(raw))}
        except Exception as exc:reply={'ok':False,'error':str(exc)[:300]}
        data=json.dumps(reply,ensure_ascii=False).encode('utf-8')
        outgoing.write(struct.pack('<I',len(data))+data);outgoing.flush()


if __name__=='__main__':raise SystemExit(main())
