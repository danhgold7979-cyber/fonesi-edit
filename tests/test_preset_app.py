import json
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time

import pytest
from PySide6.QtWidgets import QApplication

from fonesi_edit import app as app_module
from fonesi_edit.app import MainWindow
from fonesi_edit.domain import Clip, Composition, Layer
from fonesi_edit.presets import build_preset_document, parse_preset_file

APP = QApplication.instance() or QApplication([])


def _close(window):
    window.force_close = True
    window.close()
    deadline = time.monotonic() + 20
    while (window.tasks or window.scheduler.active) and time.monotonic() < deadline:
        APP.processEvents()
        time.sleep(0.02)
    APP.processEvents()


def test_invalid_preset_import_is_atomic_and_does_not_change_active_project(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / "state")
    try:
        window.editor.set_composition(Composition(layers=[Layer(text="Keep active")]))
        before = window.editor.composition.to_dict()
        invalid = tmp_path / "duplicate.fonesipreset"
        invalid.write_text(
            '{"schema_version":1,"schema_version":1,"name":"Bad","composition":{}}',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            app_module.QFileDialog,
            "getOpenFileName",
            lambda *_args, **_kwargs: (str(invalid), ""),
        )
        with pytest.raises(ValueError, match="Duplicate JSON object key"):
            window.import_preset()
        assert window.store.list_named("presets") == []
        assert window.editor.composition.to_dict() == before
    finally:
        _close(window)


def test_valid_preset_import_reports_missing_assets_without_mutating_project(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / "state")
    try:
        window.editor.set_composition(Composition(layers=[Layer(text="Keep active")]))
        before = window.editor.composition.to_dict()
        missing = tmp_path / "not-installed-logo.png"
        document = build_preset_document(
            Composition(layers=[Layer(kind="image", path=str(missing))]),
            "Imported safely",
        )
        source = tmp_path / "valid.fonesipreset"
        source.write_text(json.dumps(document), encoding="utf-8")
        monkeypatch.setattr(
            app_module.QFileDialog,
            "getOpenFileName",
            lambda *_args, **_kwargs: (str(source), ""),
        )
        window.import_preset()
        saved = window.store.list_named("presets")
        assert len(saved) == 1
        assert saved[0]["name"] == "Imported safely"
        assert saved[0]["data"]["layers"][0]["path"] == str(missing)
        assert "not-installed-logo.png" in window.status.text()
        assert window.editor.composition.to_dict() == before
    finally:
        _close(window)


def test_export_preset_uses_shared_schema_and_strips_source_clip_identity(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / "state")
    try:
        clip = Clip(str(tmp_path / "source.mp4"))
        layer = Layer(kind="image", path=str(tmp_path / "logo.png"), clip_ids=[clip.id])
        window.editor.set_composition(Composition(clips=[clip], layers=[layer]))
        destination = tmp_path / "Portable.fonesipreset"
        monkeypatch.setattr(
            app_module.QFileDialog,
            "getSaveFileName",
            lambda *_args, **_kwargs: (str(destination), ""),
        )
        window.export_preset()
        parsed = parse_preset_file(destination)
        assert parsed.name == "Portable"
        assert parsed.composition.clips == []
        assert parsed.composition.layers[0].clip_ids == []
        assert parsed.composition.layers[0].path == str(tmp_path / "logo.png")
    finally:
        _close(window)
