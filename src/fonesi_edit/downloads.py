"""Downloader adapters. Live capability remains separate from implementation."""
from pathlib import Path
from urllib.parse import urlsplit
import io
import logging
import re

from .browser import cookie_jar,DOMAINS
from .prototypes.media import probe
from .prototypes.tools import locate_tool


def platform_for(url):
    parsed=urlsplit(url)
    if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Chỉ nhận HTTP(S) URL không chứa thông tin đăng nhập')
    host=parsed.hostname.lower()
    aliases={'youtu.be':'YouTube','b23.tv':'Bilibili','t.co':'X'}
    if host in aliases:return aliases[host]
    for platform,domains in DOMAINS.items():
        if any(host==d or host.endswith('.'+d) for d in domains):return platform
    return 'Generic'


def safe_name(value):
    name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',str(value)).strip(' .')[:100]
    if not name or name.upper().split('.')[0] in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:name='_'+name
    return name


class QuietLogger:
    def debug(self,message):pass
    def warning(self,message):pass
    def error(self,message):pass


def execute_download_job(store,job,progress,cancel):
    payload=job['payload'];url=payload['url'];platform=platform_for(url)
    binding=payload.get('account_ref');jar=cookie_jar(store,binding,payload.get('expected_identity')) if binding else None
    engine=payload.get('engine','auto')
    if engine=='auto' and payload.get('media')=='both' and platform in {'Facebook','TikTok','Douyin','Kuaishou'}:
        combined=[];warnings=[]
        for index,(chosen,media) in enumerate([('video','videos'),('gallery','images')]):
            if cancel.is_set():raise RuntimeError('Canceled')
            try:
                child={**job,'payload':{**payload,'engine':chosen,'media':media}}
                result=execute_download_job(store,child,lambda value,i=index:progress((i+value)/2),cancel)
                combined.extend(result.get('files' if job['kind']=='download' else 'items',[]))
            except Exception as exc:
                if cancel.is_set():raise
                warnings.append(chosen+': '+str(exc)[-500:])
        if not combined:raise RuntimeError('Không có artifact hợp lệ. '+'; '.join(warnings))
        return {'platform':platform,'files' if job['kind']=='download' else 'items':combined,'count':len(combined),'warnings':warnings,'complete':None,'live_channel_verified':False}
    if engine=='auto':engine='gallery' if payload.get('media')=='images' or (payload.get('media')=='both' and platform in {'Instagram','Threads','X','Xiaohongshu'}) else 'video'
    root=Path(payload.get('folder',store.path.parent/'downloads')).resolve()
    root.mkdir(parents=True,exist_ok=True)
    if engine=='gallery':return _gallery(store,job,platform,root,jar,progress,cancel)
    from yt_dlp import YoutubeDL
    from yt_dlp.postprocessor.common import PostProcessor
    files=[]
    def hook(data):
        if cancel.is_set():raise RuntimeError('Canceled')
        total=data.get('total_bytes') or data.get('total_bytes_estimate')
        if total:progress(data.get('downloaded_bytes',0)/total*.9)
    prefix=str(root/platform).replace('%','%%')+'/%(channel,uploader,creator|channel)s__%(channel_id,uploader_id,id)s'
    limit=max(0,int(payload.get('limit',0)))
    options={'quiet':True,'no_warnings':True,'logger':QuietLogger(),'socket_timeout':15,'retries':2,'fragment_retries':2,
        'noprogress':True,'overwrites':False,'continuedl':True,'windowsfilenames':True,'progress_hooks':[hook],
        'outtmpl':{'default':prefix+'/videos/%(upload_date|NA)s_%(title).100B__%(id)s.%(ext)s',
                   'subtitle':prefix+'/subtitles/%(id)s.%(ext)s','infojson':prefix+'/metadata/%(id)s.%(ext)s'},
        'writesubtitles':bool(payload.get('subtitles',True)),'writeautomaticsub':bool(payload.get('auto_subtitles',True)),
        'subtitleslangs':payload.get('languages',['vi','zh.*','en']),'subtitlesformat':'srt/vtt/best',
        'writethumbnail':bool(payload.get('thumbnail',False)),'writeinfojson':False,
        'format':f"bestvideo[height<={int(payload.get('height',1080))}]+bestaudio/best[height<={int(payload.get('height',1080))}]/best",
        'merge_output_format':'mp4','playlistend':limit or None,
        'extract_flat':'in_playlist' if job['kind']=='scan' else False,'lazy_playlist':True}
    runtime=locate_tool('node')
    if runtime:options['js_runtimes']={'node':{'path':runtime}}
    ffmpeg=locate_tool('ffmpeg')
    if ffmpeg:options['ffmpeg_location']=str(Path(ffmpeg).parent)
    if payload.get('rate_limit'):options['ratelimit']=int(payload['rate_limit'])
    if payload.get('date_after') or payload.get('date_before'):
        from yt_dlp.utils import DateRange
        options['daterange']=DateRange(payload.get('date_after'),payload.get('date_before'))
    with YoutubeDL(options) as ydl:
        if jar:
            for cookie in jar:ydl.cookiejar.set_cookie(cookie)
        class Recorder(PostProcessor):
            def run(self,info):
                path=Path(info.get('filepath') or info.get('_filename') or ydl.prepare_filename(info))
                if path.is_file():
                    actual=probe(path);files.append({'path':str(path),'id':str(info.get('id','')),'duration':actual.duration,'kind':'video'})
                return [],info
        ydl.add_post_processor(Recorder(),when='after_move')
        info=ydl.extract_info(url,download=job['kind']=='download')
        if not info:raise RuntimeError('Source returned no accessible items')
        if job['kind']=='scan':
            entries=info.get('entries') if info.get('_type') in {'playlist','multi_video'} else [info]
            items=[]
            for entry in entries or []:
                if cancel.is_set():raise RuntimeError('Canceled')
                if not entry:continue
                item={k:entry.get(k) for k in ('id','title','webpage_url','duration','upload_date')}
                item['url']=entry.get('webpage_url') or (entry.get('url') if entry.get('_type') in {'url','url_transparent'} else url)
                items.append(item)
                if limit and len(items)>=limit:break
            return {'platform':platform,'items':items,'count':len(items),'complete':False if limit and len(items)>=limit else None,'account_ref':binding,'live_channel_verified':False}
    if not files:raise RuntimeError('Downloader finished without a validated media artifact')
    progress(1)
    return {'platform':platform,'files':files,'count':len(files),'account_ref':binding,'live_channel_verified':False}


