"""The inspector must not round untouched rational fields."""
import os
from PySide6.QtCore import QCoreApplication,QEvent
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def test_editing_rotation_preserves_unmodified_third_coordinate(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Rational precision',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor;editor.add_mask()
            data=window.session.project.plan.to_dict()
            data['layers'][0]['transform']['x']=[1,3]
            data['revision']+=1
            data['provenance']['project_revision']=data['revision']
            window.session.commit(CompletedCommand(
                window.session.project.with_plan(CompositionPlan.parse(data)),
                window.session.revision))
            editor.update_project()
            editor.spins['rotation'].setValue(45)
            editor.apply_inspector()
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['x']==[1,3]
            assert transform['rotation']==[45,1]
            assert window.session.revision==3
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
