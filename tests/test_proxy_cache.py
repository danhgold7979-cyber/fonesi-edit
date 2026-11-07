from hashlib import sha256
import os
import json
from pathlib import Path

import pytest

from fonesi_edit.media.proxy_cache import (
    PersistentProxyCache, ProxyCacheCanceled, ProxyCacheError, ProxyCacheKey,
)


def _key(**changes):
    values = dict(
        source_sha256=sha256(b"source").hexdigest(),
        tool_sha256=sha256(b"ffmpeg").hexdigest(),
        stream_index=2,
        width=640,
        height=360,
        algorithm_version="proxy-v1",
    )
    values.update(changes)
    return ProxyCacheKey(**values)


def test_key_is_content_addressed_by_all_media_and_encoder_dimensions():
    base = _key()
    assert base.cache_id == _key().cache_id
    for change in (
        {"source_sha256": sha256(b"other-source").hexdigest()},
        {"tool_sha256": sha256(b"other-tool").hexdigest()},
        {"stream_index": 3},
        {"width": 1280},
        {"height": 720},
        {"algorithm_version": "proxy-v2"},
    ):
        assert _key(**change).cache_id != base.cache_id


@pytest.mark.parametrize("changes", [
    {"source_sha256": "A" * 64},
    {"tool_sha256": "bad"},
    {"stream_index": True},
    {"stream_index": -1},
    {"width": 0},
    {"height": 2161},
    {"algorithm_version": ""},
    {"algorithm_version": "x" * 65},
])
def test_key_rejects_invalid_identity_and_dimensions(changes):
    with pytest.raises(ProxyCacheError):
        _key(**changes)


def test_persistent_cache_round_trip_and_reopen(tmp_path):
    key = _key()
    payload = b"encoded-proxy-payload"
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    assert cache.get(key) is None
    assert cache.put(key, payload) is True
    assert cache.get(key) == payload
    reopened = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    assert reopened.get(key) == payload


