"""Retained-hardlink publication on a pinned local destination.

Receipts are internal coordinator records, never authority from untrusted project
JSON. This substrate does not implement the durable journal or mark jobs successful.
It never removes a final path, nor releases retained staging after publication.
A live opened staging anchor prevents inode recycling within this session. Restart
receipts alone are UNKNOWN until an incarnation-safe recovery capability exists.
"""
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
import uuid

class PublicationError(RuntimeError): pass
class PublicationConflict(PublicationError): pass
class PublicationUnknown(PublicationError): pass
class PublicationCanceled(PublicationError):
    def __init__(self,message,receipt=None):
        super().__init__(message)
        self.receipt=receipt


def _identity(info):
    if not info.st_ino:
        raise PublicationError('Filesystem lacks usable physical file identity')
    return info.st_dev, info.st_ino


def _plain(info, directory=False):
    if (stat.S_ISLNK(info.st_mode) or
        getattr(info, 'st_file_attributes', 0) & 0x400 or
        not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        raise PublicationError('Symlink/reparse/nonregular publication path refused')
    return _identity(info)


def safe_name(value):
    """One Windows-compatible leaf; no normalization changes the requested name."""
    if not isinstance(value,str):raise PublicationError('Output filename must be text')
    try:units=len(value.encode('utf-16-le'))//2
    except UnicodeError as e:raise PublicationError('Invalid Unicode filename') from e
    if (not value or units>255 or
        value in {'.', '..'} or value[-1] in ' .' or
        any(ord(c) < 32 or c in '<>:"/\\|?*' for c in value) or
        re.fullmatch(r'(?i)(CON|CONIN\$|CONOUT\$|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])', value.split('.')[0].rstrip(' '))):
        raise PublicationError('Unsafe output filename')
    return value


@dataclass(frozen=True)
class StageOwnership:
    """Live exclusive-creation provenance only; never validation or publication."""
    root_identity: tuple[int, int]
    directory: str
    directory_identity: tuple[int, int]
    file_identity: tuple[int, int]


@dataclass(frozen=True)
class StageReceipt:
    root_identity: tuple[int, int]
    directory: str
    directory_identity: tuple[int, int]
    file_identity: tuple[int, int]
    size: int
    sha256: str


def _pin_windows_directory(path):
    """No-delete share pins ancestors against rename/junction replacement."""
    import ctypes
    from ctypes import wintypes as w
    api=ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    api.CreateFileW.restype=w.HANDLE
    api.CloseHandle.argtypes=[w.HANDLE];api.CloseHandle.restype=w.BOOL
    handle=api.CreateFileW(str(path),0x80,0x1|0x2,None,3,0x02000000|0x00200000,None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    def close():
        if not api.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())
    return close


class _OwnedFD:
    """Close-once transferable descriptor; no raw close callback survives handoff."""
    def __init__(self,fd):self.fd=fd
    def close(self):
        if self.fd is not None:
            fd=self.fd;self.fd=None
            os.close(fd)


class Destination:
    """One existing explicit local root. Use as a context manager, coordinator only."""
    def __init__(self, root):
        raw=Path(root)
        if not raw.is_absolute() or '..' in raw.parts:
            raise PublicationError('Explicit absolute destination required')
        if os.name=='nt' and str(raw).startswith('\\\\'):
            raise PublicationError('Network destination needs separate durability capability')
        self.root=raw
        self._stack=ExitStack(); self.fd=None; self.closed=True; self._anchors={}; self._directory_anchors={}; self._created={}; self._attempted_directories=set()
        try:
            for part in [*reversed(raw.parents),raw]:
                if os.name=='nt': self._stack.callback(_pin_windows_directory(part))
                _plain(part.lstat(), True)
            if os.name!='nt':
                self.fd=os.open(raw,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                self._stack.callback(os.close,self.fd)
                self.identity=_plain(os.fstat(self.fd),True)
            else: self.identity=_plain(raw.lstat(),True)
            self.closed=False;self._check()
        except BaseException:
            self._stack.close();raise

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def close(self):
        self.closed=True;self._stack.close();self._anchors.clear();self._directory_anchors.clear();self._created.clear();self._attempted_directories.clear()
    def _check(self):
        if self.closed: raise PublicationError('Destination is closed')
        if _plain(self.root.lstat(),True)!=self.identity:
            raise PublicationUnknown('Destination identity changed; do not reuse paths')
    def _open(self,name,flags,mode=0o600,*,base_fd=None):
        if self.fd is not None:
            return os.open(name,flags|os.O_NOFOLLOW,mode,dir_fd=self.fd if base_fd is None else base_fd)
        return os.open(self.root/name,flags|getattr(os,'O_BINARY',0),mode)
    def _stat(self,name,base_fd=None):
        return os.stat(name,dir_fd=self.fd if base_fd is None else base_fd,follow_symlinks=False) if self.fd is not None else (self.root/name).lstat()

    def create_stage(self, data: bytes):
        """Bounded small-sidecar writer; no existing file is opened for writing."""
        if type(data) is not bytes or len(data)>32*1024*1024:
            raise PublicationError('Stage bytes must be bounded to32MiB')
        return self._create_stage_chunks((data,))

    def copy_stage(self, source, *, cancel=lambda:False):
        """Copy a regular source incrementally, retaining ownership and original bytes.

        Reading is bounded by opened source size+1, not a moving EOF. Cancellation
        occurs at chunk boundaries, not inside blocking OS I/O. Failures retain the
        exclusively created staging directory for later journal-aware reconciliation.
        """
        if cancel():raise PublicationCanceled('Staging copy canceled before opening source')
        source=Path(source).absolute()
        named_before=source.lstat();_plain(named_before)
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
        fd=os.open(source,flags)
        try:
            before=os.fstat(fd);_plain(before)
            if _identity(before)!=_identity(named_before):raise PublicationUnknown('Source identity changed before copy')
            def signature(info):return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns
            def chunks():
                total=0
                while True:
                    if cancel():raise PublicationCanceled('Staging copy canceled; owned partial stage retained')
                    block=os.read(fd,min(1024*1024,before.st_size+1-total))
                    if not block:break
                    total+=len(block)
                    if total>before.st_size:raise PublicationUnknown('Source grew during staging copy')
                    yield block
                after=os.fstat(fd);named_after=source.lstat()
                if (total!=before.st_size or signature(before)!=signature(after) or
                    signature(named_before)!=signature(named_after) or _identity(after)!=_identity(named_after)):
                    raise PublicationUnknown('Source changed during staging copy')
                if cancel():raise PublicationCanceled('Staging copy canceled; owned stage retained')
            receipt=self._create_stage_chunks(chunks())
            if cancel():raise PublicationCanceled('Staging copy canceled; complete owned stage retained',receipt)
            return receipt
        finally:os.close(fd)

    def _create_stage_chunks(self, chunks):
        self._check();directory='.fonesi-stage-'+str(uuid.uuid4())
        if self.fd is not None:os.mkdir(directory,0o700,dir_fd=self.fd)
        else:os.mkdir(self.root/directory,0o700)
        self._attempted_directories.add(directory)
        # Retain on any fault: journal-aware cleanup is a separate operation.
        directory_id=_plain(self._stat(directory),True)
        digest=sha256();size=0
        with self._stage_directory(directory,directory_id) as stage_fd:
            if os.name=='nt':
                from .windows_cleanup import NativeObject
                directory_anchor=NativeObject(self.root/directory,directory=True)
                self._stack.callback(directory_anchor.close)
                if directory_anchor.identity!=directory_id:
                    raise PublicationUnknown('Original stage directory changed before retention')
                self._directory_anchors[directory]=directory_anchor
            leaf="payload" if stage_fd is not None else directory+"/payload"
            fd=self._open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL,base_fd=stage_fd)
            with os.fdopen(fd,'wb') as out:
                # Preserve exclusive creation BEFORE a producer/cancel callback can fail.
                anchor=_OwnedFD(os.dup(out.fileno()))
                self._stack.callback(anchor.close)
                self._anchors[directory]=anchor
                original_id=_plain(os.fstat(out.fileno()))
                self._created[directory]=StageOwnership(self.identity,directory,directory_id,original_id)
                for block in chunks:
                    if type(block) is not bytes:raise PublicationError('Internal stage chunk must be bytes')
                    if out.write(block)!=len(block):raise PublicationError('Incomplete staging write')
                    digest.update(block);size+=len(block)
                out.flush();os.fsync(out.fileno())
                info=os.fstat(out.fileno());file_id=_plain(info)
                if file_id!=original_id:raise PublicationUnknown('Creating writer identity changed')
            if stage_fd is not None:os.fsync(stage_fd)
        self._flush_root();self._check()
        return StageReceipt(self.identity,directory,directory_id,file_id,size,digest.hexdigest())

    @contextmanager
    def _stage_directory(self,name,expected):
        with ExitStack() as stack:
            stage_fd=None
            if os.name=='nt':stack.callback(_pin_windows_directory(self.root/name))
            else:
                stage_fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=self.fd)
                stack.callback(os.close,stage_fd)
                if _plain(os.fstat(stage_fd),True)!=expected:
                    raise PublicationUnknown('Staging handle identity changed')
            if _plain(self._stat(name),True)!=expected:
                raise PublicationUnknown('Retained staging directory identity changed')
            yield stage_fd
            if _plain(self._stat(name),True)!=expected:
                raise PublicationUnknown('Retained staging path changed during operation')

    def _verify(self,receipt,name,base_fd=None):
        before=self._stat(name,base_fd);_plain(before)
        fd=self._open(name,os.O_RDONLY,base_fd=base_fd)
        try:
            current=os.fstat(fd)
            if _plain(current)!=receipt.file_identity or _identity(before)!=receipt.file_identity:
                raise PublicationConflict('File is not the retained physical staging object')
            if current.st_size!=receipt.size:
                raise PublicationUnknown('Staging size does not match validation receipt')
            digest=sha256();size=0
            while block:=os.read(fd,min(1024*1024,receipt.size+1-size)):
                digest.update(block);size+=len(block)
                if size>receipt.size:break
            after=os.fstat(fd)
            if (size!=receipt.size or digest.hexdigest()!=receipt.sha256 or
                (current.st_size,current.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or
                _plain(self._stat(name,base_fd))!=receipt.file_identity):
                raise PublicationUnknown('Staged/published content changed or failed validation')
        finally:os.close(fd)

    def _receipt(self,r):
        self._check()
        if (not isinstance(r,StageReceipt) or r.root_identity!=self.identity or
            not re.fullmatch(r'\.fonesi-stage-[0-9a-f-]{36}',r.directory) or
            not re.fullmatch(r'\.fonesi-stage-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',r.directory) or
            type(r.size) is not int or not 0<=r.size<=2**63-1 or not re.fullmatch('[0-9a-f]{64}',r.sha256)):
            raise PublicationError('Invalid internal staging receipt')
        anchor=self._anchors.get(r.directory)
        if anchor is None or anchor.fd is None or _plain(os.fstat(anchor.fd))!=r.file_identity:
            raise PublicationUnknown('No surviving live owned anchor; persisted inode may be recycled. Restart reconciliation requires an incarnation-safe capability not yet implemented')

    def verify_published(self,receipt,name):
        """Live-session verification only; persisted receipt alone is always UNKNOWN."""
        self._receipt(receipt);safe_name(name)
        try:
            with self._stage_directory(receipt.directory,receipt.directory_identity) as stage_fd:
                self._verify(receipt,'payload' if stage_fd is not None else receipt.directory+'/payload',stage_fd)
                self._verify(receipt,name)
                self._check()
        except FileNotFoundError as e:
            raise PublicationUnknown('Retained staging/final missing; publication ownership unproven') from e

    def publish(self,receipt,name,*,before_link=lambda:None):
        """Call only after durable publication claim. Collision never means success."""
        self._receipt(receipt);safe_name(name)
        with self._stage_directory(receipt.directory,receipt.directory_identity) as stage_fd:
            source='payload' if stage_fd is not None else receipt.directory+'/payload'
            self._verify(receipt,source,stage_fd)
            self._check()
            before_link() # coordinator authority rechecked after slow readback
            try:
                if self.fd is not None:
                    os.link(source,name,src_dir_fd=stage_fd,dst_dir_fd=self.fd,follow_symlinks=False)
                else:os.link(self.root/source,self.root/name,follow_symlinks=False)
            except FileExistsError as e:
                raise PublicationConflict('Final destination already exists; left untouched') from e
            except OSError as e:
                raise PublicationError('No-replace hardlink unavailable; no weaker fallback') from e
            self._flush_root()
            self.verify_published(receipt,name)
        return self.root/name

    def _flush_root(self):
        if self.fd is not None:os.fsync(self.fd)
        # Windows has no portable directory fsync here. Process-crash evidence is
        # separate from power-loss durability; never advertise the latter.
