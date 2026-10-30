import json
import pytest
from fonesi_edit.prototypes.browser import PLATFORMS, chrome_command, create_profile, list_profiles


def test_profiles_are_independent_and_recovered_without_credentials(tmp_path):
    a = create_profile(tmp_path, 'Chrome A / Tiếng Việt')
    b = create_profile(tmp_path, 'Chrome B')
    assert a.id != b.id and a.directory != b.directory
    assert {p.id for p in list_profiles(tmp_path)} == {a.id, b.id}
    saved = json.loads((a.directory / 'fonesi-profile.json').read_text(encoding='utf-8'))
    assert set(saved) == {'id', 'label', 'owner'}
    assert {'Facebook', 'TikTok', 'YouTube', 'Bilibili'} <= PLATFORMS.keys()


def test_missing_official_chrome_does_not_launch_chromium(tmp_path):
    profile = create_profile(tmp_path, 'A')
    with pytest.raises(RuntimeError, match='Chrome chính thức'):
        chrome_command(profile, 'Facebook', chrome=str(tmp_path / 'missing-chrome'))


def test_unknown_platform_cannot_inject_a_browser_url(tmp_path):
    with pytest.raises(ValueError):
        chrome_command(create_profile(tmp_path, 'A'), 'https://untrusted.invalid/')


def test_revoke_pairing_is_scoped_and_preserves_chrome_profiles(tmp_path):
    import hashlib
    from pathlib import Path

    from fonesi_edit.browser import (
        bind,
        bindings,
        create_profile as create_store_profile,
        pair,
        pairing_code,
        profiles,
        revoke_pairing,
    )
    from fonesi_edit.storage import Store

    store = Store(tmp_path / "state" / "fonesi.db")
    profile_a = create_store_profile(store, "Chrome A / Facebook A")
    profile_b = create_store_profile(store, "Chrome B / Facebook B")
    binding_a = bind(store, profile_a, "Facebook")
    binding_b = bind(store, profile_b, "Facebook")

    code_a = pairing_code(store, profile_a)
    token_a = pair(store, code_a)
    pending_code_a = pairing_code(store, profile_a)
    code_b = pairing_code(store, profile_b)
    token_b = pair(store, code_b)

    profile_paths = {item["id"]: Path(item["path"]) for item in profiles(store)}
    assert profile_paths[profile_a].is_dir()
    assert profile_paths[profile_b].is_dir()

    revoke_pairing(store, profile_a)

    bridge_a = "bridge:" + hashlib.sha256(token_a.encode()).hexdigest()
    bridge_b = "bridge:" + hashlib.sha256(token_b.encode()).hexdigest()
    pending_a = "pair:" + hashlib.sha256(pending_code_a.encode()).hexdigest()
    assert store.setting(bridge_a) is None
    assert store.setting(pending_a) is None
    assert store.setting(bridge_b) == {"profile_id": profile_b}

    remaining_profiles = {item["id"] for item in profiles(store)}
    assert remaining_profiles == {profile_a, profile_b}
    assert profile_paths[profile_a].is_dir()
    assert profile_paths[profile_b].is_dir()
    assert {item["id"] for item in bindings(store)} == {binding_a, binding_b}

