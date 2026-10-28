"""Downloader adapters. Live capability remains separate from implementation."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
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


def selectable_scan_url(value):
    """Return a public, re-downloadable URL or None, never a signed media URL.

    Playlist scan metadata may contain temporary CDN URLs with authentication
    in query strings. Those must not be persisted into SQLite job results.
    Only ordinary HTTP(S) links and canonical YouTube watch IDs are accepted.
    """
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme not in {'http', 'https'} or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.fragment):
            return None
        if parts.query:
            host = parts.hostname.lower()
            if (host not in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}
                    or parts.path != '/watch'):
                return None
            pairs = parse_qsl(parts.query, keep_blank_values=True, strict_parsing=True)
            if (not pairs or any(k not in {'v', 'list', 'index'} or
                    not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', v)
                    for k, v in pairs)):
                return None
        # Keep the original canonical link, including YouTube watch IDs,
        # but never the URL fragment or a URL carrying other query keys.
        return value
    except (TypeError, ValueError):
        return None



def scan_video_item_url(entry, source_url=None, *, single=False):
    """Resolve a stable page URL from yt-dlp scan metadata without probing live."""
    candidates = [entry.get('webpage_url'), entry.get('original_url')]
    if entry.get('_type') in {'url','url_transparent'}:
        candidates.append(entry.get('url'))
    if single:
        candidates.append(source_url)
    for candidate in candidates:
        safe = selectable_scan_url(candidate)
        if safe:
            return safe
    # yt-dlp playlist flat entries may only expose extractor + stable ID.
    # Generate a canonical watch URL *only* for known video ID formats.
    source_id = entry.get('id')
    key = entry.get('ie_key')
    if key in {'Youtube', 'YoutubeIE'} and isinstance(source_id, str):
        if re.fullmatch(r'[A-Za-z0-9_-]{11}', source_id):
            return f'https://www.youtube.com/watch?v={source_id}'
    if key in {'BiliBili', 'Bilibili', 'BiliBiliIE'} and isinstance(source_id, str):
        if re.fullmatch(r'BV[A-Za-z0-9]{10}', source_id):
            return f'https://www.bilibili.com/video/{source_id}'
    return None


def selected_download_payloads(scan_job, indices):
    """Turn verified scan row indices into individual frozen download requests.

    Only selectable items from this *successful* scan are accepted. Account
    binding and output settings are inherited from the scan snapshot, not from
    whatever profile is currently selected in the desktop UI.
    """
    if scan_job.get('kind') != 'scan' or scan_job.get('state') != 'succeeded':
        raise ValueError('Chỉ chọn mục từ job quét đã hoàn tất')
    original = scan_job.get('payload') or {}
    result = scan_job.get('result') or {}
    source_platform = platform_for(original.get('url', ''))
    if result.get('platform') != source_platform:
        raise ValueError('Nguồn quét không trùng nền tảng trong snapshot')
    entries = result.get('items')
    if not isinstance(entries, list):
        raise ValueError('Kết quả quét không có danh sách nội dung')
    indices = list(indices)
    if not indices or len(set(indices)) != len(indices):
        raise ValueError('Chọn ít nhất một mục không trùng lặp')
    requests = []
    for index in indices:
        if type(index) is not int or not 0 <= index < len(entries):
            raise ValueError('Chỉ số nội dung quét không hợp lệ')
        item = entries[index]
        if not isinstance(item, dict):
            raise ValueError('Nội dung quét không hợp lệ')
        url = selectable_scan_url(item.get('url'))
        if not url or item.get('selectable') is False:
            raise ValueError('Mục đã chọn không có URL tải lại an toàn')
        item_platform = platform_for(url)
        if original.get('account_ref') and item_platform != source_platform:
            raise PermissionError('Không chuyển phiên tài khoản sang host khác từ kết quả quét')
        kind = item.get('kind', 'video')
        if kind not in {'video', 'videos', 'images'}:
            raise ValueError('Loại media chưa có adapter tải từng mục')
        # A gallery extractor can carry video media too; do not switch it
        # to yt-dlp and silently alter extractor behaviour.
        engine = 'gallery' if kind == 'images' or kind == 'videos' and (
            original.get('engine') == 'gallery' or source_platform in {'Instagram','Threads','X','Xiaohongshu'}
        ) else 'video'
        payload = {key:value for key,value in original.items() if key != '_tools'}
        payload.update(url=url,engine=engine,
                       media='images' if kind == 'images' else 'videos',limit=1)
        requests.append(payload)
    return requests


class QuietLogger:
    def debug(self,message):pass
    def warning(self,message):pass
    def error(self,message):pass


def execute_download_job(store,job,progress,cancel):
    payload=job['payload'];url=payload['url'];platform=platform_for(url)
    engine=payload.get('engine','auto')
    media=payload.get('media','both')
    if engine not in {'auto','video','gallery'}:
        raise ValueError('Unsupported downloader engine; use auto, video or gallery')
    if media not in {'both','videos','images'}:
        raise ValueError('Unsupported media type; use both, videos or images')
    try:
        limit=int(payload.get('limit',0))
    except (ValueError,TypeError):
        raise ValueError('Download limit must be a nonnegative integer') from None
    if limit<0:
        raise ValueError('Download limit must be a nonnegative integer')
    binding=payload.get('account_ref');jar=cookie_jar(store,binding,payload.get('expected_identity')) if binding else None
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
                from .worker import sanitize_error_message
                warnings.append(chosen+': '+sanitize_error_message(exc,limit=500))
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
                item={k:entry.get(k) for k in ('id','title','duration','upload_date')}
                item['url']=scan_video_item_url(entry,url,single=entry is info)
                item['kind']='video'
                item['selectable']=bool(item['url'])
                if not item['selectable']:
                    item['reason']='Không có URL tải lại an toàn; hãy mở bài trực tiếp'
                items.append(item)
                if limit and len(items)>=limit:break
            return {'platform':platform,'items':items,'count':len(items),'complete':False if limit and len(items)>=limit else None,'account_ref':binding,'live_channel_verified':False}
    if not files:raise RuntimeError('Downloader finished without a validated media artifact')
    progress(1)
    return {'platform':platform,'files':files,'count':len(files),'account_ref':binding,'live_channel_verified':False}


def _gallery(store,job,platform,root,jar,progress,cancel):
    from gallery_dl import config,job as gallery_job,exception
    payload=job['payload'];limit=max(0,int(payload.get('limit',0))) or 1000000
    config.clear();config.set(('output',),'mode','null')
    config.set(('extractor',),'base-directory',str(root/platform))
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
            candidates=[data.get('post_url'),data.get('postlink'),
                        data.get('webpage_url'),url]
            safe=next((link for candidate in candidates
                if (link:=selectable_scan_url(candidate))),None)
            entry={'id':data['_fonesi_id'],'kind':data['_fonesi_kind'],
                   'title':str(data.get('description',''))[:200],
                   'url':safe,'selectable':bool(safe)}
            if not safe:
                entry['reason']='URL media chỉ có dạng tạm/đã ký hoặc không hợp lệ'
            items.append(entry)
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
        # gallery-dl only creates the requests session during extractor.initialize().
        # Initialize first, then attach the selected account's cookies to that
        # session. Job.run() safely calls the now-idempotent initializer again.
        instance.extractor.initialize()
        for cookie in jar:
            instance.extractor.session.cookies.set_cookie(cookie)

    # gallery-dl handles many extractor exceptions internally and returns a status
    # code. Capture warning/error records so a failed packaged proof is diagnosable,
    # without enabling verbose logging or leaking signed URL query strings.
    diagnostics=[]
    class DiagnosticCapture(logging.Handler):
        def emit(self,record):
            try:
                from .worker import sanitize_error_message
                message=sanitize_error_message(record.getMessage(),limit=500)
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
