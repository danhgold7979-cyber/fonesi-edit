"""Shared session-local history across Layer Editor and Timeline."""
import os
from fractions import Fraction

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file,load_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _project_file(tmp_path):
    project=empty_project(NewProjectIntent('Shared history',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'shared-history.json'
    save_project_file(path,project)
    return path


def _close(window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater()
    qt_app.processEvents()


def test_layer_and_timeline_share_one_monotonic_undo_redo_stack(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            timeline=window.timeline_panel

            editor.add_mask()
            assert window.session.revision==1
            assert len(window.project_history.undo_stack)==1

            assert timeline._commit_range_markers(5,20)
            assert window.session.revision==2
            assert len(window.project_history.undo_stack)==2
            plan=window.session.project.plan.to_dict()
            assert len(plan['layers'])==1
            assert plan['timeline_range']=={'in_frame':5,'out_frame':20}
            assert editor.undo_button.isEnabled() and timeline.undo_button.isEnabled()

            # Undo initiated from Timeline must undo the latest Timeline command.
            timeline.undo_button.click()
            assert window.session.revision==3
            plan=window.session.project.plan.to_dict()
            assert len(plan['layers'])==1 and 'timeline_range' not in plan

            # Undo initiated from Layer Editor continues the same global stack.
            editor.undo_button.click()
            assert window.session.revision==4
            assert window.session.project.plan.to_dict()['layers']==[]

            # Redo from either panel follows the original command order.
            timeline.redo_button.click()
            assert window.session.revision==5
            assert len(window.session.project.plan.to_dict()['layers'])==1
            editor.redo_button.click()
            assert window.session.revision==6
            plan=window.session.project.plan.to_dict()
            assert plan['timeline_range']=={'in_frame':5,'out_frame':20}
            assert len(window.project_history.undo_stack)==2
            assert not window.project_history.redo_stack

            window.save_current_project()
            saved,_=load_project_file(path)
            assert saved==window.session.project
        finally:
            _close(window,qt_app)


def test_timeline_focus_ctrl_z_undoes_layer_command_without_project_revision_rewind(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.layer_editor.add_mask()
            before=window.session.revision
            assert before==1
            window.timeline_panel.clip_list.setFocus()
            QTest.keyClick(window.timeline_panel.clip_list,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
            assert window.session.revision==before+1
            assert window.session.project.plan.to_dict()['layers']==[]
            assert len(window.project_history.redo_stack)==1
        finally:
            _close(window,qt_app)


def test_untracked_external_revision_invalidates_shared_history_without_replay(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'projects.sqlite3') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.layer_editor.add_mask()
            assert window.project_history.can_undo()
            data=window.session.project.plan.to_dict()
            data['revision']+=1
            data['provenance']['project_revision']=data['revision']
            plan=CompositionPlan.parse(data)
            window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
            window._project_changed()
            assert not window.project_history.undo_stack
            assert not window.project_history.redo_stack
            assert not window.layer_editor.undo_button.isEnabled()
            assert not window.timeline_panel.undo_button.isEnabled()
            assert len(window.session.project.plan.to_dict()['layers'])==1
        finally:
            _close(window,qt_app)
