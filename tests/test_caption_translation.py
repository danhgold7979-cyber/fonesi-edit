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


def test_changing_only_daily_translation_quota_reuses_cached_cues(tmp_path):
    store=Store(tmp_path/'state.db')
    calls=[]
    def fake(texts,*args):
        calls.append(tuple(texts))
        return ['Bản dịch '+text for text in texts]
    cue=Caption(0,1200,'Original')
    first=translate_captions(store,[cue],config={'provider':'test','daily_limit':100},transport=fake)
    assert first[0].text=='Bản dịch Original'
    second=translate_captions(store,[cue],config={'provider':'test','daily_limit':1},transport=fake)
    assert second[0].text==first[0].text
    assert len(calls)==1


def test_overwriting_subtitle_is_atomic_and_failure_keeps_manual_edits(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    path=tmp_path/'manual.srt'
    module.write_captions(path,[Caption(0,1000,'Sửa tay đã lưu')])
    original=path.read_bytes()
    bad=Caption(0,1000,'Invalid')
    bad.end_ms=0
    with pytest.raises(ValueError):
        module.write_captions(path,[bad],overwrite=True)
    assert path.read_bytes()==original
    def fail_replace(*args):
        raise OSError('synthetic rename failure')
    with monkeypatch.context() as patch:
        patch.setattr(module.os,'replace',fail_replace)
        with pytest.raises(OSError,match='rename failure'):
            module.write_captions(path,[Caption(0,1000,'Ghi mới')],overwrite=True)
    assert path.read_bytes()==original
    assert not list(tmp_path.glob('.fonesi-caption-*'))
    module.write_captions(path,[Caption(0,1000,'Ghi mới')],overwrite=True)
    assert read_captions(path)[0].text=='Ghi mới'
