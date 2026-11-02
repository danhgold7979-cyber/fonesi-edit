"""Layer geometry commands persist through the shared project session, not widget-only state."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.storage.project_creation import NewProjectIntent, empty_project
from fonesi_edit.storage.projects import ProjectStore, save_project_file, load_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _project_file(tmp_path):
    project=empty_project(NewProjectIntent('Layer editor',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json'
    save_project_file(path,project)
    return path


def test_mask_layer_add_numeric_edit_undo_redo_and_save_reopen(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            editor.add_mask()
            assert window.session.revision==1
            layer=window.session.project.plan.to_dict()['layers'][0]
            layer_id=layer['id']
            assert layer['type']=='mask' and layer['visible']
            assert window.session.project.plan.to_dict()['clips']==[]
            assert editor.layers.count()==1
            assert 'chưa giải mã video' in editor.notice.text().lower()

            editor.spins['x'].setValue(0.6)
            editor.spins['y'].setValue(0.4)
            editor.apply_inspector()
            assert window.session.revision==2
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['x']==[3,5] and transform['y']==[2,5]

            editor.undo()
            assert window.session.revision==3
            restored=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert restored['x']==[1,2] and restored['y']==[1,2]

            editor.redo()
            assert window.session.revision==4
            redone=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert redone['x']==[3,5] and redone['y']==[2,5]

            window.save_current_project()
            saved,_=load_project_file(path)
            assert saved==window.session.project
            assert saved.plan.to_dict()['layers'][0]['id']==layer_id
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_transform_lock_visibility_and_undo_are_model_changes(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            editor.add_mask()
            editor.toggle_lock()
            assert window.session.revision==2
            layer=window.session.project.plan.to_dict()['layers'][0]
            assert 'transform' in layer['locked_fields']
            assert not editor.spins['x'].isEnabled()
            editor.spins['x'].setValue(0.75)
            editor.apply_inspector()
            assert window.session.revision==2
            assert window.session.project.plan.to_dict()['layers'][0]['transform']['x']==[1,2]

            editor.toggle_lock()
            assert window.session.revision==3
            editor.toggle_visibility()
            assert window.session.revision==4
            assert window.session.project.plan.to_dict()['layers'][0]['visible'] is False
            editor.undo()
            assert window.session.revision==5
            assert window.session.project.plan.to_dict()['layers'][0]['visible'] is True
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_delete_layer_never_deletes_any_source_file(tmp_path,qt_app):
    path=_project_file(tmp_path)
    sentinel=tmp_path/'original-media.bin'
    sentinel.write_bytes(b'original source stays untouched')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            editor.add_mask()
            editor.delete_selected()
            assert window.session.revision==2
            assert window.session.project.plan.to_dict()['layers']==[]
            assert sentinel.read_bytes()==b'original source stays untouched'
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_external_revision_change_invalidates_session_undo_history(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            editor.add_mask()
            assert editor.undo_stack
            # Simulate a separate completed project edit by committing the same
            # validated composition at the next revision through the session.
            from fonesi_edit.domain.composition import CompositionPlan
            from fonesi_edit.storage.autosave import CompletedCommand
            data=window.session.project.plan.to_dict()
            data['revision']+=1
            data['provenance']['project_revision']=data['revision']
            plan=CompositionPlan.parse(data)
            window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
            editor.update_project()
            assert not editor.undo_stack and not editor.redo_stack
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()
