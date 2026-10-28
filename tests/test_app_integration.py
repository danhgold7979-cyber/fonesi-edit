import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import time
from PySide6.QtWidgets import QApplication
from fonesi_edit.app import MainWindow
from fonesi_edit.domain import Composition,Clip,Layer
from fonesi_edit.prototypes.media import create_fixture,probe

APP=QApplication.instance() or QApplication([])


def wait_until(condition,seconds=20):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        APP.processEvents()
        if condition():return
        time.sleep(.02)
    raise AssertionError('Timed out waiting for application state')


def close(window):
    window.force_close=True;window.close()
    wait_until(lambda:not window.tasks and not window.scheduler.active)
    APP.processEvents()


def test_app_project_queue_worker_output_and_reopen(tmp_path):
    fixture=create_fixture(tmp_path/'media',duration=.5)
    window=MainWindow(tmp_path/'state')
    assert window.nav.count()==8
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(fixture['source']),end=.5)],layers=[Layer(text='App thật',style={'font_size':18})])
    window.editor.set_composition(c);window.autosave();project=window.project_id
    output=tmp_path/'actual.mp4';job=window.store.submit('render',{'composition':c.to_dict(),'output':str(output)})
    wait_until(lambda:window.store.job(job)['state'] in {'succeeded','failed'})
    assert window.store.job(job)['state']=='succeeded',window.store.job(job)['error']
    assert probe(output).width==320
    close(window)
    restored=MainWindow(tmp_path/'state')
    assert restored.project_id==project and restored.editor.composition.layers[0].text=='App thật'
    assert restored.store.job(job)['result']['validated']
    close(restored)


def test_menu_shortcut_callback_does_not_receive_checked_as_function(tmp_path):
    window=MainWindow(tmp_path/'state');window.show();window.nav.setCurrentWidget(window.editor)
    window.editor.add_layer('text');window.editor.canvas.setFocus();APP.processEvents()
    assert len(window.editor.composition.layers)==1
    window.actions['Undo'].trigger();assert len(window.editor.composition.layers)==0
    window.actions['Redo'].trigger();assert len(window.editor.composition.layers)==1
    assert not window.failures
    close(window)


def test_subtitle_draft_keeps_unsaved_raw_edits_and_restores(tmp_path):
    from fonesi_edit.subtitles import Caption
    window=MainWindow(tmp_path/'state');window.subtitles.captions=[Caption(0,500,'Nội dung')];window.subtitles.refresh()
    window.subtitles.table.item(0,0).setText('0.125');window.subtitles.table.item(0,3).setText('Đang sửa, chưa xuất');window.subtitles.persist();close(window)
    reopened=MainWindow(tmp_path/'state')
    assert reopened.subtitles.table.item(0,0).text()=='0.125' and reopened.subtitles.collect()[0].text=='Đang sửa, chưa xuất'
    close(reopened)


def test_refresh_accounts_keeps_the_selected_chrome_profile(tmp_path):
    from fonesi_edit.browser import create_profile,rename_profile
    window=MainWindow(tmp_path/'state');create_profile(window.store,'A');second=create_profile(window.store,'B')
    window.settings.refresh_profiles();window.settings.profile.setCurrentIndex(window.settings.profile.findData(second));window.settings.refresh_profiles()
    assert window.settings.current_profile()==second
    rename_profile(window.store,second,'B renamed');window.settings.refresh_profiles();assert window.settings.profile.currentText()=='B renamed'
    close(window)


def test_attach_bilingual_creates_independent_draggable_tracks(tmp_path):
    from fonesi_edit.subtitles import Caption,read_captions
    f=create_fixture(tmp_path/'media',duration=.5);window=MainWindow(tmp_path/'state')
    window.editor.set_composition(Composition(clips=[Clip(str(f['source']),end=.5)]))
    window.subtitles.captions=[Caption(0,400,'Bản dịch','Original')];window.subtitles.refresh();window.subtitles.bilingual.setChecked(True);window.subtitles.attach()
    roles={layer.style['subtitle_role']:layer for layer in window.editor.composition.layers}
    assert read_captions(Path(roles['source'].path))[0].text=='Original'
    assert read_captions(Path(roles['target'].path))[0].text=='Bản dịch' and roles['source'].y!=roles['target'].y
    window.editor.undo.undo();assert not window.editor.composition.layers
    close(window)


def test_undo_while_editing_text_uses_the_input_history(tmp_path):
    window=MainWindow(tmp_path/'state');window.show();window.nav.setCurrentWidget(window.editor);window.editor.add_layer('text')
    try:
        window.editor.inspector.setCurrentIndex(1);window.activateWindow();field=window.editor.fields['text'][0];field.setText('Gốc');field.setFocus();APP.processEvents()
        assert QApplication.focusWidget() is field
        field.insert(' mới');window.actions['Undo'].trigger()
        assert field.text()=='Gốc' and len(window.editor.composition.layers)==1
    finally:close(window)


def test_scan_selection_tree_enqueues_only_checked_items_and_survives_reopen(tmp_path):
    from PySide6.QtCore import Qt
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True  # Do not send synthetic example.test jobs to network.
    try:
        payload={'url':'https://example.test/channel','folder':str(tmp_path/'downloads'),
                 'engine':'gallery','media':'images','limit':0,'subtitles':False}
        scan_id=window.store.submit('scan',payload)
        window.store.claim(allowed={'scan'})
        result={'platform':'Generic','complete':None,'items':[
            {'id':'image-A','kind':'images','title':'Ảnh A',
             'url':'https://example.test/media/a.png','selectable':True},
            {'id':'image-B','kind':'images','title':'Ảnh có URL ký',
             'url':None,'selectable':False,'reason':'URL tạm không thể tải lại'},
            {'id':'image-C','kind':'images','title':'Ảnh C',
             'url':'https://example.test/media/c.png','selectable':True},
        ],'count':3}
        window.store.finish(scan_id,result)
        window.downloads.show_scan()
        tree=window.downloads.scan_tree
        root=tree.topLevelItem(0)
        assert root.childCount()==3
        assert 'chưa rõ' in window.downloads.scan_note.text()
        assert not (root.child(1).flags() & Qt.ItemFlag.ItemIsEnabled)
        assert not (root.child(1).flags() & Qt.ItemFlag.ItemIsUserCheckable)
        window.downloads.check_scan_items(True)
        assert root.child(0).checkState(0)==Qt.CheckState.Checked
        assert root.child(2).checkState(0)==Qt.CheckState.Checked
        assert root.child(1).checkState(0)!=Qt.CheckState.Checked
        root.child(0).setCheckState(0,Qt.CheckState.Unchecked)
        window.downloads.download_selected()
        window.downloads.download_selected()  # same scan row must not enqueue twice
        requests=[job for job in window.store.jobs() if job['kind']=='download']
        assert len(requests)==1
        assert requests[0]['payload']['url']=='https://example.test/media/c.png'
        assert requests[0]['payload']['engine']=='gallery'
        assert requests[0]['payload']['folder']==payload['folder']
        assert requests[0]['payload']['limit']==1
        assert window.store.job(scan_id)['result']==result
    finally:
        close(window)

    reopened=MainWindow(tmp_path/'state')
    reopened.scheduler.paused=True
    try:
        reopened.downloads.show_scan()
        assert reopened.downloads.scan_tree.topLevelItem(0).childCount()==3
        assert reopened.downloads.scans.currentData()==scan_id
    finally:
        close(reopened)