def test_cache_key_changes_invalidate_tool_stream_size_and_algorithm(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    cache.put(key, b"proxy")
    assert cache.get(_key(tool_sha256=sha256(b"new-tool").hexdigest())) is None
    assert cache.get(_key(stream_index=4)) is None
    assert cache.get(_key(width=1280)) is None
    assert cache.get(_key(algorithm_version="proxy-v2")) is None


def test_corrupt_payload_digest_is_a_cache_miss(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    cache.put(key, b"valid-proxy")
    payload_path = tmp_path / "cache" / key.cache_id / "proxy.bin"
    payload_path.write_bytes(b"tampered-proxy")
    assert cache.get(key) is None


def test_corrupt_manifest_and_oversized_entry_are_not_returned(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=8)
    with pytest.raises(ProxyCacheError):
        cache.put(key, b"this payload is too large")
    cache.put(key, b"small")
    manifest = tmp_path / "cache" / key.cache_id / "manifest.json"
    manifest.write_text("{broken", encoding="utf-8")
    assert cache.get(key) is None


def test_cancellation_before_and_after_staging_never_publishes_ready_entry(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    with pytest.raises(ProxyCacheCanceled):
        cache.put(key, b"proxy", cancel=lambda: True)
    calls = 0

    def cancel_after_staging():
        nonlocal calls
        calls += 1
        return calls >= 2

    with pytest.raises(ProxyCacheCanceled):
        cache.put(key, b"proxy", cancel=cancel_after_staging)
    assert cache.get(key) is None
    assert not list((tmp_path / "cache").glob(".proxy-pending-*"))


def test_invalidate_one_key_and_all_entries_for_changed_source(tmp_path):
    source_hash = sha256(b"source").hexdigest()
    first = _key()
    second = _key(tool_sha256=sha256(b"another-tool").hexdigest())
    other_source = _key(source_sha256=sha256(b"other-source").hexdigest())
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    for key in (first, second, other_source):
        cache.put(key, b"proxy")
    assert cache.invalidate(first) is True
    assert cache.invalidate(first) is False
    assert cache.get(first) is None
    assert cache.invalidate_source(source_hash) == 1
    assert cache.get(second) is None
    assert cache.get(other_source) == b"proxy"


def test_cache_refuses_symlink_root_and_symlink_entry(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(ProxyCacheError):
        PersistentProxyCache(linked)

    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    key = _key()
    target = tmp_path / "target"
    target.mkdir()
    (cache.root / key.cache_id).symlink_to(target, target_is_directory=True)
    with pytest.raises(ProxyCacheError):
        cache.get(key)


def test_cache_refuses_non_absolute_root_and_invalid_payload(tmp_path, monkeypatch):
    with pytest.raises(ProxyCacheError):
        PersistentProxyCache(Path("relative-cache"))
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    key = _key()
    for payload in (b"", bytearray(b"proxy"), "proxy"):
        with pytest.raises(ProxyCacheError):
            cache.put(key, payload)
    with pytest.raises(ProxyCacheError):
        cache.put(key, b"proxy", cancel=None)



def test_invalidate_source_never_deletes_unrelated_directory_with_forged_manifest(tmp_path):
    source_hash = sha256(b"source").hexdigest()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    unrelated = cache.root / "user-data"
    unrelated.mkdir()
    key_data = _key().to_dict()
    (unrelated / "manifest.json").write_text(json.dumps({
        "schema": 1,
        "key": key_data,
        "size": 5,
        "payload_sha256": sha256(b"other").hexdigest(),
    }), encoding="utf-8")
    (unrelated / "important.txt").write_text("preserve", encoding="utf-8")
    assert cache.invalidate_source(source_hash) == 0
    assert (unrelated / "important.txt").read_text(encoding="utf-8") == "preserve"


def test_cache_root_rejects_parent_path_traversal(tmp_path):
    with pytest.raises(ProxyCacheError):
        PersistentProxyCache(tmp_path / ".." / "outside")



def test_persistent_cache_evicts_oldest_entries_to_respect_total_byte_budget(tmp_path):
    first = _key()
    second = _key(tool_sha256=sha256(b"second-tool").hexdigest())
    cache = PersistentProxyCache(
        tmp_path / "cache", max_entry_bytes=10, max_total_bytes=10, max_entries=8
    )
    cache.put(first, b"first!")
    first_dir = cache.root / first.cache_id
    os.utime(first_dir, ns=(1, 1))
    cache.put(second, b"second")
    assert cache.get(first) is None
    assert cache.get(second) == b"second"


def test_persistent_cache_enforces_maximum_entry_count(tmp_path):
    first = _key()
    second = _key(tool_sha256=sha256(b"second-tool").hexdigest())
    cache = PersistentProxyCache(
        tmp_path / "cache", max_entry_bytes=32, max_total_bytes=64, max_entries=1
    )
    cache.put(first, b"first")
    first_dir = cache.root / first.cache_id
    os.utime(first_dir, ns=(1, 1))
    cache.put(second, b"second")
    assert cache.get(first) is None
    assert cache.get(second) == b"second"


def test_persistent_cache_rejects_budget_smaller_than_entry_limit(tmp_path):
    with pytest.raises(ProxyCacheError):
        PersistentProxyCache(
            tmp_path / "cache", max_entry_bytes=1024, max_total_bytes=512
        )



def test_put_replaces_existing_entry_as_one_complete_generation(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    cache.put(key, b"generation-one")
    assert cache.get(key) == b"generation-one"
    cache.put(key, b"generation-two")
    assert cache.get(key) == b"generation-two"
    assert not list(cache.root.glob(".proxy-pending-*"))
    assert not list(cache.root.glob(".proxy-backup-*"))


def test_get_rejects_symlink_payload_and_manifest(tmp_path):
    key = _key()
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    cache.put(key, b"valid")
    entry = cache.root / key.cache_id
    payload = entry / "proxy.bin"
    payload.unlink()
    external = tmp_path / "external.bin"
    external.write_bytes(b"external")
    payload.symlink_to(external)
    assert cache.get(key) is None

    payload.unlink()
    payload.write_bytes(b"valid")
    manifest = entry / "manifest.json"
    manifest.unlink()
    external_manifest = tmp_path / "external.json"
    external_manifest.write_text("{}", encoding="utf-8")
    manifest.symlink_to(external_manifest)
    assert cache.get(key) is None


def test_invalidate_refuses_symlink_and_preserves_external_target(tmp_path):
    cache = PersistentProxyCache(tmp_path / "cache", max_entry_bytes=1024)
    key = _key()
    external = tmp_path / "external"
    external.mkdir()
    (external / "keep.txt").write_text("keep", encoding="utf-8")
    (cache.root / key.cache_id).symlink_to(external, target_is_directory=True)
    with pytest.raises(ProxyCacheError):
        cache.invalidate(key)
    assert (external / "keep.txt").read_text(encoding="utf-8") == "keep"



def test_cache_revalidates_root_if_directory_is_replaced_by_symlink(tmp_path):
    root = tmp_path / "cache"
    cache = PersistentProxyCache(root, max_entry_bytes=1024)
    key = _key()
    cache.put(key, b"cache-bytes")
    moved = tmp_path / "cache-moved"
    root.rename(moved)
    external = tmp_path / "external-cache"
    external.mkdir()
    root.symlink_to(external, target_is_directory=True)
    with pytest.raises(ProxyCacheError):
        cache.get(key)
    with pytest.raises(ProxyCacheError):
        cache.put(key, b"new-cache-bytes")
    assert list(moved.iterdir())
    assert not list(external.iterdir())



def test_verified_cache_read_refreshes_lru_recency_before_eviction(tmp_path):
    first = _key()
    second = _key(tool_sha256=sha256(b"second-tool").hexdigest())
    cache = PersistentProxyCache(
        tmp_path / "cache", max_entry_bytes=10, max_total_bytes=20, max_entries=8
    )
    cache.put(first, b"first!")
    cache.put(second, b"second")
    first_dir = cache.root / first.cache_id
    second_dir = cache.root / second.cache_id
    os.utime(first_dir, ns=(1, 1))
    os.utime(second_dir, ns=(2, 2))
    assert cache.get(first) == b"first!"
    assert first_dir.stat().st_mtime_ns > second_dir.stat().st_mtime_ns

    cache.max_total_bytes = 7
    third = _key(tool_sha256=sha256(b"third-tool").hexdigest())
    cache.put(third, b"x")
    assert cache.get(first) == b"first!"
    assert cache.get(second) is None
    assert cache.get(third) == b"x"
