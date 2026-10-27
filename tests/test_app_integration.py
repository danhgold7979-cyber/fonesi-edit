import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import time
from PySide6.QtWidgets import QApplication
from fonesi_edit.app import MainWindow
from fonesi_edit.domain import Composition,Clip,Layer
from fonesi_edit.prototypes.media import create_fixture,probe

APP=QApplication.instance() or QApplication([])


def wait_until(condition,seconds=20):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        APP.processEvents()
        if condition():return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for application state')


def close(window):
    window.force_close=True;window.close()
    wait_until(lambda:not window.tasks and not window.scheduler.active)
    APP.processEvents()


def test_app_project_queue_worker_output_and_reopen(tmp_path):
    fixture=create_fixture(tmp_path/'media',duration=.5)
    window=MainWindow(tmp_path/'state')
    assert window.nav.count()==8
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(fixture['source']),end=.5)],layers=[Layer(text='App thật',style={'font_size':18})])
    window.editor.set_composition(c);window.autosave();project=window.project_id
    output=tmp_path/'actual.mp4';job=window.store.submit('render',{'composition':c.to_dict(),'output':str(output)})
    wait_until(lambda:window.store.job(job)['state'] in {'succeeded','failed'})
    assert window.store.job(job)['state']=='succeeded',window.store.job(job)['error']
    assert probe(output).width==320
    close(window)
    restored=MainWindow(tmp_path/'state')
    assert restored.project_id==project and restored.editor.composition.layers[0].text=='App thật'
    assert restored.store.job(job)['result']['validated']
    close(restored)


def test_menu_shortcut_callback_does_not_receive_checked_as_function(tmp_path):
    window=MainWindow(tmp_path/'state');window.show();window.nav.setCurrentWidget(window.editor)
    window.editor.add_layer('text');window.editor.canvas.setFocus();APP.processEvents()
    assert len(window.editor.composition.layers)==1
    window.actions['Undo'].trigger();assert len(window.editor.composition.layers)==0
    window.actions['Redo'].trigger();assert len(window.editor.composition.layers)==1
    assert not window.failures
    close(window)
