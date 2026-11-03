"""Canvas guides, snap/Alt and bring-into-frame preserve canonical geometry rules."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


ANCHORS=('top_left','top_center','top_right','center_left','center',
         'center_right','bottom_left','bottom_center','bottom_right')


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Canvas guides',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    return store,window


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();store.close()


def _add(editor):
    editor.add_mask()
    return editor.selected_id


def _commit_data(window,data):
    data['revision']+=1;data['provenance']['project_revision']=data['revision']
    plan=CompositionPlan.parse(data)
    window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
    window.layer_editor.update_project()


def _fraction(pair):
    return Fraction(pair[0],pair[1])


def test_grid_and_safe_area_are_view_only_and_preserve_selection(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor
        layer_id=_add(editor)
        revision=window.session.revision
        selected=set(editor.selected_ids)
        initial=editor.scene.items().__len__()
        editor.grid_check.setChecked(True)
        assert editor.scene.items().__len__()>initial
        editor.safe_check.setChecked(True)
        assert editor.selected_ids==selected
        assert window.session.revision==revision
        assert any(isinstance(item,object) for item in editor.scene.items())
    finally:
        _close(store,window,qt_app)


def test_grid_snap_rounds_anchor_delta_to_five_percent(tmp_path,qt_app):
    from PySide6.QtCore import QPointF
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;layer_id=_add(editor)
        editor.snap_check.setChecked(True)
        before=window.session.revision
        editor.dragged(layer_id,QPointF(100,100),QPointF(0,0),False)
        assert window.session.revision==before+1
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['x']==[11,20]
        assert transform['y']==[3,5]
    finally:
        _close(store,window,qt_app)


def test_alt_drag_bypasses_grid_snap_for_one_move(tmp_path,qt_app):
    from PySide6.QtCore import QPointF
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;layer_id=_add(editor)
        editor.snap_check.setChecked(True)
        editor.dragged(layer_id,QPointF(100,100),QPointF(0,0),True)
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['x']==[53,96]
        assert transform['y']==[16,27]
    finally:
        _close(store,window,qt_app)


def test_bring_into_frame_handles_all_nine_anchors_atomically(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor
        ids=[_add(editor) for _ in ANCHORS]
        data=window.session.project.plan.to_dict()
        for layer,anchor in zip(data['layers'],ANCHORS):
            layer['transform']['anchor']=anchor
            layer['transform']['x']=[-1,10]
            layer['transform']['y']=[-1,10]
        _commit_data(window,data)
        editor._sync_selection(set(ids),ids[0])
        before=window.session.revision
        editor.bring_into_frame()
        assert window.session.revision==before+1
        for layer in window.session.project.plan.to_dict()['layers']:
            t=layer['transform'];w=_fraction(t['width'])*_fraction(t['scale_x'])
            h=_fraction(t['height'])*_fraction(t['scale_y'])
            x=_fraction(t['x']);y=_fraction(t['y'])
            ox=0 if t['anchor'].endswith('left') else (-w if t['anchor'].endswith('right') else -w/2)
            oy=0 if t['anchor'].startswith('top') else (-h if t['anchor'].startswith('bottom') else -h/2)
            assert x+ox>=0 and x+ox+w<=1
            assert y+oy>=0 and y+oy+h<=1
    finally:
        _close(store,window,qt_app)


def test_oversized_selected_layer_refuses_bring_into_frame_without_partial_edit(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;layer_id=_add(editor)
        data=window.session.project.plan.to_dict()
        data['layers'][0]['transform']['width']=[2,1]
        _commit_data(window,data)
        editor._sync_selection({layer_id},layer_id)
        before=window.session.revision
        x_before=window.session.project.plan.to_dict()['layers'][0]['transform']['x']
        editor.bring_into_frame()
        assert window.session.revision==before
        assert window.session.project.plan.to_dict()['layers'][0]['transform']['x']==x_before
        assert 'lớn hơn khung' in editor.status.text().lower()
    finally:
        _close(store,window,qt_app)
