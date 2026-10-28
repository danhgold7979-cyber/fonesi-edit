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


def test_scan_selection_never_switches_a_stale_account_to_public(tmp_path):
    import pytest
    from fonesi_edit.browser import create_profile,bind
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        profile=create_profile(window.store,'Personal Facebook')
        facebook_binding=bind(window.store,profile,'Facebook')
        payload={'url':'https://example.test/channel',
                 'account_ref':facebook_binding,'expected_identity':'user-A'}
        scan_id=window.store.submit('scan',payload)
        window.store.claim(allowed={'scan'})
        window.store.finish(scan_id,{'platform':'Generic','items':[{
            'id':'item','kind':'video','url':'https://example.test/clip.mp4',
            'selectable':True}],'complete':None})
        window.downloads.show_scan()
        window.downloads.check_scan_items(True)
        with pytest.raises(PermissionError,match='khác nền tảng'):
            window.downloads.download_selected()
        assert not any(job['kind']=='download' for job in window.store.jobs())
    finally:
        close(window)


def test_paginated_scan_preserves_checkbox_selection_across_pages(tmp_path):
    from PySide6.QtCore import Qt
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        payload={'url':'https://example.test/gallery',
                 'folder':str(tmp_path/'output'),'engine':'gallery','media':'images'}
        scan_id=window.store.submit('scan',payload)
        window.store.claim(allowed={'scan'})
        urls=['https://example.test/media/a.png',
              'https://example.test/media/b.png',
              'https://example.test/media/c.png',
              'https://example.test/media/a.png',  # duplicate on second page
              'https://example.test/media/e.png']
        items=[{'id':str(i),'title':'Image '+str(i),'kind':'images',
                'engine':'gallery','url':url,'selectable':True}
               for i,url in enumerate(urls)]
        window.store.finish(scan_id,{'platform':'Generic','items':items,
                                     'count':len(items),'complete':None})
        downloads=window.downloads
        downloads.scan_page_size=2
        downloads.show_scan()
        first=downloads.scan_tree.topLevelItem(0)
        assert first.childCount()==2
        first.child(0).setCheckState(0,Qt.CheckState.Checked)
        downloads.change_scan_page(1)
        second=downloads.scan_tree.topLevelItem(0)
        assert second.childCount()==2
        assert not (second.child(1).flags() & Qt.ItemFlag.ItemIsUserCheckable)
        second.child(0).setCheckState(0,Qt.CheckState.Checked)
        downloads.change_scan_page(1)
        last=downloads.scan_tree.topLevelItem(0)
        assert last.childCount()==1
        last.child(0).setCheckState(0,Qt.CheckState.Checked)
        downloads.change_scan_page(-2)
        assert downloads.scan_tree.topLevelItem(0).child(0).checkState(0)==Qt.CheckState.Checked
        assert len(downloads.scan_selected[scan_id])==3
        assert 'đã chọn 3' in downloads.scan_note.text()
        downloads.download_selected()
        jobs=[job for job in window.store.jobs() if job['kind']=='download']
        assert len(jobs)==3
        assert {job['payload']['url'] for job in jobs}=={urls[0],urls[2],urls[4]}
    finally:
        close(window)


def test_batch_ui_exposes_separate_audio_mapping_modes(tmp_path):
    window=MainWindow(tmp_path/'state')
    try:
        choices={window.batch.audio_mode.itemData(i) for i in range(window.batch.audio_mode.count())}
        assert choices=={'shared','by_name','ordered','random'}
        assert window.batch.audio_mode.currentData()=='shared'
        window.batch.audio_mode.setCurrentIndex(window.batch.audio_mode.findData('random'))
        assert window.batch.audio_mode.currentData()=='random'
        assert window.batch.audio_folder is not window.batch.audio
    finally:
        close(window)


def test_matrix_selected_row_regeneration_preserves_other_rows_and_locked_cells(tmp_path):
    from fonesi_edit.matrix import Angle,generate,matrix_rows_valid,combination
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        scene_angles=[[Angle(i+1,j+1,f'/fixture/{i}/{j}.mp4',f'fixture-{i}-{j}')
                       for j in range(4)] for i in range(2)]
        rows=generate(scene_angles,4,seed=8,window=1,different=2)['rows']
        page=window.matrix
        page.window.setValue(1);page.different.setValue(2);page.seed.setValue(11)
        page.old_history=[]
        page.model.replace(scene_angles,rows)
        page.model.locked.add((1,1))  # GUI columns are 1-based scene indices.
        page.table.setCurrentIndex(page.model.index(1,2))
        unchanged=[combination(row) for row in page.model.rows]
        pinned=page.model.rows[1][0].hash
        page.regenerate()
        wait_until(lambda: combination(page.model.rows[1])!=unchanged[1] or
                   not window.tasks,seconds=12)
        assert combination(page.model.rows[1])!=unchanged[1], window.failures
        assert page.model.rows[1][0].hash==pinned
        assert [combination(row) for i,row in enumerate(page.model.rows) if i!=1] == \
            [value for i,value in enumerate(unchanged) if i!=1]
        assert (1,1) in page.model.locked
        assert matrix_rows_valid(page.model.rows,[],window=1,different=2)
        assert 'Đã tạo lại hàng' in page.summary.text()
    finally:
        close(window)


