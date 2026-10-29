"""Downloader adapters. Live capability remains separate from implementation."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
import io
import logging
import math
import re
from datetime import date, datetime
from copy import deepcopy

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


def normalize_scan_date(value):
    """Return a calendar-validated YYYYMMDD date, or None for unknown metadata."""
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime('%Y%m%d')
    if not isinstance(value, str) or not re.fullmatch(
            r'(?:[0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2})', value):
        return None
    try:
        return datetime.strptime(value.replace('-', ''), '%Y%m%d').strftime('%Y%m%d')
    except ValueError:
        return None


def _scan_number(value, *, integer=False, positive=False):
    """Reject booleans, nonfinite/negative numbers and malformed numeric strings."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    if isinstance(value, str) and not re.fullmatch(
            r'[0-9]+(?:\.[0-9]+)?', value.strip()):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number < 0 or (positive and number == 0):
        return None
    if integer:
        return int(number) if number.is_integer() else None
    return number


def normalize_scan_metadata(data):
    """Keep only safe, known metadata from an extractor; never its raw URLs."""
    if not isinstance(data, dict):
        return {}
    metadata = {}
    for candidate in (data.get('upload_date'), data.get('date')):
        date_value = normalize_scan_date(candidate)
        if date_value is not None:
            metadata['upload_date'] = date_value
            break
    for key in ('duration', 'width', 'height'):
        number = _scan_number(data.get(key), integer=key != 'duration',
                              positive=key != 'duration')
        if number is not None:
            metadata[key] = number
    return metadata


def parse_scan_metadata_filters(*, after='', before='', duration_min='',
                                duration_max='', max_height='', include_missing=True):
    """Validate user inputs atomically; an unfinished edit is not a valid filter."""
    if not isinstance(include_missing, bool):
        raise ValueError('Giữ metadata thiếu phải là lựa chọn đúng/sai')

    def date_bound(value, label):
        if not isinstance(value, str):
            raise ValueError(label + ': ngày không hợp lệ')
        if not value.strip():
            return None
        result = normalize_scan_date(value.strip())
        if result is None:
            raise ValueError(label + ': dùng YYYYMMDD hoặc YYYY-MM-DD hợp lệ')
        return result

    def number_bound(value, label, *, integer=False, positive=False):
        if not isinstance(value, str):
            raise ValueError(label + ': số không hợp lệ')
        if not value.strip():
            return None
        result = _scan_number(value, integer=integer, positive=positive)
        if result is None:
            raise ValueError(label + ': nhập số hữu hạn ' +
                             ('nguyên dương' if integer else 'không âm'))
        return result

    parsed = {
        'after': date_bound(after, 'Ngày từ'),
        'before': date_bound(before, 'Ngày đến'),
        'duration_min': number_bound(duration_min, 'Thời lượng tối thiểu'),
        'duration_max': number_bound(duration_max, 'Thời lượng tối đa'),
        'max_height': number_bound(max_height, 'Chiều cao tối đa',
                                   integer=True, positive=True),
        'include_missing': include_missing,
    }
    if parsed['after'] and parsed['before'] and parsed['after'] > parsed['before']:
        raise ValueError('Ngày từ phải không muộn hơn ngày đến')
    if (parsed['duration_min'] is not None and parsed['duration_max'] is not None
            and parsed['duration_min'] > parsed['duration_max']):
        raise ValueError('Thời lượng tối thiểu phải không lớn hơn tối đa')
    return parsed


def scan_matches_metadata(item, filters):
    """Inclusive local filtering; missing metadata passes only when opted in."""
    values = normalize_scan_metadata(item)
    missing_allowed = filters['include_missing']
    after, before = filters['after'], filters['before']
    if after is not None or before is not None:
        uploaded = values.get('upload_date')
        if uploaded is None:
            if not missing_allowed:
                return False
        elif (after is not None and uploaded < after) or (before is not None and uploaded > before):
            return False
    lower, upper = filters['duration_min'], filters['duration_max']
    if lower is not None or upper is not None:
        duration = values.get('duration')
        if duration is None:
            if not missing_allowed:
                return False
        elif (lower is not None and duration < lower) or (upper is not None and duration > upper):
            return False
    if filters['max_height'] is not None:
        height = values.get('height')
        if height is None:
            if not missing_allowed:
                return False
        elif height > filters['max_height']:
            return False
    return True


