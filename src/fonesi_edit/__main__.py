"""Application and headless validation entry points."""
import argparse
from pathlib import Path
import sys
from fonesi_edit import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog='fonesi-edit')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--validate-plan', type=Path, help='Validate a CompositionPlan without GUI or user-data writes')
    parser.add_argument('--data-dir', type=Path, help='Explicit user-data directory (never installation directory by default)')
    args = parser.parse_args(argv)
    if args.validate_plan:
        from fonesi_edit.domain.composition import CompositionPlan, MAX_PLAN_BYTES
        from fonesi_edit.fileio import read_bounded
        try:
            plan = CompositionPlan.parse(read_bounded(args.validate_plan, MAX_PLAN_BYTES))
        except (OSError, ValueError) as exc:
            print(f'Invalid plan: {exc}', file=sys.stderr)
            return 2
        print(f'Valid CompositionPlan; {len(plan.diagnostics)} diagnostic(s). No media/render verification.')
        return 0
    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication, QMessageBox
    from fonesi_edit.storage.projects import ProjectStore
    from fonesi_edit.ui.shell import MainWindow
    app = QApplication([sys.argv[0]])
    app.setOrganizationName('Fonesi')
    app.setApplicationName('Fonesi Edit')
    data = args.data_dir or Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
    try:
        store = ProjectStore(data / 'projects.sqlite3')
    except Exception as exc:
        QMessageBox.critical(None, 'Không thể mở dữ liệu ứng dụng', str(exc))
        return 2
    try:
        window = MainWindow(store)
        window.show()
        return app.exec()
    finally:
        store.close()

if __name__ == '__main__':
    raise SystemExit(main())
