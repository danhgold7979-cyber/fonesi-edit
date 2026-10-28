"""Owned installations: verified staging, immutable versions, leases and rollback."""
from dataclasses import dataclass,asdict
from pathlib import Path,PurePosixPath
from urllib.parse import urlparse
from urllib.request import urlopen
import hashlib
import importlib.metadata
import json
import os
import shutil
import stat
import tempfile
import time
import zipfile
from ..core.paths import content_hash,contained
from ..core.process import run,Cancelled


@dataclass
class ToolStatus:
    name:str
    path:str=''
    version:str=''
    state:str='missing'
    origin:str='system'
    capabilities:list[str]|None=None
    error:str=''
    checked_at:float=0


def inspect_tool(name,path='',required=()) -> ToolStatus:
    chosen=path or shutil.which(name)
    status=ToolStatus(name,path=chosen or '',origin='user' if path else 'system',checked_at=time.time())
    if not chosen:status.error='Không tìm thấy công cụ';return status
    if not Path(chosen).is_file():status.state='invalid_path';status.error='Đường dẫn được chọn không tồn tại; không tự đổi sang bản khác';return status
    try:
        version=run([chosen,'-version' if name in {'ffmpeg','ffprobe'} else '--version'],timeout=10).splitlines()[0]
        status.version=version;status.capabilities=[]
        if name=='ffmpeg':
            output=run([chosen,'-hide_banner','-filters'],timeout=10)
            status.capabilities=[r for r in required if r in output]
            if len(status.capabilities)!=len(required):status.state='missing_capability';return status
        if name=='chrome' and 'Google Chrome' not in version:status.state='incompatible';status.error='Cần Google Chrome chính thức, không thay bằng Chromium';return status
        status.state='ready'
    except Exception as exc:status.state='launch_failed';status.error=str(exc)
    return status


def scan_tools(overrides=None):
    overrides=overrides or {};result=[]
    for name in ['ffmpeg','ffprobe','chrome']:
        path=overrides.get(name,'')
        if name=='chrome' and not path:
            candidates=[shutil.which('google-chrome'),shutil.which('google-chrome-stable')]
            candidates += [str(Path(os.environ.get(e,''))/'Google/Chrome/Application/chrome.exe') for e in ['PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA']]
            path=next((p for p in candidates if p and Path(p).is_file()),'')
        result.append(asdict(inspect_tool(name,path,required=['scale','overlay','subtitles'] if name=='ffmpeg' else [])))
    for name in ['yt-dlp','gallery-dl']:
        try:result.append(asdict(ToolStatus(name,path='bundled Python module',version=importlib.metadata.version(name),state='ready',origin='bundled',checked_at=time.time())))
        except importlib.metadata.PackageNotFoundError:result.append(asdict(ToolStatus(name)))
    return result


class ToolManager:
    def __init__(self,root:Path,store):self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True);self.store=store
    def lease(self,name,version,job_id):self.store.put('tool_lease',job_id+':'+name,{'name':name,'version':version,'job_id':job_id})
    def release(self,job_id):
        with self.store.connection() as db:db.execute("DELETE FROM objects WHERE namespace='tool_lease' AND id LIKE ?",(job_id+':%',))
    def activate(self,name,version):
        installs=self.store.objects('tool_installation');key=name+':'+version
        if key not in installs or not installs[key]['verified']:raise ValueError('Tool not verified')
        previous=self.store.objects('tool_active').get(name)
        self.store.put('tool_active',name,{'version':version,'previous':previous['version'] if previous else None})
    def rollback(self,name):
        current=self.store.objects('tool_active').get(name)
        if not current or not current.get('previous'):raise ValueError('No verified prior version')
        self.activate(name,current['previous'])
    def install(self,manifest:dict,*,trusted_manifest_hash:str,cancel=lambda:False,progress=lambda *a:None):
        canonical=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
        if hashlib.sha256(canonical).hexdigest()!=trusted_manifest_hash:raise ValueError('Manifest does not match trusted pinned hash')
        name,version=manifest['name'],manifest['version']
        if any('/' in x or '\\' in x or x in {'.','..',''} for x in [name,version]):raise ValueError('Unsafe tool identity')
        parsed=urlparse(manifest['url'])
        if parsed.scheme!='https' or parsed.username or parsed.password:raise ValueError('Trusted artifacts require HTTPS')
        target=self.root/name/version
        if target.exists():raise FileExistsError('Version already installed; verify or choose another version')
        with tempfile.TemporaryDirectory(prefix='.stage-',dir=self.root) as d:
            stage=Path(d);archive=stage/'artifact';h=hashlib.sha256();received=0
            with urlopen(manifest['url'],timeout=30) as source,archive.open('wb') as out:
                total=int(source.headers.get('Content-Length',0))
                while block:=source.read(1024*1024):
                    if cancel():raise Cancelled('Tool download canceled')
                    received+=len(block)
                    if received>manifest.get('max_bytes',2*1024**3):raise ValueError('Artifact exceeds manifest size limit')
                    h.update(block);out.write(block);progress('download',received/total if total else None)
            if h.hexdigest()!=manifest['sha256']:raise ValueError('Artifact checksum mismatch; previous version retained')
            unpack=stage/'unpacked';unpack.mkdir()
            if manifest.get('archive')=='zip':
                with zipfile.ZipFile(archive) as z:
                    if sum(x.file_size for x in z.infolist())>manifest.get('max_unpacked_bytes',4*1024**3):raise ValueError('Archive size limit exceeded')
                    for member in z.infolist():
                        p=PurePosixPath(member.filename.replace('\\','/'))
                        if p.is_absolute() or '..' in p.parts or ':' in str(p) or stat.S_ISLNK(member.external_attr>>16):raise ValueError('Unsafe archive member')
                    z.extractall(unpack)
            else:shutil.copy2(archive,unpack/manifest['executable'])
            binary=unpack/manifest['executable']
            if not contained(binary,unpack) or not binary.is_file():raise ValueError('Missing/unsafe executable')
            binary.chmod(binary.stat().st_mode|stat.S_IXUSR)
            status=inspect_tool(name,str(binary),manifest.get('required_capabilities',[]))
            if status.state!='ready':raise ValueError('Tool self-test failed: '+status.error)
            target.parent.mkdir(exist_ok=True);os.rename(unpack,target)
            self.store.put('tool_installation',name+':'+version,{'name':name,'version':version,'path':str(target/manifest['executable']),'origin':'app_managed','verified':True,'sha256':manifest['sha256']})
            self.activate(name,version)
        return str(target/manifest['executable'])
