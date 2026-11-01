"""Explicit filesystem-path subtitle import; caller applies the returned value atomically.

Run off the UI thread: bounded reads do not impose a deadline on OS I/O. Cancellation
is checked before reading, before parsing and before returning, not within blocking I/O.
"""
from pathlib import Path
from typing import Callable

from fonesi_edit.fileio import read_bounded
from .adapter import MAX_BYTES, SubtitleDocument, SubtitleError, parse_subtitles


class SubtitleCanceled(SubtitleError):
    pass


def load_subtitles(path: Path | str, format_: str, *, encoding: str = 'utf-8-sig',
                   allow_empty: bool = False,
                   cancel: Callable[[], bool] = lambda: False) -> SubtitleDocument:
    def check_cancel():
        if cancel():
            raise SubtitleCanceled('Subtitle import canceled; current track unchanged')

    check_cancel()
    try:
        source=Path(path)
        if not source.is_file():
            raise SubtitleError('Subtitle source must be an existing regular file')
        data=read_bounded(source,MAX_BYTES)
    except SubtitleError:
        raise
    except (OSError,ValueError,TypeError):
        raise SubtitleError('Subtitle file could not be read within the byte limit') from None
    check_cancel()
    result=parse_subtitles(data,format_,encoding=encoding,allow_empty=allow_empty)
    check_cancel()
    return result
