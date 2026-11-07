"""Cancellable Qt adapter for the owned FFmpeg video proxy encoder.

This worker does not mutate project state or display proxy frames. Timeline
must still explicitly adopt a completed result after checking session identity.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from fonesi_edit.media.proxy_encode import (
    EncodedVideoProxy, ProxyEncodeCanceled, ProxyEncodeError,
    ProxyEncodeRetirementUnknown, ProxyProgress, ProxySpec,
    encode_video_proxy,
)
from fonesi_edit.media.proxy_cache import PersistentProxyCache


class ProxyEncodeWorker(QThread):
    """Runs one proxy encode on a QThread; cancellation owns process retirement.

    Consumers must hold this worker until finished() and must never regard
    progress events as proof that a cache entry is ready.
    """
    progress_changed = Signal(object)

    def __init__(
        self, source: Path | str, ffmpeg: Path | str, ffprobe: Path | str,
        cache: PersistentProxyCache, *, expected_source_sha256: str,
        stream_index: int, spec: ProxySpec = ProxySpec(),
        timeout: float = 900, parent=None,
    ):
        super().__init__(parent)
        if not isinstance(cache, PersistentProxyCache):
            raise ValueError("a validated persistent proxy cache is required")
        if not isinstance(spec, ProxySpec):
            raise ValueError("a validated video proxy profile is required")
        self.source = Path(source)
        self.ffmpeg = Path(ffmpeg)
        self.ffprobe = Path(ffprobe)
        self.cache = cache
        self.expected_source_sha256 = expected_source_sha256
        self.stream_index = stream_index
        self.spec = spec
        self.timeout = timeout
        self.result: EncodedVideoProxy | None = None
        self.error: str | None = None
        self.canceled = False
        self.retirement_unknown = False

    def _observe_progress(self, event: ProxyProgress) -> None:
        if self.isInterruptionRequested():
            raise ProxyEncodeCanceled("proxy encode interrupted")
        self.progress_changed.emit(event)

    def run(self) -> None:
        self.result = None
        self.error = None
        self.canceled = False
        self.retirement_unknown = False
        try:
            if self.isInterruptionRequested():
                raise ProxyEncodeCanceled("proxy encode interrupted before launch")
            result = encode_video_proxy(
                self.source, self.ffmpeg, self.ffprobe, self.cache,
                expected_source_sha256=self.expected_source_sha256,
                stream_index=self.stream_index, spec=self.spec,
                cancel=self.isInterruptionRequested,
                progress=self._observe_progress, timeout=self.timeout,
            )
            if self.isInterruptionRequested():
                raise ProxyEncodeCanceled("proxy encode interrupted before adoption")
            self.result = result
        except ProxyEncodeRetirementUnknown as exc:
            self.retirement_unknown = True
            self.error = str(exc)
        except ProxyEncodeCanceled:
            self.canceled = True
        except ProxyEncodeError as exc:
            self.error = str(exc)
        except BaseException:
            # Do not leak arbitrary paths, subprocess output or exception text.
            self.error = "Video proxy worker failed; no proxy result was adopted."