MAX_SCAN_PAGE_SIZE = 200
MAX_SCAN_SNAPSHOT_ITEMS = 2000
SCAN_WINDOW_MODE = 'yt-dlp-index-window-v1'


def continuation_scan_payload(scan_job):
    """Generate a frozen next-window request only from a verified scan snapshot.

    The cursor is an yt-dlp playlist index window, NOT a provider checkpoint.
    A source can change ordering or ignore playliststart; full-channel
    completion is never inferred from this cursor.
    """
    if not isinstance(scan_job, dict) or scan_job.get('kind') != 'scan' or scan_job.get('state') != 'succeeded':
        raise ValueError('Chỉ quét tiếp từ kết quả scan đã hoàn tất')
    original = scan_job.get('payload')
    result = scan_job.get('result')
    if not isinstance(original, dict) or not isinstance(result, dict):
        raise ValueError('Thiếu snapshot quét trước')
    if original.get('engine') != 'video':
        raise ValueError('Quét tiếp chỉ hỗ trợ playlist với bộ tải video yt-dlp được chọn rõ')
    limit = original.get('limit')
    window = result.get('scan_window')
    if (type(limit) is not int or not 1 <= limit <= MAX_SCAN_PAGE_SIZE
            or not isinstance(window, dict)
            or window.get('mode') != SCAN_WINDOW_MODE
            or type(window.get('start')) is not int
            or type(window.get('limit')) is not int
            or window['limit'] != limit
            or window['start'] < 1):
        raise ValueError('Lần quét không có khoảng yt-dlp có thể tiếp tục (cần giới hạn 1–200)')
    start = window['start']
    next_start = window.get('next_start')
    if (type(next_start) is not int or next_start != start + limit
            or next_start > MAX_SCAN_SNAPSHOT_ITEMS + 1):
        raise ValueError('Không có vị trí quét tiếp hợp lệ; nguồn có thể chưa hỗ trợ hoặc đã dừng')
    if 'scan_parent_id' in original or 'scan_start' in original:
        if (not isinstance(original.get('scan_parent_id'), str)
                or type(original.get('scan_start')) is not int
                or original['scan_start'] != start):
            raise ValueError('Chuỗi quét có thông tin trang trước không hợp lệ')
    elif start != 1:
        raise ValueError('Vị trí bắt đầu không khớp scan gốc')
    if result.get('platform') != platform_for(original.get('url')):
        raise ValueError('Nền tảng trong snapshot quét không khớp nguồn')
    items = result.get('items')
    if (not isinstance(items, list) or not items
            or len(items) > MAX_SCAN_SNAPSHOT_ITEMS - limit
            or any(not isinstance(item, dict) or
                   (item.get('url') is not None and not selectable_scan_url(item.get('url')))
                   for item in items)):
        raise ValueError('Snapshot quét đầy, không hợp lệ hoặc chứa URL không an toàn')
    scan_id = scan_job.get('id')
    if not isinstance(scan_id, str) or not scan_id:
        raise ValueError('Thiếu ID scan gốc')
    payload = deepcopy({key:value for key,value in original.items()
                        if key not in {'_tools', 'scan_parent_id', 'scan_start'}})
    payload.update(scan_parent_id=scan_id, scan_start=next_start)
    return payload


