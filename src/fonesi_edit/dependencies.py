"""User-owned, versioned tool installations with TLS and digest verification."""
from pathlib import Path,PurePosixPath
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener
import zipfile

from .domain import fingerprint,atomic_json,canonical,checked_payload,identifier
from .prototypes.tools import check_tool,scan_tools,configure_tools


def statuses(store):
    from .prototypes.tools import ToolStatus
    overrides=store.setting('tool_paths',{})
    result=scan_tools(overrides)
    for i,item in enumerate(result):
        if item.name in {'yt-dlp','gallery-dl'} and item.name not in overrides:
            if item.name=='yt-dlp':
                from yt_dlp.version import __version__
            else:
                from gallery_dl.version import __version__
            result[i]=ToolStatus(item.name,'Gói kèm module Python','ready',__version__,'Backend đang dùng module đã khóa trong ứng dụng')
    return result


class SecureRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not newurl.startswith('https://'):raise PermissionError('Refusing a non-HTTPS artifact redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def download_verified(url,destination,sha256,progress=lambda p:None,cancel=None):
    if not url.startswith('https://') or not re.fullmatch('[a-fA-F0-9]{64}',sha256):raise ValueError('HTTPS and SHA256 are required')
    digest=hashlib.sha256();size=0
    with build_opener(SecureRedirect()).open(Request(url,headers={'User-Agent':'FonesiEdit/0.1'}),timeout=30) as response, destination.open('xb') as output:
        length=int(response.headers.get('Content-Length',0))
        while True:
            if cancel and cancel.is_set():raise RuntimeError('Canceled')
            block=response.read(1024*1024)
            if not block:break
            size+=len(block)
            if size>2*1024**3:raise ValueError('Artifact exceeds 2 GiB budget')
            digest.update(block);output.write(block)
            if length:progress(min(.8,size/length*.8))
    if digest.hexdigest().lower()!=sha256.lower():raise ValueError('Artifact SHA256 mismatch; installation not activated')


def _windows_reserved_component(component):
    stem=component.split('.',1)[0].rstrip(' .').upper()
    return (stem in {'CON','PRN','AUX','NUL','CONIN$','CONOUT$'}
            or bool(re.fullmatch(r'(?:COM|LPT)(?:[1-9¹²³])',stem)))


def extract_zip(archive,destination):
    with zipfile.ZipFile(archive) as package:
        members=package.infolist()
        if sum(item.file_size for item in members)>4*1024**3:
            raise ValueError('Archive exceeds extraction budget')
        seen={}
        normalized_names=[]
        # Validate every member before writing the first file. A later malicious
        # entry must not leave a partially extracted archive behind.
        for item in members:
            raw_name=item.filename
            normalized=raw_name.replace('\\','/')
            normalized_parts=normalized.rstrip('/')
            path=PurePosixPath(normalized_parts)
            components=normalized_parts.split('/') if normalized_parts else []
            mode=(item.external_attr>>16)&0o170000
            is_directory=normalized.endswith('/')
            if (not raw_name or not normalized_parts or '\x00' in raw_name
                    or any(ord(char)<32 or ord(char)==127 for char in raw_name)
                    or path.is_absolute() or not path.parts
                    or any(part in {'', '.', '..'} for part in components)
                    or ':' in normalized
                    or any(any(char in '<>:"|?*' for char in part)
                           or part[-1] in {' ', '.'}
                           or _windows_reserved_component(part)
                           for part in components)
                    or mode not in {0,0o100000,0o040000}
                    or (mode==0o040000 and not is_directory)
                    or (mode==0o100000 and is_directory)
                    or item.flag_bits & 0x1):
                raise ValueError('Unsafe archive path/type/flags')
            key='/'.join(part.casefold() for part in components)
            if key in seen:
                raise ValueError('Duplicate or case-colliding archive path')
            for index in range(1,len(components)):
                parent='/'.join(part.casefold() for part in components[:index])
                if seen.get(parent)=='file':
                    raise ValueError('Archive file/directory path collision')
            if not is_directory and any(existing.startswith(key+'/') for existing in seen):
                raise ValueError('Archive file/directory path collision')
            seen[key]='directory' if is_directory else 'file'
            normalized_names.append(normalized)
        # ZipInfo filenames are normalized only after the entire archive passes
        # preflight, so backslash-separated paths behave consistently on Linux
        # and Windows without weakening the all-or-nothing validation boundary.
        for item,normalized in zip(members,normalized_names):
            item.filename=normalized
        package.extractall(destination,members=members)


def _check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise RuntimeError('Canceled')


def _verified_receipt(name, final, manifest):
    """Return an intact receipt only when every path remains inside its version folder."""
    try:
        if final.is_symlink():
            return None
        receipt=json.loads((final/'receipt.json').read_text(encoding='utf-8'))
        if not isinstance(receipt,dict):
            return None
        if (receipt.get('name')!=name or receipt.get('version')!=final.name
                or receipt.get('upstream_version')!=manifest['version']
                or str(receipt.get('artifact_sha256','')).lower()!=manifest['sha256'].lower()):
            return None
        expected_hash=receipt.get('hash')
        if not isinstance(expected_hash,str) or not re.fullmatch('[a-fA-F0-9]{64}',expected_hash):
            return None
        root=final.resolve(strict=True)
        path=Path(receipt['path']).resolve(strict=True)
        if not path.is_file() or not path.is_relative_to(root):
            return None
        if fingerprint(path).lower()!=expected_hash.lower():
            return None
        if check_tool(name,str(path)).status!='ready':
            return None
        companion=receipt.get('ffprobe')
        if companion:
            companion_path=Path(companion).resolve(strict=True)
            if not companion_path.is_file() or not companion_path.is_relative_to(root):
                return None
        return receipt
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        return None


def _save_tool_activation(store,name,version,receipt):
    """Commit active-version metadata and runtime path selection as one transaction."""
    with store.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute("SELECT value FROM settings WHERE key='tool_paths'").fetchone()
        overrides=json.loads(row['value']) if row else {}
        overrides[name]=receipt['path']
        if name=='ffmpeg':
            if receipt.get('ffprobe'):
                overrides['ffprobe']=receipt['ffprobe']
            else:
                overrides.pop('ffprobe',None)
        encoded=canonical(checked_payload(overrides))
        conn.execute('UPDATE tool_versions SET active=0 WHERE name=?',(name,))
        conn.execute('INSERT OR REPLACE INTO tool_versions VALUES(?,?,?,?,1)',
                     (name,version,receipt['path'],receipt['hash']))
        conn.execute("INSERT INTO settings(key,value) VALUES('tool_paths',?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value",(encoded,))
    # Workers in this process must use the newly committed path immediately.
    configure_tools(overrides)


def _version_directory(store,name,version,row_path=None):
    """Resolve a version folder only inside the app-managed tools root."""
    if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+',name)
            or not isinstance(version,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+',version)
            or version in {'.','..'}):
        return None
    tools_root=store.path.parent/'tools'
    root=tools_root/name
    if tools_root.is_symlink() or root.is_symlink():
        return None
    folder=root/version
    if folder.is_symlink():
        return None
    try:
        resolved_root=root.resolve(strict=False)
        resolved_folder=folder.resolve(strict=False)
        if resolved_folder.parent!=resolved_root:
            return None
        if row_path is not None:
            executable=Path(row_path).resolve(strict=False)
            if executable==resolved_folder or resolved_folder not in executable.parents:
                return None
    except (OSError,RuntimeError,ValueError):
        return None
    return folder


def _path_is_within(path,folder):
    try:
        candidate=Path(path).resolve(strict=False)
        boundary=Path(folder).resolve(strict=False)
        return candidate==boundary or boundary in candidate.parents
    except (OSError,RuntimeError,ValueError,TypeError):
        return False


def _job_tool_paths(payload):
    if not isinstance(payload,dict):
        raise ValueError('Job payload is not an object')
    tools=payload.get('_tools',{})
    if not isinstance(tools,dict):
        raise ValueError('Job tool snapshot is not an object')
    paths=[]
    for value in tools.values():
        if value is None:
            continue
        if not isinstance(value,str) or not value:
            raise ValueError('Job tool path is invalid')
        paths.append(value)
    return paths


def managed_tool_versions(store):
    """List app-managed versions and explain why each one is or is not removable."""
    with store.connect() as conn:
        rows=[dict(row) for row in conn.execute(
            'SELECT name,version,path,hash,active FROM tool_versions ORDER BY name,version')]
        setting=conn.execute("SELECT value FROM settings WHERE key='tool_paths'").fetchone()
        configured=json.loads(setting['value']) if setting else {}
        jobs=[dict(row) for row in conn.execute(
            "SELECT id,state,payload FROM jobs WHERE state!='succeeded'")]
    if not isinstance(configured,dict):
        configured={}
        invalid_configuration=True
    else:
        invalid_configuration=False
    parsed_jobs=[]
    unknown_jobs=[]
    for job in jobs:
        try:
            parsed_jobs.append((job['id'],_job_tool_paths(json.loads(job['payload']))))
        except (ValueError,TypeError,json.JSONDecodeError):
            unknown_jobs.append(job['id'])
    result=[]
    for row in rows:
        folder=_version_directory(store,row['name'],row['version'],row['path'])
        reasons=[]
        if folder is None:
            reasons.append('Đường dẫn quản lý không hợp lệ; chặn gỡ an toàn')
        if row['active']:
            reasons.append('Phiên bản đang active')
        if invalid_configuration:
            reasons.append('Cấu hình tool_paths không đọc được')
        configured_paths=[value for value in configured.values() if isinstance(value,str)]
        if folder is not None and any(_path_is_within(path,folder) for path in configured_paths):
            reasons.append('Đang được cấu hình làm tool hiện tại')
        held=[]
        if folder is not None:
            for job_id,paths in parsed_jobs:
                if any(_path_is_within(path,folder) for path in paths):
                    held.append(job_id)
        if unknown_jobs:
            held.extend(unknown_jobs)
            reasons.append('Có job snapshot lỗi; fail-closed')
        if held:
            reasons.append('Được giữ bởi job: '+', '.join(sorted(set(held))[:4]))
        result.append({
            **row,
            'folder':str(folder) if folder is not None else None,
            'job_ids':sorted(set(held)),
            'in_use':bool(reasons),
            'reason':'; '.join(reasons) if reasons else 'Có thể gỡ an toàn',
        })
    return result


def remove_tool_version(store,name,version):
    """Remove one inactive app-managed version only when no runnable/retryable job leases it."""
    with store.connect() as conn:
        # Store.submit/submit_many use the same writer lock while acquiring a
        # snapshot. This closes the race between checking leases and new jobs.
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute(
            'SELECT name,version,path,hash,active FROM tool_versions WHERE name=? AND version=?',
            (name,version)).fetchone()
        if not row:
            raise ValueError('Managed tool version was not found')
        folder=_version_directory(store,name,version,row['path'])
        if folder is None:
            raise ValueError('Refusing to remove a path outside the app-managed version root')
        if row['active']:
            raise ValueError('Cannot remove the active tool version')
        setting=conn.execute("SELECT value FROM settings WHERE key='tool_paths'").fetchone()
        configured=json.loads(setting['value']) if setting else {}
        if not isinstance(configured,dict):
            raise ValueError('Tool path configuration is invalid; refusing cleanup')
        if any(isinstance(path,str) and _path_is_within(path,folder)
               for path in configured.values()):
            raise ValueError('Tool version is still selected in current tool paths')
        held=[]
        for job in conn.execute("SELECT id,state,payload FROM jobs WHERE state!='succeeded'"):
            try:
                paths=_job_tool_paths(json.loads(job['payload']))
            except (ValueError,TypeError,json.JSONDecodeError) as exc:
                raise ValueError(
                    f"Cannot verify tool leases because job {job['id']} has an invalid snapshot"
                ) from exc
            if any(_path_is_within(path,folder) for path in paths):
                held.append(job['id'])
        if held:
            raise ValueError(
                'Tool version is held by pending/running/retryable jobs: '+', '.join(held[:8])
            )
        if folder.exists():
            if folder.is_symlink() or not folder.is_dir():
                raise ValueError('Managed version folder is not a safe directory')
            # Reject unexpected symlinks rather than risk deleting through a
            # tampered folder tree. Installed ZIPs already reject such entries.
            for root,dirs,files in os.walk(folder,followlinks=False):
                if any((Path(root)/item).is_symlink() for item in [*dirs,*files]):
                    raise ValueError('Managed version contains a symlink; refusing cleanup')
            shutil.rmtree(folder)
        deleted=conn.execute(
            'DELETE FROM tool_versions WHERE name=? AND version=? AND active=0',
            (name,version))
        if deleted.rowcount!=1:
            raise RuntimeError('Managed tool version changed during cleanup')
    return {'name':name,'version':version,'folder':str(folder),'directory_removed':True}


def install(store,manifest,progress=lambda p:None,cancel=None,fetch=download_verified):
    if not isinstance(manifest,dict):
        raise ValueError('Tool manifest must be an object')
    name,version=manifest.get('name'),manifest.get('version')
    executable=manifest.get('executable')
    url,sha256=manifest.get('url'),manifest.get('sha256')
    if (not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9_.-]+',name)
            or not isinstance(version,str) or not re.fullmatch('[A-Za-z0-9_.-]+',version)):
        raise ValueError('Invalid tool/version')
    if (not isinstance(executable,str) or not re.fullmatch('[A-Za-z0-9_.-]+',executable)
            or executable in {'.','..'}):
        raise ValueError('Executable must be a simple filename')
    if not isinstance(url,str) or not url.startswith('https://') or not isinstance(sha256,str) or not re.fullmatch('[a-fA-F0-9]{64}',sha256):
        raise ValueError('HTTPS and SHA256 are required')
    _check_cancel(cancel)
    root=store.path.parent/'tools'/name
    root.mkdir(parents=True,exist_ok=True)
    final=root/version
    receipt=None
    if final.exists() or final.is_symlink():
        receipt=_verified_receipt(name,final,manifest)
        if receipt is None:
            # Never overwrite a corrupt/old folder that immutable jobs may still reference.
            version=version+'.repair.'+str(time.time_ns())
            final=root/version
    if receipt is None:
        _check_cancel(cancel)
        with tempfile.TemporaryDirectory(prefix='.staging-',dir=root) as temp:
            stage=Path(temp)
            archive=stage/'artifact'
            fetch(url,archive,sha256,progress,cancel)
            _check_cancel(cancel)
            if fingerprint(archive).lower()!=sha256.lower():
                raise ValueError('Artifact SHA256 mismatch')
            unpack=stage/'unpacked'
            unpack.mkdir()
            if manifest.get('archive')=='zip':
                extract_zip(archive,unpack)
            else:
                shutil.copyfile(archive,unpack/executable)
            _check_cancel(cancel)
            matches=list(unpack.rglob(executable))
            if len(matches)!=1:
                raise ValueError('Tool executable is missing or ambiguous')
            target_stage=matches[0]
            if os.name!='nt':
                target_stage.chmod(target_stage.stat().st_mode|0o100)
            status=check_tool(name,str(target_stage))
            if status.status!='ready':
                raise ValueError('Downloaded tool failed its startup/version check')
            _check_cancel(cancel)
            relative=target_stage.relative_to(unpack)
            os.rename(unpack,final)
            target=final/relative
            receipt={
                'name':name,
                'version':version,
                'upstream_version':manifest['version'],
                'path':str(target),
                'hash':fingerprint(target),
                'artifact_sha256':sha256.lower(),
            }
            if name=='ffmpeg':
                companion=target.parent/('ffprobe.exe' if os.name=='nt' else 'ffprobe')
                if companion.is_file():
                    receipt['ffprobe']=str(companion)
            atomic_json(final/'receipt.json',receipt)
    _check_cancel(cancel)
    _save_tool_activation(store,name,version,receipt)
    progress(1)
    return receipt


