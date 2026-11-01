"""Isolated P02 synthetic frozen Qt experiment, not the Fonesi Edit application."""
import argparse,json,sys,platform
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    # Exclusive report ownership established before Qt initialization; never truncate a foreign file.
    with args.report.open('x',encoding='utf-8') as report_file:
        from PySide6.QtCore import QTimer,qVersion
        from PySide6.QtWidgets import QApplication,QLabel
        from PySide6.QtGui import QFontDatabase
        app=QApplication([]);window=QLabel('P02 synthetic frozen startup probe — Tiếng Việt 中文');window.resize(640,160);window.show();app.processEvents()
        report={'experiment':'P02 frozen Qt only; not product','frozen':bool(getattr(sys,'frozen',False)),'qt':qVersion(),'visible':window.isVisible(),'font_family_count':len(QFontDatabase.families()),'platform':platform.platform(),'windows_target_acceptance':'NOT_RUN'}
        json.dump(report,report_file,indent=2);report_file.flush();QTimer.singleShot(50,app.quit)
        return app.exec()

if __name__=='__main__':raise SystemExit(main())