def selected_download_payloads(scan_job, indices, *, subtitles_only=False):
    """Turn verified scan row indices into individual frozen download requests.

    Only selectable items from this *successful* scan are accepted. Account
    binding and output settings are inherited from the scan snapshot, not from
    whatever profile is currently selected in the desktop UI.
    """
    if type(subtitles_only) is not bool:
        raise ValueError('Chế độ tải phụ đề phải là boolean')
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
    seen_urls = set()
    for index in indices:
        if type(index) is not int or not 0 <= index < len(entries):
            raise ValueError('Chỉ số nội dung quét không hợp lệ')
        item = entries[index]
        if not isinstance(item, dict):
            raise ValueError('Nội dung quét không hợp lệ')
        url = selectable_scan_url(item.get('url'))
        if not url or item.get('selectable') is False:
            raise ValueError('Mục đã chọn không có URL tải lại an toàn')
        if url in seen_urls:
            raise ValueError('URL lặp lại trong các mục đã chọn')
        seen_urls.add(url)
        item_platform = platform_for(url)
        if original.get('account_ref') and item_platform != source_platform:
            raise PermissionError('Không chuyển phiên tài khoản sang host khác từ kết quả quét')
        kind = item.get('kind', 'video')
        if kind not in {'video', 'videos', 'images'}:
            raise ValueError('Loại media chưa có adapter tải từng mục')
        # A gallery extractor can carry video media too; do not switch it
        # to yt-dlp and silently alter extractor behaviour.
        adapter=item.get('engine')
        if adapter not in {None,'video','gallery'}:
            raise ValueError('Kết quả quét có adapter không hợp lệ')
        if kind == 'images' and adapter == 'video':
            raise ValueError('Bộ tải video không hỗ trợ mục ảnh này')
        # Keep the extractor that produced the scanned item, even when one
        # source was scanned via both engines (Facebook/TikTok mixed media).
        engine=adapter or ('gallery' if kind in {'images','videos'} else 'video')
        if subtitles_only and (kind not in {'video','videos'} or engine != 'video'):
            raise ValueError('Chỉ tải phụ đề riêng cho mục video có adapter yt-dlp, không hỗ trợ ảnh/gallery')
        payload = {key:value for key,value in original.items()
                   if key not in {'_tools','scan_parent_id','scan_start','download_mode'}}
        payload.update(url=url,engine=engine,
                       media='images' if kind == 'images' else 'videos',limit=1)
        if subtitles_only:
            payload.pop('workflow',None)
            payload.update(download_mode='subtitles_only',subtitles=True,
                           auto_subtitles=True,thumbnail=False)
        requests.append(payload)
    return requests


SUBTITLE_EXTENSIONS = frozenset({'srt', 'vtt', 'ass', 'ssa'})
MAX_SUBTITLE_BYTES = 16 * 1024 * 1024


