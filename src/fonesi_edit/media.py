"""Real local probe with exact duration; no claim of full codec compatibility."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import json
import re
from fonesi_edit.process import run_bounded

@dataclass(frozen=True)
class MediaInfo:
    duration: Fraction
    stream_types: tuple[str,...]


def parse_probe(data: bytes) -> MediaInfo:
    if not isinstance(data,bytes) or len(data)>65536: raise ValueError('INVALID_PROBE')
    try:
        obj=json.loads(data)
        duration_text=obj['format']['duration']
        if not isinstance(duration_text,str) or len(duration_text)>64 or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',duration_text): raise ValueError()
        duration=Fraction(duration_text)
        if duration<=0 or duration>86400*365: raise ValueError()
        streams=obj['streams']
        if not isinstance(streams,list) or not 1<=len(streams)<=128: raise ValueError()
        kinds=tuple(s['codec_type'] for s in streams)
        if not all(k in {'video','audio','subtitle','data','attachment'} for k in kinds): raise ValueError()
        if not any(k in {'video','audio'} for k in kinds): raise ValueError()
        return MediaInfo(duration,kinds)
    except (ValueError,TypeError,KeyError,ZeroDivisionError,RecursionError):
        raise ValueError('INVALID_PROBE') from None


def probe(source: Path, executable: Path, *, cancel=None) -> MediaInfo:
    source=source.resolve(strict=True)
    if not source.is_file(): raise ValueError('REGULAR_SOURCE_REQUIRED')
    result=run_bounded([str(executable),'-v','error','-protocol_whitelist','file,pipe',
        '-show_entries','format=duration:stream=codec_type','-of','json',str(source)],cancel=cancel)
    if result.status!='OK': raise ValueError(result.status)
    return parse_probe(result.stdout)
