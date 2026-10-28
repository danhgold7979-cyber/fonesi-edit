"""Common cue model, explicit language selection and loss-aware import/export."""
from dataclasses import replace
from pathlib import Path
from typing import Iterable
import re
import pysubs2
from ..core.model import Cue, TimeMap, US, uid


def read_subtitles(path: Path, language='und') -> tuple[list[Cue],list[str]]:
    subs=pysubs2.load(str(path),encoding='utf-8')
    warnings=[]
    if path.suffix.lower()=='.ass':
        warnings.append('ASS imported as timed plain text; positioning, drawings, karaoke and unsupported style overrides are not preserved. Original file is unchanged.')
    cues=[Cue(round(e.start*1000),round(e.end*1000),e.plaintext,language=language) for e in subs if not e.is_comment]
    return cues,warnings


def write_subtitles(cues: Iterable[Cue], path: Path, *, translated=True,bilingual=False):
    subs=pysubs2.SSAFile()
    for c in cues:
        text=c.translation if translated and c.translation else c.text
        if bilingual and c.translation:text=c.text+'\n'+c.translation
        subs.events.append(pysubs2.SSAEvent(start=round(c.start/1000),end=round(c.end/1000),text=text.replace('\n',r'\N')))
    subs.save(str(path),encoding='utf-8')


def map_cues(cues:list[Cue],maps:list[TimeMap]) -> list[Cue]:
    out=[]
    for m in maps:
        for c in cues:
            interval=m.interval(c.start,c.end)
            if interval:out.append(replace(c,id=uid(),start=interval[0],end=interval[1]))
    return sorted(out,key=lambda c:(c.start,c.end))


def warnings(cues:list[Cue],duration:int,max_chars=84,min_duration=300000) -> list[dict]:
    result=[];ordered=sorted(cues,key=lambda c:c.start)
    for i,c in enumerate(ordered):
        reasons=[]
        if c.start<0 or c.end<=c.start:reasons.append('invalid_time')
        if c.end>duration:reasons.append('past_video_end')
        if c.end-c.start<min_duration:reasons.append('short_duration')
        if len(c.translation or c.text)>max_chars:reasons.append('long_text')
        if any(p.end>c.start for p in ordered[:i]):reasons.append('overlap')
        result.extend({'cue_id':c.id,'reason':r} for r in reasons)
    return result


def split_cue(cue:Cue,time:int,character:int) -> tuple[Cue,Cue]:
    if not cue.start<time<cue.end or not 0<character<len(cue.text):raise ValueError('Split needs interior time and text boundary')
    if cue.translation:raise ValueError('Split translated cue explicitly in both languages first; translation is not guessed')
    return replace(cue,end=time,text=cue.text[:character].rstrip()),replace(cue,id=uid(),start=time,text=cue.text[character:].lstrip())


def merge_cues(cues:list[Cue]) -> Cue:
    if not cues:raise ValueError('No cues')
    cues=sorted(cues,key=lambda c:c.start)
    return replace(cues[0],end=max(c.end for c in cues),text='\n'.join(c.text for c in cues),
                   translation='\n'.join(c.translation for c in cues) if all(c.translation for c in cues) else '',locked=any(c.locked for c in cues))


def shift_cues(cues:list[Cue],offset:int,selected:set[str]|None=None) -> list[Cue]:
    if any(c.start+offset<0 for c in cues if selected is None or c.id in selected):raise ValueError('Offset would create negative cue time')
    return [replace(c,start=c.start+offset,end=c.end+offset) if selected is None or c.id in selected else replace(c) for c in cues]


def choose_track(tracks:list[dict],target='vi',fallback_languages=(),translation_configured=False) -> dict:
    target_tracks=[t for t in tracks if t['language']==target]
    if target_tracks:return {'track':min(target_tracks,key=lambda t:bool(t.get('automatic'))),'translate':False}
    for lang in fallback_languages:
        matching=[t for t in tracks if t['language']==lang]
        if matching:return {'track':min(matching,key=lambda t:bool(t.get('automatic'))),'translate':translation_configured}
    if translation_configured and tracks:return {'track':min(tracks,key=lambda t:bool(t.get('automatic'))),'translate':True}
    return {'track':None,'translate':False,'warning':'No permitted subtitle language; continue without subtitles by default'}


def match_subtitle(video:Path,paths:list[Path],source_id='') -> Path|None:
    matches=[p for p in paths if p.stem==video.stem or p.stem.startswith(video.stem+'.') or (source_id and source_id in re.split(r'[._-]',p.stem))]
    if len(matches)>1:raise ValueError('Ambiguous subtitle match; select language/file explicitly')
    return matches[0] if matches else None
