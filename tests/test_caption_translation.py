from dataclasses import replace
import pytest
from fonesi_edit.storage import Store
from fonesi_edit.subtitles import Caption,read_captions,write_captions,translate_captions,caption_warnings,split_caption,merge_captions


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


def test_new_subtitle_never_publishes_partial_file_when_fsync_fails(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    destination=tmp_path/'new'/'translated.srt'
    def broken_sync(_descriptor):
        raise OSError('simulated disk full before subtitle publication')
    with monkeypatch.context() as patch:
        patch.setattr(module.os,'fsync',broken_sync)
        with pytest.raises(OSError,match='simulated disk full'):
            module.write_captions(destination,[Caption(0,1000,'Tiếng Việt 中文')])
    assert not destination.exists()
    assert not list(destination.parent.glob('.fonesi-caption-*'))
    module.write_captions(destination,[Caption(0,1000,'Tiếng Việt 中文')])
    assert read_captions(destination)[0].text=='Tiếng Việt 中文'


def test_new_subtitle_racing_publisher_never_overwrites_existing_bytes(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    destination=tmp_path/'racing.srt'
    preserved=b'User supplied subtitle; no overwrite'
    actual_link=module.os.link
    def publish_other_file_then_link(source,target):
        destination.write_bytes(preserved)
        return actual_link(source,target)
    with monkeypatch.context() as patch:
        patch.setattr(module.os,'link',publish_other_file_then_link)
        with pytest.raises(FileExistsError):
            module.write_captions(destination,[Caption(0,1000,'Queued subtitle')])
    assert destination.read_bytes()==preserved
    assert not list(tmp_path.glob('.fonesi-caption-*'))


def test_new_subtitle_unsupported_atomic_link_fails_closed(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    destination=tmp_path/'no-link.srt'
    with monkeypatch.context() as patch:
        patch.setattr(module.os,'link',
                      lambda *_args: (_ for _ in ()).throw(OSError('unsupported link')))
        with pytest.raises(RuntimeError,match='hard-link support'):
            module.write_captions(destination,[Caption(0,1000,'No partial output')])
    assert not destination.exists()
    assert not list(tmp_path.glob('.fonesi-caption-*'))


def test_translation_recovery_after_failed_publish_uses_cache_not_partial_file(tmp_path,monkeypatch):
    import fonesi_edit.subtitles as module
    from dataclasses import asdict
    store=Store(tmp_path/'state.db')
    destination=tmp_path/'translated.srt'
    calls=[]
    def translate(texts,*_args):
        calls.append(tuple(texts))
        return ['Bản dịch '+text for text in texts]
    monkeypatch.setattr(module,'_request_translation',translate)
    payload={'captions':[asdict(Caption(0,1000,'Original'))],
             'output':str(destination),'config':{'provider':'test'}}
    with monkeypatch.context() as patch:
        patch.setattr(module.os,'link',
                      lambda *_args: (_ for _ in ()).throw(OSError('synthetic unsupported link')))
        with pytest.raises(RuntimeError,match='hard-link support'):
            module.execute_translation(store,payload,lambda _progress:None,None)
    assert not destination.exists()
    result=module.execute_translation(store,payload,lambda _progress:None,None)
    assert not result['reused']
    assert len(calls)==1
    assert read_captions(destination)[0].text=='Bản dịch Original'


def test_bilingual_split_preserves_every_character_timing_and_lock():
    original=Caption(100,1000,'中文字幕沒有空格','Tiếng Việt có ngữ cảnh',locked=True)
    first,second=split_caption(original)
    assert first.end_ms==second.start_ms
    assert first.start_ms==original.start_ms and second.end_ms==original.end_ms
    assert first.text+second.text==original.text
    assert first.source_text+second.source_text==original.source_text
    assert all(c.locked for c in (first,second))
    assert {first.id,second.id}.isdisjoint({original.id})
    assert '…' not in first.text+second.text
    merged=merge_captions([first,second])
    assert merged.text.replace('\n','')==original.text
    assert merged.source_text.replace('\n','')==original.source_text
    assert merged.locked
    assert (merged.start_ms,merged.end_ms)==(original.start_ms,original.end_ms)


def test_short_or_unseparable_bilingual_cue_is_rejected_without_fabrication():
    for cue in (Caption(0,1,'中文','Tiếng Việt'),
                Caption(0,1000,'字','Text with spaces'),
                Caption(0,1000,'Text with spaces','字'),
                Caption(0,1000,'    ','Text')):
        with pytest.raises(ValueError,match='(ngắn|vị trí)'):
            split_caption(cue)


def test_merge_maintains_all_source_text_and_cue_time_coverage():
    first=Caption(500,1500,'Dịch một','Nguồn một',locked=True)
    second=Caption(300,900,'Dịch hai','',locked=False)
    merged=merge_captions([first,second])
    assert merged.start_ms==300 and merged.end_ms==1500
    assert merged.text=='Dịch một\nDịch hai'
    assert merged.source_text=='Nguồn một\nDịch hai'
    assert merged.locked
    with pytest.raises(ValueError,match='ít nhất hai'):
        merge_captions([first])


def test_ass_import_reports_non_roundtrippable_style_without_mutating_source(tmp_path):
    import pysubs2
    from fonesi_edit.subtitles import (
        ASS_PRESENTATION_WARNING,read_captions_with_warnings)
    path=tmp_path/'source.ass'
    document=pysubs2.SSAFile()
    document.styles['Custom']=pysubs2.SSAStyle(
        fontname='Arial',fontsize=34)
    document.events.append(pysubs2.SSAEvent(
        start=100,end=1200,style='Custom',
        text=r'{\pos(100,120)}Tiếng Việt\N中文'))
    document.save(str(path),encoding='utf-8')
    initial_bytes=path.read_bytes()
    captions,warnings=read_captions_with_warnings(path)
    assert len(captions)==1
    assert (captions[0].start_ms,captions[0].end_ms)==(100,1200)
    assert 'Tiếng Việt' in captions[0].text and '中文' in captions[0].text
    assert ASS_PRESENTATION_WARNING in warnings
    assert read_captions(path)[0].text==captions[0].text
    assert path.read_bytes()==initial_bytes  # Read-only import


def test_plain_srt_import_does_not_invent_style_loss_warning(tmp_path):
    from fonesi_edit.subtitles import read_captions_with_warnings
    path=tmp_path/'plain.srt'
    write_captions(path,[Caption(100,800,'Văn bản thường 中文')])
    captions,warnings=read_captions_with_warnings(path)
    assert not warnings
    assert len(captions)==1
    assert (captions[0].start_ms,captions[0].end_ms)==(100,800)
    assert captions[0].text=='Văn bản thường 中文'