def verified_subtitle_artifacts(info, ydl, platform_root):
    """Accept only parsable, expected sidecars; never persist subtitle source URLs.

    yt-dlp supplies requested_subtitles[lang].filepath after downloading.
    When an existing subtitle is skipped without a filepath, the expected
    name can be derived from the yt-dlp subtitle output template.
    """
    requested = info.get('requested_subtitles')
    if not isinstance(requested, dict) or not requested:
        raise RuntimeError('Nguồn không cung cấp phụ đề trong ngôn ngữ đã chọn')
    if len(requested) > 32:
        raise ValueError('Danh sách track phụ đề quá lớn')
    platform_root = Path(platform_root).resolve()
    try:
        template = Path(ydl.prepare_filename(info, outtmpl_type='subtitle'))
    except (TypeError, ValueError, KeyError, OSError) as exc:
        raise RuntimeError('Không xác định được đường dẫn phụ đề hợp lệ') from None
    base = str(template.with_suffix(''))
    results = []
    from .subtitles import read_captions
    for language, track in requested.items():
        if (not isinstance(language, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', language)
                or not isinstance(track, dict)):
            raise ValueError('Ngôn ngữ/track phụ đề không hợp lệ')
        ext = track.get('ext')
        if not isinstance(ext, str) or ext.lower() not in SUBTITLE_EXTENSIONS:
            raise ValueError('Định dạng phụ đề chưa được hỗ trợ để kiểm tra')
        ext = ext.lower()
        expected = Path(f'{base}.{language}.{ext}')
        raw = track.get('filepath', str(expected))
        if not isinstance(raw, str) or not raw:
            raise ValueError('Đường dẫn phụ đề thiếu hoặc không hợp lệ')
        candidate = Path(raw)
        # Compare the extractor-reported path to the expected template *before*
        # reading any file. Reject substitutions, symlinks and path traversal.
        if (candidate.resolve() != expected.resolve()
                or candidate.is_symlink()
                or candidate.parent.name != 'subtitles'
                or not candidate.resolve().is_relative_to(platform_root)):
            raise ValueError('Đường dẫn phụ đề không khớp thư mục đầu ra')
        if not candidate.is_file():
            raise RuntimeError('Không có tệp phụ đề đã tải để kiểm tra')
        size = candidate.stat().st_size
        if not 0 < size <= MAX_SUBTITLE_BYTES:
            raise RuntimeError('Tệp phụ đề trống hoặc vượt giới hạn an toàn')
        try:
            cues = read_captions(candidate)
        except Exception:
            raise RuntimeError('Tệp phụ đề không giải mã được hoặc không đúng định dạng') from None
        if not cues:
            raise RuntimeError('Tệp phụ đề không có câu/timecode hợp lệ')
        results.append({'path':str(candidate),'kind':'subtitle',
                        'id':safe_name(info.get('id','unknown')),
                        'language':language,'cues':len(cues)})
    return results


class QuietLogger:
    def debug(self,message):pass
    def warning(self,message):pass
    def error(self,message):pass


def execute_download_job(store,job,progress,cancel):
    if not isinstance(job,dict) or not isinstance(job.get('payload'),dict):
        raise ValueError('Invalid downloader job payload')
    payload=job['payload']
    if job.get('kind') not in {'scan','download'}:
        raise ValueError('Unsupported downloader job kind')
    url=payload.get('url')
    if not isinstance(url,str) or not url.strip():
        raise ValueError('Download URL must be a non-empty HTTP(S) string')
    platform=platform_for(url)
    engine=payload.get('engine','auto')
    media=payload.get('media','both')
    if not isinstance(engine,str) or engine not in {'auto','video','gallery'}:
        raise ValueError('Unsupported downloader engine; use auto, video or gallery')
    if not isinstance(media,str) or media not in {'both','videos','images'}:
        raise ValueError('Unsupported media type; use both, videos or images')
    raw_limit=payload.get('limit',0)
    if isinstance(raw_limit,bool) or not isinstance(raw_limit,(int,str)):
        raise ValueError('Download limit must be a nonnegative integer')
    if isinstance(raw_limit,str):
        raw_limit=raw_limit.strip()
        if not raw_limit.isdigit():
            raise ValueError('Download limit must be a nonnegative integer')
    limit=int(raw_limit)
    if limit<0:
        raise ValueError('Download limit must be a nonnegative integer')
    download_mode=payload.get('download_mode','media')
    if type(download_mode) is not str or download_mode not in {'media','subtitles_only'}:
        raise ValueError('Download mode không hợp lệ')
    subtitles_only=download_mode=='subtitles_only'
    if subtitles_only:
        languages=payload.get('languages',['vi','zh.*','en'])
        if (job['kind']!='download' or engine!='video' or media!='videos'
                or limit!=1 or payload.get('workflow') is not None
                or payload.get('thumbnail') not in (None,False)
                or not isinstance(languages,list) or not 1<=len(languages)<=16
                or any(not isinstance(lang,str) or not 1<=len(lang)<=64
                       or not lang.strip() or '\n' in lang or '\r' in lang
                       for lang in languages)):
            raise ValueError('Sub-only yêu cầu 1 video yt-dlp, ngôn ngữ hợp lệ và không edit/thumbnail')
    scan_parent = None
    scan_start = 1
    has_cursor = 'scan_parent_id' in payload or 'scan_start' in payload
    if has_cursor:
        if (job['kind'] != 'scan'
                or not isinstance(payload.get('scan_parent_id'), str)
                or type(payload.get('scan_start')) is not int
                or payload['scan_start'] <= 1):
            raise ValueError('Scan continuation requires a valid parent scan and positive offset')
        try:
            scan_parent = store.job(payload['scan_parent_id'])
        except KeyError as exc:
            raise ValueError('Không tìm thấy scan gốc để quét tiếp') from exc
        expected = continuation_scan_payload(scan_parent)
        actual = {key:value for key,value in payload.items() if key != '_tools'}
        if actual != expected:
            raise ValueError('Scan continuation snapshot mismatch: URL, account or options changed')
        scan_start = payload['scan_start']
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
        'writethumbnail':False if subtitles_only else bool(payload.get('thumbnail',False)),
        'writeinfojson':False,'skip_download':subtitles_only,'noplaylist':subtitles_only,
        'format':f"bestvideo[height<={int(payload.get('height',1080))}]+bestaudio/best[height<={int(payload.get('height',1080))}]/best",
        'merge_output_format':'mp4','playliststart':scan_start,
        'playlistend':(scan_start + limit - 1) if limit else None,
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
        if not subtitles_only:
            ydl.add_post_processor(Recorder(),when='after_move')
        info=ydl.extract_info(url,download=job['kind']=='download')
        if not info:raise RuntimeError('Source returned no accessible items')
        if subtitles_only:
            if cancel.is_set():raise RuntimeError('Canceled')
            if info.get('_type') in {'playlist','multi_video'}:
                raise ValueError('Chỉ tải phụ đề cho một video, không phải playlist')
            subtitles=verified_subtitle_artifacts(info,ydl,root/platform)
            progress(1)
            return {'platform':platform,'files':subtitles,'count':len(subtitles),
                    'download_mode':'subtitles_only',
                    'account_ref':binding,'live_channel_verified':False}
        if job['kind']=='scan':
            is_playlist=info.get('_type') in {'playlist','multi_video'}
            if scan_parent and not is_playlist:
                raise ValueError('Nguồn không trả playlist cho vị trí quét tiếp đã yêu cầu')
            entries=info.get('entries') if is_playlist else [info]
            previous=(scan_parent.get('result') or {}).get('items',[]) if scan_parent else []
            # Do not modify the parent snapshot; original scan indices remain
            # stable across the new, cumulative job.
            items=list(previous)
            seen_urls={item.get('url') for item in items
                       if isinstance(item,dict) and selectable_scan_url(item.get('url'))}
            seen_signatures={(str(item.get('id')),item.get('url')) for item in items
                             if isinstance(item,dict)}
            fresh=0
            page_items=[]
            for entry in entries or []:
                if cancel.is_set():raise RuntimeError('Canceled')
                if not isinstance(entry,dict):continue
                item={k:entry.get(k) for k in ('id','title')}
                item.update(normalize_scan_metadata(entry))
                item['url']=scan_video_item_url(entry,url,single=entry is info)
                item['kind']='video'
                item['engine']='video'
                item['selectable']=bool(item['url'])
                if not item['selectable']:
                    item['reason']='Không có URL tải lại an toàn; hãy mở bài trực tiếp'
                signature=(str(item.get('id')),item['url'])
                if signature not in seen_signatures:
                    fresh+=1
                seen_signatures.add(signature)
                if item['url'] and item['url'] in seen_urls:
                    item['selectable']=False
                    item['reason']='URL đã có trong khoảng quét trước; bỏ qua tải trùng'
                if item['url']:
                    seen_urls.add(item['url'])
                page_items.append(item)
                if limit and len(page_items)>=limit:break
            items.extend(page_items)
            can_continue=(payload.get('engine')=='video' and is_playlist
                          and 1<=limit<=MAX_SCAN_PAGE_SIZE)
            next_start=(scan_start+limit if can_continue and
                        len(page_items)==limit and fresh>0 and
                        len(items)+limit<=MAX_SCAN_SNAPSHOT_ITEMS else None)
            result={'platform':platform,'items':items,'count':len(items),
                    'complete':False if limit and len(page_items)>=limit else None,
                    'account_ref':binding,'live_channel_verified':False}
            if can_continue:
                result['scan_window']={'mode':SCAN_WINDOW_MODE,'start':scan_start,
                                       'limit':limit,'next_start':next_start}
            return result
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
                   'engine':'gallery','title':str(data.get('description',''))[:200],
                   'url':safe,'selectable':bool(safe)}
            entry.update(normalize_scan_metadata(data))
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
