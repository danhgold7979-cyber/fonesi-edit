"""Thin strict boundary around pinned pysubs2, not a replacement subtitle parser."""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import re
import uuid
import warnings

import pysubs2
from pysubs2.formats.subrip import SubripFormat
from pysubs2.formats.webvtt import WebVTTFormat
from pysubs2.formats.substation import EVENT_FORMAT_LINE, STYLE_FORMAT_LINE

MAX_BYTES=2*1024*1024
MAX_LINE=16384
MAX_LINES=50000
MAX_CUES=10000
ENCODINGS=frozenset({'utf-8','utf-8-sig','utf-16','utf-16-le','utf-16-be','cp1258','cp1252','gb18030','big5'})
NAMESPACE=uuid.UUID('1530bf6b-a329-4f65-9781-93c529a010e3')

class SubtitleError(ValueError):pass

@dataclass(frozen=True)
class SubtitleCue:
    id:str
    source_label:str|None
    start:Fraction
    end:Fraction
    markup_text:str # upstream text; no rendering/HTML evaluation here
    style_name:str
    layer:int
    word_timings:None=None # never infer timings from cue duration/word count

@dataclass(frozen=True)
class SubtitleDocument:
    source_sha256:str
    source_format:str
    encoding:str
    original_bytes:bytes
    cues:tuple[SubtitleCue,...]
    diagnostics:tuple[str,...]


def _timed_blocks(text,format_):
    """Validate framing and preserve labels; timestamp/text conversion stays upstream."""
    blocks=re.split(r'\n[ \t]*\n',text.strip()) if text.strip() else []
    if format_=='vtt':
        if not blocks or blocks[0].strip()!='WEBVTT':
            raise SubtitleError('Only plain WEBVTT header supported; metadata/layout needs explicit mapping')
        blocks=blocks[1:]
    normalized=[];labels=[]
    parser=WebVTTFormat if format_=='vtt' else SubripFormat
    for block in blocks:
        lines=block.split('\n')
        if len(lines)>1 and '-->' not in lines[0]:
            label=lines.pop(0)
            if format_=='srt' and not label.isdecimal():raise SubtitleError('Invalid SRT cue label')
            if format_=='vtt' and (label in {'STYLE','REGION'} or label.startswith('NOTE')):
                raise SubtitleError('VTT metadata block needs explicit mapping')
        else:label=None
        if not lines or lines[0].count('-->')!=1:raise SubtitleError('Missing cue timestamp separator')
        times=lines[0].split('-->')
        for value in times:
            match=parser.TIMESTAMP.fullmatch(value.strip())
            if match is None:raise SubtitleError('Invalid timestamp or unsupported VTT cue settings')
            parts=match.groups()
            if len(parts[-1])!=3 or int(parts[-2])>=60 or int(parts[-3])>=60:
                raise SubtitleError('Timestamp precision/range invalid')
        if len(lines)<2 or not '\n'.join(lines[1:]).strip():raise SubtitleError('Empty subtitle cue')
        labels.append(label)
        # Avoid upstream VTT treating a named next cue ID as prior cue text.
        normalized.append('\n'.join(lines))
        if len(labels)>MAX_CUES:raise SubtitleError('Subtitle cue limit exceeded')
    return '\n\n'.join(normalized),labels



