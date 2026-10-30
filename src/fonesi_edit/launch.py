"""CLI entry and explicit startup-only packaging smoke test."""

import argparse
import json
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fonesi Edit rebuild")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication([sys.argv[0]])
    window = MainWindow()
    window.show()
    if args.smoke_test:

        def inspect():
            checks = {}
            try:
                window.open_subtitles()
                window.open_batch()
                app.processEvents()
                checks = {
                    "main_visible": window.isVisible(),
                    "subtitle_visible": window.subtitle_window.isVisible(),
                    "batch_visible": window.batch_window.isVisible(),
                    "empty_export_disabled": not window.export.isEnabled(),
                    "empty_batch_disabled": not window.batch_window.run_button.isEnabled(),
                    "workers_idle": window.worker is None
                    and window.batch_window.worker is None
                    and window.subtitle_window.worker is None,
                }
                ok = all(checks.values())
            except Exception:  # noqa: BLE001 - smoke reports fixed failure without private paths.
                ok = False
            print(
                json.dumps(
                    {
                        "kind": "fonesi-startup-smoke",
                        "frozen": bool(getattr(sys, "frozen", False)),
                        "checks": checks,
                        "passed": ok,
                    }
                ),
                flush=True,
            )
            window.close()
            app.exit(0 if ok else 1)

        QTimer.singleShot(100, inspect)
    return app.exec()