def test_matrix_regeneration_does_not_overwrite_edits_done_while_worker_runs(tmp_path,monkeypatch):
    from threading import Event
    import fonesi_edit.ui.pages as page_module
    from fonesi_edit.matrix import Angle,generate,combination
    started=Event();proceed=Event()
    actual=page_module.regenerate_row
    def gated(*args,**kwargs):
        started.set()
        assert proceed.wait(8)
        return actual(*args,**kwargs)
    monkeypatch.setattr(page_module,'regenerate_row',gated)
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        scenes=[[Angle(i+1,j+1,f'/fixture/{i}/{j}.mp4',f'key-{i}-{j}')
                 for j in range(4)] for i in range(2)]
        rows=generate(scenes,3,seed=8,window=1,different=2)['rows']
        page=window.matrix
        page.window.setValue(1);page.different.setValue(2);page.seed.setValue(9)
        page.model.replace(scenes,rows)
        page.table.setCurrentIndex(page.model.index(1,1))
        page.regenerate()
        wait_until(started.is_set,seconds=5)
        page.seed.setValue(10)  # User changed options before worker finished.
        original=combination(page.model.rows[1])
        proceed.set()
        wait_until(lambda:not window.tasks,seconds=15)
        APP.processEvents()
        assert combination(page.model.rows[1])==original
        assert 'kết quả cũ bị bỏ' in page.host.status.text()
    finally:
        proceed.set()
        close(window)



def test_matrix_ui_angle_usage_summary_labels_planned_not_rendered(tmp_path):
    from fonesi_edit.matrix import Angle
    window=MainWindow(tmp_path/'state')
    try:
        source=[[Angle(1,1,'/fake/1.mp4','s1'),Angle(1,2,'/fake/2.mp4','s2')],
                [Angle(2,1,'/fake/3.mp4','s3')]]
        window.matrix.model.replace(source,[[source[0][0],source[1][0]]])
        groups=window.matrix.statistics()
        assert [item['uses'] for item in groups[0]]==[1,0]
        assert [item['uses'] for item in groups[1]]==[1]
        assert 'không phải số video đã render' in window.matrix.summary.text()
        assert 'C1: G1=1' in window.matrix.summary.text()
    finally:
        close(window)



def test_matrix_edit_updates_formula_and_non_angle_columns_cannot_be_locked(tmp_path):
    from PySide6.QtCore import Qt
    from fonesi_edit.matrix import Angle
    window=MainWindow(tmp_path/'state')
    try:
        scene=[[Angle(1,1,'/fake/a.mp4','a'),Angle(1,2,'/fake/b.mp4','b')],
               [Angle(2,1,'/fake/c.mp4','c')]]
        page=window.matrix
        page.model.replace(scene,[[scene[0][0],scene[1][0]]])
        formula=page.model.index(0,len(scene)+1)
        assert page.model.data(formula)=='C1G1+C2G1'
        updates=[]
        page.model.dataChanged.connect(lambda start,end: updates.append(
            (start.column(),end.column())))
        assert page.model.setData(page.model.index(0,1),'G2')
        assert page.model.data(formula)=='C1G2+C2G1'
        assert updates==[(1,len(scene)+1)]
        assert not page.model.setData(formula,'G1')
        page.model.locked.add((0,1))
        assert not page.model.setData(page.model.index(0,1),'G1')
        assert page.model.data(formula)=='C1G2+C2G1'
        page.model.locked.clear()
        page.table.setCurrentIndex(formula)
        page.lock()
        assert not page.model.locked
    finally:
        close(window)


def test_matrix_weights_ui_validates_all_scenes_without_silent_fallback(tmp_path):
    from fonesi_edit.matrix import Angle
    import pytest
    window=MainWindow(tmp_path/'state')
    try:
        page=window.matrix
        groups=[[Angle(1,1,'/mock/a','A')],[Angle(2,1,'/mock/b','B')]]
        page.model.replace(groups,[[groups[0][0],groups[1][0]]])
        assert 'weights' in [page.allocation.itemText(i)
            for i in range(page.allocation.count())]
        page.allocation.setCurrentText('weights')
        page.scene_weights.setText('1,3')
        assert page.duration_weights()==[1,3]
        page.scene_weights.setText('1')
        with pytest.raises(ValueError,match='Số trọng số'):
            page.duration_weights()
        for invalid in ('1,0','1,-2','1,nan','1,inf','1,bad'):
            page.scene_weights.setText(invalid)
            with pytest.raises(ValueError):
                page.duration_weights()
        page.allocation.setCurrentText('equal')
        assert page.duration_weights() is None
    finally:
        close(window)


