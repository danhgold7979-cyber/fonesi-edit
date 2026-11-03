"""Timeline playhead uses integer output frames and commits split commands once."""
import os
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
            window.deleteLater()


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
            window.deleteLater()

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
            window.deleteLater()

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
            window.deleteLater()
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
                    current.deleteLater()


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
            window.deleteLater()


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
            window.deleteLater()