def _gallery(store,job,platform,root,jar,progress,cancel):
    from gallery_dl import config,job as gallery_job,exception
    payload=job['payload'];limit=int(payload.get('limit',0)) or 1000000
    config.clear();config.set(('extractor',),'base-directory',str(root/platform))
    config.set(('extractor',),'directory',['{_fonesi_channel}','{_fonesi_kind}'])
    config.set(('extractor',),'filename','{_fonesi_id}.{extension}')
    config.set(('extractor',),'timeout',15);config.set(('extractor',),'retries',2)
    files=[];items=[]
    def metadata(data):
        user=data.get('user') or data.get('author') or {}
        if not isinstance(user,dict):user={'name':str(user)}
        label=user.get('name') or user.get('username') or data.get('username') or payload.get('channel','channel')
        import hashlib
        uid=user.get('id') or data.get('user_id') or hashlib.sha256(payload['url'].encode()).hexdigest()[:12]
        data['_fonesi_channel']=safe_name(label)+'__'+safe_name(uid)
        ext=str(data.get('extension','')).lower()
        data['_fonesi_kind']='videos' if ext in {'mp4','webm','mov','mkv','m4v'} else 'images'
        data['_fonesi_id']=safe_name(str(data.get('id') or data.get('post_id') or data.get('filename') or len(items)))+'_'+str(data.get('num',len(items)))
        return data
    class Scanner(gallery_job.DataJob):
        def handle_url(self,url,data):
            if cancel.is_set():raise RuntimeError('Canceled')
            data=metadata(data)
            items.append({'id':data['_fonesi_id'],'kind':data['_fonesi_kind'],'title':str(data.get('description',''))[:200]})
            if len(items)>=limit:raise exception.StopExtraction()
    class Downloader(gallery_job.DownloadJob):
        def handle_directory(self,data):super().handle_directory(metadata(data))
        def handle_url(self,url,data):
            if cancel.is_set():raise RuntimeError('Canceled')
            data=metadata(data)
            wanted=payload.get('media','both')
            if wanted=='images' and data['_fonesi_kind']!='images':return
            if wanted=='videos' and data['_fonesi_kind']!='videos':return
            self.pathfmt.set_directory(data)
            super().handle_url(url,data)
            path=Path(self.pathfmt.path)
            if path.is_file():
                if data['_fonesi_kind']=='videos':probe(path)
                else:
                    from PySide6.QtGui import QImageReader
                    reader=QImageReader(str(path))
                    if not reader.canRead():
                        supported=','.join(bytes(fmt).decode('ascii','replace') for fmt in QImageReader.supportedImageFormats())
                        detected=bytes(reader.format()).decode('ascii','replace')
                        raise RuntimeError(f'Image decoder unavailable or image invalid (detected={detected or path.suffix.lstrip(".")}; supported={supported[:300]})')
                    image=reader.read()
                    if image.isNull():raise RuntimeError(f'Image decoder failed: {reader.errorString()[:240]}')
                files.append({'path':str(path),'id':data['_fonesi_id'],'kind':data['_fonesi_kind']})
            if len(files)>=limit:raise exception.StopExtraction()
    instance=Scanner(payload['url'],file=io.StringIO()) if job['kind']=='scan' else Downloader(payload['url'])
    if jar:
        for cookie in jar:instance.extractor.session.cookies.set_cookie(cookie)

    # gallery-dl handles many extractor exceptions internally and returns a status
    # code. Capture warning/error records so a failed packaged proof is diagnosable,
    # without enabling verbose logging or leaking signed URL query strings.
    diagnostics=[]
    class DiagnosticCapture(logging.Handler):
        def emit(self,record):
            try:
                message=record.getMessage()
                message=re.sub(r'(?i)\b(token|api[_-]?key|password|cookie|secret|signature|access_token)=([^&\s]+)',r'\1=[redacted]',message)
                def safe_url(match):
                    value=match.group(0)
                    parts=urlsplit(value.rstrip('),.;'))
                    return f'{parts.scheme}://{parts.netloc}{parts.path}'
                message=re.sub(r'https?://[^\s\'\"<>]+',safe_url,message)
                diagnostics.append(f'{record.levelname}: {message[:500]}')
                if len(diagnostics)>12:del diagnostics[:-12]
            except Exception:
                diagnostics.append(f'{record.levelname}: <diagnostic unavailable>')
    capture=DiagnosticCapture(level=logging.WARNING)
    logger=logging.getLogger()
    logger.addHandler(capture)
    try:
        instance.run()
    finally:
        logger.removeHandler(capture)
        capture.close()
    status=int(getattr(instance,'status',0) or 0)
    if status and not files and not items:
        detail=' | '.join(diagnostics[-6:])
        if detail:
            raise RuntimeError(f'Gallery extractor failed (status={status}): {detail[:1800]}')
        raise RuntimeError(f'Gallery extractor failed (status={status}); no valid media returned. Check extractor, HTTP transport, and image decoder.')
    result=items if job['kind']=='scan' else files
    if not result:raise RuntimeError('No accessible gallery media returned')
    progress(1)
    return {'platform':platform,'items' if job['kind']=='scan' else 'files':result,'count':len(result),'complete':False if len(result)>=limit else None,'live_channel_verified':False}
