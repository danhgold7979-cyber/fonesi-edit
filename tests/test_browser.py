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
