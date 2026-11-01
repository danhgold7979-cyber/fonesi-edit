"""Application and headless validation entry points."""
import argparse
from pathlib import Path
import sys
from fonesi_edit import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog='fonesi-edit')
    parser.add_argument('--version', action='version', version=__version__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--validate-plan', type=Path, help='Validate a CompositionPlan without GUI or user-data writes')
    modes.add_argument('--validate-subtitles', type=Path, help='Parse subtitle input without GUI or user-data writes')
    modes.add_argument('--scan-tools',action='store_true',help='Read-only executable candidates; never execute or install')
    parser.add_argument('--tool-path',action='append',default=[],metavar='TOOL=PATH',help='Explicit selected executable; invalid selection never falls back')
    parser.add_argument('--tool-dir',type=Path,action='append',default=[],help='Additional named executable search directory')
    modes.add_argument('--scan-media',type=Path,help='Read-only bounded source candidate discovery; no decoding')
    parser.add_argument('--exclude-root',type=Path,action='append',default=[],help='Existing output/cache directory excluded from source discovery')
    parser.add_argument('--subtitle-format', choices=('srt','vtt','ass','ssa'))
    parser.add_argument('--subtitle-encoding', default=None)
    parser.add_argument('--data-dir', type=Path, help='Explicit user-data directory (never installation directory by default)')
    modes.add_argument('--restore-project-store',type=Path,help='Restore an offline project backup to a NEW database; never overwrite')
    parser.add_argument('--restore-destination',type=Path,help='New absolute database path in an existing private directory')
    parser.add_argument('--restore-timeout',type=float,default=None,help='Cooperative restore deadline in seconds (maximum 3600)')
    args = parser.parse_args(argv)
    if args.restore_project_store is not None:
        if (args.restore_destination is None or args.data_dir is not None or args.tool_path or args.tool_dir or
            args.exclude_root or args.subtitle_format is not None or args.subtitle_encoding is not None):
            parser.error('Restore requires --restore-destination and cannot accompany unrelated mode options')
        from fonesi_edit.storage.restore import restore_project_backup,RestoreError
        try:
            result=restore_project_backup(args.restore_project_store,args.restore_destination,
                                          timeout=300 if args.restore_timeout is None else args.restore_timeout)
        except RestoreError as exc:
            print('Project restore not confirmed. Source is not modified; any new destination is retained. Do not automatically retry.',file=sys.stderr)
            if exc.ownership_unknown:
                print('Destination ownership outcome requires reconciliation.',file=sys.stderr)
            return 2
        print(f'Restored {result.project_count} project(s) to a new store; schema {result.schema_version}. Original backup is unchanged.')
        return 0
    if args.restore_destination is not None or args.restore_timeout is not None:
        parser.error('Restore options require --restore-project-store')
    if args.scan_tools:
        if args.subtitle_format is not None or args.subtitle_encoding is not None or args.exclude_root:
            parser.error('Media/subtitle options cannot accompany --scan-tools')
        from fonesi_edit.dependencies.discovery import discover_tools,system_search_dirs
        from dataclasses import asdict
        import json
        try:
            configured={}
            for value in args.tool_path:
                key,separator,path=value.partition('=')
                if not separator or not path or key in configured:raise ValueError('Invalid/repeated explicit selection')
                configured[key]=path
            result=discover_tools(configured=configured,system_dirs=system_search_dirs(),extra_dirs=args.tool_dir)
        except (OSError,ValueError,TypeError):
            print('Tool discovery refused; check explicit absolute paths and bounded search roots.',file=sys.stderr)
            return 2
        print(json.dumps(asdict(result),ensure_ascii=True))
        return 0 if result.status=='COMPLETE' else 3
    if args.tool_path or args.tool_dir:parser.error('Tool path/directory options require --scan-tools')
    if args.scan_media:
        if args.subtitle_format is not None or args.subtitle_encoding is not None:
            parser.error('Subtitle options require --validate-subtitles')
        from fonesi_edit.media.discovery import scan_media,DiscoveryError
        import json
        try:
            result=scan_media(args.scan_media,excluded_roots=tuple(args.exclude_root))
        except DiscoveryError:
            print('Source discovery refused; check explicit local source/output/cache roots.',file=sys.stderr)
            return 2
        print(json.dumps({'status':result.status,'examined':result.examined,'excluded':result.excluded,
                          'candidates':[str(path) for path in result.paths],
                          'media_validated':False},ensure_ascii=True))
        return 0 if result.status=='COMPLETE' else 3
    if args.exclude_root:
        parser.error('--exclude-root requires --scan-media')
    if args.validate_subtitles:
        if args.subtitle_format is None:
            parser.error('--validate-subtitles requires --subtitle-format')
        from fonesi_edit.subtitles.files import load_subtitles
        from fonesi_edit.subtitles.adapter import SubtitleError
        try:
            document=load_subtitles(args.validate_subtitles,args.subtitle_format,
                                    encoding='utf-8-sig' if args.subtitle_encoding is None else args.subtitle_encoding)
        except SubtitleError as exc:
            print(f'Invalid subtitles: {exc}',file=sys.stderr)
            return 2
        print(f'Parsed subtitles; {len(document.cues)} cue(s). No style/render fidelity verification.')
        for diagnostic in document.diagnostics:
            print(diagnostic)
        return 0
    if args.subtitle_format is not None or args.subtitle_encoding is not None:
        parser.error('Subtitle options require --validate-subtitles')
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
    from PySide6.QtCore import QStandardPaths,QCoreApplication,QEvent
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
    window=None
    try:
        window = MainWindow(store)
        window.show()
        return app.exec()
    finally:
        if window is not None:
            # QApplication must outlive all GUI objects and their worker cleanup.
            import time
            window.request_stop()
            while window.background_busy:
                app.processEvents();time.sleep(.01)
            window.close();window.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
            app.processEvents()
        store.close()

if __name__ == '__main__':
    raise SystemExit(main())
