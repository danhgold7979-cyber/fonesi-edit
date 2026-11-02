"""Layer ordering is durable project state, not widget-only stacking."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def test_layer_order_updates_z_values_and_undoes(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Layer order',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            editor=window.layer_editor
            editor.add_mask();first=window.session.project.plan.to_dict()['layers'][0]['id']
            editor.add_mask();second=window.session.project.plan.to_dict()['layers'][1]['id']
            assert window.session.revision==2
            editor.move_selected(1)
            ordered=sorted(window.session.project.plan.to_dict()['layers'],key=lambda x:x['z'])
            assert [x['id'] for x in ordered]==[second,first]
            assert [x['z'] for x in ordered]==[0,1]
            editor.undo()
            ordered=sorted(window.session.project.plan.to_dict()['layers'],key=lambda x:x['z'])
            assert [x['id'] for x in ordered]==[first,second]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()
