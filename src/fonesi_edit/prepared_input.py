"""Owned validated input copy. Cooperative I/O bounds, not hostile-FS isolation."""

import math
import os
import re
import stat
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class PreparedInput:
    path: Path
    sha256: str
    size: int


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@contextmanager
def stage_verified_input(
    source, expected_sha256, staging_parent, *, max_bytes, timeout=30, cancel=None
):
    if (
        not isinstance(source, Path)
        or not source.is_absolute()
        or not isinstance(staging_parent, Path)
        or not staging_parent.is_absolute()
        or not staging_parent.is_dir()
    ):
        raise ValueError("NATIVE_PATHS_REQUIRED")
    if (
        not isinstance(expected_sha256, str)
        or re.fullmatch("[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError("INVALID_INPUT_DIGEST")
    if type(max_bytes) is not int or not 0 < max_bytes < 2**63:
        raise ValueError("INVALID_BYTE_BUDGET")
    if (
        type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 60
    ):
        raise ValueError("INVALID_COPY_TIMEOUT")
    deadline = time.monotonic() + timeout

    def check():
        if cancel is not None and cancel.is_set():
            raise ValueError("INPUT_COPY_CANCELED")
        if time.monotonic() >= deadline:
            raise TimeoutError("INPUT_COPY_TIMEOUT")

    check()
    original = source.lstat()
    if not stat.S_ISREG(original.st_mode):
        raise ValueError("REGULAR_SOURCE_REQUIRED")
    if original.st_size > max_bytes:
        raise ValueError("INPUT_BYTE_BUDGET_EXCEEDED")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(source, flags)
    with os.fdopen(descriptor, "rb") as reader:
        opened = os.fstat(reader.fileno())
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(original):
            raise ValueError("INPUT_CHANGED")
        with tempfile.TemporaryDirectory(
            prefix=".fonesi-input-", dir=staging_parent
        ) as directory:
            staged = Path(directory) / "input.bin"
            digest = sha256()
            count = 0
            with staged.open("xb") as writer:
                while True:
                    check()
                    data = reader.read(1024 * 1024)
                    if not data:
                        break
                    count += len(data)
                    if count > max_bytes:
                        raise ValueError("INPUT_BYTE_BUDGET_EXCEEDED")
                    writer.write(data)
                    digest.update(data)
                writer.flush()
                os.fsync(writer.fileno())
            check()
            if _identity(os.fstat(reader.fileno())) != _identity(opened) or _identity(
                source.lstat()
            ) != _identity(opened):
                raise ValueError("INPUT_CHANGED")
            if count != opened.st_size or digest.hexdigest() != expected_sha256:
                raise ValueError("INPUT_DIGEST_MISMATCH")
            reader.close()
            check()
            yield PreparedInput(staged, digest.hexdigest(), count)
