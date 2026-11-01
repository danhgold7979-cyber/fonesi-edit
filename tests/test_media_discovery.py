import json
import os
from pathlib import Path
import pytest
from fonesi_edit.media.discovery import scan_media,DiscoveryError,MEDIA_EXTENSIONS
from fonesi_edit.__main__ import main


def tree(tmp_path):
    source=tmp_path/'nguồn 中文';source.mkdir()
    (source/'clip.mp4').write_bytes(b'candidate not yet validated')
    (source/'unusual.format').write_bytes(b'unknown format still a candidate')
    nested=source/'nested';nested.mkdir();(nested/'sound.wav').write_bytes(b'sound')
    output=source/'output';output.mkdir();(output/'rendered.mp4').write_bytes(b'output sentinel')
    cache=source/'cache';cache.mkdir();(cache/'cache.mp4').write_bytes(b'cache sentinel')
    stage=source/'.fonesi-stage-owned';stage.mkdir();(stage/'payload').write_bytes(b'stage sentinel')
    return source,output,cache


def test_nested_outputs_cache_staging_excluded_no_content_mutation(tmp_path):
    source,output,cache=tree(tmp_path)
    before={p:p.read_bytes() for p in source.rglob('*') if p.is_file()}
    result=scan_media(source,excluded_roots=(output,cache))
    assert result.status=='COMPLETE'
    assert set(result.paths)=={source/'clip.mp4',source/'unusual.format',source/'nested'/'sound.wav'}
    assert before=={p:p.read_bytes() for p in source.rglob('*') if p.is_file()}
    filtered=scan_media(source,excluded_roots=(output,cache),extensions=MEDIA_EXTENSIONS)
    assert source/'unusual.format' not in filtered.paths


def test_source_output_overlap_refused(tmp_path):
    source,output,cache=tree(tmp_path)
    with pytest.raises(DiscoveryError,match='overlaps'):scan_media(source,excluded_roots=(source,))
    with pytest.raises(DiscoveryError,match='overlaps'):scan_media(output,excluded_roots=(source,))


def test_hardlink_candidates_deduplicated_and_known_artifact_identity_excluded(tmp_path):
    source,output,cache=tree(tmp_path)
    os.link(source/'clip.mp4',source/'alias.mp4')
    os.link(output/'rendered.mp4',source/'foreign-output-alias.mp4')
    info=(output/'rendered.mp4').stat()
    result=scan_media(source,excluded_roots=(output,cache),excluded_file_ids=((info.st_dev,info.st_ino),))
    assert len([p for p in result.paths if p.name in {'clip.mp4','alias.mp4'}])==1
    assert source/'foreign-output-alias.mp4' not in result.paths


def test_symlink_loop_and_external_directory_never_followed(tmp_path):
    source,output,cache=tree(tmp_path)
    external=tmp_path/'external';external.mkdir();(external/'private.mp4').write_bytes(b'outside')
    try:(source/'loop').symlink_to(source,target_is_directory=True);(source/'external').symlink_to(external,target_is_directory=True)
    except OSError:
        if os.name=='nt':pytest.skip('Windows symlink creation unavailable; native junction gate remains open')
        raise
    result=scan_media(source,excluded_roots=(output,cache))
    assert all('loop' not in p.parts and 'external' not in p.parts for p in result.paths)
    with pytest.raises(DiscoveryError):scan_media(source/'loop')


@pytest.mark.parametrize('limit', [{'max_entries':1},{'max_results':1},{'max_depth':1}])
def test_limits_are_truthful_partial_not_complete(tmp_path,limit):
    source,output,cache=tree(tmp_path)
    deep=source/'nested'/'deeper';deep.mkdir();(deep/'x.mp4').write_bytes(b'x')
    result=scan_media(source,excluded_roots=(output,cache),**limit)
    assert result.status=='PARTIAL_LIMIT'


def test_cancel_before_scan_and_during_scan(tmp_path):
    source,output,cache=tree(tmp_path)
    result=scan_media(source,excluded_roots=(output,cache),cancel=lambda:True)
    assert result.status=='PARTIAL_CANCELED' and result.paths==()
    calls=[0]
    def cancel():calls[0]+=1;return calls[0]>3
    assert scan_media(source,excluded_roots=(output,cache),cancel=cancel).status=='PARTIAL_CANCELED'


def test_cli_returns_real_candidates_without_userdata_or_validation_claim(tmp_path,capsys):
    source,output,cache=tree(tmp_path)
    assert main(['--scan-media',str(source),'--exclude-root',str(output),'--exclude-root',str(cache)])==0
    result=json.loads(capsys.readouterr().out)
    assert result['media_validated'] is False and len(result['candidates'])==3
    assert not list(tmp_path.rglob('*.sqlite3'))
    assert main(['--scan-media',str(source),'--exclude-root',str(source)])==2
    assert str(source) not in capsys.readouterr().err


def test_fresh_nofollow_stat_not_direntry_cached_identity(tmp_path,monkeypatch):
    """Windows cached DirEntry identity is zero; never use it for aliases."""
    import fonesi_edit.media.discovery as module
    source,output,cache=tree(tmp_path)
    os.link(source/'clip.mp4',source/'alias.mp4')
    real_scan=os.scandir
    class Entry:
        def __init__(self,entry):self.name=entry.name
        def stat(self,**kwargs):raise AssertionError('Cached DirEntry identity must not be used')
    class Entries:
        def __init__(self,path):self.inner=real_scan(path)
        def __enter__(self):return (Entry(entry) for entry in self.inner)
        def __exit__(self,*args):self.inner.close()
    monkeypatch.setattr(module.os,'scandir',Entries)
    result=scan_media(source,excluded_roots=(output,cache))
    assert result.status=='COMPLETE' and len(result.paths)==3
    assert len([p for p in result.paths if p.name in {'clip.mp4','alias.mp4'}])==1
