"""Qt integration coverage for managed tool inventory and safe cleanup."""
import hashlib
import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from fonesi_edit.app import MainWindow
from fonesi_edit.browser import bind, bindings, create_profile, profiles
from fonesi_edit.prototypes.tools import ToolStatus


APP = QApplication.instance() or QApplication([])


class _FakeTask(QObject):
    finished = Signal()

    def __init__(self, already_finished=False):
        super().__init__()
        self._finished = already_finished

    def isFinished(self):
        return self._finished

    def finish(self):
        self._finished = True
        self.finished.emit()


def _wait_until(condition, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        APP.processEvents()
        if condition():
            return
        time.sleep(0.02)
    raise AssertionError("Timed out waiting for Qt application state")


def _close(window):
    window.force_close = True
    window.close()
    _wait_until(lambda: not window.tasks and not window.scheduler.active)
    APP.processEvents()


def _window(tmp_path):
    window = MainWindow(tmp_path / "state")
    _wait_until(lambda: not window.tasks)
    return window


def _register_version(window, version, payload, active=False):
    executable_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    folder = window.data / "tools" / "ffmpeg" / version
    executable = folder / "bin" / executable_name
    executable.parent.mkdir(parents=True, exist_ok=False)
    executable.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with window.store.connect() as conn:
        conn.execute(
            "INSERT INTO tool_versions(name,version,path,hash,active) VALUES(?,?,?,?,?)",
            ("ffmpeg", version, str(executable), digest, int(active)),
        )
    return folder, executable


def _seed_versions(window):
    old_folder, old_executable = _register_version(
        window, "1.0.0", b"old managed ffmpeg"
    )
    active_folder, active_executable = _register_version(
        window, "2.0.0", b"active managed ffmpeg", active=True
    )
    window.store.set_setting("tool_paths", {"ffmpeg": str(active_executable)})
    window.settings.refresh_managed_tools()
    return old_folder, old_executable, active_folder, active_executable


def _row_for(table, identity):
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is not None and item.data(Qt.ItemDataRole.UserRole) == identity:
            return row
    raise AssertionError(f"Managed tool row not found: {identity}")


def test_settings_inventory_and_confirmed_cleanup_preserve_active_tool_and_chrome(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        old_folder, old_executable, active_folder, active_executable = _seed_versions(window)
        profile_id = create_profile(window.store, "Chrome A")
        binding_id = bind(window.store, profile_id, "YouTube")
        profile = next(item for item in profiles(window.store) if item["id"] == profile_id)
        profile_folder = Path(profile["path"])
        marker = profile_folder / "fonesi-profile.json"
        marker_before = marker.read_bytes()
        bindings_before = bindings(window.store)

        table = window.settings.managed_tools
        old_row = _row_for(table, ("ffmpeg", "1.0.0"))
        active_row = _row_for(table, ("ffmpeg", "2.0.0"))
        assert table.item(old_row, 3).text() == "Có thể gỡ"
        assert table.item(old_row, 3).toolTip() == "Có thể gỡ an toàn"
        assert table.item(active_row, 3).text() == "Đang được giữ"
        assert "active" in table.item(active_row, 3).toolTip().lower()

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
        )
        table.setCurrentCell(old_row, 0)
        table.selectRow(old_row)
        window.settings.remove_managed_tool()
        _wait_until(lambda: not window.tasks and table.rowCount() == 1)

        assert not old_folder.exists()
        assert not old_executable.exists()
        assert active_folder.is_dir()
        assert active_executable.read_bytes() == b"active managed ffmpeg"
        assert window.store.setting("tool_paths") == {
            "ffmpeg": str(active_executable)
        }
        with window.store.connect() as conn:
            assert conn.execute(
                "SELECT 1 FROM tool_versions WHERE name='ffmpeg' AND version='1.0.0'"
            ).fetchone() is None
            active = conn.execute(
                "SELECT version,active,path FROM tool_versions WHERE name='ffmpeg' AND active=1"
            ).fetchone()
            assert tuple(active) == ("2.0.0", 1, str(active_executable))

        assert profile_folder.is_dir()
        assert marker.read_bytes() == marker_before
        assert bindings(window.store) == bindings_before
        assert any(item["id"] == binding_id for item in bindings(window.store))
    finally:
        _close(window)


def test_settings_cleanup_cancel_keeps_directory_registry_and_selection(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        old_folder, old_executable, active_folder, active_executable = _seed_versions(window)
        table = window.settings.managed_tools
        old_row = _row_for(table, ("ffmpeg", "1.0.0"))
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
        )
        table.setCurrentCell(old_row, 0)
        table.selectRow(old_row)

        window.settings.remove_managed_tool()

        assert old_folder.is_dir()
        assert old_executable.read_bytes() == b"old managed ffmpeg"
        assert active_folder.is_dir()
        assert window.store.setting("tool_paths") == {
            "ffmpeg": str(active_executable)
        }
        with window.store.connect() as conn:
            assert conn.execute(
                "SELECT 1 FROM tool_versions WHERE name='ffmpeg' AND version='1.0.0'"
            ).fetchone() is not None
    finally:
        _close(window)


def test_settings_rejects_removal_of_job_leased_version_before_confirmation(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        old_folder, old_executable, active_folder, active_executable = _seed_versions(window)
        window.store.set_setting("tool_paths", {"ffmpeg": str(old_executable)})
        job_id = window.store.submit(
            "render", {"output": str(window.data / "leased-output.mp4")}
        )
        window.store.set_setting("tool_paths", {"ffmpeg": str(active_executable)})
        window.settings.refresh_managed_tools()

        table = window.settings.managed_tools
        old_row = _row_for(table, ("ffmpeg", "1.0.0"))
        assert table.item(old_row, 3).text() == "Đang được giữ"
        assert job_id in table.item(old_row, 3).toolTip()

        def unexpected_confirmation(*_args, **_kwargs):
            pytest.fail("A leased tool must be rejected before confirmation")

        monkeypatch.setattr(QMessageBox, "question", unexpected_confirmation)
        table.setCurrentCell(old_row, 0)
        table.selectRow(old_row)
        with pytest.raises(ValueError, match="Được giữ bởi job"):
            window.settings.remove_managed_tool()

        assert old_folder.is_dir()
        assert old_executable.read_bytes() == b"old managed ffmpeg"
        assert active_folder.is_dir()
        assert window.store.setting("tool_paths") == {
            "ffmpeg": str(active_executable)
        }
        assert window.store.job(job_id)["payload"]["_tools"]["ffmpeg"] == str(
            old_executable
        )
    finally:
        _close(window)



def test_settings_per_tool_busy_guard_rejects_ffprobe_alias_and_releases_finished_tasks(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        scheduled = []

        def fake_background(function, done):
            task = _FakeTask()
            scheduled.append((function, done, task))
            return task

        monkeypatch.setattr(window, "background", fake_background)
        settings = window.settings

        ffmpeg_task = settings.install_name("ffmpeg")
        with pytest.raises(ValueError, match="ffmpeg.*đang"):
            settings.install_name("ffprobe")
        assert len(scheduled) == 1
        assert settings._tool_is_busy("ffmpeg")
        assert settings._tool_is_busy("ffprobe")
        assert "ffmpeg" in settings.tool_busy_label.text()

        node_task = settings.install_name("node")
        assert len(scheduled) == 2
        assert settings._tool_is_busy("node")

        ffmpeg_task.finish()
        _wait_until(lambda: not settings._tool_is_busy("ffmpeg"))
        assert settings._tool_is_busy("node")
        node_task.finish()
        _wait_until(lambda: not settings._tool_busy)
        assert settings.tool_busy_label.text() == ""
    finally:
        _close(window)


def test_settings_install_missing_skips_busy_tools_but_schedules_independent_tools(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        scheduled = []

        def fake_background(function, done):
            task = _FakeTask()
            scheduled.append(task)
            return task

        monkeypatch.setattr(window, "background", fake_background)
        settings = window.settings
        settings.statuses = [
            ToolStatus("ffmpeg", None, "missing"),
            ToolStatus("ffprobe", None, "missing"),
            ToolStatus("Google Chrome", None, "missing"),
            ToolStatus("node", None, "missing"),
        ]

        ffmpeg_task = settings.install_name("ffmpeg")
        settings.install_missing()

        assert len(scheduled) == 3
        assert set(settings._tool_busy) == {"ffmpeg", "Google Chrome", "node"}
        assert "ffmpeg" in window.status.text()
        assert not settings.tool_actions["Cài phần bắt buộc thiếu"].isEnabled()

        for task in scheduled:
            task.finish()
        _wait_until(lambda: not settings._tool_busy)
    finally:
        _close(window)


def test_settings_busy_tool_disables_and_rejects_path_rollback_and_cleanup(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        old_folder, old_executable, active_folder, active_executable = _seed_versions(window)
        scheduled = []

        def fake_background(function, done):
            task = _FakeTask()
            scheduled.append(task)
            return task

        monkeypatch.setattr(window, "background", fake_background)
        settings = window.settings
        tool_row = next(
            row for row in range(settings.tools.rowCount())
            if settings.tools.item(row, 0).text() == "ffmpeg"
        )
        settings.tools.setCurrentCell(tool_row, 0)
        task = settings.install_name("ffmpeg")

        assert not settings.tool_actions["Chọn đường dẫn"].isEnabled()
        assert not settings.tool_actions["Tải / cài công cụ chọn"].isEnabled()
        assert not settings.tool_actions["Rollback"].isEnabled()
        with pytest.raises(ValueError, match="đang được cập nhật"):
            settings.path()
        with pytest.raises(ValueError, match="đang được cập nhật"):
            settings.rollback()

        old_row = _row_for(settings.managed_tools, ("ffmpeg", "1.0.0"))
        settings.managed_tools.setCurrentCell(old_row, 0)
        assert not settings.managed_actions["Gỡ bản đã chọn"].isEnabled()

        def unexpected_confirmation(*_args, **_kwargs):
            pytest.fail("A busy tool must be rejected before cleanup confirmation")

        monkeypatch.setattr(QMessageBox, "question", unexpected_confirmation)
        with pytest.raises(ValueError, match="đang được cập nhật"):
            settings.remove_managed_tool()
        assert old_folder.is_dir()
        assert old_executable.is_file()
        assert active_folder.is_dir()
        assert active_executable.is_file()

        task.finish()
        _wait_until(lambda: not settings._tool_is_busy("ffmpeg"))
        assert settings.tool_actions["Chọn đường dẫn"].isEnabled()
        assert settings.tool_actions["Tải / cài công cụ chọn"].isEnabled()
        assert settings.tool_actions["Rollback"].isEnabled()
    finally:
        _close(window)


def test_settings_tool_busy_state_clears_if_background_scheduling_raises(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        def fail_scheduling(_function, _done):
            raise RuntimeError("synthetic scheduler failure")

        monkeypatch.setattr(window, "background", fail_scheduling)
        settings = window.settings
        with pytest.raises(RuntimeError, match="scheduler failure"):
            settings.install_name("node")
        assert not settings._tool_busy
        assert settings.tool_busy_label.text() == ""
    finally:
        _close(window)


def test_settings_tool_busy_state_handles_task_finishing_before_signal_connection(
    tmp_path, monkeypatch
):
    window = _window(tmp_path)
    try:
        task = _FakeTask(already_finished=True)
        monkeypatch.setattr(window, "background", lambda _function, _done: task)
        settings = window.settings
        settings.install_name("node")
        assert not settings._tool_busy
        assert settings.tool_busy_label.text() == ""
    finally:
        _close(window)
