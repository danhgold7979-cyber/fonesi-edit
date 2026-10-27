from functools import lru_cache
from pathlib import Path
import os
from fontTools.ttLib import TTFont


def font_roots():
    roots=[Path('/usr/share/fonts'),Path.home()/'.local/share/fonts',Path('/System/Library/Fonts'),Path('/Library/Fonts')]
    if os.name=='nt':roots=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',Path(os.environ.get('LOCALAPPDATA',''))/'Microsoft/Windows/Fonts']
    return [r for r in roots if r.is_dir()]


@lru_cache(maxsize=4)
def font_catalog(extra=''):
    result=[]
    for root in [*font_roots(),*([Path(extra)] if extra else [])]:
        for path in root.rglob('*'):
            if path.suffix.lower() not in {'.ttf','.otf'}:continue
            try:
                with TTFont(path,lazy=True) as font:
                    name=font['name'].getDebugName(1) or path.stem
                    style=font['name'].getDebugName(2) or 'Regular'
                result.append({'family':name,'style':style,'path':str(path)})
            except Exception:continue
            if len(result)>=3000:return result
    return result


def resolve_font(style):
    if style.get('font_file'):
        path=Path(style['font_file'])
        if not path.is_file():raise FileNotFoundError(f'Font missing: {path.name}')
        return path
    family=style.get('font_family','').casefold()
    fonts=font_catalog()
    matching=[f for f in fonts if f['family'].casefold()==family]
    if family and matching:
        wanted='bold' if style.get('bold') else 'regular'
        return Path(next((f['path'] for f in matching if wanted in f['style'].lower()),matching[0]['path']))
    if family and family not in {'arial','sans','sans-serif',''}:raise FileNotFoundError('Font family unavailable; choose a font file: '+style['font_family'])
    from .prototypes.media import find_font
    return find_font()


def missing_glyphs(path,text):
    with TTFont(path,lazy=True) as font:
        cmap=font.getBestCmap() or {}
        return sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cmap})
