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
