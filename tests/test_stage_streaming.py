import hashlib,os
import pytest
from fonesi_edit.artifacts.filesystem import Destination,PublicationCanceled,PublicationUnknown,PublicationError


def test_actual_copy_larger_than_sidecar_limit_has_bounded_reads(tmp_path,monkeypatch):
    source=tmp_path/'source.bin';chunk=b'abcd'*(256*1024)
    with source.open('wb') as stream:
        for _ in range(33):stream.write(chunk)
    original=source.stat();destination=tmp_path/'outputs';destination.mkdir()
    read=os.read;sizes=[]
    def bounded(fd,size):
        sizes.append(size);assert size<=1024*1024
        return read(fd,size)
    monkeypatch.setattr(os,'read',bounded)
    with Destination(destination) as dest:
        receipt=dest.copy_stage(source)
        assert receipt.size==33*1024*1024
        expected=hashlib.sha256()
        for _ in range(33):expected.update(chunk)
        assert receipt.sha256==expected.hexdigest()
        final=dest.publish(receipt,'large.bin')
        assert os.path.samefile(final,destination/receipt.directory/'payload')
    assert len(sizes)>=34 and source.stat().st_size==original.st_size
    assert source.stat().st_mtime_ns==original.st_mtime_ns


@pytest.mark.parametrize('point',[1,3])
def test_cancel_keeps_source_and_never_publishes(tmp_path,point):
    source=tmp_path/'source';source.write_bytes(b'x'*(2*1024*1024))
    out=tmp_path/'out';out.mkdir();calls=0
    def cancel():
        nonlocal calls
        calls+=1
        return calls==point
    with Destination(out) as dest:
        with pytest.raises(PublicationCanceled):dest.copy_stage(source,cancel=cancel)
    assert source.read_bytes()==b'x'*(2*1024*1024)
    assert all(p.is_dir() and p.name.startswith('.fonesi-stage-') for p in out.iterdir())
    if point==1:assert not list(out.iterdir())


def test_growing_source_does_not_follow_eof(tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'original')
    out=tmp_path/'out';out.mkdir();read=os.read;calls=0
    def grow(fd,size):
        nonlocal calls
        calls+=1
        assert calls<=2
        value=read(fd,size)
        with source.open('ab') as stream:stream.write(b'x')
        return value
    monkeypatch.setattr(os,'read',grow)
    with Destination(out) as dest:
        with pytest.raises(PublicationUnknown,match='grew'):dest.copy_stage(source)
    assert all(p.is_dir() for p in out.iterdir())


def test_source_symlink_is_not_opened(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'untouched');link=tmp_path/'link'
    try:link.symlink_to(source)
    except OSError:pytest.skip('Symlink privilege unavailable')
    out=tmp_path/'out';out.mkdir()
    with Destination(out) as dest:
        with pytest.raises(PublicationError):dest.copy_stage(link)
    assert source.read_bytes()==b'untouched' and not list(out.iterdir())


def test_cancel_after_writer_flush_retains_exact_receipt(tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'original');out=tmp_path/'out';out.mkdir()
    with Destination(out) as dest:
        finished=[];create=dest._create_stage_chunks
        def flushed(chunks):
            receipt=create(chunks);finished.append(True);return receipt
        monkeypatch.setattr(dest,'_create_stage_chunks',flushed)
        with pytest.raises(PublicationCanceled) as error:
            dest.copy_stage(source,cancel=lambda:bool(finished))
        receipt=error.value.receipt
        assert receipt is not None and (out/receipt.directory/'payload').read_bytes()==b'original'
        assert not (out/'final').exists()


@pytest.mark.parametrize('size',[2**63,True,33*1024*1024])
def test_forged_large_receipt_never_accepts_small_actual_file(tmp_path,size):
    from dataclasses import replace
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'small')
        with pytest.raises(PublicationError):dest.publish(replace(receipt,size=size),'final')
    assert not (tmp_path/'final').exists()
