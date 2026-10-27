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


def test_provider_endpoint_cannot_carry_secret_query_or_userinfo():
    from fonesi_edit.subtitles import translation_endpoint
    for value in ['https://user:password@translate.example','https://translate.example?api_key=secret','http://remote.example','https://translate.example/#token']:
        with pytest.raises(ValueError):translation_endpoint(value)
    assert translation_endpoint('http://localhost:5000/')=='http://localhost:5000'


def test_completed_translation_file_is_reused_after_worker_recovery(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    calls=[]
    def transport(*args):calls.append(True);return ['Bản dịch']
    monkeypatch.setattr(module,'_request_translation',transport)
    store=Store(tmp_path/'state.db');output=tmp_path/'translated.srt';cue=Caption(0,500,'Original')
    from dataclasses import asdict
    payload={'captions':[asdict(cue)],'output':str(output),'config':{'provider':'test'}}
    assert not module.execute_translation(store,payload,lambda _:None,None)['reused']
    stamp=output.stat().st_mtime_ns
    assert module.execute_translation(store,payload,lambda _:None,None)['reused'] and len(calls)==1 and output.stat().st_mtime_ns==stamp
    output.write_text('1\n00:00:00,000 --> 00:00:00,500\nEdited by user\n')
    with pytest.raises(FileExistsError):module.execute_translation(store,payload,lambda _:None,None)
