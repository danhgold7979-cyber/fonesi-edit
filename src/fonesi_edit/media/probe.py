"""Bounded explicit-tool probing and cancellation-aware content fingerprints."""
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Callable

class ProbeError(RuntimeError):
    pass

class ProbeCanceled(ProbeError):
    pass


def _check_cancel(cancel):
    if cancel():
        raise ProbeCanceled('Media inspection canceled')


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate metadata key')
        result[key] = value
    return result


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Nonfinite metadata number')
    return number


def _reject_constant(value):
    raise ValueError(f'Nonfinite metadata constant {value}')


def _signature(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def fingerprint(path: Path, cancel: Callable[[], bool] = lambda: False) -> str:
    digest = sha256()
    named_before = _signature(path.stat())
    with path.open('rb') as stream:
        before = _signature(os.fstat(stream.fileno()))
        if before[:2] != named_before[:2]:
            raise ProbeError('Source identity changed before fingerprinting')
        while True:
            _check_cancel(cancel)
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = _signature(os.fstat(stream.fileno()))
    named_after = _signature(path.stat())
    # Windows path-stat and descriptor-stat timestamps can have different precision.
    # Compare each API against itself; physical identity still matches across APIs.
    if before != after or named_before != named_after or after[:2] != named_after[:2]:
        raise ProbeError(f'Source changed during fingerprinting: descriptor={before!r}->{after!r}; named={named_before!r}->{named_after!r}')
    return digest.hexdigest()


@dataclass(frozen=True)
class ProbeResult:
    sha256: str
    metadata_json: str
    tool_path: str
    diagnostics: tuple[str, ...]

    def metadata(self):
        return json.loads(self.metadata_json)


def inspect_media(path: Path | str, executable: Path | str, *,
                  cancel: Callable[[], bool] = lambda: False,
                  timeout: float = 30, max_output_bytes: int = 16 * 1024 * 1024) -> ProbeResult:
    path = Path(path).absolute()
    executable = Path(executable).absolute()
    if timeout <= 0 or max_output_bytes < 1:
        raise ValueError('Positive timeout and output limit required')
    if not path.is_file():
        raise ProbeError('Media path is not a regular file')
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ProbeError('Explicit ffprobe path is invalid; no fallback')
    _check_cancel(cancel)
    before = _signature(path.stat())
    digest = fingerprint(path, cancel)
    args = [str(executable), '-v', 'error', '-show_format', '-show_streams',
            '-print_format', 'json', '-protocol_whitelist', 'file,pipe', '-i', str(path)]
    # Files rather than pipes avoid pipe backpressure and bound memory capture.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=output,
                                     stderr=errors, shell=False)
        except OSError as exc:
            raise ProbeError(f'Unable to launch explicit ffprobe: {exc}') from exc
        started = time.monotonic()
        try:
            while child.poll() is None:
                _check_cancel(cancel)
                if time.monotonic() - started > timeout:
                    raise ProbeError('ffprobe timed out')
                if os.fstat(output.fileno()).st_size + os.fstat(errors.fileno()).st_size > max_output_bytes:
                    raise ProbeError('ffprobe output exceeds limit')
                time.sleep(0.01)
            _check_cancel(cancel)
            if os.fstat(output.fileno()).st_size + os.fstat(errors.fileno()).st_size > max_output_bytes:
                raise ProbeError('ffprobe output exceeds limit')
            if child.returncode != 0:
                # Do not leak arbitrary tool stderr (may contain paths/credentials).
                raise ProbeError(f'ffprobe exited with code {child.returncode}')
            output.seek(0)
            raw = output.read(max_output_bytes + 1)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
    if before != _signature(path.stat()):
        raise ProbeError('Source changed during inspection')
    try:
        data = json.loads(raw, object_pairs_hook=_json_pairs, parse_constant=_reject_constant, parse_float=_finite_float)
    except (ValueError, UnicodeError) as exc:
        raise ProbeError('ffprobe returned invalid JSON') from exc
    if not isinstance(data, dict) or not isinstance(data.get('streams'), list) or not data['streams']:
        raise ProbeError('No usable stream metadata')
    indices = set()
    diagnostics = []
    for stream in data['streams']:
        if not isinstance(stream, dict) or type(stream.get('index')) is not int or stream['index'] in indices:
            raise ProbeError('Invalid or duplicate stream index')
        indices.add(stream['index'])
        if stream.get('codec_type') not in {'audio', 'video', 'subtitle', 'attachment', 'data'}:
            diagnostics.append(f'Unknown stream type at index {stream["index"]}')
    if not any(s.get('codec_type') == 'audio' for s in data['streams']):
        diagnostics.append('No audio stream')
    return ProbeResult(digest, json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False),
                       str(executable), tuple(diagnostics))
