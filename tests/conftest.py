from pathlib import Path
import os
import subprocess
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/fonesi-test-cache')

@pytest.fixture(scope='session')
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])

@pytest.fixture
def media(tmp_path):
    p=tmp_path/'nguồn 中文.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=25','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1.2','-c:v','libx264','-c:a','aac',str(p)],check=True)
    return p