def _substation_framing(lines, format_):
    """Reject layouts upstream would silently reinterpret; conversion remains upstream."""
    style_section='[V4+ Styles]' if format_=='ass' else '[V4 Styles]'
    allowed={'[Script Info]', '[Events]', style_section}
    section=None; declared=False; dialogues=0
    for raw in lines:
        line=raw.strip()
        if not line or line.startswith(';'):continue
        if line.startswith('['):
            if line not in allowed:raise SubtitleError('Unsupported ASS/SSA section or attachment')
            section=line;declared=False;continue
        if section is None:raise SubtitleError('Missing ASS/SSA section framing')
        if section=='[Script Info]':
            if ':' not in line or line.startswith(('Dialogue:', 'Comment:', 'Style:', 'Format:')):
                raise SubtitleError('Invalid ASS/SSA script metadata')
            continue
        expected=EVENT_FORMAT_LINE[format_] if section=='[Events]' else STYLE_FORMAT_LINE[format_]
        if line.startswith('Format:'):
            # Whitespace is harmless; field order/spelling is not. Text must remain last.
            if [p.strip() for p in line.split(':',1)[1].split(',')] != [p.strip() for p in expected.split(':',1)[1].split(',')]:
                raise SubtitleError('Unsupported ASS/SSA field layout')
            declared=True;continue
        prefixes=('Dialogue:', 'Comment:') if section=='[Events]' else ('Style:',)
        if not declared or not line.startswith(prefixes):
            raise SubtitleError('Invalid ASS/SSA record or missing canonical Format declaration')
        count=len(expected.split(':',1)[1].split(','))
        values=line.split(':',1)[1].lstrip().split(',',count-1) if section=='[Events]' else line.split(':',1)[1].lstrip().split(',')
        if len(values)!=count:raise SubtitleError('Invalid ASS/SSA field count')
        if section=='[Events]':
            for value in values[1:3]:
                if re.fullmatch(r'[0-9]:[0-5][0-9]:[0-5][0-9]\.[0-9]{2}',value.strip()) is None:
                    raise SubtitleError('ASS/SSA timestamp precision/range invalid')
            if line.startswith('Dialogue:'):
                dialogues+=1
                if dialogues>MAX_CUES:raise SubtitleError('Subtitle cue limit exceeded')
    return dialogues


def parse_subtitles(data:bytes,format_:str,*,encoding='utf-8-sig',allow_empty=False):
    if type(data) is not bytes or len(data)>MAX_BYTES:raise SubtitleError('Subtitle byte limit/type invalid')
    if type(format_) is not str or format_ not in {'srt','vtt','ass','ssa'}:raise SubtitleError('Explicit supported subtitle format required')
    if type(encoding) is not str or encoding not in ENCODINGS:raise SubtitleError('Explicit supported encoding required')
    if type(allow_empty) is not bool:raise SubtitleError('Explicit empty policy required')
    try:text=data.decode(encoding).replace('\r\n','\n').replace('\r','\n')
    except UnicodeError:raise SubtitleError('Subtitle encoding is invalid') from None
    if '\0' in text:raise SubtitleError('NUL in subtitle text')
    lines=text.split('\n')
    if len(lines)>MAX_LINES or any(len(line)>MAX_LINE for line in lines):
        raise SubtitleError('Subtitle line/resource limit exceeded')
    labels=None;diagnostics=[];expected_dialogues=None
    if format_ in {'srt','vtt'}:
        parsed_text,labels=_timed_blocks(text,format_)
    else:
        expected_dialogues=_substation_framing(lines,format_)
        parsed_text=text
        diagnostics.append('ASS_STYLE_MAPPING_PENDING_ORIGINAL_PRESERVED')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error') # reject upstream default/clamp/fidelity warnings
            parsed=pysubs2.SSAFile.from_string(parsed_text,format_=format_,keep_html_tags=True)
    except Exception:
        # Upstream#120 can raise bare ValueError. Never replace bad times by zero.
        raise SubtitleError('Malformed or unsupported subtitle data') from None
    events=[e for e in parsed if not e.is_comment]
    if (len(events)>MAX_CUES or (labels is not None and len(events)!=len(labels)) or
        (expected_dialogues is not None and len(events)!=expected_dialogues)):
        raise SubtitleError('Cue count mismatch or resource limit exceeded')
    if not events and not allow_empty:raise SubtitleError('No usable subtitle cues')
    if not events and text.strip() and format_ not in {'vtt','ass','ssa'}:
        raise SubtitleError('Nonempty subtitle content could not be parsed')
    digest=sha256(data).hexdigest();cues=[]
    for i,event in enumerate(events):
        if (type(event.start) is not int or type(event.end) is not int or
            not 0<=event.start<event.end or event.is_drawing):
            raise SubtitleError('Invalid cue time interval or unsupported ASS drawing')
        if len(event.text)>MAX_LINE*4 or not event.text.strip():raise SubtitleError('Empty/oversized cue text')
        cues.append(SubtitleCue(str(uuid.uuid5(NAMESPACE,f'{digest}:{format_}:{i}')),
                    None if labels is None else labels[i],Fraction(event.start,1000),
                    Fraction(event.end,1000),event.text,event.style,event.layer))
    return SubtitleDocument(digest,format_,encoding,data,tuple(cues),tuple(diagnostics))
