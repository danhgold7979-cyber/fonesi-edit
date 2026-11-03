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
    target=edit.viewport() if hasattr(edit,'viewport') else edit
    enter = QDragEnterEvent(QPoint(2, 2), Qt.CopyAction, mime,
                            Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(target, enter)
    drop = QDropEvent(QPointF(2.0, 2.0), Qt.CopyAction, mime,
                      Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(target, drop)
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


def test_multiple_local_file_drop_queues_without_import_until_explicit_selection(editor,tmp_path):
    window=editor
    panel,tool=_trusted_panel(window)
    first=tmp_path/'first 中文.mp4';first.write_bytes(b'first source')
    second=tmp_path/'second.mov';second.write_bytes(b'second source')
    revision=window.session.revision

    entered,accepted=_send_drop(panel.drop_queue,[
        QUrl.fromLocalFile(str(first)),QUrl.fromLocalFile(str(second))
    ])

    assert entered and accepted
    assert panel.drop_queue.count()==2
    assert panel.drop_queue.item(0).text().startswith('Chờ chọn')
    assert panel.drop_queue.item(1).text().startswith('Chờ chọn')
    assert panel.drop_queue.item(0).data(Qt.UserRole)==str(first)
    assert panel.drop_queue.item(1).data(Qt.UserRole)==str(second)
    assert panel.source.text()=='' and panel.worker is None
    assert panel.use_drop_button.isEnabled() is False
    assert window.session.revision==revision and window.session.project.library is None
    assert first.read_bytes()==b'first source' and second.read_bytes()==b'second source'

    panel.drop_queue.setCurrentRow(1)
    assert panel.use_drop_button.isEnabled()
    panel.use_drop_button.click()
    assert panel.source.text()==str(second)
    assert panel.tool.text()==tool and panel.trust.isChecked()
    assert panel.worker is None and window.session.revision==revision
    assert window.session.project.library is None
    assert second.read_bytes()==b'second source'
    assert 'Chưa chạy kiểm tra' in panel.message.text()


def test_mixed_multi_file_drop_keeps_valid_item_and_marks_unsupported_items(editor,tmp_path):
    panel,tool=_trusted_panel(editor)
    valid=tmp_path/'valid.mp4';valid.write_bytes(b'valid bytes')
    folder=tmp_path/'folder';folder.mkdir()
    missing=tmp_path/'missing.mp4'
    urls=[
        QUrl.fromLocalFile(str(valid)),
        QUrl('https://example.invalid/remote.mp4'),
        QUrl.fromLocalFile(str(folder)),
        QUrl.fromLocalFile(str(missing)),
    ]
    revision=editor.session.revision

    entered,accepted=_send_drop(panel.drop_queue,urls)

    assert entered and accepted
    assert panel.drop_queue.count()==4
    assert panel.drop_queue.item(0).data(Qt.UserRole)==str(valid)
    assert all(panel.drop_queue.item(i).data(Qt.UserRole) is None for i in (1,2,3))
    assert all(panel.drop_queue.item(i).text().startswith('Từ chối') for i in (1,2,3))
    assert 'Đã xếp 1 tệp hợp lệ; 3 mục' in panel.message.text()
    assert panel.source.text()=='' and panel.worker is None
    assert editor.session.revision==revision and editor.session.project.library is None
    assert valid.read_bytes()==b'valid bytes'


def test_drop_queue_deduplicates_and_caps_valid_files(editor,tmp_path):
    panel,_tool=_trusted_panel(editor)
    duplicate=tmp_path/'duplicate.mp4';duplicate.write_bytes(b'duplicate')
    accepted,rejected=panel.drop_queue.add_urls([
        QUrl.fromLocalFile(str(duplicate)),QUrl.fromLocalFile(str(duplicate))
    ])
    assert (accepted,rejected)==(1,1)
    assert panel.drop_queue.count()==2
    assert panel.drop_queue.item(1).data(Qt.UserRole) is None
    assert 'trùng lặp' in panel.drop_queue.item(1).text().lower()

    panel.drop_queue.clear_queue()
    paths=[]
    for index in range(65):
        path=tmp_path/f'clip-{index}.mp4';path.write_bytes(str(index).encode());paths.append(path)
    accepted,rejected=panel.drop_queue.add_urls([QUrl.fromLocalFile(str(path)) for path in paths])
    assert accepted==64 and rejected==1
    assert sum(panel.drop_queue.item(i).data(Qt.UserRole) is not None
               for i in range(panel.drop_queue.count()))==64
    assert any('giới hạn 64' in panel.drop_queue.item(i).text().lower()
               for i in range(panel.drop_queue.count()))
    assert panel.source.text()=='' and panel.worker is None
    assert editor.session.revision==0 and editor.session.project.library is None


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
