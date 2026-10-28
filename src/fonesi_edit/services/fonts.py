from pathlib import Path
from functools import lru_cache
import os
from PIL import ImageFont
from fontTools.ttLib import TTFont


def discover_fonts(extra=()) -> list[dict]:
    roots=[Path('/usr/share/fonts'),Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',Path.home()/'.fonts',*[Path(p) for p in extra]]
    found=[]
    for root in roots:
        if not root.exists():continue
        for path in sorted(root.rglob('*')):
            if path.suffix.lower() not in {'.ttf','.otf'}:continue
            try:
                with TTFont(path,lazy=True) as font:
                    names=font['name'];family=names.getDebugName(1) or path.stem;style=names.getDebugName(2) or 'Regular'
                found.append({'path':str(path),'family':family,'style':style})
            except Exception:continue
    return found


@lru_cache(maxsize=64)
def font_file(preferred='') -> str:
    if preferred:
        if not Path(preferred).is_file():raise FileNotFoundError('Missing selected font: '+preferred)
        return preferred
    fonts=discover_fonts()
    for f in fonts:
        if f['family']=='DejaVu Sans' and f['style']=='Book':return f['path']
    if fonts:return fonts[0]['path']
    raise FileNotFoundError('No usable font; select a licensed TTF/OTF')


@lru_cache(maxsize=128)
def load_font(path:str,size:int):return ImageFont.truetype(font_file(path),size=max(1,size))


@lru_cache(maxsize=128)
def missing_glyphs(path:str,text:str) -> tuple[str,...]:
    with TTFont(font_file(path),lazy=True) as font:
        cmap=font.getBestCmap() or {}
        return tuple(sorted({c for c in text if not c.isspace() and ord(c) not in cmap}))
