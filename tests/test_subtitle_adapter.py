from fractions import Fraction
import pytest
from fonesi_edit.subtitles.adapter import parse_subtitles,SubtitleError,MAX_BYTES

SRT='1\n00:00:00,125 --> 00:00:01,500\nXin chào 中文\n\n2\n00:00:01,000 --> 00:00:02,000\n<i>Overlap</i>\n'

def test_upstream_srt_unicode_exact_time_overlap_and_original():
    raw=SRT.encode();doc=parse_subtitles(raw,'srt');again=parse_subtitles(raw,'srt')
    assert doc.original_bytes==raw and doc==again
    assert doc.cues[0].start==Fraction(1,8) and doc.cues[0].end==Fraction(3,2)
    assert doc.cues[1].start<doc.cues[0].end
    assert doc.cues[0].source_label=='1' and len({c.id for c in doc.cues})==2
    assert doc.cues[1].markup_text=='<i>Overlap</i>' and doc.cues[0].word_timings is None
    with pytest.raises(AttributeError):doc.cues=()


def test_named_vtt_ids_are_not_appended_to_previous_text():
    raw=b'WEBVTT\n\nfirst\n00:00.000 --> 00:01.000\nHello\n\nsecond\n00:01.000 --> 00:02.000\nWorld\n'
    doc=parse_subtitles(raw,'vtt')
    assert [c.source_label for c in doc.cues]==['first','second']
    assert [c.markup_text for c in doc.cues]==['Hello','World']


def test_ass_original_styles_retained_but_not_fidelity_claim():
    raw=b'[Script Info]\nScriptType: v4.00+\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.12,0:00:01.50,Default,,0,0,0,,Hello\n'
    doc=parse_subtitles(raw,'ass')
    assert doc.cues[0].start==Fraction(3,25)
    assert doc.original_bytes==raw and 'ASS_STYLE_MAPPING_PENDING' in doc.diagnostics[0]


def test_upstream_malformed_ass_timestamp_is_controlled():
    with pytest.raises(SubtitleError):parse_subtitles(b'[Events]\nFormat: Start, End, Text\nDialogue: x,y,secret\n','ass')


@pytest.mark.parametrize('raw,fmt',[
 (b'garbage','srt'),
 (b'1\n00:00:70,000 --> 00:01:00,000\nBad','srt'),
 (b'1\n00:00:00,12 --> 00:01:00,000\nBad','srt'),
 (b'1\n00:01:00,000 --> 00:00:00,000\nBad','srt'),
 (b'1\n00:00:00,000 --> 00:00:00,000\nBad','srt'),
 (b'WEBVTT\n\n00:00.000 --> 00:01.000 align:start\nHello','vtt'),
 (b'WEBVTT\n\nNOTE comment\ntext','vtt'),
 (b'[Fonts]\nfontname: unsafe.ttf','ass'),
 (b'\xff','srt'),
])
def test_malformed_unsupported_fails_closed(raw,fmt):
    with pytest.raises(SubtitleError):parse_subtitles(raw,fmt)


def test_empty_policy_and_resource_caps():
    with pytest.raises(SubtitleError):parse_subtitles(b'','srt')
    assert parse_subtitles(b'','srt',allow_empty=True).cues==()
    assert parse_subtitles(b'WEBVTT\n','vtt',allow_empty=True).cues==()
    with pytest.raises(SubtitleError):parse_subtitles(b'x'*(MAX_BYTES+1),'srt')
    with pytest.raises(SubtitleError):parse_subtitles(('x'*16385).encode(),'srt')


def test_explicit_legacy_encoding():
    raw='1\n00:00:00,000 --> 00:00:01,000\nCafé'.encode('cp1252')
    doc=parse_subtitles(raw,'srt',encoding='cp1252');assert doc.cues[0].markup_text=='Café'
    with pytest.raises(SubtitleError):parse_subtitles(raw,'srt',encoding='auto')


@pytest.mark.parametrize('kwargs',[{'format_':[]},{'format_':'srt','encoding':[]},{'format_':'srt','allow_empty':1}])
def test_typed_boundary_rejects_unstructured_options(kwargs):
    with pytest.raises(SubtitleError):parse_subtitles(b'',**kwargs)


def test_ass_ignored_garbage_not_empty_success():
    with pytest.raises(SubtitleError):parse_subtitles(b'garbage','ass',allow_empty=True)
    with pytest.raises(SubtitleError):parse_subtitles(b'[Events]\ndialogue: bad\n','ass',allow_empty=True)


def test_cue_cap_precedes_library_and_source_labels_remain_unique(monkeypatch):
    import fonesi_edit.subtitles.adapter as adapter
    monkeypatch.setattr(adapter,'MAX_CUES',1)
    with pytest.raises(SubtitleError,match='limit'):parse_subtitles(SRT.encode(),'srt')


@pytest.mark.parametrize('fmt,first', [('ass','Layer'),('ssa','Marked')])
def test_substation_canonical_layout_and_comma_text(fmt,first):
    raw=(f'[Events]\nFormat: {first}, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
         f'Dialogue: {"0" if fmt=="ass" else "Marked=0"},0:00:00.00,0:00:01.00,Default,Actor,0,0,0,,Actual, caption\n').encode()
    assert parse_subtitles(raw,fmt).cues[0].markup_text=='Actual, caption'
    swapped=raw.replace(b'Style, Name, MarginL, MarginR, MarginV, Effect, Text',b'Style, Text, MarginL, MarginR, MarginV, Effect, Name')
    with pytest.raises(SubtitleError,match='layout'):parse_subtitles(swapped,fmt)
    with pytest.raises(SubtitleError):parse_subtitles(raw+b'GARBAGE IGNORED\n',fmt)
    with pytest.raises(SubtitleError):parse_subtitles(raw.replace(b'0:00:00.00',b'0:00:70.00'),fmt)
    with pytest.raises(SubtitleError):parse_subtitles(raw.replace(b'0:00:00.00',b'0:00:00.000'),fmt)
    with pytest.raises(SubtitleError):parse_subtitles(raw.replace(b',0,0,0,,Actual, caption',b',Actual'),fmt)
    with pytest.raises(SubtitleError):parse_subtitles(raw.replace(b'[Events]',b'[Script Info]'),fmt)


def test_substation_style_layout_is_also_explicit():
    from pysubs2.formats.substation import STYLE_FORMAT_LINE
    import pysubs2
    subs=pysubs2.SSAFile();subs.append(pysubs2.SSAEvent(start=0,end=1000,text='Hello'))
    raw=subs.to_string('ass').encode()
    assert parse_subtitles(raw,'ass').cues[0].markup_text=='Hello'
    with pytest.raises(SubtitleError,match='layout'):
        parse_subtitles(raw.replace(STYLE_FORMAT_LINE['ass'].encode(),b'Format: Fontname, Name'),'ass')
