"""Pinned downloader adapters with explicit evidence and non-overwriting publication."""
from pathlib import Path
from urllib.parse import urlparse,urlunparse,parse_qs,urlencode
from urllib.request import Request,urlopen
import importlib.metadata
import json
import shutil
import sys
import tempfile
from ..core.paths import safe_name,publish_no_clobber,channel_directory
from ..core.process import run,Cancelled
from .media import validate_media,validate_image
from .browser import PLATFORMS


def identify(url:str):
    parsed=urlparse(url.strip())
    if parsed.scheme not in {'https','http'} or not parsed.hostname or parsed.username or parsed.password:raise ValueError('URL must be HTTP(S) without credentials')
    host=parsed.hostname.lower();platform=None
    for name,(domain,_) in PLATFORMS.items():
        if host==domain or host.endswith('.'+domain):platform=name;break
    if host in {'youtu.be'}:platform='YouTube'
    if host in {'twitter.com','www.twitter.com'}:platform='X'
    if host in {'threads.com','www.threads.com'}:platform='Threads'
    if host in {'127.0.0.1','localhost','::1'}:platform='Local test HTTP'
    if not platform:raise ValueError('URL platform is not in the configured connector registry')
    query=parse_qs(parsed.query)
    if platform=='YouTube':query={k:v for k,v in query.items() if k in {'v','list'}}
    else:query={k:v for k,v in query.items() if not k.startswith('utm_')}
    canonical=urlunparse((parsed.scheme,parsed.netloc,parsed.path.rstrip('/') or '/',parsed.params,urlencode(query,doseq=True),''))
    kind='item'
    if 'list' in query:kind='playlist'
    elif any(x in parsed.path for x in ['/channel/','/@','/user/']) or parsed.path.startswith('/@'):kind='profile'
    return {'platform':platform,'url':canonical,'kind':kind,'capability':'unverified' if platform!='Local test HTTP' else 'local_fixture_only'}


def identify_many(text:str):
    result=[];seen=set()
    for url in text.splitlines():
        if not url.strip():continue
        item=identify(url)
        if item['url'] not in seen:result.append(item);seen.add(item['url'])
    return result


def module_command(module):
    if getattr(sys,'frozen',False):return [sys.executable,'--tool',module]
    return [sys.executable,'-m',module]


def scan(url:str,filters=None,cancel=lambda:False):
    info=identify(url);filters=filters or {}
    if info['platform']=='Local test HTTP':return {'items':[{'id':Path(urlparse(url).path).stem,'url':url,'title':Path(urlparse(url).path).name}],'completeness':'single_item','source':info}
    args=module_command('yt_dlp')+['--flat-playlist','--dump-single-json','--skip-download','--no-warnings','--socket-timeout','20','--retries','2']
    if filters.get('limit'):args+=['--playlist-end',str(filters['limit'])]
    args+=[info['url']];data=json.loads(run(args,cancel=cancel,timeout=120))
    entries=data.get('entries') or [data];items=[]
    for e in entries:
        if not e:continue
        duration=e.get('duration')
        if duration is not None and (duration<filters.get('min_duration',0) or duration>filters.get('max_duration',float('inf'))):continue
        items.append({'id':str(e.get('id','')),'url':e.get('webpage_url') or e.get('url'),'title':e.get('title','Untitled'),'duration':duration,'source_id':data.get('channel_id') or data.get('uploader_id') or data.get('id')})
    return {'items':items,'completeness':'partial' if filters.get('limit') else 'unknown' if 'entries' in data else 'single_item',
            'warning':'A returned playlist does not prove a complete historical channel scan','source':info,'tool_version':importlib.metadata.version('yt-dlp')}


def download(snapshot,*,cancel=lambda:False,progress=lambda *a:None):
    info=identify(snapshot['url'])
    if snapshot.get('binding_id'):raise ValueError('Authenticated download is blocked until real Chrome session handoff is verified; no public fallback')
    root=Path(snapshot['output_root']).resolve();root.mkdir(parents=True,exist_ok=True)
    item_id=safe_name(str(snapshot.get('item_id') or Path(urlparse(info['url']).path).stem or 'item'),60)
    directory=channel_directory(root,info['platform'],snapshot.get('channel','Nguồn'),snapshot.get('source_id',item_id))
    kind=snapshot.get('media_kind','video');directory=directory/('images' if kind=='image' else 'videos');directory.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.fonesi-download-',dir=directory) as d:
        stage=Path(d);progress('downloading',None,'Tải vào staging; chưa công nhận hoàn tất')
        if info['platform']=='Local test HTTP':
            suffix=Path(urlparse(info['url']).path).suffix or ('.png' if kind=='image' else '.mp4');path=stage/('media'+suffix)
            with urlopen(Request(info['url'],headers={'User-Agent':'FonesiEdit-local-proof'}),timeout=20) as source,path.open('wb') as out:
                total=int(source.headers.get('Content-Length',0));read=0
                while block:=source.read(1024*1024):
                    if cancel():raise Cancelled('Download canceled')
                    read+=len(block);out.write(block);progress('downloading',read/total if total else None,f'{read} bytes')
        elif kind=='image':
            run(module_command('gallery_dl')+['--no-input','--directory',str(stage),'--retries','2',info['url']],cancel=cancel,timeout=600)
        else:
            height=int(snapshot.get('max_height',1080));args=module_command('yt_dlp')+['--no-playlist','--no-warnings','--retries','2','--socket-timeout','20','-f',f'bv*[height<={height}]+ba/b[height<={height}]','--merge-output-format','mp4','-o',str(stage/'%(id)s.%(ext)s')]
            if snapshot.get('rate_limit'):args+=['--limit-rate',str(snapshot['rate_limit'])]
            if snapshot.get('subtitles'):args+=['--write-subs','--write-auto-subs','--sub-langs',snapshot.get('subtitle_languages','vi,en,zh.*')]
            run(args+[info['url']],cancel=cancel,timeout=3600)
        candidates=[p for p in stage.rglob('*') if p.is_file() and p.suffix.lower() in ({'.jpg','.jpeg','.png','.webp','.gif'} if kind=='image' else {'.mp4','.mkv','.webm','.mov'})]
        if not candidates:raise ValueError('Downloader produced no candidate media; no success claimed')
        artifacts=[]
        for n,path in enumerate(sorted(candidates)):
            evidence=validate_image(path) if kind=='image' else validate_media(path,cancel=cancel)
            if cancel():raise Cancelled('Canceled before publication')
            output=publish_no_clobber(path,directory/(item_id+(f'_{n+1:03}' if len(candidates)>1 else '')+path.suffix))
            evidence['path']=str(output);artifacts.append(evidence)
        sidecars=[]
        for path in stage.rglob('*'):
            if path.is_file() and path.suffix in {'.srt','.vtt','.ass'}:
                from .subtitles import read_subtitles
                read_subtitles(path);dest=directory.parent/'subtitles';dest.mkdir(exist_ok=True);sidecars.append(str(publish_no_clobber(path,dest/path.name)))
        return {'validated':True,'path':artifacts[0]['path'],'artifacts':artifacts,'subtitles':sidecars,'platform':info['platform'],
                'evidence_scope':'localhost transport only' if info['platform']=='Local test HTTP' else 'single URL download; not full-channel certification'}
