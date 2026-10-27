import pytest
from fonesi_edit.prototypes.tools import check_tool, scan_tools
from fonesi_edit.prototypes.translation import TranslationNotConfigured, translate
from fonesi_edit.prototypes.subtitles import Cue


def test_explicit_missing_tool_path_does_not_fall_back_to_system(tmp_path):
    missing = str(tmp_path / 'missing-ffmpeg')
    tools = scan_tools({'ffmpeg': missing})
    ffmpeg = next(t for t in tools if t.name == 'ffmpeg')
    assert ffmpeg.status == 'missing' and ffmpeg.path == missing


def test_missing_chrome_is_not_replaced_by_chromium(tmp_path):
    assert check_tool('Google Chrome', str(tmp_path / 'missing-chrome')).status == 'missing'


def test_translation_requires_config_and_never_fakes_output(monkeypatch):
    monkeypatch.delenv('FONESI_GOOGLE_TRANSLATE_API_KEY', raising=False)
    with pytest.raises(TranslationNotConfigured):
        translate([Cue(0, 1000, '你好')])
