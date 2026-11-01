"""Actual native capability gates; never simulated as Windows cleanup evidence."""
import os
from pathlib import Path
import pytest
from fonesi_edit.artifacts.filesystem import PublicationError,PublicationUnknown
from fonesi_edit.artifacts.windows_cleanup import NativeObject,DeleteCapability,DELETE,READ_ATTRIBUTES,SHARE_READ

windows=pytest.mark.skipif(os.name!='nt',reason='Actual Windows object-bound deletion capability required')


def parent_id(path):
    info=path.parent.stat();return info.st_dev,info.st_ino


def test_nonwindows_cleanup_fails_closed(tmp_path):
    if os.name=='nt':pytest.skip('Non-Windows unsupported-capability branch')
    path=tmp_path/'owned';path.write_bytes(b'owned')
    with pytest.raises(PublicationError):NativeObject(path)
    assert path.read_bytes()==b'owned'


class Original:
    def __init__(self,path):self.fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0))
    def close(self):
        if self.fd is not None:
            fd=self.fd;self.fd=None;os.close(fd)


@windows
def test_native_stage_link_only_removed_final_same_bytes_survives(tmp_path):
    stage=tmp_path/'payload';stage.write_bytes(b'owned output');final=tmp_path/'final.mp4';os.link(stage,final)
    original=Original(stage);identity=(os.fstat(original.fd).st_dev,os.fstat(original.fd).st_ino)
    try:
        with DeleteCapability(stage,original.fd,original.close,parent_identity=parent_id(stage)) as capability:
            assert capability.identity==identity
            assert os.read(capability.fd,100)==b'owned output'
            capability.mark(before_effect=lambda:None)
        assert not stage.exists() and final.read_bytes()==b'owned output'
        assert (final.stat().st_dev,final.stat().st_ino)==identity
    finally:original.close()


@windows
def test_native_file_handoff_replacement_never_deletes_foreign(tmp_path):
    path=tmp_path/'payload';path.write_bytes(b'owned');original=Original(path)
    def replace():
        original.close();path.rename(tmp_path/'original');path.write_bytes(b'FOREIGN')
    try:
        with pytest.raises(PublicationUnknown):DeleteCapability(path,original.fd,replace,parent_identity=parent_id(path))
        assert path.read_bytes()==b'FOREIGN' and (tmp_path/'original').read_bytes()==b'owned'
    finally:original.close()


@windows
def test_native_directory_handoff_replacement_never_deletes_foreign(tmp_path):
    path=tmp_path/'stage';path.mkdir()
    with NativeObject(path,directory=True) as original:
        def replace():
            original.close();path.rename(tmp_path/'original');path.mkdir();(path/'foreign').write_bytes(b'foreign')
        with pytest.raises(PublicationUnknown):DeleteCapability(path,original.fd,replace,parent_identity=parent_id(path),directory=True)
    assert (path/'foreign').read_bytes()==b'foreign' and (tmp_path/'original').is_dir()


@windows
def test_native_empty_directory_removal_and_nonempty_foreign_preserved(tmp_path):
    empty=tmp_path/'empty';empty.mkdir()
    with NativeObject(empty,directory=True) as original:
        with DeleteCapability(empty,original.fd,original.close,parent_identity=parent_id(empty),directory=True) as capability:
            capability.mark(before_effect=lambda:None)
    assert not empty.exists()
    nonempty=tmp_path/'nonempty';nonempty.mkdir();(nonempty/'foreign').write_bytes(b'foreign')
    with NativeObject(nonempty,directory=True) as original:
        with DeleteCapability(nonempty,original.fd,original.close,parent_identity=parent_id(nonempty),directory=True) as capability:
            with pytest.raises(OSError):capability.mark(before_effect=lambda:None)
    assert (nonempty/'foreign').read_bytes()==b'foreign'


@windows
def test_native_late_foreign_directory_child_prevents_removal(tmp_path):
    path=tmp_path/'stage';path.mkdir()
    with NativeObject(path,directory=True) as original:
        with DeleteCapability(path,original.fd,original.close,parent_identity=parent_id(path),directory=True) as capability:
            def arrive():(path/'foreign').write_bytes(b'late')
            with pytest.raises(OSError):capability.mark(before_effect=arrive)
    assert (path/'foreign').read_bytes()==b'late'


@windows
def test_native_authority_loss_before_disposition_has_no_delete(tmp_path):
    path=tmp_path/'payload';path.write_bytes(b'owned');original=Original(path)
    def lost():raise PublicationUnknown('lost epoch')
    try:
        with DeleteCapability(path,original.fd,original.close,parent_identity=parent_id(path)) as capability:
            with pytest.raises(PublicationUnknown):capability.mark(before_effect=lost)
            with pytest.raises(PublicationUnknown,match='replayed'):capability.mark(before_effect=lambda:None)
        assert path.read_bytes()==b'owned'
    finally:original.close()


@windows
def test_native_conflicting_delete_handle_fails_without_unlink(tmp_path):
    path=tmp_path/'payload';path.write_bytes(b'owned');original=Original(path);peers=[]
    def conflicting():
        original.close();peers.append(NativeObject(path,access=DELETE|READ_ATTRIBUTES,share=SHARE_READ))
    try:
        with pytest.raises(OSError):DeleteCapability(path,original.fd,conflicting,parent_identity=parent_id(path))
    finally:
        original.close()
        for peer in peers:peer.close()
    assert path.read_bytes()==b'owned'


@windows
def test_native_unmarked_capability_retirement_never_deletes(tmp_path):
    path=tmp_path/'payload';path.write_bytes(b'owned');original=Original(path)
    try:
        with DeleteCapability(path,original.fd,original.close,parent_identity=parent_id(path)):pass
        assert path.read_bytes()==b'owned'
    finally:original.close()


@windows
def test_native_capability_handle_count_plateau(tmp_path):
    import ctypes as C
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=C.c_void_p
    kernel.GetProcessHandleCount.argtypes=[C.c_void_p,C.POINTER(C.c_uint32)]
    kernel.GetProcessHandleCount.restype=C.c_int
    def count():
        value=C.c_uint32()
        assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(),C.byref(value))
        return value.value
    def cycle(index):
        path=tmp_path/('owned-'+str(index));path.write_bytes(b'owned');original=Original(path)
        try:
            with DeleteCapability(path,original.fd,original.close,parent_identity=parent_id(path)) as capability:
                assert not os.get_inheritable(capability.fd)
                capability.mark(before_effect=lambda:None)
            assert not path.exists()
        finally:original.close()
    cycle('warm');before=count()
    for index in range(20):cycle(index)
    assert count()<=before # Warm per-call leak gate, not cold-start handle attribution.


def test_authority_failure_consumes_mark_before_any_native_call():
    capability=DeleteCapability.__new__(DeleteCapability)
    capability.mark_attempted=False;capability.revoked=False
    capability.guard=lambda:None
    def lost():raise PublicationUnknown('lost authority')
    with pytest.raises(PublicationUnknown,match='lost authority'):capability.mark(before_effect=lost)
    assert capability.mark_attempted and capability.revoked
    with pytest.raises(PublicationUnknown,match='replayed'):capability.mark(before_effect=lambda:None)
