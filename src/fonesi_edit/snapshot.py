"""Versioned immutable render intent. Credentials are outside this contract."""

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath, PureWindowsPath
from uuid import UUID


def local_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "://" in value:
        raise ValueError("Expected an absolute local media path")
    if not (PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()):
        raise ValueError("Expected an absolute local media path")
    return value


@dataclass(frozen=True)
class RenderIntent:
    project_id: str
    source_path: str
    output_directory: str
    seed: int
    schema_version: int = 1

    def __post_init__(self):
        if not isinstance(self.project_id, str):
            raise ValueError("Invalid project ID")  # noqa: TRY004 - stable public validation error contract.
        try:
            parsed = UUID(self.project_id)
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid project ID") from exc
        if str(parsed) != self.project_id:
            raise ValueError("Project ID must be canonical UUID")
        local_path(self.source_path)
        local_path(self.output_directory)
        if type(self.seed) is not int or not 0 <= self.seed < 2**63:
            raise ValueError("Seed outside signed 64-bit range")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("Unsupported schema version")

    def canonical(self) -> str:
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "project_id": self.project_id,
                "source_path": self.source_path,
                "output_directory": self.output_directory,
                "seed": self.seed,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @property
    def digest(self) -> str:
        return sha256(self.canonical().encode("utf-8")).hexdigest()

    @classmethod
    def parse(cls, payload: str) -> "RenderIntent":
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > 65536:
            raise ValueError("Invalid snapshot size")

        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate snapshot key")
                result[key] = value
            return result

        try:
            obj = json.loads(payload, object_pairs_hook=unique)
        except (ValueError, RecursionError) as exc:
            raise ValueError("Invalid snapshot JSON") from exc
        if not isinstance(obj, dict) or set(obj) != {
            "schema_version",
            "project_id",
            "source_path",
            "output_directory",
            "seed",
        }:
            raise ValueError("Unknown or missing snapshot field")
        return cls(**obj)
