from dataclasses import replace
import os
from pathlib import Path
import pytest
from fonesi_edit.artifacts.filesystem import Destination,PublicationError,PublicationConflict,PublicationUnknown,safe_name


def test_retained_link_and_reopen(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'validated bytes')
        final=dest.publish(receipt,'Kết quả 中文.bin')
        assert final.read_bytes()==b'validated bytes'
        assert os.path.samefile(final,tmp_path/receipt.directory/'payload')
    with Destination(tmp_path) as dest:
        with pytest.raises(PublicationUnknown,match='anchor'):dest.verify_published(receipt,final.name)
    assert (tmp_path/receipt.directory/'payload').exists()


def test_foreign_identical_never_adopted(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'identical')
        foreign=tmp_path/'output';foreign.write_bytes(b'identical');identity=foreign.stat().st_ino
        with pytest.raises(PublicationConflict):dest.publish(receipt,'output')
        with pytest.raises(PublicationConflict):dest.verify_published(receipt,'output')
        assert foreign.read_bytes()==b'identical' and foreign.stat().st_ino==identity


def test_missing_staging_never_adopts_own_final(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good');dest.publish(receipt,'output')
    (tmp_path/receipt.directory/'payload').unlink()
    with Destination(tmp_path) as dest:
        with pytest.raises(PublicationUnknown):dest.verify_published(receipt,'output')
        assert (tmp_path/'output').read_bytes()==b'good'


def test_corrupt_staging_not_published(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good');(tmp_path/receipt.directory/'payload').write_bytes(b'evil')
        with pytest.raises(PublicationUnknown):dest.publish(receipt,'output')
        assert not (tmp_path/'output').exists()


def test_replaced_staging_same_bytes_refused(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good');p=tmp_path/receipt.directory/'payload';
        try:p.rename(p.with_name('original'))
        except PermissionError:
            assert os.name=='nt' # live anchor denies deletion/rename on this target
            dest.publish(receipt,'output');return
        p.write_bytes(b'good')
        with pytest.raises(PublicationConflict):dest.publish(receipt,'output')
        assert not (tmp_path/'output').exists()


def test_collision_between_validation_and_link(tmp_path,monkeypatch):
    real=os.link
    def race(src,dst,**kwargs):
        (tmp_path/'output').write_bytes(b'foreign racer')
        return real(src,dst,**kwargs)
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good');monkeypatch.setattr(os,'link',race)
        with pytest.raises(PublicationConflict):dest.publish(receipt,'output')
        assert (tmp_path/'output').read_bytes()==b'foreign racer'


def test_hardlink_unsupported_never_falls_back(tmp_path,monkeypatch):
    def fail(*args,**kwargs):raise OSError('unsupported')
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good');monkeypatch.setattr(os,'link',fail)
        with pytest.raises(PublicationError,match='no weaker'):dest.publish(receipt,'output')
        assert not (tmp_path/'output').exists() and (tmp_path/receipt.directory/'payload').read_bytes()==b'good'


@pytest.mark.parametrize('name',['../source','a/b','a\\b','CON','nul.txt','COM1.mp4','LPT².log','file:stream','trailing.','trailing ','', 'a\x00b','CON .txt','CONIN$','CONOUT$','\ud800'])
def test_windows_leaf_rejected(name):
    with pytest.raises(PublicationError):safe_name(name)


def test_symlink_root_or_stage_refused(tmp_path):
    real=tmp_path/'real';real.mkdir();link=tmp_path/'alias'
    try:link.symlink_to(real,target_is_directory=True)
    except OSError:pytest.skip('Symlink creation unavailable')
    with pytest.raises(PublicationError):Destination(link)
    with Destination(real) as dest:
        receipt=dest.create_stage(b'good');stage=real/receipt.directory
        try:stage.rename(real/'retained')
        except PermissionError:
            assert os.name=='nt' # held file anchor may pin its directory tree
            return
        stage.symlink_to(real/'retained',target_is_directory=True)
        with pytest.raises((PublicationError,OSError)):dest.publish(receipt,'output')
        assert not (real/'output').exists()


def test_receipt_root_and_lifetime_guard(tmp_path):
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'good')
        with pytest.raises(PublicationError):dest.publish(replace(receipt,root_identity=(0,0)),'out')
    with pytest.raises(PublicationError):dest.publish(receipt,'out')


@pytest.mark.parametrize('published',[False,True])
def test_owned_child_kill_retains_physical_recovery_proof(tmp_path,published):
    import json,subprocess,sys,time
    from fonesi_edit.artifacts.filesystem import StageReceipt
    marker=tmp_path/'ready';record=tmp_path/'test-receipt.json'
    if not published:(tmp_path/'output').write_bytes(b'good')
    code=f'''from dataclasses import asdict
from pathlib import Path
import json,time
from fonesi_edit.artifacts.filesystem import Destination
with Destination({str(tmp_path)!r}) as d:
 r=d.create_stage(b'good')
 Path({str(record)!r}).write_text(json.dumps(asdict(r)))
 if {published!r}: d.publish(r,'output')
 Path({str(marker)!r}).write_text('READY')
 time.sleep(30)
'''
    child=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if child.poll() is not None:
                out,err=child.communicate();pytest.fail(f'Child exited before boundary: {out!r} {err!r}')
            if marker.exists() and marker.read_text()=='READY':break
            time.sleep(.01)
        else:pytest.fail('No owned child boundary reached')
        child.kill();child.wait(timeout=5)
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
        child.stdout.close();child.stderr.close()
    raw=json.loads(record.read_text())
    for key in ['root_identity','directory_identity','file_identity']:raw[key]=tuple(raw[key])
    receipt=StageReceipt(**raw)
    with Destination(tmp_path) as d:
        # A receipt without a surviving owned handle cannot prove incarnation.
        with pytest.raises(PublicationUnknown,match='anchor'):d.verify_published(receipt,'output')
    assert (tmp_path/'output').read_bytes()==b'good'


def test_root_namespace_change_never_writes_replacement(tmp_path):
    root=tmp_path/'destination';root.mkdir()
    with Destination(root) as d:
        receipt=d.create_stage(b'good')
        try:root.rename(tmp_path/'original')
        except PermissionError:
            assert os.name=='nt' # actual no-delete directory pin, not a simulation
            return
        root.mkdir();(root/'sentinel').write_bytes(b'foreign')
        with pytest.raises(PublicationUnknown):d.publish(receipt,'out')
        assert list(root.iterdir())==[root/'sentinel']
        assert (root/'sentinel').read_bytes()==b'foreign'
