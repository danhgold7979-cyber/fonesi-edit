import hashlib
import io
import json
import os
import sqlite3
import zipfile
from pathlib import Path
from threading import Event, Thread

import pytest

from fonesi_edit import dependencies
from fonesi_edit.dependencies import install, rollback, managed_tool_versions, remove_tool_version
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
    archive = _zip_with_members([
        ("bin\\tools\\", b"", 0o40755),
        ("bin\\tools\\ffmpeg.exe", b"binary", None),
    ])
    destination = tmp_path / "unpack"
    destination.mkdir()
    dependencies.extract_zip(archive, destination)
    assert (destination / "bin" / "tools" / "ffmpeg.exe").read_bytes() == b"binary"



def _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch):
    store = Store(tmp_path / "state" / "fonesi.db")
    payload = _artifact(b"known-good-ffmpeg", b"known-good-ffprobe")
    manifest = _manifest("1.0.0", payload)
    monkeypatch.setattr(dependencies, "check_tool", _ready_tool)
    monkeypatch.setattr(dependencies, "configure_tools", lambda _paths: None)
    receipt = install(store, manifest, fetch=_fake_fetch({manifest["url"]: payload}, []))
    return store, receipt


def _assert_previous_tool_remains_active(store, receipt, new_version):
    assert store.setting("tool_paths") == {
        "ffmpeg": receipt["path"],
        "ffprobe": receipt["ffprobe"],
    }
    assert _active_versions(store) == {"1.0.0": 1}
    assert Path(receipt["path"]).read_bytes() == b"known-good-ffmpeg"
    assert Path(receipt["ffprobe"]).read_bytes() == b"known-good-ffprobe"
    root = store.path.parent / "tools" / "ffmpeg"
    assert not (root / new_version).exists()
    assert list(root.glob(".staging-*")) == []


def test_interrupted_tool_download_preserves_active_version_and_cleans_staging(tmp_path, monkeypatch):
    store, receipt = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    replacement_payload = _artifact(b"replacement-ffmpeg", b"replacement-ffprobe")
    manifest = _manifest("2.0.0", replacement_payload)
    progress_values = []

    def interrupted_fetch(_url, destination, _sha256, progress, _cancel):
        destination.write_bytes(b"partial archive bytes")
        progress(0.25)
        raise ConnectionResetError("synthetic interrupted download")

    with pytest.raises(ConnectionResetError, match="interrupted download"):
        install(store, manifest, progress_values.append, fetch=interrupted_fetch)

    assert 1 not in progress_values
    _assert_previous_tool_remains_active(store, receipt, "2.0.0")


def test_tool_checksum_mismatch_preserves_active_version_and_cleans_staging(tmp_path, monkeypatch):
    store, receipt = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    expected_payload = _artifact(b"replacement-ffmpeg", b"replacement-ffprobe")
    manifest = _manifest("2.0.0", expected_payload)
    progress_values = []

    def tampered_fetch(_url, destination, _sha256, progress, _cancel):
        destination.write_bytes(b"tampered artifact bytes")
        progress(0.6)

    with pytest.raises(ValueError, match="Artifact SHA256 mismatch"):
        install(store, manifest, progress_values.append, fetch=tampered_fetch)

    assert 1 not in progress_values
    _assert_previous_tool_remains_active(store, receipt, "2.0.0")


def test_tool_cancel_after_download_preserves_active_version_and_cleans_staging(tmp_path, monkeypatch):
    store, receipt = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    replacement_payload = _artifact(b"replacement-ffmpeg", b"replacement-ffprobe")
    manifest = _manifest("2.0.0", replacement_payload)
    cancel = Event()
    progress_values = []

    def finish_then_cancel(_url, destination, _sha256, progress, _cancel):
        destination.write_bytes(replacement_payload)
        progress(0.75)
        cancel.set()

    with pytest.raises(RuntimeError, match="Canceled"):
        install(store, manifest, progress_values.append, cancel=cancel, fetch=finish_then_cancel)

    assert 1 not in progress_values
    _assert_previous_tool_remains_active(store, receipt, "2.0.0")


