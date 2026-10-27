from dataclasses import replace
import pytest
from fonesi_edit.storage import Store
from fonesi_edit.subtitles import Caption,read_captions,write_captions,translate_captions,caption_warnings


def test_vtt_ass_srt_unicode_roundtrip(tmp_path):
    captions=[Caption(100,1200,'Tiếng Việt\n中文')]
    for ext in ('srt','vtt','ass'):
        path=tmp_path/f'sub.{ext}';write_captions(path,captions)
        actual=read_captions(path)
        assert actual[0].text==captions[0].text and actual[0].start_ms==100
        with pytest.raises(FileExistsError):write_captions(path,captions)


def test_locked_cues_cache_glossary_and_quota_are_preserved(tmp_path):
    store=Store(tmp_path/'state.db');calls=[]
    def fake(texts,*args):calls.append(texts);return ['VI '+t for t in texts]
    cues=[Caption(0,1000,'品牌'),Caption(1000,2000,'manual',locked=True)]
    config={'glossary':{'品牌':'Tên riêng'},'daily_limit':100,'provider':'test'}
    result=translate_captions(store,cues,config=config,transport=fake)
    assert result[0].text=='VI Tên riêng' and result[1].text=='manual'
    assert len(calls)==1
    assert translate_captions(store,cues,config=config,transport=fake)[0].text==result[0].text and len(calls)==1
    with pytest.raises(PermissionError):translate_captions(store,[Caption(0,1000,'long new text')],config={'daily_limit':1,'provider':'test'},transport=fake)


def test_timing_warnings_are_not_silent_data_loss():
    cues=[Caption(0,1000,'a'),Caption(900,1100,'b')]
    assert any('chồng' in w for w in caption_warnings(cues,1000))
    assert any('vượt' in w for w in caption_warnings(cues,1000))