def rollback(store,name,version):
    with store.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT * FROM tool_versions WHERE name=? AND version=?',(name,version)).fetchone()
        if not row:
            raise ValueError('Rollback version unavailable/modified')
        path=Path(row['path'])
        try:
            intact=path.is_file() and fingerprint(path).lower()==str(row['hash']).lower()
        except OSError:
            intact=False
        if not intact:
            raise ValueError('Rollback version unavailable/modified')
        selection_row=conn.execute("SELECT value FROM settings WHERE key='tool_paths'").fetchone()
        overrides=json.loads(selection_row['value']) if selection_row else {}
        overrides[name]=str(path.resolve())
        if name=='ffmpeg':
            companion=path.with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
            if companion.is_file():
                overrides['ffprobe']=str(companion.resolve())
            else:
                overrides.pop('ffprobe',None)
        encoded=canonical(checked_payload(overrides))
        conn.execute('UPDATE tool_versions SET active=(version=?) WHERE name=?',(version,name))
        conn.execute("INSERT INTO settings(key,value) VALUES('tool_paths',?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value",(encoded,))
    configure_tools(overrides)

def resolve_manifest(name):
    if name=='node' and os.name=='nt':
        with urlopen('https://nodejs.org/dist/index.json',timeout=20) as response:releases=json.load(response)
        release=next(r['version'] for r in releases if r.get('lts') and int(r['version'].split('.')[0].lstrip('v'))>=20)
        artifact=f'node-{release}-win-x64.zip';base=f'https://nodejs.org/dist/{release}/'
        with urlopen(base+'SHASUMS256.txt',timeout=20) as response:lines=response.read(200000).decode().splitlines()
        sha=next((line.split()[0] for line in lines if line.split()[-1]==artifact),None)
        if not sha:raise ValueError('Official Node checksum missing')
        return {'name':'node','version':release,'url':base+artifact,'sha256':sha,'archive':'zip','executable':'node.exe'}
    if name=='ffmpeg' and os.name=='nt':
        url='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
        with urlopen(url+'.sha256',timeout=20) as response:text=response.read(4096).decode()
        sha=re.search(r'\b[a-fA-F0-9]{64}\b',text)
        if not sha:raise ValueError('Could not verify the official build checksum manifest')
        return {'name':'ffmpeg','version':sha.group()[:16],'url':url,'sha256':sha.group(),'archive':'zip','executable':'ffmpeg.exe'}
    if name=='yt-dlp':
        from importlib.metadata import version
        release=version('yt-dlp');asset='yt-dlp.exe' if os.name=='nt' else 'yt-dlp'
        base=f'https://github.com/yt-dlp/yt-dlp/releases/download/{release}/'
        with urlopen(base+'SHA2-256SUMS',timeout=20) as response:lines=response.read(100000).decode().splitlines()
        sha=next((line.split()[0] for line in lines if line.split()[-1].lstrip('*')==asset),None)
        if not sha:raise ValueError('Artifact checksum missing')
        return {'name':name,'version':release,'url':base+asset,'sha256':sha,'executable':asset}
    raise ValueError('Thành phần gói kèm hoặc hệ thống; chọn bản sẵn có hay manifest đã xác minh. Không tự tải artifact không có checksum.')


def install_chrome(store,progress=lambda n:None,cancel=None):
    if os.name!='nt':raise PermissionError('Chrome installer proof is Windows-only')
    with tempfile.TemporaryDirectory(prefix='chrome-',dir=store.path.parent) as folder:
        target=Path(folder)/'chrome-installer.exe'
        with urlopen('https://dl.google.com/chrome/install/latest/chrome_installer.exe',timeout=30) as response,target.open('xb') as stream:
            shutil.copyfileobj(response,stream)
        script="""$s=Get-AuthenticodeSignature -LiteralPath $env:FONESI_INSTALLER_PATH; if($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Google (LLC|Inc)'){exit 2}"""
        env={**os.environ,'FONESI_INSTALLER_PATH':str(target)}
        result=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',script],env=env,capture_output=True,timeout=30)
        if result.returncode:raise PermissionError('Chrome installer signature/publisher not verified')
        if cancel and cancel.is_set():raise RuntimeError('Canceled')
        subprocess.run([str(target)],check=True,timeout=600)
    status=next(t for t in scan_tools() if t.name=='Google Chrome')
    if status.status!='ready':raise RuntimeError('Installer đã mở; cần hoàn thành bước Windows rồi quét lại')
    progress(1);return status.to_dict()
