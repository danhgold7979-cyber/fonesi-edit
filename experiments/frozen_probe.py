"""Isolated P02 synthetic frozen Qt experiment, not the Fonesi Edit application."""
import argparse,json,sys,platform
from pathlib import Path
from PySide6.QtCore import QTimer,qVersion
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtGui import QFontDatabase
p=argparse.ArgumentParser();p.add_argument('--report',required=True);a=p.parse_args()
app=QApplication([]);w=QLabel('P02 synthetic frozen startup probe — Tiếng Việt 中文');w.resize(640,160);w.show();app.processEvents()
report={'experiment':'P02 frozen Qt only; not product','frozen':bool(getattr(sys,'frozen',False)),'qt':qVersion(),'visible':w.isVisible(),'font_family_count':len(QFontDatabase.families()),'platform':platform.platform(),'windows_target_acceptance':'NOT_RUN'}
Path(a.report).write_text(json.dumps(report,indent=2));QTimer.singleShot(50,app.quit);raise SystemExit(app.exec())