def test_installer_archive_preflight_failure_preserves_active_tool_and_cleans_staging(tmp_path, monkeypatch):
    store, receipt = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    malicious = _zip_with_members([
        ("../escape.txt", b"must not escape", None),
        (f"bin/{_executable_name('ffmpeg')}", b"replacement-ffmpeg", None),
        (f"bin/{_executable_name('ffprobe')}", b"replacement-ffprobe", None),
    ]).getvalue()
    manifest = _manifest("2.0.0", malicious)
    progress_values = []

    def malicious_fetch(_url, destination, _sha256, progress, _cancel):
        destination.write_bytes(malicious)
        progress(0.8)

    with pytest.raises(ValueError, match="Unsafe archive"):
        install(store, manifest, progress_values.append, fetch=malicious_fetch)

    assert 1 not in progress_values
    tool_root = store.path.parent / "tools" / "ffmpeg"
    assert not (tool_root / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()
    _assert_previous_tool_remains_active(store, receipt, "2.0.0")



def test_store_submit_holds_writer_lock_until_tool_snapshot_is_inserted(tmp_path, monkeypatch):
    from fonesi_edit import storage as storage_module

    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    snapshot_read = Event()
    release_submit = Event()
    update_at_activation = Event()
    update_finished = Event()
    submitted = {}
    failures = []
    original_checked_payload = storage_module.checked_payload
    original_activation = dependencies._save_tool_activation

    def pause_after_tool_snapshot(payload):
        if (isinstance(payload, dict) and "_tools" in payload
                and payload["_tools"].get("ffmpeg") == first["path"]):
            snapshot_read.set()
            if not release_submit.wait(10):
                raise AssertionError("test did not release the submit transaction")
        return original_checked_payload(payload)

    def observe_activation(*args, **kwargs):
        update_at_activation.set()
        return original_activation(*args, **kwargs)

    monkeypatch.setattr(storage_module, "checked_payload", pause_after_tool_snapshot)
    monkeypatch.setattr(dependencies, "_save_tool_activation", observe_activation)

    def submit_job():
        try:
            submitted["id"] = store.submit("render", {"output": str(tmp_path / "race.mp4")})
        except BaseException as exc:
            failures.append(exc)

    def update_tool():
        try:
            _install_next_ffmpeg_version(store, monkeypatch)
        except BaseException as exc:
            failures.append(exc)
        finally:
            update_finished.set()

    submit_thread = Thread(target=submit_job)
    submit_thread.start()
    assert snapshot_read.wait(10)
    update_thread = Thread(target=update_tool)
    update_thread.start()
    assert update_at_activation.wait(10)
    # A second writer must be unable to acquire SQLite's write reservation
    # while submit is paused after reading the immutable tool snapshot.
    probe = sqlite3.connect(store.path, timeout=0)
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            probe.execute("BEGIN IMMEDIATE")
    finally:
        probe.close()
    assert not update_finished.is_set()
    release_submit.set()
    submit_thread.join(10)
    update_thread.join(10)
    assert not submit_thread.is_alive() and not update_thread.is_alive()
    assert not failures
    assert submitted["id"]
    payload = store.job(submitted["id"])["payload"]
    assert payload["_tools"]["ffmpeg"] == first["path"]
    with pytest.raises(ValueError, match="held by"):
        remove_tool_version(store, "ffmpeg", "1.0.0")


def _install_next_ffmpeg_version(store, monkeypatch, version="2.0.0"):
    payload = _artifact(b"replacement-ffmpeg", b"replacement-ffprobe")
    manifest = _manifest(version, payload)
    return install(store, manifest, fetch=_fake_fetch({manifest["url"]: payload}, []))


def test_active_tool_version_is_protected_and_old_version_can_be_removed(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="active"):
        remove_tool_version(store, "ffmpeg", "1.0.0")

    second = _install_next_ffmpeg_version(store, monkeypatch)
    inventory = managed_tool_versions(store)
    old = next(item for item in inventory if item["version"] == "1.0.0")
    new = next(item for item in inventory if item["version"] == "2.0.0")
    assert not old["in_use"] and old["reason"] == "Có thể gỡ an toàn"
    assert new["in_use"] and new["active"]
    removed = remove_tool_version(store, "ffmpeg", "1.0.0")
    assert removed["directory_removed"]
    assert not Path(first["path"]).parent.parent.exists()
    assert Path(second["path"]).is_file()
    with store.connect() as conn:
        assert conn.execute(
            "SELECT 1 FROM tool_versions WHERE name='ffmpeg' AND version='1.0.0'"
        ).fetchone() is None


@pytest.mark.parametrize("state", ["pending", "running", "blocked", "failed", "canceled"])
def test_tool_version_lease_is_held_by_runnable_or_retryable_jobs(tmp_path, monkeypatch, state):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    job_id = store.submit("render", {"output": str(tmp_path / "job.mp4")})
    if state != "pending":
        with store.connect() as conn:
            conn.execute("UPDATE jobs SET state=? WHERE id=?", (state, job_id))
    _install_next_ffmpeg_version(store, monkeypatch)

    inventory = managed_tool_versions(store)
    old = next(item for item in inventory if item["version"] == "1.0.0")
    assert old["in_use"] and job_id in old["job_ids"]
    with pytest.raises(ValueError, match="held by"):
        remove_tool_version(store, "ffmpeg", "1.0.0")
    assert Path(first["path"]).is_file()


def test_ffprobe_companion_path_also_leases_its_ffmpeg_version_folder(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    store.set_setting("tool_paths", {"ffprobe": first["ffprobe"]})
    job_id = store.submit("scan", {"source": "synthetic"})
    _install_next_ffmpeg_version(store, monkeypatch)

    old = next(item for item in managed_tool_versions(store) if item["version"] == "1.0.0")
    assert job_id in old["job_ids"]
    with pytest.raises(ValueError, match="held by"):
        remove_tool_version(store, "ffmpeg", "1.0.0")


def test_succeeded_job_releases_its_old_tool_version_lease(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    job_id = store.submit("render", {"output": str(tmp_path / "done.mp4")})
    _install_next_ffmpeg_version(store, monkeypatch)
    store.finish(job_id, {"output": str(tmp_path / "done.mp4"), "validated": True})

    old = next(item for item in managed_tool_versions(store) if item["version"] == "1.0.0")
    assert not old["in_use"]
    remove_tool_version(store, "ffmpeg", "1.0.0")
    assert not Path(first["path"]).parent.parent.exists()


def test_submit_many_captures_one_tool_snapshot_and_holds_old_version(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    jobs = store.submit_many("render", [
        {"output": str(tmp_path / "one.mp4")},
        {"output": str(tmp_path / "two.mp4")},
    ])
    _install_next_ffmpeg_version(store, monkeypatch)
    for job_id in jobs:
        payload = store.job(job_id)["payload"]
        assert payload["_tools"]["ffmpeg"] == first["path"]
        assert payload["_tools"]["ffprobe"] == first["ffprobe"]
    with pytest.raises(ValueError, match="held by"):
        remove_tool_version(store, "ffmpeg", "1.0.0")


def test_tool_cleanup_refuses_database_path_outside_managed_root(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    _install_next_ffmpeg_version(store, monkeypatch)
    external = tmp_path / "external-system-tool"
    external.write_bytes(b"must not be deleted")
    with store.connect() as conn:
        conn.execute(
            "UPDATE tool_versions SET path=? WHERE name='ffmpeg' AND version='1.0.0'",
            (str(external),),
        )
    with pytest.raises(ValueError, match="outside"):
        remove_tool_version(store, "ffmpeg", "1.0.0")
    assert external.read_bytes() == b"must not be deleted"
    assert Path(first["path"]).is_file()


def test_tool_cleanup_permission_failure_keeps_metadata_and_active_paths(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    second = _install_next_ffmpeg_version(store, monkeypatch)
    old_folder = Path(first["path"]).parent.parent
    original_rmtree = dependencies.shutil.rmtree

    def denied(path, *args, **kwargs):
        if Path(path) == old_folder:
            raise PermissionError("synthetic access denied")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(dependencies.shutil, "rmtree", denied)
    with pytest.raises(PermissionError, match="access denied"):
        remove_tool_version(store, "ffmpeg", "1.0.0")
    assert old_folder.is_dir()
    assert Path(second["path"]).is_file()
    assert store.setting("tool_paths")["ffmpeg"] == second["path"]
    with store.connect() as conn:
        assert conn.execute(
            "SELECT 1 FROM tool_versions WHERE name='ffmpeg' AND version='1.0.0'"
        ).fetchone() is not None


def test_submit_many_validates_all_payloads_before_inserting_any_job(tmp_path):
    store = Store(tmp_path / "state" / "fonesi.db")
    with pytest.raises(ValueError, match="Secret values"):
        store.submit_many("render", [
            {"output": str(tmp_path / "good.mp4")},
            {"output": str(tmp_path / "bad.mp4"), "token": "must-not-store"},
        ])
    assert store.jobs() == []



@pytest.mark.skipif(os.name == "nt", reason="Windows symlink privilege requires user-machine acceptance")
def test_tool_cleanup_refuses_symlink_inside_managed_version_folder(tmp_path, monkeypatch):
    store, first = _install_active_ffmpeg_for_failure_tests(tmp_path, monkeypatch)
    _install_next_ffmpeg_version(store, monkeypatch)
    old_folder = Path(first["path"]).parent.parent
    outside = tmp_path / "outside-target"
    outside.write_bytes(b"must remain untouched")
    link = old_folder / "external-link"
    link.symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        remove_tool_version(store, "ffmpeg", "1.0.0")

    assert outside.read_bytes() == b"must remain untouched"
    assert old_folder.is_dir()
    assert Path(first["path"]).is_file()
