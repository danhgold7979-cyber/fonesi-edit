from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def empty_plan():
    return json.loads((ROOT/'docs/schemas/examples/empty-composition.json').read_text())
@pytest.fixture
def multi_plan():
    return json.loads((ROOT/'docs/schemas/examples/multi-stream-composition.json').read_text())


@pytest.fixture(scope='session')
def qt_app():
    # One QApplication lifetime for all GUI tests; do not recreate it per test
    # while Qt still has deferred QObject/QThread deletions.
    import os
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication,QEvent,QThread
    app=QApplication.instance() or QApplication([])
    yield app
    # QWidget wrappers may remain in Python/Qt signal cycles after close().
    # Dispose every top-level widget while QApplication still owns GUI services.
    for widget in app.topLevelWidgets():
        widget.close()
        for thread in widget.findChildren(QThread):
            thread.requestInterruption()
            assert thread.wait(5000),'GUI fixture retained a live thread at teardown'
        widget.deleteLater()
    app.processEvents()
    QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
    app.processEvents()
