"""Bound actual reads, including files that grow after stat."""
from pathlib import Path


def read_bounded(path: Path | str, max_bytes: int) -> bytes:
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError('Nonnegative byte limit required')
    with Path(path).open('rb') as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f'File exceeds {max_bytes}-byte limit')
    return data
