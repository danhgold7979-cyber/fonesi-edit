import builtins
import pytest
from fonesi_edit.__main__ import main


def test_subtitle_cli_headless_and_no_user_data(tmp_path,capsys,monkeypatch):
    path=tmp_path/'Phụ đề 中文.srt'
    raw='1\n00:00:00,000 --> 00:00:01,000\nPRIVATE CAPTION'.encode();path.write_bytes(raw)
    original_import=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.startswith('PySide6'):pytest.fail('Headless validation imported Qt')
        return original_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    data=tmp_path/'not-created'
    assert main(['--validate-subtitles',str(path),'--subtitle-format','srt','--data-dir',str(data)])==0
    output=capsys.readouterr()
    assert '1 cue(s)' in output.out and 'No style/render fidelity' in output.out
    assert 'PRIVATE' not in output.out+output.err and str(path) not in output.out+output.err
    assert not data.exists() and path.read_bytes()==raw


@pytest.mark.parametrize('options',[
 ['--validate-subtitles','input.srt'],
 ['--subtitle-format','srt'],
 ['--subtitle-encoding','utf-8'],
 ['--validate-subtitles','input.srt','--subtitle-format','bad'],
 ['--validate-subtitles','input.srt','--subtitle-format','srt','--validate-plan','plan.json'],
])
def test_subtitle_cli_argument_contract(options):
    with pytest.raises(SystemExit) as result:main(options)
    assert result.value.code==2


def test_subtitle_cli_invalid_data_and_encoding_are_controlled(tmp_path,capsys):
    path=tmp_path/'PRIVATE.srt';path.write_bytes(b'1\n00:00:70,000 --> 00:02:00,000\nSECRET')
    args=['--validate-subtitles',str(path),'--subtitle-format','srt']
    assert main(args)==2
    assert main(args+['--subtitle-encoding','auto'])==2
    output=capsys.readouterr()
    assert 'SECRET' not in output.err and 'PRIVATE' not in output.err


def test_explicit_empty_encoding_is_not_silently_defaulted(tmp_path,capsys):
    path=tmp_path/'input.srt';path.write_bytes(b'1\n00:00:00,000 --> 00:00:01,000\nHello')
    assert main(['--validate-subtitles',str(path),'--subtitle-format','srt','--subtitle-encoding',''])==2
    assert 'Explicit supported encoding required' in capsys.readouterr().err