def test_matrix_manual_durations_ui_rejects_missing_and_nonnumeric_values(tmp_path):
    from fonesi_edit.matrix import Angle
    import pytest
    window=MainWindow(tmp_path/'state')
    try:
        page=window.matrix
        scenes=[[Angle(1,1,'a','a')],[Angle(2,1,'b','b')]]
        page.model.replace(scenes,[[scenes[0][0],scenes[1][0]]])
        assert page.minimum.value()==.5 and page.maximum.value()==2
        page.minimum.setValue(.1);page.maximum.setValue(10)
        assert page.minimum.value()==.1 and page.maximum.value()==10
        page.allocation.setCurrentText('manual')
        page.scene_durations.setText('0.25,0.75')
        assert page.duration_scene_lengths()==[.25,.75]
        for value in ('', '1', '1,0', '-1,2', 'nan,2', '1,inf', 'one,two'):
            page.scene_durations.setText(value)
            with pytest.raises(ValueError):
                page.duration_scene_lengths()
        page.allocation.setCurrentText('proportional')
        assert page.duration_scene_lengths() is None
    finally:
        close(window)


def test_proxy_preview_quality_is_source_only_and_runs_in_background(tmp_path):
    from fonesi_edit.proxy import proxy_identity
    files=create_fixture(tmp_path/'media',duration=.5)
    source=files['source'];original_stamp=source.stat().st_mtime_ns
    window=MainWindow(tmp_path/'state')
    try:
        comp=Composition(width=320,height=180,clips=[
            Clip(str(source),end=.5,source_duration=.5)])
        window.editor.set_composition(comp)
        assert window.editor.proxy_actions['off'].isChecked()
        window.editor.proxy_actions['fast'].trigger()
        assert window.editor.composition.adjustments['playback_proxy_quality']=='fast'
        try:
            wait_until(lambda:proxy_identity(source,'fast') in window.editor.proxy_cache,
                       seconds=12)
        except AssertionError:
            raise AssertionError(
                f"Proxy UI: clip_row={window.editor.clips.currentRow()}, "
                f"loading={window.editor._loading}, "
                f"quality={window.editor.composition.adjustments.get('playback_proxy_quality')}, "
                f"pending={window.editor._proxy_pending}, "
                f"failed={window.editor._proxy_failed}, "
                f"tasks={[task.isRunning() for task in window.tasks]}, "
                f"status={window.status.text()}, app_errors={window.failures}"
            ) from None
        expected=window.editor.proxy_cache[proxy_identity(source,'fast')]['path']
        wait_until(lambda:window.editor.player.source().toLocalFile()==expected,
                   seconds=10)
        assert Path(expected).is_file()
        assert probe(Path(expected)).duration>.4
        assert source.stat().st_mtime_ns==original_stamp
        assert window.editor.preview_fingerprint is None
        window.editor.proxy_actions['off'].trigger()
        assert window.editor.player.source().toLocalFile()==str(source.resolve())
    finally:
        close(window)


def test_proxy_cache_quota_persisted_and_swept_in_background(tmp_path,monkeypatch):
    from PySide6.QtCore import QUrl
    import fonesi_edit.app as app_module
    calls=[]
    def fake_cleanup(root,maximum,protected):
        calls.append((Path(root),maximum,list(protected)))
        return {'scanned_bytes':0,'remaining_bytes':0,'deleted_bytes':0,
                'deleted':[],'over_budget':False}
    monkeypatch.setattr(app_module,'evict_proxy_cache',fake_cleanup)
    window=MainWindow(tmp_path/'state')
    try:
        window.settings.cache_budget_mb.setValue(128)
        window.settings.save_resources()
        assert window.store.setting('proxy_cache_limit_mb')==128
        active=tmp_path/'current-proxy.mp4'
        active.write_bytes(b'not real, used only to verify protection')
        window.editor.player.setSource(QUrl.fromLocalFile(str(active)))
        window.cleanup_cache(force=True)
        wait_until(lambda:not window._cache_cleanup_busy and bool(calls),seconds=10)
        assert calls[0][0]==window.data/'cache'/'proxies'
        assert calls[0][1]==128*1024**2
        assert any(Path(protected).resolve()==active.resolve() for protected in calls[0][2])
    finally:
        close(window)
    reopened=MainWindow(tmp_path/'state')
    try:
        assert reopened.settings.cache_budget_mb.value()==128
    finally:
        close(reopened)
