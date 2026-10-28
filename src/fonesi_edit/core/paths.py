"""Owned runtime paths and source-preserving filesystem operations."""
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
import unicodedata

RESERVED = {'CON','PRN','AUX','NUL',*[f'{p}{n}' for p in ('COM','LPT') for n in range(1,10)]}


def user_data() -> Path:
    override = os.environ.get('FONESI_DATA_DIR')
    path = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', Path.home()/'.local/share'))/'FonesiEdit'
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_name(text: str, limit: int = 80) -> str:
    value = re.sub(r'[\x00-\x1f<>:"/\\|?*]', '_', unicodedata.normalize('NFC', text)).strip(' .') or 'untitled'
    if value.split('.')[0].upper() in RESERVED:
        value = '_'+value
    return value[:limit].rstrip(' .') or 'untitled'


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def contained(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def atomic_write(path: Path, data: str | bytes) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.'+path.name+'.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data.encode('utf8') if isinstance(data,str) else data); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def publish_no_clobber(temp: Path, target: Path) -> Path:
    """Atomic link publication; fail safely on filesystems without hardlink support."""
    target.parent.mkdir(parents=True, exist_ok=True)
    for n in range(10_000):
        candidate = target if n == 0 else target.with_name(f'{target.stem} ({n}){target.suffix}')
        try:
            os.link(temp, candidate)
        except FileExistsError:
            continue
        temp.unlink()
        return candidate
    raise FileExistsError('Output version limit reached')


def channel_directory(root: Path, platform: str, name: str, source_id: str, edited=False) -> Path:
    # A title change must not create a second folder for the same source ID.
    base = root/safe_name(platform)
    suffix = '__'+safe_name(source_id,40)
    for p in sorted(base.glob('*')) if base.exists() else []:
        if p.is_dir() and p.name.endswith(suffix+(' edit' if edited else '')):
            return p
    return base/(safe_name(name,50)+suffix+(' edit' if edited else ''))
