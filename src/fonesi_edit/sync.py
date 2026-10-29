"""P05-06: plan manual new-only sync from already-scanned safe media URLs.

This is NOT provider-side full-channel synchronization. It uses exact safe URLs
and per-account/per-output history. Existing files are never removed or edited.
"""
from pathlib import Path

from .downloads import platform_for, selected_download_payloads
from .prototypes.media import probe

MAX_SYNC_ITEMS = 500


def selectable_sync_indices(items):
    """Select each safe URL once, ignoring earlier explicitly disabled rows."""
    from .downloads import selectable_scan_url
    if not isinstance(items,list):
        raise ValueError('Danh sách nội dung scan không hợp lệ')
    seen=set()
    indices=[]
    for index,item in enumerate(items):
        if not isinstance(item,dict) or item.get('selectable') is False:
            continue
        url=selectable_scan_url(item.get('url'))
        if url and url not in seen:
            seen.add(url)
            indices.append(index)
            if len(indices)>MAX_SYNC_ITEMS:
                raise ValueError(f'Tối đa {MAX_SYNC_ITEMS} mục có thể đồng bộ trong một chu kỳ')
    return indices


def sync_media_identity(payload):
    """Same stable identity for manual and scheduled new-only media jobs."""
    from .domain import canonical
    return 'sync-media-v1:'+canonical([
        payload['url'],payload['folder'],payload['engine'],payload['media'],
        payload.get('account_ref'),payload.get('expected_identity')])

_ACTIVE = frozenset({'pending', 'running'})
_NEEDS_ATTENTION = frozenset({'failed', 'canceled', 'blocked'})


def _verified_download_files(job, request):
    """Check saved artifacts again before considering a media download complete."""
    result = job.get('result')
    if not isinstance(result, dict) or result.get('platform') != platform_for(request['url']):
        return False
    files = result.get('files')
    if not isinstance(files, list) or not 1 <= len(files) <= 1000:
        return False
    folder = request.get('folder')
    if type(folder) is not str or not folder:
        return False
    root = (Path(folder).resolve() / platform_for(request['url'])).resolve()
    wanted = 'images' if request['media'] == 'images' else 'videos'
    for media in files:
        if not isinstance(media, dict) or type(media.get('path')) is not str:
            return False
        path = Path(media['path'])
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            return False
        try:
            relative = path.resolve(strict=True).relative_to(root)
            # Path.resolve() alone follows symlinked channel directories;
            # do not mark artifacts through those aliases as verified.
            for ancestor in (path, *path.parents):
                if ancestor.is_symlink():
                    return False
                if ancestor == root:
                    break
            if (len(relative.parts) != 3 or relative.parts[1] != wanted
                    or path.stat().st_size <= 0):
                return False
            if wanted == 'videos':
                if media.get('kind') not in {'video', 'videos'}:
                    return False
                video = probe(path)
                if video.width <= 0 or video.height <= 0 or video.duration <= 0:
                    return False
            else:
                if media.get('kind') != 'images':
                    return False
                from PySide6.QtCore import QSize
                from PySide6.QtGui import QImageReader
                reader = QImageReader(str(path))
                size = reader.size()
                if not reader.canRead() or not size.isValid():
                    return False
                reader.setScaledSize(QSize(64, 64))
                if reader.read().isNull():
                    return False
        except (OSError, ValueError, TypeError, KeyError, RuntimeError):
            return False
    return True


def plan_new_only_sync(scan_job, indices, historical_jobs):
    """Return atomic requests and confirmed skip counts across multiple scans."""
    requests = selected_download_payloads(scan_job, indices)
    if not isinstance(historical_jobs, list) or any(
            not isinstance(job, dict) for job in historical_jobs):
        raise ValueError('Lịch sử job đồng bộ không hợp lệ')
    new_requests = []
    valid_count = active_count = 0
    for request in requests:
        if type(request.get('folder')) is not str or not request['folder']:
            raise ValueError('Thiếu thư mục đầu ra trong snapshot scan')
        matching = []
        for old in historical_jobs:
            if old.get('kind') != 'download':
                continue
            prior = old.get('payload')
            if (not isinstance(prior, dict)
                    or prior.get('download_mode', 'media') != 'media'
                    or prior.get('url') != request['url']
                    or prior.get('folder') != request['folder']):
                continue
            matching.append(old)
            if any(prior.get(key) != request.get(key) for key in (
                    'engine', 'media', 'account_ref', 'expected_identity')):
                raise PermissionError(
                    'URL đã có job ở cùng thư mục với adapter/tài khoản khác; '
                    'không đồng bộ hoặc dùng lẫn phiên')
        if not matching:
            new_requests.append(request)
            continue
        successes = [job for job in matching if job.get('state') == 'succeeded']
        if successes:
            if any(_verified_download_files(job, request) for job in successes):
                valid_count += 1
                continue
            raise ValueError(
                'Job cũ thành công nhưng tệp media không còn hợp lệ; '
                'kiểm tra file và xử lý thủ công, không tự xóa/ghi đè')
        if any(job.get('state') in _NEEDS_ATTENTION for job in matching):
            raise ValueError(
                'Đã có job media bị lỗi/hủy/chặn; xử lý tại Hàng đợi → Retry, '
                'không tự tạo job trùng')
        if any(job.get('state') in _ACTIVE for job in matching):
            active_count += 1
            continue
        raise ValueError('Lịch sử job media có trạng thái chưa được hỗ trợ')
    return {'payloads': new_requests, 'already_valid': valid_count,
            'already_queued': active_count, 'total': len(requests)}
