"""Smoke runs in a child process so a native Qt failure keeps its real exit status."""
import os
import json
from pathlib import Path
import subprocess
import sys

from fonesi_edit.prototypes.media import RenderSpec, create_fixture, extract_frame, render


def test_qt_window_opens_with_real_frame_and_closes_cleanly(tmp_path):
    source = create_fixture(tmp_path / 'media', duration=0.5)['source']
    screenshot = tmp_path / 'ui.png'
    result = subprocess.run([sys.executable, '-X', 'faulthandler', '-m', 'fonesi_edit.prototypes.cli',
        'ui', '--smoke', '--source', str(source), '--screenshot', str(screenshot)],
        env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'FONESI_PROTOTYPE_DATA_DIR': str(tmp_path / 'profiles')},
        capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stderr
    assert screenshot.read_bytes().startswith(b'\x89PNG') and screenshot.stat().st_size > 10000


def test_smoke_does_not_report_success_when_requested_media_cannot_load(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'fonesi_edit.prototypes.cli', 'ui', '--smoke',
        '--source', str(tmp_path / 'missing.mp4')], env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen',
        'FONESI_PROTOTYPE_DATA_DIR': str(tmp_path / 'profiles')}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1


def test_qt_multimedia_actually_decodes_frames_not_just_a_window(tmp_path):
    files = create_fixture(tmp_path / 'media', duration=1)
    source = tmp_path / 'composition.mp4'
    render(files['source'], source, RenderSpec(subtitles=files['subtitles'], logo=files['logo']))
    image = tmp_path / 'decoded.png'
    script = '''
import sys, json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
app=QApplication([])
player=QMediaPlayer()
sink=QVideoSink()
player.setVideoSink(sink)
count=[0]
def frame_ready(frame):
    if frame.isValid():
        count[0]+=1
        if count[0] == 2:
            image=frame.toImage()
            ok=not image.isNull() and image.save(sys.argv[2])
            with open(sys.argv[2]+'.json', 'w') as stream:
                json.dump({'start_us': frame.startTime()}, stream)
            player.stop()
            app.exit(0 if ok else 4)
sink.videoFrameChanged.connect(frame_ready)
player.errorOccurred.connect(lambda *args: app.exit(3))
player.setSource(QUrl.fromLocalFile(sys.argv[1]))
QTimer.singleShot(10000, lambda: app.exit(2))
player.play()
raise SystemExit(app.exec())
'''
    result = subprocess.run([sys.executable, '-X', 'faulthandler', '-c', script, str(source), str(image)],
        env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert image.is_file() and image.stat().st_size > 10000
    timestamp = json.loads(Path(str(image) + '.json').read_text())['start_us']
    assert timestamp >= 0
    reference = tmp_path / 'ffmpeg-reference.png'
    extract_frame(source, reference, timestamp / 1_000_000)
    from PySide6.QtGui import QImage
    actual = QImage(str(image)).convertToFormat(QImage.Format.Format_RGB888)
    expected = QImage(str(reference)).convertToFormat(QImage.Format.Format_RGB888)
    assert actual.size() == expected.size()
    a, b = bytes(actual.constBits()), bytes(expected.constBits())
    mean_error = sum(abs(x - y) for x, y in zip(a, b, strict=True)) / len(a)
    assert mean_error < 3, f'Qt vs FFmpeg RGB mean error: {mean_error}'
