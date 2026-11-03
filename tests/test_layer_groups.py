"""Persistent layer groups, multi-selection and batch actions use one project CAS."""
import os
from fractions import Fraction
from uuid import UUID

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file,load_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Layer groups',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    return store,window,path


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();store.close()


def _add(editor,count):
    ids=[]
    for _ in range(count):
        editor.add_mask()
        ids.append(editor.selected_id)
    return ids


def _layers(window):
    return window.session.project.plan.to_dict()['layers']


def test_multi_select_group_auto_select_ungroup_and_persist(tmp_path,qt_app):
    store,window,path=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        editor._sync_selection({first,second},first)
        assert editor.selected_ids=={first,second}
        before=window.session.revision
        editor.group_selected()
        assert window.session.revision==before+1
        layers={x['id']:x for x in _layers(window)}
        group_id=layers[first]['group_id']
        assert UUID(group_id) and layers[second]['group_id']==group_id
        assert editor.layers.selectedItems() and len(editor.layers.selectedItems())==2

        # Selecting just one group member expands selection to the whole group.
        editor._sync_selection({first},first)
        assert editor.selected_ids=={first,second}
        editor.ungroup_selected()
        assert window.session.revision==before+2
        assert all('group_id' not in x for x in _layers(window))
        window.save_current_project()
        saved,_=load_project_file(path)
        assert saved==window.session.project
    finally:
        _close(store,window,qt_app)


def test_group_batch_hide_lock_unlock_and_undo_are_atomic(tmp_path,qt_app):
    store,window,_=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        editor._sync_selection({first,second},first)
        editor.group_selected()
        grouped_revision=window.session.revision

        editor.toggle_visibility()
        assert window.session.revision==grouped_revision+1
        assert all(not x['visible'] for x in _layers(window))
        editor.toggle_lock()
        assert window.session.revision==grouped_revision+2
        assert all('transform' in x['locked_fields'] for x in _layers(window))
        editor.toggle_lock()
        assert window.session.revision==grouped_revision+3
        assert all(not x['locked_fields'] for x in _layers(window))
        editor.undo()
        assert window.session.revision==grouped_revision+4
        assert all('transform' in x['locked_fields'] for x in _layers(window))
        editor.redo()
        assert window.session.revision==grouped_revision+5
        assert all(not x['locked_fields'] for x in _layers(window))
    finally:
        _close(store,window,qt_app)


def test_group_drag_moves_visible_and_hidden_members_by_same_delta(tmp_path,qt_app):
    store,window,_=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        editor._sync_selection({first,second},first)
        editor.group_selected()
        data=window.session.project.plan.to_dict()
        hidden=next(x for x in data['layers'] if x['id']==second)
        hidden['visible']=False
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        editor.update_project()
        editor._sync_selection({first},first)
        before={x['id']:x['transform'] for x in _layers(window)}
        revision=window.session.revision
        from PySide6.QtCore import QPointF
        editor.dragged(first,QPointF(692,508),QPointF(500,400))
        assert window.session.revision==revision+1
        after={x['id']:x['transform'] for x in _layers(window)}
        assert after[first]['x']==[3,5] and after[first]['y']==[3,5]
        assert after[second]['x']==[3,5] and after[second]['y']==[3,5]
        assert before[first]['x']==before[second]['x']==[1,2]
    finally:
        _close(store,window,qt_app)


def test_mixed_locked_multi_selection_refuses_all_drag(tmp_path,qt_app):
    store,window,_=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        data=window.session.project.plan.to_dict()
        next(x for x in data['layers'] if x['id']==second)['locked_fields']=['transform']
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        editor.update_project();editor._sync_selection({first,second},first)
        revision=window.session.revision
        from PySide6.QtCore import QPointF
        editor.dragged(first,QPointF(700,500),QPointF(500,500))
        assert window.session.revision==revision
        assert all(x['transform']['x']==[1,2] for x in _layers(window))
        assert all(x['transform']['y']==[1,2] for x in _layers(window))
    finally:
        _close(store,window,qt_app)


def test_group_z_order_and_batch_delete_preserve_source_file(tmp_path,qt_app):
    store,window,_=_open(tmp_path)
    sentinel=tmp_path/'source.bin';sentinel.write_bytes(b'unchanged original source')
    try:
        editor=window.layer_editor
        first,second,third=_add(editor,3)
        editor._sync_selection({first,second},first);editor.group_selected()
        editor.move_selected(1)
        ordered=sorted(_layers(window),key=lambda x:x['z'])
        assert [x['id'] for x in ordered]==[third,first,second]
        editor._sync_selection({first},first)
        assert editor.selected_ids=={first,second}
        editor.delete_selected()
        assert {x['id'] for x in _layers(window)}=={third}
        assert sentinel.read_bytes()==b'unchanged original source'
    finally:
        _close(store,window,qt_app)

def test_tree_extended_selection_auto_expands_existing_group(tmp_path,qt_app):
    store,window,_=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        editor._sync_selection({first,second},first)
        editor.group_selected()
        editor.layers.clearSelection()
        editor.layers.item(0).setSelected(True)
        from PySide6.QtWidgets import QAbstractItemView
        assert editor.layers.selectionMode()==QAbstractItemView.SelectionMode.ExtendedSelection
        assert editor.selected_ids=={first,second}
        assert len(editor.layers.selectedItems())==2
    finally:
        _close(store,window,qt_app)


def test_context_menu_group_action_uses_same_atomic_command(tmp_path,qt_app,monkeypatch):
    from PySide6.QtCore import QPoint
    from fonesi_edit.ui import layer_editor as layer_editor_module
    class FakeAction:
        def __init__(self,label):self.label=label;self.enabled=True
        def text(self):return self.label
        def setEnabled(self,value):self.enabled=value
    class FakeMenu:
        def __init__(self,parent):self.items=[]
        def addAction(self,label):
            action=FakeAction(label);self.items.append(action);return action
        def addSeparator(self):self.items.append(None)
        def exec(self,position):
            return next(x for x in self.items if x is not None and x.text()=='Nhóm các layer đã chọn')
    monkeypatch.setattr(layer_editor_module,'QMenu',FakeMenu)
    store,window,_=_open(tmp_path)
    try:
        editor=window.layer_editor
        first,second=_add(editor,2)
        editor._sync_selection({first,second},first)
        before=window.session.revision
        editor.show_layer_context_menu(QPoint(1,1))
        layers={x['id']:x for x in _layers(window)}
        assert window.session.revision==before+1
        assert layers[first]['group_id']==layers[second]['group_id']
    finally:
        _close(store,window,qt_app)
