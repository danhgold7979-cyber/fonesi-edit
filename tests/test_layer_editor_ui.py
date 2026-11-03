"""Layer geometry commands persist through the shared project session, not widget-only state."""
import os
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.storage.project_creation import NewProjectIntent, empty_project
from fonesi_edit.storage.projects import ProjectStore, save_project_file, load_project_file
from fonesi_edit.ui.shell import MainWindow
from PySide6.QtCore import Qt,QCoreApplication,QEvent
from PySide6.QtTest import QTest
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
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_inspector_slider_drag_commits_once_and_keyboard_step_commits_once(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            editor=window.layer_editor;editor.add_mask()
            slider=editor.sliders['x']
            before=window.session.revision
            slider.setSliderDown(True)
            slider.setValue(60)
            slider.setValue(70)
            assert editor.spins['x'].value()==0.7
            assert window.session.revision==before
            slider.setSliderDown(False)
            slider.sliderReleased.emit()
            assert window.session.revision==before+1
            assert window.session.project.plan.to_dict()['layers'][0]['transform']['x']==[7,10]

            before=window.session.revision
            slider.setFocus()
            QTest.keyClick(slider,Qt.Key.Key_Right)
            assert window.session.revision==before+1
            assert window.session.project.plan.to_dict()['layers'][0]['transform']['x']==[71,100]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_inspector_property_and_group_resets_commit_once_and_preserve_other_fields(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            editor=window.layer_editor;editor.add_mask()
            editor.spins['x'].setValue(0.75)
            editor.spins['y'].setValue(0.25)
            editor.apply_inspector()
            before=window.session.revision
            editor.reset_buttons['x'].click()
            assert window.session.revision==before+1
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['x']==[1,2] and transform['y']==[1,4]

            editor.syncing=True
            try:
                editor.spins['x'].setValue(0.7);editor.spins['y'].setValue(0.3)
                editor.spins['width'].setValue(0.5);editor.spins['height'].setValue(0.5)
                editor.spins['scale_x'].setValue(2);editor.spins['scale_y'].setValue(0.5)
                editor.spins['rotation'].setValue(45);editor.spins['opacity'].setValue(0.4)
                editor.anchor.setCurrentText('top_left')
                editor.flip_x.setChecked(True);editor.flip_y.setChecked(True)
            finally:editor.syncing=False
            editor.apply_inspector()
            before=window.session.revision
            editor.reset_transform_button.click()
            assert window.session.revision==before+1
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform=={
                'x':[1,2],'y':[1,2],'width':[1,4],'height':[1,6],
                'scale_x':[1,1],'scale_y':[1,1],'rotation':[0,1],'opacity':[1,1],
                'anchor':'center','flip_x':False,'flip_y':False,
            }
            before=window.session.revision
            editor.reset_transform_button.click()
            assert window.session.revision==before
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_anchor_and_flip_individual_resets_restore_only_selected_property(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            editor=window.layer_editor;editor.add_mask()
            editor.anchor.setCurrentText('top_left');editor.apply_inspector()
            editor.flip_x.setChecked(True)
            before=window.session.revision
            editor.reset_anchor_button.click()
            assert window.session.revision==before+1
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['anchor']=='center' and transform['flip_x'] is True
            before=window.session.revision
            editor.reset_flip_x_button.click()
            assert window.session.revision==before+1
            transform=window.session.project.plan.to_dict()['layers'][0]['transform']
            assert transform['flip_x'] is False and transform['anchor']=='center'
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_inspector_basic_advanced_search_units_and_tooltips(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.navigation.setCurrentRow(3)
            editor=window.layer_editor
            assert 'Mở hoặc tạo dự án' in editor.inspector_reason.text()
            window.open_project(path)
            assert 'Chọn một layer' in editor.inspector_reason.text()

            assert not editor.inspector_advanced.isChecked()
            for name in ('x','y','width','height','opacity'):
                assert editor.inspector_rows[name][0].isVisible()
            for name in ('scale_x','scale_y','rotation','anchor','flip_x','flip_y'):
                assert not editor.inspector_rows[name][0].isVisible()

            editor.inspector_advanced.setChecked(True)
            for name in ('scale_x','scale_y','rotation','anchor','flip_x','flip_y'):
                assert editor.inspector_rows[name][0].isVisible()

            editor.inspector_search.setText('xoay')
            assert editor.inspector_rows['rotation'][0].isVisible()
            assert not editor.inspector_rows['scale_x'][0].isVisible()
            editor.inspector_search.clear()
            assert editor.inspector_rows['rotation'][0].isVisible()

            editor.inspector_advanced.setChecked(False)
            assert not editor.inspector_rows['rotation'][0].isVisible()
            editor.inspector_search.setText('xoay')
            assert editor.inspector_rows['rotation'][0].isVisible()
            assert not editor.inspector_rows['width'][0].isVisible()
            editor.inspector_search.clear()
            assert editor.inspector_rows['width'][0].isVisible()
            assert not editor.inspector_rows['rotation'][0].isVisible()

            editor.add_mask()
            assert 'Đang chỉnh một layer' in editor.inspector_reason.text()
            assert 'Đang chỉnh một layer' in editor.spins['x'].toolTip()
            assert 'Đang chỉnh một layer' in editor.sliders['rotation'].toolTip()
            assert 'tỷ lệ khung' in editor.inspector_rows['x'][1].text()
            assert '°' in editor.inspector_rows['rotation'][1].text()
            assert '0–1' in editor.inspector_rows['opacity'][1].text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_inspector_disabled_reasons_follow_multi_selection_and_lock(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.navigation.setCurrentRow(3)
            window.open_project(path)
            editor=window.layer_editor
            assert 'Chọn một layer' in editor.inspector_reason.text()
            editor.add_mask();first=editor.selected_id
            editor.add_mask();second=editor.selected_id
            editor._sync_selection({first,second},first);editor.update_actions()
            assert 'nhiều layer' in editor.inspector_reason.text()
            assert not editor.sliders['x'].isEnabled()
            assert not editor.reset_buttons['x'].isEnabled()

            editor._sync_selection({first},first);editor.update_actions()
            editor.toggle_lock()
            assert 'đang khóa biến đổi' in editor.inspector_reason.text()
            assert not editor.spins['x'].isEnabled()
            assert not editor.sliders['x'].isEnabled()
            assert not editor.reset_transform_button.isEnabled()
            assert 'đang khóa biến đổi' in editor.reset_anchor_button.toolTip().lower()
            assert 'đang khóa biến đổi' in editor.reset_flip_x_button.toolTip().lower()
            assert 'đang khóa biến đổi' in editor.reset_transform_button.toolTip().lower()

            editor.toggle_lock()
            assert 'Đang chỉnh một layer' in editor.inspector_reason.text()
            assert editor.spins['x'].isEnabled()
            assert editor.sliders['x'].isEnabled()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


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
            assert not editor.sliders['x'].isEnabled()
            assert not editor.reset_buttons['x'].isEnabled()
            assert not editor.reset_transform_button.isEnabled()
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
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


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
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


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
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_inspector_controls_have_localized_accessible_names_and_help(tmp_path,qt_app):
    path=_project_file(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            editor=window.layer_editor
            labels={
                'x':'X (tỷ lệ khung)',
                'y':'Y (tỷ lệ khung)',
                'width':'Rộng (tỷ lệ khung)',
                'height':'Cao (tỷ lệ khung)',
                'scale_x':'Tỷ lệ X (×)',
                'scale_y':'Tỷ lệ Y (×)',
                'rotation':'Xoay (°)',
                'opacity':'Độ mờ (0–1)',
            }
            for key,label in labels.items():
                assert editor.spins[key].accessibleName()==f'{label} — giá trị số'
                assert editor.spins[key].accessibleDescription()
                assert editor.sliders[key].accessibleName()==f'Thanh trượt {label}'
                assert editor.sliders[key].accessibleDescription()
                assert editor.reset_buttons[key].accessibleName()==f'Đặt lại {label}'

            assert editor.anchor.accessibleName()=='Điểm neo layer'
            assert editor.reset_anchor_button.accessibleName()=='Đặt lại điểm neo'
            assert editor.flip_x.accessibleName()=='Lật layer theo chiều ngang'
            assert editor.flip_y.accessibleName()=='Lật layer theo chiều dọc'
            assert editor.reset_flip_x_button.accessibleName()=='Đặt lại lật ngang'
            assert editor.reset_flip_y_button.accessibleName()=='Đặt lại lật dọc'
            assert editor.reset_transform_button.accessibleName()=='Đặt lại toàn bộ biến đổi layer'
            assert editor.reset_transform_button.toolTip()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
