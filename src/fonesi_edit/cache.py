"""Conservative cache janitor; never delete user media or symlink targets."""
from pathlib import Path


def evict_proxy_cache(directory,max_bytes,protected=()):
    """Remove only regular completed MP4 proxies, oldest first, until within quota.

    Keep active playback paths even if they exceed quota. Never recurse or
    follow links, and never delete incomplete worker output.
    """
    if type(max_bytes) is not int or max_bytes<0:
        raise ValueError('Proxy cache quota must be a nonnegative integer')
    root=Path(directory)
    if root.is_symlink():
        raise PermissionError('Cache root cannot be a symlink')
    if not root.exists():
        return {'scanned_bytes':0,'remaining_bytes':0,'deleted_bytes':0,
                'deleted':[],'over_budget':False}
    if not root.is_dir():
        raise NotADirectoryError(root)
    protected_paths={str(Path(p).resolve()) for p in protected if p}
    files=[]
    total=0
    for item in root.iterdir():
        # Ignore partials, other file types, nested folders and symlink files.
        if (item.is_symlink() or not item.is_file()
                or item.suffix.casefold()!='.mp4'
                or item.name.startswith('.')):
            continue
        info=item.stat()
        files.append((info.st_mtime_ns,item.name,info.st_size,item))
        total+=info.st_size
    original=total
    removed=[]
    if total>max_bytes:
        for _,name,size,path in sorted(files):
            if total<=max_bytes:break
            if str(path.resolve()) in protected_paths:continue
            # A concurrent worker can replace/modify a cache file. If it did,
            # leave it alone and recompute on a later sweep.
            current=path.stat()
            if current.st_size!=size:continue
            path.unlink()
            removed.append(str(path))
            total-=size
    return {'scanned_bytes':original,'remaining_bytes':total,
            'deleted_bytes':original-total,'deleted':removed,
            'over_budget':total>max_bytes}
