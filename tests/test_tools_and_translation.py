import hashlib
import io
import json
import os
import sqlite3
import zipfile
from pathlib import Path
from threading import Event

import pytest

from fonesi_edit import dependencies
from fonesi_edit.dependencies import install, rollback
from fonesi_edit.prototypes.tools import ToolStatus, check_tool, scan_tools
from fonesi_edit.prototypes.translation import TranslationNotConfigured, translate
from fonesi_edit.prototypes.subtitles import Cue
from fonesi_edit.storage import Store


def _executable_name(name):
    return name + ".exe" if os.name == "nt" else name


def _artifact(ffmpeg=b"synthetic-ffmpeg", ffprobe=b"synthetic-ffprobe"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(f"bin/{_executable_name('ffmpeg')}", ffmpeg)
        archive.writestr(f"bin/{_executable_name('ffprobe')}", ffprobe)
    return buffer.getvalue()


def _manifest(version, payload):
    return {
        "name": "ffmpeg",
        "version": version,
        "url": f"https://artifacts.invalid/ffmpeg-{version}.zip",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "archive": "zip",
        "executable": _executable_name("ffmpeg"),
    }


def _fake_fetch(artifacts, calls):
    def fetch(url, destination, sha256, progress, cancel):
        calls.append(url)
        payload = artifacts[url]
        assert hashlib.sha256(payload).hexdigest() == sha256
        destination.write_bytes(payload)
        progress(0.5)
    return fetch


def _ready_tool(name, path):
    return ToolStatus(name, path, "ready", "synthetic version")


def _active_versions(store):
    with store.connect() as conn:
        return {
            row["version"]: row["active"]
            for row in conn.execute(
                "SELECT version,active FROM tool_versions WHERE name='ffmpeg'"
            )
        }


def test_install_reuses_verified_receipt_without_downloading_again(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    payload = _artifact()
    manifest = _manifest("7.1.1", payload)
    calls = []
    activated = []
    monkeypatch.setattr(dependencies, "check_tool", _ready_tool)
    monkeypatch.setattr(dependencies, "configure_tools", lambda paths: activated.append(dict(paths)))
    fetch = _fake_fetch({manifest["url"]: payload}, calls)

    first = install(store, manifest, fetch=fetch)
    second = install(store, manifest, fetch=fetch)

    assert first == second
    assert calls == [manifest["url"]]
    assert Path(second["path"]).is_file()
    assert Path(second["ffprobe"]).is_file()
    assert store.setting("tool_paths") == {
        "ffmpeg": second["path"],
        "ffprobe": second["ffprobe"],
    }
    assert _active_versions(store) == {"7.1.1": 1}
    assert activated[-1] == store.setting("tool_paths")


def test_install_activation_is_atomic_and_retry_reuses_staged_receipt(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    first_payload = _artifact(b"ffmpeg-v1", b"ffprobe-v1")
    second_payload = _artifact(b"ffmpeg-v2", b"ffprobe-v2")
    first_manifest = _manifest("1.0.0", first_payload)
    second_manifest = _manifest("2.0.0", second_payload)
    artifacts = {
        first_manifest["url"]: first_payload,
        second_manifest["url"]: second_payload,
    }
    calls = []
    monkeypatch.setattr(dependencies, "check_tool", _ready_tool)
    monkeypatch.setattr(dependencies, "configure_tools", lambda _paths: None)
    fetch = _fake_fetch(artifacts, calls)

    first = install(store, first_manifest, fetch=fetch)
    old_paths = store.setting("tool_paths")
    with store.connect() as conn:
        conn.execute(
            "CREATE TRIGGER fail_tool_paths_update BEFORE UPDATE ON settings "
            "WHEN NEW.key='tool_paths' BEGIN "
            "SELECT RAISE(ABORT,'synthetic tool path activation failure'); END"
        )

    with pytest.raises(sqlite3.IntegrityError, match="synthetic tool path activation failure"):
        install(store, second_manifest, fetch=fetch)

    assert store.setting("tool_paths") == old_paths
    assert _active_versions(store) == {"1.0.0": 1}
    staged = store.path.parent / "tools" / "ffmpeg" / "2.0.0" / "receipt.json"
    assert staged.is_file()

    with store.connect() as conn:
        conn.execute("DROP TRIGGER fail_tool_paths_update")
    second = install(store, second_manifest, fetch=fetch)

    assert calls == [first_manifest["url"], second_manifest["url"]]
    assert store.setting("tool_paths") == {
        "ffmpeg": second["path"],
        "ffprobe": second["ffprobe"],
    }
    assert _active_versions(store) == {"1.0.0": 0, "2.0.0": 1}
    assert Path(first["path"]).is_file()


def test_install_cancellation_after_startup_check_does_not_publish_or_activate(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    payload = _artifact()
    manifest = _manifest("3.0.0", payload)
    cancel = Event()
    calls = []
    monkeypatch.setattr(
        dependencies,
        "check_tool",
        lambda name, path: (cancel.set() or _ready_tool(name, path)),
    )
    monkeypatch.setattr(dependencies, "configure_tools", lambda _paths: pytest.fail("must not activate"))
    fetch = _fake_fetch({manifest["url"]: payload}, calls)

    with pytest.raises(RuntimeError, match="Canceled"):
        install(store, manifest, cancel=cancel, fetch=fetch)

    assert calls == [manifest["url"]]
    assert store.setting("tool_paths", {}) == {}
    assert _active_versions(store) == {}
    assert not (store.path.parent / "tools" / "ffmpeg" / "3.0.0").exists()


def test_invalid_existing_receipt_repairs_to_new_folder_without_overwriting_old_version(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    payload = _artifact(b"original-ffmpeg", b"original-ffprobe")
    manifest = _manifest("4.0.0", payload)
    calls = []
    monkeypatch.setattr(dependencies, "check_tool", _ready_tool)
    monkeypatch.setattr(dependencies, "configure_tools", lambda _paths: None)
    fetch = _fake_fetch({manifest["url"]: payload}, calls)

    original = install(store, manifest, fetch=fetch)
    original_path = Path(original["path"])
    original_bytes = original_path.read_bytes()
    final_dir = original_path.parents[1]
    receipt_path = final_dir / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["hash"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    repaired = install(store, manifest, fetch=fetch)

    assert repaired["path"] != original["path"]
    assert ".repair." in repaired["version"]
    assert original_path.read_bytes() == original_bytes
    assert Path(repaired["path"]).is_file()
    assert calls == [manifest["url"], manifest["url"]]


def test_failed_startup_verification_does_not_activate_or_publish(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    payload = _artifact()
    manifest = _manifest("5.0.0", payload)
    monkeypatch.setattr(
        dependencies,
        "check_tool",
        lambda name, path: ToolStatus(name, path, "incompatible", "bad version"),
    )
    monkeypatch.setattr(dependencies, "configure_tools", lambda _paths: pytest.fail("must not activate"))
    fetch = _fake_fetch({manifest["url"]: payload}, [])

    with pytest.raises(ValueError, match="startup/version check"):
        install(store, manifest, fetch=fetch)

    assert store.setting("tool_paths", {}) == {}
    assert _active_versions(store) == {}
    assert not (store.path.parent / "tools" / "ffmpeg" / "5.0.0").exists()


def test_rollback_updates_ffmpeg_and_matching_ffprobe_and_live_resolver(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    first_payload = _artifact(b"ffmpeg-old", b"ffprobe-old")
    second_payload = _artifact(b"ffmpeg-new", b"ffprobe-new")
    first_manifest = _manifest("6.0.0", first_payload)
    second_manifest = _manifest("7.0.0", second_payload)
    artifacts = {
        first_manifest["url"]: first_payload,
        second_manifest["url"]: second_payload,
    }
    calls = []
    activated = []
    monkeypatch.setattr(dependencies, "check_tool", _ready_tool)
    monkeypatch.setattr(dependencies, "configure_tools", lambda paths: activated.append(dict(paths)))
    fetch = _fake_fetch(artifacts, calls)

    first = install(store, first_manifest, fetch=fetch)
    install(store, second_manifest, fetch=fetch)
    rollback(store, "ffmpeg", "6.0.0")

    assert store.setting("tool_paths") == {
        "ffmpeg": first["path"],
        "ffprobe": first["ffprobe"],
    }
    assert _active_versions(store) == {"6.0.0": 1, "7.0.0": 0}
    assert activated[-1] == store.setting("tool_paths")


def test_explicit_missing_tool_path_does_not_fall_back_to_system(tmp_path):
    missing = str(tmp_path / "missing-ffmpeg")
    tools = scan_tools({"ffmpeg": missing})
    ffmpeg = next(tool for tool in tools if tool.name == "ffmpeg")
    assert ffmpeg.status == "missing" and ffmpeg.path == missing


def test_missing_chrome_is_not_replaced_by_chromium(tmp_path):
    assert check_tool("Google Chrome", str(tmp_path / "missing-chrome")).status == "missing"


def test_translation_requires_config_and_never_fakes_output(monkeypatch):
    monkeypatch.delenv("FONESI_GOOGLE_TRANSLATE_API_KEY", raising=False)
    with pytest.raises(TranslationNotConfigured):
        translate([Cue(0, 1000, "你好")])



def _zip_with_members(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload, mode in members:
            info = zipfile.ZipInfo(name)
            if mode is not None:
                info.external_attr = mode << 16
            archive.writestr(info, payload)
    buffer.seek(0)
    return buffer


@pytest.mark.parametrize(
    "unsafe_name",
    [
        "../escape.txt",
        "/absolute.txt",
        "C:/drive.txt",
        "folder/../../escape.txt",
        ".",
        "",
        "folder/./file.txt",
    ],
)
def test_extract_zip_rejects_unsafe_names_before_writing_any_member(tmp_path, unsafe_name):
    archive = _zip_with_members([
        ("safe/first.txt", b"safe", None),
        (unsafe_name, b"unsafe", None),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Unsafe archive"):
        dependencies.extract_zip(archive, destination)
    assert list(destination.rglob("*")) == []
    assert not (tmp_path / "escape.txt").exists()


def test_extract_zip_rejects_symlink_member_before_writing_any_member(tmp_path):
    archive = _zip_with_members([
        ("safe/first.txt", b"safe", None),
        ("link", b"target", 0o120777),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Unsafe archive"):
        dependencies.extract_zip(archive, destination)
    assert list(destination.rglob("*")) == []


def test_extract_zip_keeps_safe_nested_files_and_directory_entries(tmp_path):
    archive = _zip_with_members([
        ("bin/", b"", 0o40755),
        ("bin/tool.exe", b"binary", None),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    dependencies.extract_zip(archive, destination)
    assert (destination / "bin" / "tool.exe").read_bytes() == b"binary"



@pytest.mark.parametrize(
    "unsafe_name",
    [
        "CON", "nul.txt", "COM1.log", "LPT9", "CONIN$",
        "folder/name.", "folder/name ", "folder/bad<name>.txt",
        "folder/bad|name.txt", "folder\\..\\escape.txt",
    ],
)
def test_extract_zip_rejects_windows_reserved_and_nonportable_components(tmp_path, unsafe_name):
    archive = _zip_with_members([
        ("safe/first.txt", b"safe", None),
        (unsafe_name, b"unsafe", None),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Unsafe archive"):
        dependencies.extract_zip(archive, destination)
    assert list(destination.rglob("*")) == []


@pytest.mark.parametrize(
    "members",
    [
        [("Bin/tool.exe", b"one", None), ("bin/TOOL.EXE", b"two", None)],
        [("folder", b"file", None), ("folder/child.txt", b"child", None)],
        [("folder/child.txt", b"child", None), ("folder", b"file", None)],
    ],
)
def test_extract_zip_rejects_casefold_and_file_directory_collisions(tmp_path, members):
    archive = _zip_with_members(members)
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Duplicate|collision"):
        dependencies.extract_zip(archive, destination)
    assert list(destination.rglob("*")) == []


@pytest.mark.parametrize("mode", [0o010644, 0o020600, 0o140600])
def test_extract_zip_rejects_special_unix_file_types_before_writing(tmp_path, mode):
    archive = _zip_with_members([
        ("safe/first.txt", b"safe", None),
        ("special-entry", b"device", mode),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Unsafe archive"):
        dependencies.extract_zip(archive, destination)
    assert list(destination.rglob("*")) == []


def test_extract_zip_rejects_encrypted_member_before_writing_any_member(tmp_path):
    archive = bytearray(_zip_with_members([
        ("safe/first.txt", b"safe", None),
        ("secret.bin", b"encrypted", None),
    ]).getvalue())
    local = archive.find(b"PK\x03\x04")
    central = archive.find(b"PK\x01\x02")
    assert local >= 0 and central >= 0
    local_flags = int.from_bytes(archive[local + 6:local + 8], "little") | 1
    central_flags = int.from_bytes(archive[central + 8:central + 10], "little") | 1
    archive[local + 6:local + 8] = local_flags.to_bytes(2, "little")
    archive[central + 8:central + 10] = central_flags.to_bytes(2, "little")
    destination = tmp_path / "unpack"
    destination.mkdir()
    with pytest.raises(ValueError, match="Unsafe archive"):
        dependencies.extract_zip(io.BytesIO(archive), destination)
    assert list(destination.rglob("*")) == []


def test_extract_zip_normalizes_safe_backslash_paths(tmp_path):
    archive = _zip_with_members([("bin\\tools\\ffmpeg.exe", b"binary", None)])
    destination = tmp_path / "unpack"
    destination.mkdir()
    dependencies.extract_zip(archive, destination)
    assert (destination / "bin" / "tools" / "ffmpeg.exe").read_bytes() == b"binary"
