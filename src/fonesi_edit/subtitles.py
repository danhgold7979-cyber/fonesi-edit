"""Bounded plain SRT import/export and exact time mapping. No translation."""
from dataclasses import dataclass
from fractions import Fraction
import re
from fonesi_edit.timing import Interval,ClipMap

@dataclass(frozen=True)
class Cue:
    id: str
    interval: Interval
    text: str
    locked: bool=False
    def __post_init__(self):
        if not isinstance(self.id,str) or not self.id or len(self.id)>128:raise ValueError('INVALID_CUE_ID')
        if not isinstance(self.interval,Interval):raise ValueError('INVALID_INTERVAL')
        if not isinstance(self.text,str) or not self.text.strip() or '\x00' in self.text or len(self.text)>100000:raise ValueError('INVALID_CUE_TEXT')
        if type(self.locked) is not bool:raise ValueError('INVALID_LOCK')

@dataclass(frozen=True)
class SubtitleDocument:
    cues: tuple[Cue,...]
    def __post_init__(self):
        if not isinstance(self.cues,tuple) or len(self.cues)>10000 or not all(isinstance(c,Cue) for c in self.cues):raise ValueError('INVALID_CUES')
        if len({c.id for c in self.cues})!=len(self.cues):raise ValueError('DUPLICATE_CUE_ID')
    def diagnostics(self):
        overlaps=set();furthest=None
        for cue in sorted(self.cues,key=lambda item:item.interval.start):
            if furthest is not None and cue.interval.start<furthest.interval.end:
                overlaps.update((cue.id,furthest.id))
            if furthest is None or cue.interval.end>furthest.interval.end:furthest=cue
        result=[];previous=None
        for cue in self.cues:
            if previous is not None and cue.interval.start<previous.interval.start:result.append(('OUT_OF_ORDER',cue.id))
            if cue.id in overlaps:result.append(('OVERLAP',cue.id))
            previous=cue
        return tuple(result)
    def map_to(self,mapping: ClipMap):
        mapped=[]
        for cue in self.cues:
            interval=mapping.map_interval(cue.interval)
            if interval is not None:mapped.append(Cue(cue.id,interval,cue.text,cue.locked))
        return SubtitleDocument(tuple(mapped))


def parse_time(value):
    match=re.fullmatch(r'(\d{2,4}):([0-5]\d):([0-5]\d),(\d{3})',value)
    if match is None:raise ValueError('INVALID_TIMESTAMP')
    hour,minute,second,milli=map(int,match.groups())
    return Fraction(((hour*60+minute)*60+second)*1000+milli,1000)


def parse_srt(data: bytes):
    if not isinstance(data,bytes) or len(data)>4194304:raise ValueError('SUBTITLE_TOO_LARGE')
    try:text=data.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').strip('\n')
    except UnicodeError:raise ValueError('UTF8_REQUIRED') from None
    if not text.strip():return SubtitleDocument(())
    blocks=re.split(r'\n[ \t]*\n',text)
    if len(blocks)>10000:raise ValueError('TOO_MANY_CUES')
    cues=[]
    for ordinal,block in enumerate(blocks,1):
        lines=block.split('\n')
        if len(lines)<3 or not re.fullmatch(r'\d{1,9}',lines[0].strip()):raise ValueError('INVALID_SRT_BLOCK')
        times=re.fullmatch(r'([^ ]+)\s+-->\s+([^ ]+)',lines[1].strip())
        if times is None:raise ValueError('INVALID_TIME_LINE')
        cues.append(Cue(f'srt-{ordinal}',Interval(parse_time(times[1]),parse_time(times[2])),'\n'.join(lines[2:])))
    return SubtitleDocument(tuple(cues))


def rounded_millis(time):
    scaled=time*1000
    return (2*scaled.numerator+scaled.denominator)//(2*scaled.denominator)


def timestamp(millis):
    total,milli=divmod(millis,1000);total,second=divmod(total,60);hour,minute=divmod(total,60)
    if hour>9999:raise ValueError('TIMESTAMP_TOO_LARGE')
    return f'{hour:02}:{minute:02}:{second:02},{milli:03}'


def export_srt(document: SubtitleDocument):
    blocks=[]
    for index,cue in enumerate(document.cues,1):
        start,end=rounded_millis(cue.interval.start),rounded_millis(cue.interval.end)
        if start>=end:raise ValueError('INTERVAL_COLLAPSED_AT_MILLISECOND_RESOLUTION')
        if cue.text.startswith('\n') or cue.text.endswith('\n') or '\r' in cue.text or re.search(r'\n[ \t]*\n',cue.text):raise ValueError('AMBIGUOUS_BLANK_LINE_IN_SRT_TEXT')
        blocks.append(f'{index}\n{timestamp(start)} --> {timestamp(end)}\n{cue.text}')
    data=('\n\n'.join(blocks)+ ('\n' if blocks else '')).encode('utf-8')
    if len(data)>4194304:raise ValueError('SUBTITLE_TOO_LARGE')
    return data
