"""Windows-only object-bound deletion capability; no pathname deletion fallback.

Only private coordinator-created staging may be passed by the live owner. Native
handles use OPEN_EXISTING and OPEN_REPARSE_POINT; no create/ACL/privilege changes.
A caller must prove required-set completion, worker quiescence and final hardlink
preservation before marking. Failed/uncertain operations are not retried.
"""
from contextlib import ExitStack
import ctypes as C
import os
from pathlib import Path

from .filesystem import PublicationError,PublicationUnknown,_plain,Destination,safe_name

READ_ATTRIBUTES=0x80
GENERIC_READ=0x80000000
DELETE=0x10000
SHARE_READ=1
SHARE_WRITE=2
SHARE_DELETE=4


def _api():
    if os.name!='nt':raise PublicationError('Object-bound cleanup requires verified Windows capability; stage retained')
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[C.c_wchar_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p]
    kernel.CreateFileW.restype=C.c_void_p
    kernel.CloseHandle.argtypes=[C.c_void_p];kernel.CloseHandle.restype=C.c_int
    kernel.SetFileInformationByHandle.argtypes=[C.c_void_p,C.c_int,C.c_void_p,C.c_uint32]
    kernel.SetFileInformationByHandle.restype=C.c_int
    return kernel


class NativeObject:
    """One noninherited HANDLE transferred exactly once into a CRT descriptor."""
    def __init__(self,path,*,access=READ_ATTRIBUTES,share=SHARE_READ|SHARE_WRITE,directory=False):
        self.fd=None;self.directory=directory;self.path=Path(path)
        if not self.path.is_absolute() or '..' in self.path.parts or str(self.path).startswith('\\\\'):
            raise PublicationError('Explicit local cleanup path required')
        safe_name(self.path.name)
        self.kernel=_api()
        flags=0x00200000|(0x02000000 if directory else 0) # OPEN_REPARSE_POINT/BACKUP_SEMANTICS
        handle=self.kernel.CreateFileW(str(self.path),access,share,None,3,flags,None)
        if handle==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
        import msvcrt
        try:self.fd=msvcrt.open_osfhandle(handle,os.O_RDONLY|os.O_BINARY|getattr(os,'O_NOINHERIT',0))
        except BaseException:
            if not self.kernel.CloseHandle(handle):raise C.WinError(C.get_last_error())
            raise
        try:self.identity=_plain(os.fstat(self.fd),directory)
        except BaseException:self.close();raise

    def close(self):
        if self.fd is not None:
            fd=self.fd;self.fd=None
            os.close(fd) # Never retry an uncertain close or double-close a recycled FD.
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


class DeleteCapability:
    """Continuous original→share-delete bridge→deny-write/delete final handle.

    release_original is a trusted internal ownership transfer, not project input.
    The bridge stays live until the final delete handle has been acquired/checked.
    Any failed handoff loses the old capability; caller must retire the session.
    """
    def __init__(self,path,original_fd,release_original,*,parent_identity,directory=False):
        self._stack=ExitStack();self.closed=False;self.mark_attempted=False;self.revoked=False
        self.path=Path(path);self.directory=directory
        try:
            self.parent=self._stack.enter_context(Destination(self.path.parent))
            if self.parent.identity!=parent_identity:raise PublicationUnknown('Cleanup parent differs from original namespace')
            original=_plain(os.fstat(original_fd),directory)
            bridge=self._stack.enter_context(NativeObject(path,share=SHARE_READ|SHARE_WRITE|SHARE_DELETE,directory=directory))
            if bridge.identity!=original:raise PublicationUnknown('Cleanup bridge does not match live original object')
            release_original()
            self.target=self._stack.enter_context(NativeObject(path,access=DELETE|(READ_ATTRIBUTES if directory else GENERIC_READ),share=SHARE_READ,directory=directory))
            self.identity=self.target.identity
            if self.identity!=bridge.identity:raise PublicationUnknown('Cleanup target changed during handoff; no deletion')
            self.guard()
        except BaseException:self.close();raise

    @property
    def fd(self):
        if self.closed or self.target.fd is None:raise PublicationUnknown('Cleanup capability retired')
        return self.target.fd

    def guard(self):
        if self.revoked:raise PublicationUnknown('Cleanup capability permanently revoked')
        try:
            self.parent._check()
            if _plain(os.fstat(self.fd),self.directory)!=self.identity or _plain(self.path.lstat(),self.directory)!=self.identity:
                raise PublicationUnknown('Cleanup object/name identity changed')
        except BaseException:
            self.revoked=True
            raise

    def mark(self,*,before_effect):
        if self.mark_attempted:raise PublicationUnknown('Deletion outcome cannot be replayed')
        self.mark_attempted=True # Authority/continuity failure also consumes this attempt.
        try:self.guard();before_effect();self.guard()
        except BaseException:
            self.revoked=True
            raise
        import msvcrt
        # FILE_DISPOSITION_INFO.DeleteFile is BOOLEAN (one byte), not Win32 BOOL.
        disposition=C.c_ubyte(1)
        if not self.target.kernel.SetFileInformationByHandle(msvcrt.get_osfhandle(self.fd),4,C.byref(disposition),C.sizeof(disposition)):
            raise C.WinError(C.get_last_error())

    def close(self):
        if not self.closed:
            self.closed=True;self._stack.close() # target then bridge; no reopen/retry.
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
