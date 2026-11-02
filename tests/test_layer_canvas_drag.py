"""Canvas release commits normalized anchor coordinates once through ProjectSession."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import QPointF
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def test_canvas_release_commits_normalized_position_once(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Canvas move',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor;editor.add_mask()
            layer_id=window.session.project.plan.to_dict()['layers'][0]['id']
            before=window.session.revision
            editor.dragged(layer_id,QPointF(1440,270))
            assert window.session.revision==before+1
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['x']==[3,4] and transform['y']==[1,4]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_locked_canvas_layer_rejects_drag_without_revision_change(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Canvas lock',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor;editor.add_mask();editor.toggle_lock()
            layer_id=window.session.project.plan.to_dict()['layers'][0]['id']
            before=window.session.revision
            editor.dragged(layer_id,QPointF(1440,270))
            assert window.session.revision==before
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['x']==[1,2] and transform['y']==[1,2]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()
