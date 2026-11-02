"""Qt file-drop preflight only: no implicit probe, import, or project mutation."""
import os
from pathlib import Path
import sys
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication

from fonesi_edit.storage.project_creation import NewProjectIntent, empty_project
from fonesi_edit.storage.projects import ProjectStore, save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


@pytest.fixture
def editor(tmp_path, qt_app):
    project = empty_project(NewProjectIntent('Drop test', 1920, 1080,
                                             Fraction(30), Fraction(10)))
    project_file = tmp_path / 'project.json'
    save_project_file(project_file, project)
    with ProjectStore(tmp_path / 'projects.sqlite3') as store:
        window = MainWindow(store)
        window.show()
        window.open_project(project_file)
        yield window
        window.close()
        wait_for(qt_app, lambda: not window.background_busy and not window.isVisible())
        window.deleteLater()
        qt_app.processEvents()


def _trusted_panel(window):
    panel = window.media_import
    tool = str(Path(sys.executable).resolve())
    panel.tool.setText(tool)
    panel.trust.setChecked(True)
    assert panel.trust.isChecked()
    return panel, tool


def _send_drop(edit, urls):
    mime = QMimeData()
    mime.setUrls(urls)
    enter = QDragEnterEvent(QPoint(2, 2), Qt.CopyAction, mime,
                            Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(edit, enter)
    drop = QDropEvent(QPointF(2.0, 2.0), Qt.CopyAction, mime,
                      Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(edit, drop)
    return enter.isAccepted(), drop.isAccepted()


def test_one_local_file_drop_only_populates_selector(editor, tmp_path):
    source = tmp_path / 'media 中文.mp4'
    payload = b'unchanged source bytes'
    source.write_bytes(payload)
    window = editor
    panel, tool = _trusted_panel(window)
    revision = window.session.revision

    entered, accepted = _send_drop(panel.source, [QUrl.fromLocalFile(str(source))])

    assert entered and accepted
    assert panel.source.text() == str(source)
    assert panel.tool.text() == tool and panel.trust.isChecked()
    assert panel.worker is None
    assert window.session.revision == revision
    assert window.session.project.library is None
    assert source.read_bytes() == payload
    assert panel.add_button.isEnabled()
    assert 'Chưa chạy kiểm tra' in panel.message.text()


@pytest.mark.parametrize('urls', [
    [QUrl('https://example.invalid/video.mp4')],
    [QUrl.fromLocalFile('/tmp/one.mp4'), QUrl.fromLocalFile('/tmp/two.mp4')],
])
def test_remote_or_multiple_drop_is_refused_without_side_effects(editor, tmp_path, urls):
    window = editor
    panel, tool = _trusted_panel(window)
    panel.source.setText('keep-this-source')
    revision = window.session.revision

    _, accepted = _send_drop(panel.source, urls)

    assert not accepted
    assert panel.source.text() == 'keep-this-source'
    assert panel.tool.text() == tool and panel.trust.isChecked()
    assert panel.worker is None
    assert window.session.revision == revision
    assert window.session.project.library is None
    assert 'Không nhận được tệp' in panel.message.text()


def test_directory_and_missing_file_drop_are_refused(editor, tmp_path):
    window = editor
    panel, tool = _trusted_panel(window)
    panel.source.setText('keep-this-source')
    directory = tmp_path / 'folder'
    directory.mkdir()
    missing = tmp_path / 'missing.mp4'

    for candidate in (directory, missing):
        _, accepted = _send_drop(panel.source, [QUrl.fromLocalFile(str(candidate))])
        assert not accepted
        assert panel.source.text() == 'keep-this-source'
        assert panel.tool.text() == tool and panel.trust.isChecked()
        assert panel.worker is None
        assert window.session.revision == 0
        assert window.session.project.library is None


def test_symlink_drop_is_refused_when_platform_can_create_symlinks(editor, tmp_path):
    target = tmp_path / 'target.mp4'
    target.write_bytes(b'unchanged')
    link = tmp_path / 'link.mp4'
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip('This runner cannot create a symlink without additional privileges')

    window = editor
    panel, tool = _trusted_panel(window)
    panel.source.setText('keep-this-source')
    _, accepted = _send_drop(panel.source, [QUrl.fromLocalFile(str(link))])

    assert not accepted
    assert panel.source.text() == 'keep-this-source'
    assert panel.tool.text() == tool and panel.trust.isChecked()
    assert panel.worker is None
    assert window.session.revision == 0
    assert window.session.project.library is None
    assert target.read_bytes() == b'unchanged'
