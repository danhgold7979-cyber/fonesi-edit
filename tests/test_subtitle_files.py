from pathlib import Path
import pytest
from fonesi_edit.subtitles.adapter import SubtitleError,parse_subtitles
from fonesi_edit.subtitles.files import load_subtitles,SubtitleCanceled
import fonesi_edit.subtitles.files as files

RAW='1\n00:00:00,000 --> 00:00:01,000\nXin chào 中文'.encode()


def test_unicode_file_import_preserves_source_and_matches_pure_parser(tmp_path):
    path=tmp_path/'Phụ đề 中文.srt';path.write_bytes(RAW)
    assert load_subtitles(path,'srt')==parse_subtitles(RAW,'srt')
    assert path.read_bytes()==RAW


@pytest.mark.parametrize('stage',[1,2,3])
def test_cancel_never_returns_replacement(tmp_path,stage):
    path=tmp_path/'input.srt';path.write_bytes(RAW)
    current=parse_subtitles(RAW,'srt');original=current;calls=0
    def cancel():
        nonlocal calls
        calls+=1
        return calls==stage
    with pytest.raises(SubtitleCanceled):current=load_subtitles(path,'srt',cancel=cancel)
    assert current is original and path.read_bytes()==RAW


def test_limit_is_actual_read_budget_and_parse_not_called(tmp_path,monkeypatch):
    path=tmp_path/'input.srt';path.write_bytes(RAW)
    class Source:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,size):
            assert size==files.MAX_BYTES+1
            return b'x'*size
    monkeypatch.setattr(Path,'open',lambda *a,**k:Source())
    monkeypatch.setattr(files,'parse_subtitles',lambda *a,**k:pytest.fail('Oversized file reached parser'))
    with pytest.raises(SubtitleError,match='byte limit'):load_subtitles(path,'srt')


def test_io_failure_redacted_and_current_document_unchanged(tmp_path,monkeypatch):
    path=tmp_path/'private-name.srt';path.write_bytes(RAW)
    current=parse_subtitles(RAW,'srt');original=current
    def denied(*args):raise PermissionError('SECRET PRIVATE PATH')
    monkeypatch.setattr(files,'read_bounded',denied)
    with pytest.raises(SubtitleError) as error:current=load_subtitles(path,'srt')
    assert 'SECRET' not in str(error.value) and 'private-name' not in str(error.value)
    assert current is original


def test_directory_missing_and_malformed_file_do_not_mutate_current(tmp_path):
    current=parse_subtitles(RAW,'srt');original=current
    bad=tmp_path/'bad.srt';bad.write_bytes(b'garbage')
    for path in (tmp_path,tmp_path/'missing',bad):
        with pytest.raises(SubtitleError):current=load_subtitles(path,'srt')
        assert current is original
    assert bad.read_bytes()==b'garbage'
