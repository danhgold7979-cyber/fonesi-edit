from pathlib import Path
import pytest
from fonesi_edit.core.model import Cue,TimeMap,US
from fonesi_edit.services.subtitles import *
from fonesi_edit.services.translation import *
from fonesi_edit.core.storage import Store

@pytest.mark.parametrize('suffix',['.srt','.vtt','.ass'])
def test_subtitle_roundtrip_unicode(tmp_path,suffix):
    cues=[Cue(0,US,'Tiếng Việt 中文',translation='Bản dịch')];p=tmp_path/('s'+suffix)
    write_subtitles(cues,p,bilingual=True);out,w=read_subtitles(p)
    assert out[0].text=='Tiếng Việt 中文\nBản dịch';assert out[0].end==US
    assert bool(w)==(suffix=='.ass')


def test_subtitle_policy_and_ambiguous(tmp_path):
    tracks=[{'language':'en','automatic':False},{'language':'vi','automatic':True},{'language':'vi','automatic':False}]
    assert choose_track(tracks)['track']==tracks[2]
    assert choose_track(tracks[:1])['track'] is None
    assert choose_track(tracks[:1],translation_configured=True)['translate']
    with pytest.raises(ValueError):match_subtitle(Path('a.mp4'),[Path('a.vi.srt'),Path('a.en.srt')])


def test_map_split_merge_shift_and_warnings():
    c=Cue(0,4*US,'hello world');a,b=split_cue(c,2*US,5)
    assert merge_cues([a,b]).text=='hello\nworld'
    out=map_cues([c],[TimeMap(US,3*US,'2',US)])
    assert (out[0].start,out[0].end)==(US,2*US)
    assert shift_cues([c],US)[0].start==US
    with pytest.raises(ValueError):shift_cues([c],-US)
    assert {'past_video_end','overlap'} <= {w['reason'] for w in warnings([c,Cue(US,5*US,'b')],3*US)}


def test_no_unconfigured_provider_request(tmp_path):
    t=Translator(Store(tmp_path/'s.db'),TranslationConfig('https://example.invalid','zh'))
    with pytest.raises(TranslationConfiguration):t.translate([Cue(0,US,'中文')])


def test_translation_cache_locked_budget_local_transport(tmp_path,monkeypatch):
    calls=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def read(self,n):return b'{"translatedText":["Xin chao"]}'
    def send(request,timeout):calls.append(request);return Response()
    monkeypatch.setattr('fonesi_edit.services.translation.urlopen',send)
    s=Store(tmp_path/'s.db');t=Translator(s,TranslationConfig('https://configured.example','en',enabled=True,consent_remote=True,character_limit=5))
    cues=[Cue(0,US,'Hello'),Cue(US,2*US,'locked',locked=True,translation='manual')]
    a=t.translate(cues);assert a[0].translation=='Xin chao';assert a[1].translation=='manual';assert not cues[0].translation
    assert t.translate(cues)[0].translation=='Xin chao';assert len(calls)==1
    with pytest.raises(TranslationConfiguration):t.translate([Cue(0,US,'Other')])


def test_uncertain_request_not_auto_retried(tmp_path,monkeypatch):
    count=[]
    def send(*a,**k):count.append(1);raise TimeoutError()
    monkeypatch.setattr('fonesi_edit.services.translation.urlopen',send)
    s=Store(tmp_path/'s.db');t=Translator(s,TranslationConfig('https://configured.example','en',enabled=True,consent_remote=True,character_limit=5))
    with pytest.raises(TranslationUncertain):t.translate([Cue(0,US,'Hello')])
    with pytest.raises(TranslationConfiguration):t.translate([Cue(0,US,'Hello')])
    assert len(count)==1
