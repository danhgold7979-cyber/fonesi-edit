"""Crop inspector edits canonical normalized crop; timeline zoom stays presentation-only."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import QCoreApplication,QEvent
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.ui.shell import MainWindow
from test_timeline_commands import _record,_scan
from test_queue_view import wait_for


def _window(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Crop and zoom',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    record=_record(tmp_path/'source.mp4',b'crop source')
    addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
    window.session.commit(addition.command);window._project_changed()
    window.timeline_panel.clip_list.setCurrentRow(0)
    return store,window,addition


def _close(window,store,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete);store.close()


def test_crop_inspector_commits_valid_rectangle_and_preserves_exact_untouched_fields(tmp_path,qt_app):
    store,window,addition=_window(tmp_path,qt_app)
    try:
        data=window.session.project.plan.to_dict()
        data['clips'][0]['crop']={'left':[0,1],'top':[1,3],'width':[1,1],'height':[2,3]}
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        window._project_changed()
        panel=window.timeline_panel
        panel.clip_list.setCurrentRow(0)
        before=window.session.revision
        panel.crop_spins['left'].setValue(0.25)
        panel.crop_spins['width'].setValue(0.75)
        panel.apply_crop()
        assert window.session.revision==before+1
        crop=window.session.project.plan.to_dict()['clips'][0]['crop']
        assert crop=={'left':[1,4],'top':[1,3],'width':[3,4],'height':[2,3]}
        assert 'chưa có crop preview' in panel.action_message.text().lower()
    finally:
        _close(window,store,qt_app)


def test_invalid_crop_is_rejected_without_project_mutation(tmp_path,qt_app):
    store,window,_=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        before=window.session.revision
        original=window.session.project.plan.to_dict()['clips'][0]['crop']
        panel.crop_spins['left'].setValue(0.8)
        panel.crop_spins['width'].setValue(0.3)
        panel.apply_crop()
        assert window.session.revision==before
        assert window.session.project.plan.to_dict()['clips'][0]['crop']==original
        assert 'không hợp lệ' in panel.action_message.text().lower()
    finally:
        _close(window,store,qt_app)


def test_stale_crop_inspector_refreshes_instead_of_overwriting_newer_revision(tmp_path,qt_app):
    store,window,_=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        panel.crop_spins['left'].setValue(0.25)
        data=window.session.project.plan.to_dict()
        data['seed']+=1
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        current=window.session.revision
        panel.apply_crop()
        assert window.session.revision==current
        assert window.session.project.plan.to_dict()['clips'][0]['crop']['left']==[0,1]
        assert 'đã đổi' in panel.action_message.text().lower()
        assert panel.crop_spins['left'].value()==0.0
    finally:
        _close(window,store,qt_app)


def test_timeline_zoom_scroll_and_playhead_marker_do_not_mutate_project(tmp_path,qt_app):
    store,window,_=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        before=window.session.revision
        panel.playhead_slider.setValue(15)
        expected_x=panel._timeline_left+0.5*panel._timeline_scale
        assert abs(panel._playhead_marker.rect().x()-expected_x)<1e-9
        panel.zoom_slider.setValue(200)
        assert panel.zoom_label.text()=='200%'
        assert panel.view.horizontalScrollBar().maximum()>0
        assert window.session.revision==before
        panel.fit_button.click()
        assert panel.zoom_slider.value()==100
        assert window.session.revision==before
    finally:
        _close(window,store,qt_app)


def test_crop_overlay_drag_stages_then_cancel_keeps_project_unchanged(tmp_path,qt_app):
    from PySide6.QtCore import Qt,QPoint
    from PySide6.QtGui import QPixmap
    from PySide6.QtTest import QTest
    store,window,addition=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        data=window.session.project.plan.to_dict()
        data['clips'][0]['crop']={'left':[1,5],'top':[1,5],'width':[2,5],'height':[2,5]}
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        window._project_changed();panel.clip_list.setCurrentRow(0)
        panel.preview_image.setPixmap(QPixmap(400,200))
        panel._refresh_crop_inspector();panel.update_actions();qt_app.processEvents()
        panel.crop_edit_toggle.setChecked(True)
        assert panel.crop_edit_toggle.isChecked()
        revision=window.session.revision
        panel.preview_image.crop_changed.emit({'left':.25,'top':.25,'width':.4,'height':.4})
        assert panel._crop_overlay_pending
        assert panel.crop_apply_button.isEnabled()
        assert window.session.revision==revision
        panel.crop_cancel_button.click()
        assert window.session.revision==revision
        assert not panel._crop_overlay_pending
        assert window.session.project.plan.to_dict()['clips'][0]['crop']=={
            'left':[1,5],'top':[1,5],'width':[2,5],'height':[2,5]}
    finally:
        _close(window,store,qt_app)


def test_crop_overlay_confirm_commits_one_normalized_project_revision(tmp_path,qt_app):
    from PySide6.QtCore import Qt,QPoint
    from PySide6.QtGui import QPixmap
    from PySide6.QtTest import QTest
    store,window,_=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        data=window.session.project.plan.to_dict()
        data['clips'][0]['crop']={'left':[1,5],'top':[1,5],'width':[2,5],'height':[2,5]}
        data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        window._project_changed();panel.clip_list.setCurrentRow(0)
        panel.preview_image.setPixmap(QPixmap(400,200))
        panel._refresh_crop_inspector();panel.update_actions();qt_app.processEvents();panel.crop_edit_toggle.setChecked(True)
        panel.crop_edit_toggle.setChecked(True)
        assert panel.crop_edit_toggle.isChecked()
        before=window.session.revision
        panel.preview_image.crop_changed.emit({'left':.25,'top':.25,'width':.4,'height':.4})
        assert window.session.revision==before
        panel.crop_apply_button.click()
        assert window.session.revision==before+1
        crop=window.session.project.plan.to_dict()['clips'][0]['crop']
        assert .24 < float(Fraction(*crop['left'])) < .26
        assert .24 < float(Fraction(*crop['top'])) < .26
        assert crop['width']==[2,5] and crop['height']==[2,5]
        assert not panel._crop_overlay_pending
        assert 'chưa có crop preview compositor' in panel.action_message.text().lower()
    finally:
        _close(window,store,qt_app)


def test_crop_overlay_stale_revision_refuses_confirm_and_reloads_model(tmp_path,qt_app):
    from PySide6.QtGui import QPixmap
    store,window,_=_window(tmp_path,qt_app)
    try:
        panel=window.timeline_panel
        panel.preview_image.setPixmap(QPixmap(400,200))
        panel._refresh_crop_inspector();panel.update_actions();qt_app.processEvents()
        panel.crop_edit_toggle.setChecked(True)
        before=window.session.revision
        original=window.session.project.plan.to_dict()['clips'][0]['crop']
        panel.preview_image.crop_changed.emit({'left':.25,'top':.25,'width':.4,'height':.4})
        assert panel._crop_overlay_pending
        data=window.session.project.plan.to_dict()
        data['seed']+=1;data['revision']+=1;data['provenance']['project_revision']=data['revision']
        plan=CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(window.session.project.with_plan(plan),window.session.revision))
        current=window.session.revision
        panel.crop_apply_button.click()
        assert current==before+1 and window.session.revision==current
        assert window.session.project.plan.to_dict()['clips'][0]['crop']==original
        assert not panel._crop_overlay_pending
        assert 'project đã đổi' in panel.action_message.text().lower()
    finally:
        _close(window,store,qt_app)


def test_crop_overlay_pending_edit_is_discarded_when_clip_changes(tmp_path,qt_app):
    from PySide6.QtGui import QPixmap
    store,window,_=_window(tmp_path,qt_app)
    try:
        second=_record(tmp_path/'second.mp4',b'second crop source')
        added=add_video_clip(window.session.project,second,_scan(second),expected_revision=window.session.revision)
        window.session.commit(added.command);window._project_changed()
        panel=window.timeline_panel;panel.clip_list.setCurrentRow(0)
        panel.preview_image.setPixmap(QPixmap(400,200))
        panel._refresh_crop_inspector();panel.update_actions();qt_app.processEvents()
        panel.crop_edit_toggle.setChecked(True)
        before=window.session.revision
        panel.preview_image.crop_changed.emit({'left':.25,'top':.25,'width':.4,'height':.4})
        assert panel._crop_overlay_pending
        panel.clip_list.setCurrentRow(1)
        assert window.session.revision==before
        assert not panel._crop_overlay_pending
        assert panel.selected_clip_id==added.clip_id
        assert window.session.project.plan.to_dict()['clips'][1]['crop']=={
            'left':[0,1],'top':[0,1],'width':[1,1],'height':[1,1]}
    finally:
        _close(window,store,qt_app)


def test_confirmed_overlay_crop_survives_project_save_and_reopen(tmp_path,qt_app):
    from PySide6.QtGui import QPixmap
    store,window,_=_window(tmp_path,qt_app)
    path=tmp_path/'project.json'
    try:
        panel=window.timeline_panel
        panel.preview_image.setPixmap(QPixmap(400,200))
        panel._refresh_crop_inspector();panel.update_actions();qt_app.processEvents()
        panel.crop_edit_toggle.setChecked(True)
        panel.preview_image.crop_changed.emit({'left':.25,'top':.25,'width':.4,'height':.4})
        panel.crop_apply_button.click()
        expected={'left':[1,4],'top':[1,4],'width':[2,5],'height':[2,5]}
        assert window.session.project.plan.to_dict()['clips'][0]['crop']==expected
        window.session.save()
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
        reopened=MainWindow(store);reopened.show();reopened.open_project(path)
        assert reopened.session.project.plan.to_dict()['clips'][0]['crop']==expected
        reopened.close()
        wait_for(qt_app,lambda:not reopened.background_busy and not reopened.isVisible())
        reopened.deleteLater();QCoreApplication.sendPostedEvents(reopened,QEvent.Type.DeferredDelete)
    finally:
        if window.isVisible():
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
        store.close()
