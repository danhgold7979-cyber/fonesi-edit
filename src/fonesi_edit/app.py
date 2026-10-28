from pathlib import Path
import argparse
import sys


def main(argv=None):
    values=list(sys.argv[1:] if argv is None else argv)
    if len(values)>=2 and values[0]=='--tool':
        module=values[1];sys.argv=[module,*values[2:]]
        if module=='yt_dlp':
            import yt_dlp;yt_dlp.main()
        elif module=='gallery_dl':
            import gallery_dl;gallery_dl.main()
        else:raise ValueError('Unsupported bundled tool')
        return 0
    parser=argparse.ArgumentParser(prog='fonesi-edit')
    parser.add_argument('--worker',nargs=3,metavar=('DATABASE','JOB','OWNER'))
    parser.add_argument('--diagnose',action='store_true')
    parser.add_argument('--verify',type=Path)
    args=parser.parse_args(argv)
    if args.worker:
        from .core.jobs import execute_job
        execute_job(Path(args.worker[0]),args.worker[1],args.worker[2]);return 0
    if args.diagnose:
        import json,platform,shutil
        from . import __version__
        print(json.dumps({'version':__version__,'os':platform.platform(),'ffmpeg':shutil.which('ffmpeg'),'ffprobe':shutil.which('ffprobe'),'acceptance':'development — see docs/CURRENT_STATUS.md'}));return 0
    if args.verify:
        from .verification import verify
        return verify(args.verify)
    from PySide6.QtWidgets import QApplication
    from .ui.window import MainWindow
    app=QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('Fonesi Edit');app.setOrganizationName('Fonesi')
    window=MainWindow();window.show()
    return app.exec()

if __name__=='__main__':
    raise SystemExit(main())
