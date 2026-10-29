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


def test_fractional_speed_cues_keep_absolute_clip_offset_and_adjacency():
    source=[
        Cue(0,120,'outside before'),Cue(200,400,'first'),
        Cue(400,700,'second'),Cue(800,1000,'outside after'),
    ]
    expected=[Cue(500,633,'first'),Cue(633,833,'second')]
    assert map_trimmed_cues(source,200,700,Fraction(3,2),500)==expected
    assert source[1].start_ms==200 and source[2].end_ms==700
    assert map_trimmed_cues([Cue(10,20,'outside')],100,500)==[]


def test_positive_source_cue_is_never_silently_dropped_by_time_quantization():
    # At 10x speed, a real 1 ms source cue (100–101 ms) becomes 0.1 ms,
    # collapsing to one output millisecond tick under rounding.
    cues=[Cue(100,101,'must not vanish'),Cue(300,400,'visible')]
    with pytest.raises(ValueError,match=r'Cue 1: duration collapses below 1 ms'):
        map_trimmed_cues(cues,0,500,Fraction(10))
    # The same cue remains representable at normal speed and with a clip offset.
    assert map_trimmed_cues(cues,0,500,Fraction(1),250)[0]==Cue(
        350,351,'must not vanish')
