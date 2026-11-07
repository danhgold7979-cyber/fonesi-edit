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

    # The corrupt six-byte entry must not count toward the quota. Adding one
    # byte keeps the valid six-byte entry within the ten-byte budget.
    third = _key(b"third-tool")
    cache.put(third, b"x")

    assert cache.get(valid) == b"valid!"
    assert cache.get(corrupt) is None
    assert cache.get(third) == b"x"
