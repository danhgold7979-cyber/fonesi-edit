"""Canvas handles commit normalized resize/rotation through the shared project CAS."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import QPointF
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Canvas handles',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    return store,window


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();store.close()


def test_resize_and_rotation_handle_commands_share_one_project_revision_each(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask();layer_id=editor.selected_id
        item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==layer_id)
        assert item.show_handles is True
        assert item.boundingRect().top()<item.rect().top()
        assert item.shape().contains(item._rotation_handle())
        assert item.shape().contains(next(iter(item._resize_handles().values())))
        before=window.session.revision
        editor.resized(layer_id,960,540,QPointF(960,540))
        assert window.session.revision==before+1
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['width']==[1,2] and transform['height']==[1,2]
        assert transform['x']==[1,2] and transform['y']==[1,2]

        editor.rotated(layer_id,37.5)
        assert window.session.revision==before+2
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['rotation']==[75,2]
    finally:
        _close(store,window,qt_app)


def test_group_selection_hides_individual_resize_handles_and_locked_layer_refuses(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first,second},first);editor.group_selected()
        items={x.layer_id:x for x in editor.scene.items() if getattr(x,'layer_id',None)}
        assert not items[first].show_handles and not items[second].show_handles

        editor._sync_selection({first},first)
        editor.toggle_lock()
        revision=window.session.revision
        editor.resized(first,960,540,QPointF(960,540))
        editor.rotated(first,90)
        assert window.session.revision==revision
        transform=next(x for x in window.session.project.plan.to_dict()['layers'] if x['id']==first)['transform']
        assert transform['width']==[1,4] and transform['rotation']==[0,1]
    finally:
        _close(store,window,qt_app)
