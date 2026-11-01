import hashlib
import pytest
from fonesi_edit.artifacts.filesystem import Destination
from fonesi_edit.artifacts.subtitle_stage import stage_subtitles,SubtitleStageCanceled
from fonesi_edit.subtitles.adapter import SubtitleError
from fonesi_edit.subtitles.files import SubtitleCanceled

RAW=b'1\n00:00:00,000 --> 00:00:01,000\nHello'


def test_parse_observation_bound_to_owned_stage_no_final_or_source_mutation(tmp_path):
    source=tmp_path/'source.srt';source.write_bytes(RAW)
    with Destination(tmp_path) as destination:
        result=stage_subtitles(destination,RAW,'srt')
        assert result.receipt.sha256==hashlib.sha256(RAW).hexdigest()
        assert result.receipt.size==len(RAW) and result.cue_count==1
        assert result.policy=='subtitle-parse-only-v1' and result.parser_version=='1.9.1'
        assert (tmp_path/result.receipt.directory/'payload').read_bytes()==RAW
        assert {p.name for p in tmp_path.iterdir()}=={'source.srt',result.receipt.directory}
        with pytest.raises(AttributeError):result.policy='fully_validated'
    assert source.read_bytes()==RAW


def test_malformed_data_never_reaches_stage_writer(tmp_path,monkeypatch):
    with Destination(tmp_path) as destination:
        monkeypatch.setattr(destination,'create_stage',lambda data:pytest.fail('Invalid data reached writer'))
        with pytest.raises(SubtitleError):stage_subtitles(destination,b'garbage','srt')
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('point',[1,2,3])
def test_cancel_preserves_postwrite_receipt_without_publishing(tmp_path,point):
    calls=0
    def cancel():
        nonlocal calls
        calls+=1
        return calls==point
    with Destination(tmp_path) as destination:
        with pytest.raises(SubtitleCanceled) as result:stage_subtitles(destination,RAW,'srt',cancel=cancel)
        if point<3:assert not list(tmp_path.iterdir())
        else:
            assert isinstance(result.value,SubtitleStageCanceled)
            receipt=result.value.receipt
            assert (tmp_path/receipt.directory/'payload').read_bytes()==RAW
            assert len(list(tmp_path.iterdir()))==1
