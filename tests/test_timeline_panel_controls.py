"""Timeline playhead uses integer output frames and commits split commands once."""
import os
import pytest
from pathlib import Path
from PySide6.QtCore import QCoreApplication,QEvent
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.ui.shell import MainWindow
from test_timeline_commands import _record,_scan
from test_queue_view import wait_for


def test_playhead_split_updates_video_and_audio_tracks_once(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Timeline controls',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    record=_record(tmp_path/'clip.mp4')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
            window.session.commit(addition.command)
            window._project_changed()
            timeline=window.timeline_panel
            assert timeline.clip_list.count()==1
            timeline.clip_list.setCurrentRow(0)
            timeline.playhead_slider.setValue(15)
            assert timeline.playhead_label.text().endswith('0.500s')
            assert timeline.split_button.isEnabled()
            before=window.session.revision
            timeline.split_button.click()
            assert window.session.revision==before+1
            data=window.session.project.plan.to_dict()
            assert len(data['clips'])==2 and len(data['audio']['clips'])==2
            assert timeline.clip_list.count()==2
            assert timeline.selected_clip_id==addition.clip_id
            assert 'Chưa phát' not in timeline.notice.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_trim_in_gap_mode_moves_left_edge_but_keeps_following_clip(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Timeline trim',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    first=_record(tmp_path/'one.mp4',b'one')
    second=_record(tmp_path/'two.mp4',b'two')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            one=add_video_clip(window.session.project,first,_scan(first),expected_revision=window.session.revision)
            window.session.commit(one.command)
            two=add_video_clip(window.session.project,second,_scan(second),expected_revision=window.session.revision)
            window.session.commit(two.command)
            window._project_changed()
            timeline=window.timeline_panel
            timeline.clip_list.setCurrentRow(0)
            timeline.playhead_slider.setValue(15)
            assert timeline.trim_in_button.isEnabled()
            timeline.trim_in_button.click()
            data=window.session.project.plan.to_dict()
            clip=next(x for x in data['clips'] if x['id']==one.clip_id)
            following=next(x for x in data['clips'] if x['id']==two.clip_id)
            assert clip['output_start']==[1,2] and clip['source_in']==[1,2]
            assert following['output_start']==[1,1]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)

def test_playhead_stops_at_last_valid_output_frame(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Frame boundary',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            timeline=window.timeline_panel
            assert timeline.playhead_slider.maximum()==299
            timeline.playhead_slider.setValue(299)
            assert timeline.playhead_label.text().startswith('Playhead: 299 frame')
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)

def test_in_out_markers_persist_across_project_file_reopen_and_clear(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Timeline range markers',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    record=_record(tmp_path/'marker.mp4',b'marker clip')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);reopened=None;window.show()
        try:
            window.open_project(path)
            addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
            window.session.commit(addition.command);window._project_changed()
            timeline=window.timeline_panel
            before=window.session.revision
            timeline.playhead_slider.setValue(10)
            timeline.set_in_button.click()
            assert timeline._in_frame==10 and timeline._out_frame is None
            assert window.session.revision==before+1
            assert window.session.project.plan.to_dict()['timeline_range']=={'in_frame':10,'out_frame':None}
            timeline.playhead_slider.setValue(20)
            timeline.set_out_button.click()
            assert timeline._out_frame==21
            assert '11 frame' in timeline.range_label.text()
            assert 'Out 21' in timeline.range_label.text()
            assert window.session.revision==before+2
            assert window.session.project.plan.to_dict()['timeline_range']=={'in_frame':10,'out_frame':21}
            from PySide6.QtWidgets import QGraphicsTextItem
            assert any(isinstance(item,QGraphicsTextItem) and item.toPlainText()=='IN' for item in timeline.scene.items())
            assert any(isinstance(item,QGraphicsTextItem) and item.toPlainText()=='OUT' for item in timeline.scene.items())
            window.session.save()
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
            window=None

            reopened=MainWindow(store);reopened.show();reopened.open_project(path)
            restored=reopened.timeline_panel
            assert restored._in_frame==10 and restored._out_frame==21
            assert '11 frame' in restored.range_label.text()
            assert reopened.session.project.plan.to_dict()['timeline_range']=={'in_frame':10,'out_frame':21}
            before_clear=reopened.session.revision
            restored.clear_range_button.click()
            assert restored._in_frame is None and restored._out_frame is None
            assert 'Chưa chọn vùng' in restored.range_label.text()
            assert reopened.session.revision==before_clear+1
            assert 'timeline_range' not in reopened.session.project.plan.to_dict()
            reopened.session.save()
        finally:
            for current in (reopened,window):
                if current is not None:
                    current.close()
                    wait_for(qt_app,lambda current=current:not current.background_busy and not current.isVisible())
                    current.deleteLater();QCoreApplication.sendPostedEvents(current,QEvent.Type.DeferredDelete)


def test_m_shortcut_adds_persistent_marker_and_selected_marker_can_be_removed(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Named timeline markers',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);reopened=None;window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            timeline=window.timeline_panel;timeline.parentWidget().setCurrentIndex(1)
            timeline.playhead_slider.setValue(12)
            before=window.session.revision
            timeline.preview_path.setFocus()
            from PySide6.QtTest import QTest
            from PySide6.QtCore import Qt,QCoreApplication,QEvent
            QTest.keyClick(timeline.preview_path,Qt.Key.Key_M)
            assert 'timeline_markers' not in window.session.project.plan.to_dict()
            assert window.session.revision==before
            timeline.preview_path.clear()
            timeline.clip_list.setFocus()
            QTest.keyClick(timeline.clip_list,Qt.Key.Key_M)
            assert window.session.revision==before+1
            markers=window.session.project.plan.to_dict()['timeline_markers']
            assert len(markers)==1 and markers[0]['frame']==12 and markers[0]['label']=='M1'
            assert timeline.marker_list.count()==1
            assert timeline.marker_count_label.text()=='1 marker'
            from PySide6.QtWidgets import QGraphicsTextItem
            assert any(isinstance(item,QGraphicsTextItem) and item.toPlainText()=='M1'
                       for item in timeline.scene.items())
            window.session.save()
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
            window=None

            reopened=MainWindow(store);reopened.show();reopened.open_project(path)
            reopened.navigation.setCurrentRow(3)
            restored=reopened.timeline_panel;restored.parentWidget().setCurrentIndex(1)
            assert restored.marker_list.count()==1
            assert restored.marker_list.item(0).text()=='M1 · frame 12'
            before_select=reopened.session.revision
            restored.marker_list.setCurrentRow(0)
            assert restored.playhead_slider.value()==12
            assert reopened.session.revision==before_select
            restored.remove_marker_button.click()
            assert 'timeline_markers' not in reopened.session.project.plan.to_dict()
            assert reopened.session.revision==before_select+1
            assert restored.marker_list.count()==0
            reopened.session.save()
        finally:
            for current in (reopened,window):
                if current is not None:
                    current.close()
                    wait_for(qt_app,lambda current=current:not current.background_busy and not current.isVisible())
                    current.deleteLater();QCoreApplication.sendPostedEvents(current,QEvent.Type.DeferredDelete)


def test_out_marker_requires_valid_in_and_strictly_later_frame(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Invalid range markers',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            timeline=window.timeline_panel
            timeline.set_out_marker()
            assert timeline._out_frame is None
            assert 'đặt điểm in trước' in timeline.action_message.text().lower()
            timeline.playhead_slider.setValue(20)
            timeline.set_in_marker()
            timeline.playhead_slider.setValue(19)
            timeline.set_out_marker()
            assert timeline._in_frame==20 and timeline._out_frame is None
            assert 'phải sau điểm In' in timeline.action_message.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_timeline_i_o_escape_shortcuts_persist_and_clear_range(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Timeline marker shortcuts',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    record=_record(tmp_path/'shortcut-marker.mp4',b'marker shortcut')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
            window.session.commit(addition.command);window._project_changed()
            window.navigation.setCurrentRow(3)
            timeline=window.timeline_panel;timeline.parentWidget().setCurrentIndex(1);timeline.clip_list.setFocus()
            before=window.session.revision
            timeline.playhead_slider.setValue(10)
            from PySide6.QtTest import QTest
            from PySide6.QtCore import Qt
            QTest.keyClick(timeline.clip_list,Qt.Key.Key_I)
            assert timeline._in_frame==10
            assert window.session.revision==before+1
            timeline.playhead_slider.setValue(20)
            QTest.keyClick(timeline.clip_list,Qt.Key.Key_O)
            assert timeline._out_frame==21
            assert window.session.revision==before+2
            QTest.keyClick(timeline.clip_list,Qt.Key.Key_Escape)
            assert timeline._in_frame is None and timeline._out_frame is None
            assert window.session.revision==before+3
            assert 'timeline_range' not in window.session.project.plan.to_dict()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_selected_timeline_marker_can_be_renamed_validated_and_undone(tmp_path,qt_app):
    from unittest.mock import patch
    from PySide6.QtWidgets import QGraphicsTextItem
    project=empty_project(NewProjectIntent('Rename timeline marker',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            timeline=window.timeline_panel;timeline.parentWidget().setCurrentIndex(1)
            timeline.playhead_slider.setValue(15)
            timeline.add_timeline_marker()
            marker_id=timeline.selected_marker_id
            assert marker_id is not None
            before=window.session.revision
            with patch('fonesi_edit.ui.timeline.QInputDialog.getText',return_value=('Opening',True)):
                timeline.rename_marker_button.click()
            assert window.session.revision==before+1
            marker=window.session.project.plan.to_dict()['timeline_markers'][0]
            assert marker['id']==marker_id and marker['label']=='Opening'
            assert timeline.marker_list.item(0).text()=='Opening · frame 15'
            assert any(isinstance(item,QGraphicsTextItem) and item.toPlainText()=='Opening'
                       for item in timeline.scene.items())
            # Invalid or duplicate names must not create history/revision entries.
            timeline.playhead_slider.setValue(20)
            timeline.add_timeline_marker()
            markers=window.session.project.plan.to_dict()['timeline_markers']
            duplicate_label=next(item['label'] for item in markers if item['id']!=marker_id)
            assert len(markers)==2
            selected_label=next(item['label'] for item in markers if item['id']==marker_id)
            assert duplicate_label.casefold()!=selected_label.casefold()
            assert any(item['id']!=marker_id and item['label'].casefold()==duplicate_label.casefold() for item in markers)
            timeline.selected_marker_id=marker_id
            assert timeline.selected_marker_id==marker_id
            before_invalid=window.session.revision
            for value in (duplicate_label,'  ','x'*65,'bad\nname'):
                with patch('fonesi_edit.ui.timeline.QInputDialog.getText',return_value=(value,True)):
                    timeline.rename_timeline_marker()
                assert window.session.revision==before_invalid
                current=next(item for item in window.session.project.plan.to_dict()['timeline_markers'] if item['id']==marker_id)
                assert current['label']=='Opening'
            with patch('fonesi_edit.ui.timeline.QInputDialog.getText',return_value=('',False)):
                timeline.rename_timeline_marker()
            assert window.session.revision==before_invalid
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_timeline_marker_rename_is_persisted_and_shared_undo_redo(tmp_path,qt_app):
    from unittest.mock import patch
    project=empty_project(NewProjectIntent('Rename marker history',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            timeline=window.timeline_panel;timeline.parentWidget().setCurrentIndex(1)
            timeline.playhead_slider.setValue(7);timeline.add_timeline_marker()
            before=window.session.revision
            with patch('fonesi_edit.ui.timeline.QInputDialog.getText',return_value=('Intro',True)):
                timeline.rename_timeline_marker()
            assert window.session.revision==before+1
            assert window.session.project.plan.to_dict()['timeline_markers'][0]['label']=='Intro'
            assert window.project_history.can_undo()
            assert window.project_history.undo()
            assert window.session.project.plan.to_dict()['timeline_markers'][0]['label']=='M1'
            assert window.project_history.redo()
            assert window.session.project.plan.to_dict()['timeline_markers'][0]['label']=='Intro'
            window.session.save()
            from fonesi_edit.storage.projects import load_project_file
            saved,_=load_project_file(path)
            assert saved.plan.to_dict()['timeline_markers'][0]['label']=='Intro'
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_timeline_loop_playback_wraps_half_open_in_out_range_and_stops_cleanly(tmp_path,qt_app):
    from PySide6.QtTest import QTest
    project=empty_project(NewProjectIntent('Timeline loop range',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.navigation.setCurrentRow(3)
            timeline=window.timeline_panel;timeline.parentWidget().setCurrentIndex(1)
            timeline._frame_total=300
            timeline.playhead_slider.setRange(0,299)
            timeline._commit_range_markers(10,13)
            timeline.update_project()
            timeline.playhead_slider.setValue(13)
            assert timeline.loop_button.isEnabled()
            timeline.loop_button.click()
            assert timeline.loop_button.text()=='Dừng vòng lặp'
            assert timeline.playhead_slider.value()==10
            QTest.qWait(120)
            assert 10<=timeline.playhead_slider.value()<13
            assert timeline.loop_button.text()=='Dừng vòng lặp'
            timeline.loop_button.click()
            assert not timeline._loop_timer.isActive()
            assert timeline.loop_button.text()=='Lặp vùng'
            # Without an In/Out pair, loop the complete output frame range.
            timeline._commit_range_markers(None,None)
            timeline.update_project()
            timeline.playhead_slider.setValue(299)
            timeline.loop_button.click()
            QTest.qWait(80)
            assert 0<=timeline.playhead_slider.value()<300
            timeline.request_stop()
            assert not timeline._loop_timer.isActive()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_move_selected_video_clip_to_playhead_keeps_original_audio_and_shared_undo_redo(tmp_path,qt_app):
    project=empty_project(NewProjectIntent('Timeline move',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    record=_record(tmp_path/'move.mp4')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
            window.session.commit(addition.command);window._project_changed()
            timeline=window.timeline_panel
            timeline.clip_list.setCurrentRow(0)
            timeline.playhead_slider.setValue(90)
            assert timeline.move_button.isEnabled()
            before=window.session.revision
            timeline.move_button.click()
            assert window.session.revision==before+1
            data=window.session.project.plan.to_dict()
            video=next(item for item in data['clips'] if item['id']==addition.clip_id)
            audio=next(item for item in data['audio']['clips'] if item['asset_id']==addition.asset_id)
            assert video['output_start']==[3,1]
            assert audio['output_start']==[3,1]
            assert window.project_history.can_undo()
            assert window.project_history.undo()
            data=window.session.project.plan.to_dict()
            assert next(item for item in data['clips'] if item['id']==addition.clip_id)['output_start']==[0,1]
            assert window.project_history.redo()
            data=window.session.project.plan.to_dict()
            assert next(item for item in data['audio']['clips'] if item['asset_id']==addition.asset_id)['output_start']==[3,1]
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


@pytest.mark.parametrize('ripple,expected_start',[(False,[1,1]),(True,[0,1])])
def test_timeline_delete_button_distinguishes_gap_and_ripple_without_deleting_source(tmp_path,qt_app,ripple,expected_start):
    project=empty_project(NewProjectIntent('Timeline delete',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    first_path=tmp_path/'first-delete.mp4';first_path.write_bytes(b'first-delete-source')
    second_path=tmp_path/'second-delete.mp4';second_path.write_bytes(b'second-delete-source')
    first=_record(first_path,b'first-delete-source')
    second=_record(second_path,b'second-delete-source')
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            one=add_video_clip(window.session.project,first,_scan(first),expected_revision=window.session.revision)
            window.session.commit(one.command)
            two=add_video_clip(window.session.project,second,_scan(second),expected_revision=window.session.revision)
            window.session.commit(two.command);window._project_changed()
            timeline=window.timeline_panel
            timeline.clip_list.setCurrentRow(0)
            timeline.ripple.setChecked(ripple)
            assert timeline.delete_clip_button.isEnabled()
            before=window.session.revision
            timeline.delete_clip_button.click()
            assert window.session.revision==before+1
            data=window.session.project.plan.to_dict()
            assert [item['id'] for item in data['clips']]==[two.clip_id]
            assert data['clips'][0]['output_start']==expected_start
            assert len(data['audio']['clips'])==1
            assert Path(first.path_ref.path).exists() and Path(first.path_ref.path).read_bytes()==b'first-delete-source'
            assert Path(second.path_ref.path).exists() and Path(second.path_ref.path).read_bytes()==b'second-delete-source'
            assert 'không bị xóa' in timeline.action_message.text()
            assert window.project_history.can_undo()
            assert window.project_history.undo()
            assert len(window.session.project.plan.to_dict()['clips'])==2
            assert Path(first.path_ref.path).exists()
            assert window.project_history.redo()
            assert len(window.session.project.plan.to_dict()['clips'])==1
            assert first.path.exists()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
