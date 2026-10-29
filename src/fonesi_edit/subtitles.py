from dataclasses import asdict,dataclass,replace
from pathlib import Path
import hashlib
import html
import json
import os
import re
import tempfile
import time
from urllib.request import Request,urlopen
from urllib.parse import urlsplit

import pysubs2
from .domain import canonical,identifier
from .prototypes.subtitles import Cue,map_trimmed_cues


@dataclass
class Caption:
    start_ms:int
    end_ms:int
    text:str
    source_text:str=''
    locked:bool=False
    id:str=''

    def __post_init__(self):
        if not self.id:self.id=identifier()
        if self.start_ms<0 or self.end_ms<=self.start_ms:raise ValueError('Invalid caption interval')


def read_captions(path:Path):
    data=pysubs2.load(str(path),encoding='utf-8-sig')
    return [Caption(event.start,event.end,event.plaintext) for event in data if not event.is_comment and event.plaintext.strip()]


def write_captions(path:Path,captions,overwrite=False):
    if path.exists() and not overwrite:raise FileExistsError(path)
    data=pysubs2.SSAFile()
    for cue in captions:
        if cue.end_ms<=cue.start_ms:raise ValueError('Invalid caption interval')
        data.events.append(pysubs2.SSAEvent(start=cue.start_ms,end=cue.end_ms,text=cue.text.replace('\n',r'\N')))
    path.parent.mkdir(parents=True,exist_ok=True)
    # Serialize before touching an existing user-edited subtitle document.
    encoded=data.to_string(format_=path.suffix.lstrip('.')).encode('utf-8')
    # Both creation and replacement stage complete bytes before publication.
    # Writing straight to path.open('xb') could expose a truncated caption if
    # the writer/fsync failed, which a subsequent recovery might see as output.
    descriptor, temporary = tempfile.mkstemp(
        prefix='.fonesi-caption-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            # Atomic swap preserves manual edits if writing the temp file fails.
            os.replace(temporary,path)
        else:
            try:
                # The destination is absent until the fully synced inode is
                # linked. A concurrent publisher fails with FileExistsError.
                os.link(temporary,path)
            except FileExistsError:
                raise
            except OSError as exc:
                raise RuntimeError(
                    'Atomic subtitle creation requires hard-link support; '
                    'the destination was not published') from exc
    finally:
        Path(temporary).unlink(missing_ok=True)


def _split_caption_text(value):
    """Split without dropping whitespace or inventing new source/target text."""
    import unicodedata
    if not isinstance(value,str) or len(value)<2:
        raise ValueError('Câu quá ngắn để tách mà không mất nội dung')
    middle=len(value)//2
    candidates=[]
    for point in range(1,len(value)):
        # Avoid splitting combining marks or a zero-width-joiner sequence.
        if (unicodedata.combining(value[point]) or value[point] in '\ufe0e\ufe0f\u200d'
                or value[point-1]=='\u200d'):
            continue
        if value[:point].strip() and value[point:].strip():
            candidates.append(point)
    if not candidates:
        raise ValueError('Câu không có vị trí tách giữ nguyên cả hai phần')
    boundary=[point for point in candidates
              if value[point-1].isspace() or value[point].isspace()]
    point=min(boundary or candidates,key=lambda item:(abs(item-middle),item))
    return value[:point],value[point:]


def split_caption(cue):
    """Split a bilingual cue into two positive intervals while preserving text."""
    if cue.end_ms-cue.start_ms<2:
        raise ValueError('Cue quá ngắn để tách thành hai khoảng dương')
    first,second=_split_caption_text(cue.text)
    if cue.source_text:
        original_first,original_second=_split_caption_text(cue.source_text)
    else:
        original_first=original_second=''
    middle=(cue.start_ms+cue.end_ms)//2
    return (Caption(cue.start_ms,middle,first,original_first,cue.locked),
            Caption(middle,cue.end_ms,second,original_second,cue.locked))


def merge_captions(cues):
    """Merge selected rows without silently discarding bilingual source text."""
    cues=list(cues)
    if len(cues)<2:
        raise ValueError('Cần ít nhất hai cue để gộp')
    original=('\n'.join(c.source_text or c.text for c in cues)
              if any(c.source_text for c in cues) else '')
    return Caption(min(c.start_ms for c in cues),
                   max(c.end_ms for c in cues),
                   '\n'.join(c.text for c in cues),
                   original,
                   any(c.locked for c in cues))


def caption_warnings(captions,duration_ms=None):
    warnings=[];last_end=0
    for i,cue in enumerate(captions,1):
        if cue.start_ms<last_end:warnings.append(f'Cue {i}: chồng thời gian')
        if cue.end_ms-cue.start_ms<400:warnings.append(f'Cue {i}: hiển thị ngắn')
        if len(cue.text)>100:warnings.append(f'Cue {i}: nhiều chữ')
        if duration_ms is not None and cue.end_ms>duration_ms:warnings.append(f'Cue {i}: vượt video')
        last_end=max(last_end,cue.end_ms)
    return warnings


def translation_endpoint(endpoint):
    value=urlsplit(endpoint)
    if value.username or value.password or value.query or value.fragment:raise ValueError('Endpoint không được chứa tài khoản, khóa hoặc query; nhập khóa qua trường API riêng')
    if not value.hostname or (value.scheme!='https' and not (value.scheme=='http' and value.hostname in {'127.0.0.1','localhost','::1'})):raise ValueError('LibreTranslate requires HTTPS or a local service')
    return endpoint.rstrip('/')


def _request_translation(texts,source,target,config):
    provider=config.get('provider','google')
    if provider=='google':
        key=os.environ.get('FONESI_GOOGLE_TRANSLATE_API_KEY')
        if not key:raise PermissionError('Thiếu FONESI_GOOGLE_TRANSLATE_API_KEY; không gọi dịch giả')
        url='https://translation.googleapis.com/language/translate/v2'
        body={'q':texts,'target':target,'format':'text'}
        if source!='auto':body['source']=source
        headers={'Content-Type':'application/json','X-Goog-Api-Key':key}
    elif provider=='libre':
        url=translation_endpoint(config.get('endpoint',''))+'/translate'
        body={'q':texts,'source':source,'target':target,'format':'text'};headers={'Content-Type':'application/json'}
        key=os.environ.get('FONESI_LIBRETRANSLATE_API_KEY')
        if key:body['api_key']=key
    else:raise ValueError('Unknown translation provider')
    try:
        with urlopen(Request(url,data=json.dumps(body).encode(),headers=headers),timeout=45) as response:data=json.load(response)
    except Exception as exc:raise RuntimeError(f'Translation request not confirmed ({type(exc).__name__}); no automatic paid retry') from None
    values=[item['translatedText'] for item in data.get('data',{}).get('translations',[])] if provider=='google' else data.get('translatedText',[])
    if isinstance(values,str):values=[values]
    if len(values)!=len(texts) or any(not str(value).strip() for value in values):raise RuntimeError('Translation cue count/content mismatch')
    return [html.unescape(str(value)) for value in values]


def translate_captions(store,captions,source='auto',target='vi',config=None,progress=lambda n:None,cancel=None,transport=None):
    config=config or {};transport=transport or _request_translation
    result=[replace(c) for c in captions];missing=[]
    glossary=config.get('glossary',{})
    for index,cue in enumerate(result):
        if cue.locked:continue
        original=cue.source_text or cue.text
        # Daily quota changes must not invalidate an otherwise identical translation.
        # Provider, glossary, endpoint and translation-affecting options stay in
        # the fingerprint so cache entries never cross incompatible settings.
        translation_config={k:v for k,v in config.items() if k not in {'daily_limit'}}
        key='translation:'+hashlib.sha256(
            canonical([original,source,target,translation_config]).encode()).hexdigest()
        cached=store.cached(key)
        if cached:cue.source_text=original;cue.text=cached['text']
        else:missing.append((index,key,original))
    for start in range(0,len(missing),32):
        if cancel and cancel.is_set():raise RuntimeError('Canceled')
        batch=missing[start:start+32];texts=[];protected=[]
        for _,_,original in batch:
            terms={}
            for number,(term,value) in enumerate(glossary.items()):
                if term and term in original:
                    marker=f'FONESIPROTECTEDTERM{number}END';original=original.replace(term,marker);terms[marker]=value
            texts.append(original);protected.append(terms)
        chars=sum(len(text) for text in texts)
        quota=int(config.get('daily_limit',100000))
        usage_key='translation_usage:'+config.get('provider','google')+':'+time.strftime('%Y-%m-%d',time.gmtime())
        with store.connect() as conn:
            conn.execute('BEGIN IMMEDIATE');row=conn.execute('SELECT value FROM settings WHERE key=?',(usage_key,)).fetchone()
            used=json.loads(row[0]) if row else 0
            if used+chars>quota:raise PermissionError('Daily translation character limit reached')
            conn.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(usage_key,json.dumps(used+chars)))
        translated=transport(texts,source,target,config)
        if len(translated)!=len(batch):raise RuntimeError('Translation result count mismatch')
        for (index,key,original),text,terms in zip(batch,translated,protected,strict=True):
            for marker,value in terms.items():
                if marker not in text:raise RuntimeError('Provider altered a protected glossary marker; review translation')
                text=text.replace(marker,value)
            result[index].source_text=original;result[index].text=text;store.cache(key,{'text':text})
        progress(min(.99,(start+len(batch))/max(1,len(missing))))
    return result


def execute_translation(store,payload,progress,cancel):
    cues=[Caption(**c) for c in payload['captions']] if 'captions' in payload else read_captions(Path(payload['source']))
    result=translate_captions(store,cues,payload.get('source_language','auto'),payload.get('target_language','vi'),payload.get('config',{}),progress,cancel)
    output=Path(payload['output']);reused=False
    if output.exists():
        expected=[(c.start_ms,c.end_ms,c.text) for c in result]
        if [(c.start_ms,c.end_ms,c.text) for c in read_captions(output)]!=expected:raise FileExistsError('Tệp sub đã có nội dung khác; không ghi đè: '+output.name)
        reused=True
    else:write_captions(output,result)
    return {'output':str(output),'captions':[asdict(c) for c in result],'warnings':caption_warnings(result),'reused':reused}
