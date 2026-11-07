from hashlib import sha256
import os

from fonesi_edit.media.proxy_cache import PersistentProxyCache, ProxyCacheKey


def _key(tool):
    return ProxyCacheKey(
        source_sha256=sha256(b"source").hexdigest(),
        tool_sha256=sha256(tool).hexdigest(),
        stream_index=0,
        width=640,
        height=360,
        algorithm_version="proxy-v1",
    )


def test_prune_does_not_evict_valid_entry_because_corrupt_entry_claims_bytes(tmp_path):
    cache = PersistentProxyCache(
        tmp_path / "cache", max_entry_bytes=10, max_total_bytes=12, max_entries=8
    )
    valid = _key(b"valid-tool")
    corrupt = _key(b"corrupt-tool")
    cache.put(valid, b"valid!")
    valid_dir = cache.root / valid.cache_id
    os.utime(valid_dir, ns=(1, 1))
    cache.put(corrupt, b"broken")
    (cache.root / corrupt.cache_id / "proxy.bin").write_bytes(b"tamper")

    # Lower the quota only after corruption. The valid six-byte entry plus
    # the new one-byte entry fit exactly; counting the corrupt entry would
    # incorrectly evict the older valid entry.
    cache.max_total_bytes = 7
    third = _key(b"third-tool")
    cache.put(third, b"x")

    assert cache.get(valid) == b"valid!"
    assert cache.get(corrupt) is None
    assert not (cache.root / corrupt.cache_id).exists()
    assert cache.get(third) == b"x"
