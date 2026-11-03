"""Canvas handles commit normalized resize/rotation through the shared project CAS."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt,QPointF,QCoreApplication,QEvent
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
    window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete);qt_app.processEvents();store.close()


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
        locked_item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==first)
        assert locked_item.show_handles is False
        revision=window.session.revision
        editor.resized(first,960,540,QPointF(960,540))
        editor.rotated(first,90)
        assert window.session.revision==revision
        transform=next(x for x in window.session.project.plan.to_dict()['layers'] if x['id']==first)['transform']
        assert transform['width']==[1,4] and transform['rotation']==[0,1]
    finally:
        _close(store,window,qt_app)


def test_invalid_canvas_geometry_is_rejected_without_project_revision(tmp_path,qt_app):
    from math import inf,nan
    from PySide6.QtCore import QPointF
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask();layer_id=editor.selected_id
        revision=window.session.revision
        editor.resized(layer_id,nan,540,QPointF(960,540))
        assert window.session.revision==revision
        editor.resized(layer_id,960,inf,QPointF(960,540))
        assert window.session.revision==revision
        editor.resized(layer_id,960,540,QPointF(nan,540))
        assert window.session.revision==revision
        editor.rotated(layer_id,nan)
        assert window.session.revision==revision
        editor.rotated(layer_id,inf)
        assert window.session.revision==revision
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['width']==[1,4] and transform['height']==[1,6]
        assert transform['rotation']==[0,1]
    finally:
        _close(store,window,qt_app)


def test_resize_preserves_each_of_nine_anchor_positions(tmp_path,qt_app):
    from fonesi_edit.ui.layer_editor import ANCHORS
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask();layer_id=editor.selected_id
        for anchor in ANCHORS:
            data=editor.data()
            layer=next(x for x in data['layers'] if x['id']==layer_id)
            layer['transform']['anchor']=anchor
            editor.commit(data,'fixture anchor')
            before=window.session.project.plan.to_dict()['layers'][0]['transform']
            anchor_x=before['x'];anchor_y=before['y']
            editor.resized(layer_id,960,540,QPointF(960,540))
            after=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert after['anchor']==anchor
            assert after['x']==anchor_x and after['y']==anchor_y
            assert after['width']==[1,2] and after['height']==[1,2]
    finally:
        _close(store,window,qt_app)


def test_all_resize_and_rotation_handles_are_in_selected_item_hit_shape(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask()
        item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==editor.selected_id)
        assert item.isSelected() and item.show_handles
        for name,local_point in item._resize_handles().items():
            scene_point=item.mapToScene(local_point)
            assert item in editor.scene.items(scene_point),name
        rotation_point=item.mapToScene(item._rotation_handle())
        assert item in editor.scene.items(rotation_point)
    finally:
        _close(store,window,qt_app)


def test_group_and_locked_items_do_not_hit_test_individual_handles(tmp_path,qt_app):
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor
        editor.add_mask();first=editor.selected_id
        editor.add_mask();second=editor.selected_id
        editor._sync_selection({first,second},first);editor.group_selected()
        items={x.layer_id:x for x in editor.scene.items() if getattr(x,'layer_id',None)}
        for item in items.values():
            assert not item.show_handles
            assert item not in editor.scene.items(item.mapToScene(item._rotation_handle()))

        editor._sync_selection({first},first);editor.toggle_lock()
        locked_item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==first)
        assert not locked_item.show_handles
        assert locked_item not in editor.scene.items(locked_item.mapToScene(locked_item._rotation_handle()))
    finally:
        _close(store,window,qt_app)


def test_deferred_canvas_gesture_callbacks_use_editor_qobject_context(tmp_path,qt_app,monkeypatch):
    from PySide6.QtCore import QTimer
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask()
        item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==editor.selected_id)
        scheduled=[];real=QTimer.singleShot
        def capture(*args):
            if len(args)==3 and args[0]==0:
                scheduled.append(args)
                return
            return real(*args)
        monkeypatch.setattr(QTimer,'singleShot',capture)
        item._defer_editor_callback(editor.dragged,item.layer_id,QPointF(10,10),QPointF(0,0),False)
        item._defer_editor_callback(editor.resized,item.layer_id,20,20,QPointF(10,10))
        item._defer_editor_callback(editor.rotated,item.layer_id,45)
        assert len(scheduled)==3
        assert all(call[1] is editor for call in scheduled)
    finally:
        _close(store,window,qt_app)


def test_viewport_pointer_drag_on_resize_handle_commits_one_geometry_command(tmp_path,qt_app):
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask()
        item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==editor.selected_id)
        handle=item._resize_handles()['se']
        start=editor.view.mapFromScene(item.mapToScene(handle))
        end=editor.view.mapFromScene(item.mapToScene(handle+QPointF(60,45)))
        before=window.session.revision
        QTest.mousePress(editor.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))
        QTest.mouseMove(editor.view.viewport(),QPoint(end))
        QTest.mouseRelease(editor.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(end))
        qt_app.processEvents()
        assert window.session.revision==before+1
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['width']==[9,32]
        assert transform['height']==[5,24]
        assert transform['x']==[1,2] and transform['y']==[1,2]
    finally:
        _close(store,window,qt_app)


def test_viewport_pointer_drag_on_rotation_handle_commits_one_geometry_command(tmp_path,qt_app):
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    store,window=_open(tmp_path)
    try:
        editor=window.layer_editor;editor.add_mask()
        item=next(x for x in editor.scene.items() if getattr(x,'layer_id',None)==editor.selected_id)
        rotation=item._rotation_handle()
        start=editor.view.mapFromScene(item.mapToScene(rotation))
        target=QPointF(item.rect().center().x()+abs(rotation.y()),item.rect().center().y())
        end=editor.view.mapFromScene(item.mapToScene(target))
        before=window.session.revision
        QTest.mousePress(editor.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(start))
        QTest.mouseMove(editor.view.viewport(),QPoint(end))
        QTest.mouseRelease(editor.view.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(end))
        qt_app.processEvents()
        assert window.session.revision==before+1
        transform=window.session.project.plan.to_dict()['layers'][0]['transform']
        assert transform['rotation']==[90,1]
    finally:
        _close(store,window,qt_app)
