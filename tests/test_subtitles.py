from fractions import Fraction
import pytest
from fonesi_edit.prototypes.subtitles import Cue, dump_srt, map_trimmed_cues, parse_srt


def test_bom_crlf_unicode_and_multiline_round_trip():
    source = '\ufeff1\r\n00:00:01,000 --> 00:00:03,000\r\nTiếng Việt\r\n中文\r\n'
    cues = parse_srt(source)
    assert cues == [Cue(1000, 3000, 'Tiếng Việt\n中文')]
    assert parse_srt(dump_srt(cues)) == cues


@pytest.mark.parametrize('text', ['', 'WEBVTT\n\nnot SRT', '1\n00:00:03,000 --> 00:00:02,000\ntext',
                                '1\n00:99:00,000 --> 00:00:04,000\ntext'])
def test_invalid_subtitles_fail_explicitly(text):
    with pytest.raises(ValueError):
        parse_srt(text)


def test_trim_intersection_speed_and_offset_use_same_time_map():
    cues = [Cue(0, 1000, 'out'), Cue(1000, 3000, 'trim left'), Cue(3000, 7000, 'trim right'), Cue(7000, 8000, 'out')]
    assert map_trimmed_cues(cues, 2000, 6000, Fraction(2), 500) == [
        Cue(500, 1000, 'trim left'), Cue(1000, 2500, 'trim right')]


def test_fractional_speed_does_not_accumulate_float_error():
    assert map_trimmed_cues([Cue(1000, 4000, 'x')], 0, 5000, Fraction(3, 2)) == [Cue(667, 2667, 'x')]
