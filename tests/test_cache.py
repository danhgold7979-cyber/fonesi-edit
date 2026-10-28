"""Cache quota regression, including protected files and owner boundaries."""
import os
from pathlib import Path

import pytest

from fonesi_edit.cache import evict_proxy_cache


def _proxy(root,key,size,modified):
    path=root/(key*64+'.mp4')
    path.write_bytes(b'x'*size)
    os.utime(path,ns=(modified,modified))
    return path


def test_cache_evicts_old_completed_outputs_without_touching_nonproxy_media(tmp_path):
    root=tmp_path/'proxies';root.mkdir()
    oldest=_proxy(root,'a',40,1)
    middle=_proxy(root,'b',40,2)
    latest=_proxy(root,'c',40,3)
    other=root/'my-vacation.mp4';other.write_bytes(b'source owned by user')
    partial=root/'.fonesi-proxy-in-progress.mp4';partial.write_bytes(b'partial')
    nested=root/'nested';nested.mkdir()
    nested_media=nested/'a'*0 if False else nested/'keep.mp4'
    nested_media.write_bytes(b'nested content')
    result=evict_proxy_cache(root,50)
    assert result['scanned_bytes']==120
    assert result['deleted_bytes']==80
    assert result['remaining_bytes']==40
    assert not result['over_budget']
    assert not oldest.exists() and not middle.exists() and latest.exists()
    assert other.read_bytes()==b'source owned by user'
    assert partial.read_bytes()==b'partial'
    assert nested_media.read_bytes()==b'nested content'
    assert evict_proxy_cache(root,50)['deleted']==[]


def test_cache_protects_active_media_even_when_over_quota(tmp_path):
    root=tmp_path/'proxies';root.mkdir()
    active=_proxy(root,'a',60,1)
    another=_proxy(root,'b',50,2)
    result=evict_proxy_cache(root,10,protected=[active])
    assert active.exists() and not another.exists()
    assert result['over_budget'] and result['remaining_bytes']==60
    with pytest.raises(ValueError):
        evict_proxy_cache(root,-1)
    with pytest.raises(ValueError):
        evict_proxy_cache(root,2.5)


def test_cache_rejects_symlink_directory_and_ignores_symlink_content(tmp_path):
    root=tmp_path/'proxies';root.mkdir()
    external=tmp_path/'external.mp4';external.write_bytes(b'keep untouched')
    symlink=root/('f'*64+'.mp4')
    link_root=tmp_path/'linked-cache'
    try:
        symlink.symlink_to(external)
        link_root.symlink_to(root,target_is_directory=True)
    except (OSError,NotImplementedError):
        pytest.skip('Symlink privilege not granted on this runner')
    assert evict_proxy_cache(root,0)['deleted']==[]
    assert external.read_bytes()==b'keep untouched'
    with pytest.raises(PermissionError):
        evict_proxy_cache(link_root,0)
