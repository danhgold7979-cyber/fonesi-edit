"""One-shot Windows cleanup of live completed staging, never final outputs."""
from contextlib import ExitStack
from hashlib import sha256
import os
from .filesystem import PublicationError,PublicationUnknown,_plain,safe_name
from .windows_cleanup import NativeObject,DeleteCapability,GENERIC_READ,SHARE_READ,SHARE_DELETE


def _content(fd,receipt):
    before=os.fstat(fd)
    if _plain(before)!=receipt.file_identity or before.st_size!=receipt.size:
        raise PublicationUnknown('Cleanup output identity/size differs from receipt')
    os.lseek(fd,0,os.SEEK_SET);digest=sha256();size=0
    while block:=os.read(fd,min(1024*1024,receipt.size+1-size)):
        digest.update(block);size+=len(block)
        if size>receipt.size:break
    after=os.fstat(fd)
    if (size!=receipt.size or digest.hexdigest()!=receipt.sha256 or
        (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)):
        raise PublicationUnknown('Cleanup final content differs from committed validation')


def cleanup_completed_stage(destination,receipt,final_name,*,before_effect):
    """Internal live-owner call only. On ANY failure retire surrounding session.

    No restart receipt, source file or caller-created path grants ownership. Native
    capability lifetime protects actual objects; names are checked against still
    live originals. Unsupported platforms retain staging; there is no unlink.
    """
    if os.name!='nt':raise PublicationError('Safe cleanup unavailable on this platform; staging retained')
    destination._receipt(receipt);safe_name(final_name)
    directory=destination._directory_anchors.get(receipt.directory)
    if directory is None or directory.fd is None or _plain(os.fstat(directory.fd),True)!=receipt.directory_identity:
        raise PublicationUnknown('No original live stage directory capability')
    original=destination._anchors[receipt.directory]
    stage=destination.root/receipt.directory;final=destination.root/final_name
    with ExitStack() as stack:
        file_cap=DeleteCapability(stage/'payload',original.fd,original.close,
                                  parent_identity=receipt.directory_identity)
        stack.callback(file_cap.close)
        if file_cap.identity!=receipt.file_identity:raise PublicationUnknown('Cleanup stage incarnation changed')
        final_bridge=stack.enter_context(NativeObject(final,access=GENERIC_READ,share=SHARE_READ|SHARE_DELETE))
        if final_bridge.identity!=receipt.file_identity:raise PublicationUnknown('Final is not original staged object')
        _content(file_cap.fd,receipt)
        def file_authority():
            before_effect();destination._check()
            if _plain(final.lstat())!=receipt.file_identity:raise PublicationUnknown('Final name changed before cleanup')
        file_cap.mark(before_effect=file_authority)
        file_cap.close() # Delete only the staged hardlink; bridge retains incarnation.
        final_pin=stack.enter_context(NativeObject(final,access=GENERIC_READ,share=SHARE_READ))
        if final_pin.identity!=final_bridge.identity or final_pin.identity!=receipt.file_identity:
            raise PublicationUnknown('Final changed during cleanup handoff')
        final_bridge.close()
        if os.path.lexists(stage/'payload'):raise PublicationUnknown('Stage link retirement not observed')
        _content(final_pin.fd,receipt)
        with DeleteCapability(stage,directory.fd,directory.close,
                              parent_identity=destination.identity,directory=True) as dir_cap:
            if dir_cap.identity!=receipt.directory_identity:raise PublicationUnknown('Cleanup directory incarnation changed')
            def directory_authority():
                before_effect();destination._check()
                if _plain(final.lstat())!=receipt.file_identity:raise PublicationUnknown('Final name changed before directory cleanup')
                _content(final_pin.fd,receipt)
                before_effect() # Recheck authority after potentially slow readback.
            dir_cap.mark(before_effect=directory_authority)
        if os.path.lexists(stage):raise PublicationUnknown('Stage directory retirement not observed')
        if _plain(final.lstat())!=receipt.file_identity:raise PublicationUnknown('Final changed after cleanup')
        _content(final_pin.fd,receipt)
        before_effect()
    return final
