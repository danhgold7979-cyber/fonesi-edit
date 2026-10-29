import os
import json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import time
from PySide6.QtWidgets import QApplication, QPushButton
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


def test_editor_shortcuts_yield_to_focused_spinbox(tmp_path, monkeypatch):
    window=MainWindow(tmp_path/'state');window.show();window.nav.setCurrentWidget(window.editor)
    calls=[]
    monkeypatch.setattr(window, 'guard', lambda callback: lambda: calls.append(callback))
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        window.editor.add_layer('text')  # Inspector fields are disabled until a layer is selected.
        spin=window.editor.fields['x'][0]
        window.activateWindow();APP.processEvents()
        QTest.mouseClick(spin.lineEdit(), Qt.MouseButton.LeftButton)
        APP.processEvents()
        focused=QApplication.focusWidget()
        from fonesi_edit.app import shortcut_focus_policy
        policy, target = shortcut_focus_policy(focused)
        # Qt may report the composite spin box or its embedded line edit
        # depending on platform/style; both must resolve to the same control.
        assert policy == 'control'
        assert target is spin
        window.actions['Phát/dừng'].trigger()
        window.actions['Marker'].trigger()
        window.actions['Thêm video'].trigger()
        assert calls == []
    finally:
        close(window)


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
        wait_until(lambda:Path(window.editor.player.source().toLocalFile()).resolve()==Path(expected).resolve(),
                   seconds=10)
        assert Path(expected).is_file()
        assert probe(Path(expected)).duration>.4
        assert source.stat().st_mtime_ns==original_stamp
        assert window.editor.preview_fingerprint is None
        window.editor.proxy_actions['off'].trigger()
        assert Path(window.editor.player.source().toLocalFile()).resolve()==source.resolve()
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



def test_audio_dialog_sfx_anchor_round_trip_and_input_validation(tmp_path,monkeypatch):
    from fonesi_edit.ui.dialogs import AudioDialog
    from PySide6.QtWidgets import QMessageBox
    from fonesi_edit.domain import Composition,Clip
    media=create_fixture(tmp_path/'media',duration=1)
    window=MainWindow(tmp_path/'state')
    try:
        path=str(media['source'])
        window.editor.set_composition(Composition(width=320,height=180,fps=25,
            clips=[Clip(path,end=1)],audio=[
                {'path':path,'mode':'sfx','volume':.8,
                 'placement':'percent','position_pct':65,'offset':.1}]))
        dialog=AudioDialog(window.editor)
        assert dialog.table.columnCount()==17
        assert dialog.table.cellWidget(0,11).currentData()=='percent'
        assert dialog.table.item(0,12).text()=='65'
        dialog.table.cellWidget(0,11).setCurrentIndex(
            dialog.table.cellWidget(0,11).findData('scene_start'))
        dialog.table.item(0,13).setText('1')
        dialog.apply()
        saved=window.editor.composition.audio[0]
        assert saved['placement']=='scene_start'
        assert saved['scene_index']==1 and saved['offset']==.1
        assert 'position_pct' not in saved
        reopened=AudioDialog(window.editor)
        assert reopened.table.cellWidget(0,11).currentData()=='scene_start'
        assert reopened.table.item(0,13).text()=='1'
        warnings=[]
        monkeypatch.setattr(QMessageBox,'warning',
            lambda *args: warnings.append(args[2]) if len(args)>2 else None)
        reopened.table.item(0,13).setText('2')  # One scene only.
        reopened.apply()
        assert warnings and 'scene index' in warnings[-1]
        assert window.editor.composition.audio[0]['scene_index']==1
    finally:
        close(window)


def test_audio_dialog_non_sfx_track_cannot_apply_relative_anchor(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from fonesi_edit.ui.dialogs import AudioDialog
    f=create_fixture(tmp_path/'media',duration=.5)
    window=MainWindow(tmp_path/'state')
    try:
        source=str(f['source'])
        window.editor.set_composition(Composition(width=320,height=180,
            clips=[Clip(source,end=.5)],audio=[
                {'path':source,'mode':'music','volume':.2}]))
        dialog=AudioDialog(window.editor)
        combo=dialog.table.cellWidget(0,11)
        combo.setCurrentIndex(combo.findData('video_end'))
        messages=[]
        monkeypatch.setattr(QMessageBox,'warning',lambda *args:messages.append(args[2]))
        dialog.apply()
        assert messages and 'chỉ dùng cho SFX' in messages[-1]
        assert window.editor.composition.audio[0].get('placement') is None
    finally:
        close(window)



def test_batch_search_format_and_visible_only_selection_keep_hidden_choices(tmp_path):
    from PySide6.QtCore import Qt
    window=MainWindow(tmp_path/'state')
    try:
        page=window.batch
        group_a=str(tmp_path/'a-channel')
        group_b=str(tmp_path/'b-channel')
        first=str(tmp_path/'a-channel'/'first.mp4')
        second=str(tmp_path/'a-channel'/'second.mkv')
        third=str(tmp_path/'b-channel'/'third.mp4')
        page.scanned({group_a:[first,second],group_b:[third]})
        assert len(page.selected()[group_a])==2
        assert len(page.selected()[group_b])==1
        page.plans=[{'output':'stale'}]
        page.search.setText('second')
        assert page.tree.topLevelItem(0).child(0).isHidden()
        assert not page.tree.topLevelItem(0).child(1).isHidden()
        assert page.tree.topLevelItem(1).isHidden()
        assert len(page.plans)==1  # Filtering alone must not change the plan.
        page.check_visible('none')
        assert page.plans==[]  # Checkbox changes invalidate the old plan.
        chosen=page.selected()
        assert chosen[group_a]==[first] and chosen[group_b]==[third]
        page.search.clear()
        page.format_filter.setCurrentIndex(page.format_filter.findData('.mp4'))
        assert not page.tree.topLevelItem(0).child(0).isHidden()
        assert page.tree.topLevelItem(0).child(1).isHidden()
        page.check_visible('invert')
        assert page.selected()=={}  # Only the two visible .mp4 files were toggled.
        page.format_filter.setCurrentIndex(0)
        page.check_visible('all')
        assert set(page.selected()[group_a])=={first,second}
        assert page.selected()[group_b]==[third]
        page.plans=[{'output':'stale-again'}]
        page.scanned({group_b:[third]})
        assert page.plans==[] and page.tree.topLevelItemCount()==1
        assert '1/1 video' in page.summary.text()
    finally:
        close(window)



def test_batch_dry_run_is_invalidated_by_settings_and_async_stale_result(tmp_path,monkeypatch):
    window=MainWindow(tmp_path/'state')
    try:
        page=window.batch
        group=str(tmp_path/'channel')
        page.scanned({group:[str(tmp_path/'channel'/'video.mp4')]})
        page.plans=[{'output':'old-plan'}]
        page.policy.setCurrentText('trim')
        assert not page.plans
        captured={}
        def background(function,done):
            captured['function']=function
            captured['done']=done
        monkeypatch.setattr(window,'background',background)
        page.plan()
        assert captured['function'] and not page.plans
        page.audio_mode.setCurrentIndex(page.audio_mode.findData('random'))
        captured['done']([{'output':'obsolete-output'}])
        assert page.plans==[]
        assert 'Đã bỏ bản dry-run cũ' in window.status.text()
        page.plans=[{'output':'editor-preset-snapshot'}]
        window.editor.changed.emit()
        assert not page.plans
    finally:
        close(window)



def test_batch_page_multiple_roots_scan_all_selected_without_duplicate_files(tmp_path,monkeypatch):
    from threading import Event
    window=MainWindow(tmp_path/'state')
    try:
        root_a=tmp_path/'Channel A'
        root_b=tmp_path/'Channel B'
        for root,name in [(root_a,'one.mp4'),(root_b,'two.mp4')]:
            target=root/'videos'/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(b'mock-input')
        page=window.batch
        page.folder.setText(str(root_a))
        page.extra_roots.setPlainText(str(root_b)+'\n'+str(root_a))
        tasks={}
        monkeypatch.setattr(window,'background',
            lambda work,done:tasks.update(work=work,done=done))
        page.scan()
        groups=tasks['work'](lambda progress:None,Event())
        tasks['done'](groups)
        selected=page.selected()
        assert len(selected)==2
        assert sum(len(paths) for paths in selected.values())==2
        page.plans=[{'output':'stale'}]
        page.extra_roots.setPlainText(str(root_a))
        assert not page.plans
        page.scan()  # Another scan is pending; never leave stale sources ready.
        assert page.selected()=={}
        assert page.tree.topLevelItemCount()==0
    finally:
        close(window)



def test_batch_async_scan_rejects_stale_results_when_source_roots_change(tmp_path,monkeypatch):
    from threading import Event
    window=MainWindow(tmp_path/'state')
    try:
        first=tmp_path/'first'
        second=tmp_path/'second'
        for root in (first,second):
            (root/'videos').mkdir(parents=True)
            (root/'videos'/'clip.mp4').write_bytes(b'placeholder')
        page=window.batch
        pending=[]
        monkeypatch.setattr(window,'background',
            lambda work,done:pending.append((work,done)))
        page.folder.setText(str(first))
        page.scan()
        assert len(pending)==1
        page.extra_roots.setPlainText(str(second))
        assert page.selected()=={}
        page.scan()
        assert len(pending)==2
        pending[0][1]({str(first):[str(first/'videos'/'clip.mp4')]})
        assert page.selected()=={}
        assert 'Bỏ kết quả quét cũ' in window.status.text()
        pending[1][1](pending[1][0](lambda _:None,Event()))
        assert sum(len(paths) for paths in page.selected().values())==2
    finally:
        close(window)



def test_batch_metadata_filter_is_async_orientation_aware_and_preserves_hidden_selection(tmp_path,monkeypatch):
    import pytest
    window=MainWindow(tmp_path/'state')
    try:
        page=window.batch
        channel=str(tmp_path/'channel')
        short=str(tmp_path/'short.mp4')
        wide=str(tmp_path/'wide.mkv')
        portrait=str(tmp_path/'portrait.mp4')
        unreadable=str(tmp_path/'damaged.mp4')
        page.scanned({channel:[short,wide,portrait,unreadable]})
        pending=[]
        monkeypatch.setattr(window,'background',
            lambda work,done:pending.append((work,done)))
        page.duration_min.setValue(1)
        assert len(pending)==1 and page.media_metadata is None
        assert sum(len(v) for v in page.selected().values())==4
        assert 'CHƯA áp dụng' in page.summary.text()
        with pytest.raises(ValueError,match='chưa áp dụng'):
            page.plan()
        pending[0][1]({'media':{
            short:{'duration':.5,'width':1920,'height':1080},
            wide:{'duration':5,'width':1280,'height':720},
            portrait:{'duration':3,'width':1080,'height':1920}},
            'errors':{unreadable:'MediaError'},'cancelled':False})
        assert page.media_metadata is not None
        assert page.tree.topLevelItem(0).child(0).isHidden()
        assert not page.tree.topLevelItem(0).child(1).isHidden()
        assert not page.tree.topLevelItem(0).child(2).isHidden()
        assert page.tree.topLevelItem(0).child(3).isHidden()
        page.short_edge.setCurrentIndex(page.short_edge.findData(1080))
        assert page.tree.topLevelItem(0).child(1).isHidden()
        assert not page.tree.topLevelItem(0).child(2).isHidden()  # portrait 1080×1920
        assert sum(len(v) for v in page.selected().values())==4
        page.plans=[{'output':'retain-filter-only'}]
        page.duration_max.setValue(.25)
        assert 'Khoảng thời lượng không hợp lệ' in page.summary.text()
        with pytest.raises(ValueError,match='Khoảng thời lượng'):
            page.plan()
        assert len(page.plans)==1   # Visibility filtering alone never alters a dry-run.
        page.duration_max.setValue(4)
        page.check_visible('none')
        assert not page.plans
        assert set(page.selected()[channel])=={short,wide,unreadable}
        page.source_changed()
        assert page.media_metadata is None and page.selected()=={}
    finally:
        close(window)


def test_batch_metadata_stale_callback_cannot_replace_new_scan(tmp_path,monkeypatch):
    window=MainWindow(tmp_path/'state')
    try:
        page=window.batch
        old=str(tmp_path/'old.mp4');new=str(tmp_path/'new.mp4')
        pending=[]
        monkeypatch.setattr(window,'background',
            lambda work,done:pending.append(done))
        page.scanned({'old':[old]})
        page.duration_min.setValue(1)
        assert len(pending)==1
        page.scanned({'new':[new]})  # Replaces the source while the old FFprobe job is pending.
        assert len(pending)==2 and page.media_metadata is None
        pending[0]({'media':{old:{'duration':20,'width':3840,'height':2160}},
                    'errors':{},'cancelled':False})
        assert page.media_metadata is None
        pending[1]({'media':{new:{'duration':2,'width':1080,'height':1920}},
                    'errors':{},'cancelled':False})
        assert page.media_metadata is not None and new in page.media_metadata
        assert old not in page.media_metadata
        assert page.selected()=={'new':[new]}
    finally:
        close(window)



def test_audio_dialog_music_loop_crossfade_round_trip_and_mode_guard(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from fonesi_edit.ui.dialogs import AudioDialog
    window=MainWindow(tmp_path/'state')
    try:
        sample='audio.wav'
        window.editor.set_composition(Composition(width=320,height=180,
            clips=[Clip('video.mp4',end=1)],
            audio=[{'path':sample,'mode':'music','loop':True,'loop_crossfade':.2}]))
        dialog=AudioDialog(window.editor)
        assert dialog.table.columnCount()==17
        assert dialog.table.item(0,14).text()=='0.2'
        dialog.table.item(0,14).setText('0.15')
        dialog.apply()
        assert window.editor.composition.audio[0]['loop_crossfade']==.15
        reopened=AudioDialog(window.editor)
        assert reopened.table.item(0,14).text()=='0.15'
        reopened.table.cellWidget(0,1).setCurrentText('sfx')
        warnings=[]
        monkeypatch.setattr(QMessageBox,'warning',lambda *args:warnings.append(args[2]))
        reopened.apply()
        assert warnings and 'crossfade' in warnings[-1]
        assert window.editor.composition.audio[0]['mode']=='music'
    finally:
        close(window)



def test_sfx_repeat_audio_dialog_round_trip_and_invalid_count(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from fonesi_edit.ui.dialogs import AudioDialog
    window=MainWindow(tmp_path/'state')
    try:
        media=create_fixture(tmp_path/'media',duration=1)
        source=str(media['source'])
        window.editor.set_composition(Composition(width=320,height=180,
            clips=[Clip(source,end=1)],audio=[
                {'path':source,'mode':'sfx','repeat_count':2,'repeat_interval':.2}]))
        dialog=AudioDialog(window.editor)
        assert dialog.table.columnCount()==17
        assert dialog.table.item(0,15).text()=='2'
        assert dialog.table.item(0,16).text()=='0.2'
        dialog.table.item(0,15).setText('3')
        dialog.table.item(0,16).setText('0.25')
        dialog.apply()
        assert window.editor.composition.audio[0]['repeat_count']==3
        assert window.editor.composition.audio[0]['repeat_interval']==.25
        reopened=AudioDialog(window.editor)
        assert reopened.table.item(0,15).text()=='3'
        invalid=[]
        monkeypatch.setattr(QMessageBox,'warning',lambda *args:invalid.append(args[2]))
        reopened.table.item(0,15).setText('1.5')
        reopened.apply()
        assert invalid and 'SFX repeat count' in invalid[-1]
        assert window.editor.composition.audio[0]['repeat_count']==3
    finally:
        close(window)

def test_save_as_creates_independent_file_and_project_record(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / 'state')
    old_file = tmp_path / 'first.fonesi'
    new_file_without_suffix = tmp_path / 'second'
    try:
        window.project_file = old_file
        window.editor.set_composition(Composition(layers=[Layer(text='Original saved version')]))
        window.save_project()
        old_id = window.project_id
        old_payload = json.loads(old_file.read_text(encoding='utf-8'))

        # Make an unsaved edit, then branch it into a new file.
        window.editor.set_composition(Composition(layers=[Layer(text='Save As version')]))
        monkeypatch.setattr(
            'fonesi_edit.app.QFileDialog.getSaveFileName',
            lambda *args: (str(new_file_without_suffix), 'Fonesi (*.fonesi)'),
        )
        window.save_project_as()

        new_file = tmp_path / 'second.fonesi'
        new_payload = json.loads(new_file.read_text(encoding='utf-8'))
        assert window.project_file == new_file
        assert window.project_id != old_id
        assert new_payload['project_id'] == window.project_id
        assert new_payload['composition']['layers'][0]['text'] == 'Save As version'
        # Save As must not rewrite the source file or the source project's DB snapshot.
        assert json.loads(old_file.read_text(encoding='utf-8')) == old_payload
        projects = {project['id']: project for project in window.store.list_named('projects')}
        assert projects[old_id]['data']['layers'][0]['text'] == 'Original saved version'
        assert projects[window.project_id]['data']['layers'][0]['text'] == 'Save As version'
        assert window.actions['Lưu thành project mới'].shortcut().toString() == 'Ctrl+Shift+S'
        assert any(button.text() == 'Lưu thành' for button in window.findChildren(QPushButton))
    finally:
        close(window)


def test_save_as_cancel_does_not_change_active_project(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / 'state')
    try:
        original_file = tmp_path / 'original.fonesi'
        window.project_file = original_file
        window.editor.set_composition(Composition(layers=[Layer(text='Keep current')]))
        window.save_project()
        original_id = window.project_id
        original_projects = {project['id'] for project in window.store.list_named('projects')}
        monkeypatch.setattr(
            'fonesi_edit.app.QFileDialog.getSaveFileName',
            lambda *args: ('', ''),
        )
        window.save_project_as()
        assert window.project_file == original_file
        assert window.project_id == original_id
        assert {project['id'] for project in window.store.list_named('projects')} == original_projects
        assert window.editor.composition.layers[0].text == 'Keep current'
    finally:
        close(window)


def test_save_as_same_path_uses_normal_save_without_new_project_id(tmp_path, monkeypatch):
    window = MainWindow(tmp_path / 'state')
    try:
        current_file = tmp_path / 'current.fonesi'
        window.project_file = current_file
        window.editor.set_composition(Composition(layers=[Layer(text='Before')]))
        window.save_project()
        original_id = window.project_id
        window.editor.set_composition(Composition(layers=[Layer(text='Updated')]))
        monkeypatch.setattr(
            'fonesi_edit.app.QFileDialog.getSaveFileName',
            lambda *args: (str(current_file), 'Fonesi (*.fonesi)'),
        )
        window.save_project_as()
        payload = json.loads(current_file.read_text(encoding='utf-8'))
        assert window.project_id == original_id
        assert payload['project_id'] == original_id
        assert payload['composition']['layers'][0]['text'] == 'Updated'
        assert len(window.store.list_named('projects')) == 1
    finally:
        close(window)

def test_canvas_layer_clipboard_shortcuts_and_native_text_routing(tmp_path):
    from PySide6.QtWidgets import QLineEdit
    window = MainWindow(tmp_path / 'state')
    try:
        window.show()
        window.nav.setCurrentWidget(window.editor)
        window.editor.set_composition(Composition(layers=[Layer(text='Layer A')]))
        window.editor.select_id(window.editor.composition.layers[0].id)
        window.editor.canvas.setFocus()
        APP.processEvents()
        APP.clipboard().setText('do not serialize layer')
        window.actions['Copy layer'].trigger()
        assert APP.clipboard().text() == 'do not serialize layer'
        window.actions['Paste layer'].trigger()
        assert len(window.editor.composition.layers) == 2
        window.actions['Cut layer'].trigger()
        assert len(window.editor.composition.layers) == 1
        window.actions['Select all'].trigger()
        assert len(window.editor.selected_layers()) == 1

        window.show()
        field = QLineEdit(window)
        field.setGeometry(10, 10, 220, 28)
        field.setText('native text')
        field.show()
        field.setFocus()
        field.selectAll()
        APP.processEvents()
        window.actions['Copy layer'].trigger()
        assert APP.clipboard().text() == 'native text'
        APP.clipboard().setText(' pasted')
        field.setCursorPosition(len(field.text()))
        window.actions['Paste layer'].trigger()
        assert field.text() == 'native text pasted'
        field.selectAll()
        window.actions['Cut layer'].trigger()
        assert field.text() == ''
        field.setText('select all')
        window.actions['Select all'].trigger()
        assert field.selectedText() == 'select all'
    finally:
        close(window)

def test_add_video_shortcut_yields_to_text_editor_focus(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QLineEdit
    window = MainWindow(tmp_path / 'state')
    calls = []
    monkeypatch.setattr(window, 'guard', lambda callback: lambda: calls.append(callback))
    try:
        window.show()
        window.nav.setCurrentWidget(window.editor)
        field = QLineEdit(window)
        field.setGeometry(10, 10, 220, 28)
        field.setText('Keep typing')
        field.show()
        window.activateWindow()
        field.setFocus()
        APP.processEvents()
        assert QApplication.focusWidget() is field
        window.actions['Thêm video'].trigger()
        assert calls == []
    finally:
        close(window)


def test_layer_clipboard_preserves_group_metadata_and_undo_is_atomic(tmp_path):
    fixture = create_fixture(tmp_path / 'media', duration=0.5)
    source = Path(fixture['source'])
    source_bytes = source.read_bytes()
    clip = Clip(str(source), end=0.5, source_duration=0.5, id='clip-1')
    style = {'font_size': 32, 'color': '#ffffff', 'outline': 2, 'outline_color': '#000000'}
    first = Layer(
        name='Group A', text='Layer A', x=0.98, y=0.98, width=0.30, height=0.30,
        style=dict(style), keyframes={'x': [{'time': 0.0, 'value': 0.98}]},
        clip_ids=[clip.id], group='source-group',
    )
    second = Layer(
        name='Group B', text='Layer B', x=0.95, y=0.95, width=0.25, height=0.25,
        style=dict(style), keyframes={'y': [{'time': 0.0, 'value': 0.95}]},
        clip_ids=[clip.id], group='source-group',
    )
    unrelated = Layer(name='Unrelated', text='Keep unchanged', group='unrelated-group')
    window = MainWindow(tmp_path / 'state')
    try:
        window.editor.set_composition(Composition(clips=[clip], layers=[first, second, unrelated]))
        window.editor.select_ids([first.id, second.id])
        APP.clipboard().setText('external clipboard sentinel')
        window.editor.copy_layers()
        assert APP.clipboard().text() == 'external clipboard sentinel'
        assert len(window.editor.composition.layers) == 3

        window.editor.paste_layers()
        layers = window.editor.composition.layers
        assert len(layers) == 5
        copies = layers[3:]
        assert all(copy.id not in {first.id, second.id, unrelated.id} for copy in copies)
        assert len({copy.id for copy in copies}) == 2
        assert copies[0].group == copies[1].group
        assert copies[0].group not in {None, 'source-group'}
        assert layers[2].group == 'unrelated-group'
        for original, copied in zip((first, second), copies):
            assert copied.kind == original.kind
            assert copied.text == original.text
            assert copied.style == original.style
            assert copied.keyframes == original.keyframes
            assert copied.clip_ids == original.clip_ids
            assert 0 <= copied.x <= 1 - copied.width
            assert 0 <= copied.y <= 1 - copied.height
        assert source.read_bytes() == source_bytes

        window.editor.undo.undo()
        assert [layer.id for layer in window.editor.composition.layers] == [first.id, second.id, unrelated.id]
        window.editor.undo.redo()
        assert len(window.editor.composition.layers) == 5
    finally:
        close(window)


def test_cut_removes_only_unlocked_layers_and_preserves_source_media(tmp_path):
    fixture = create_fixture(tmp_path / 'media', duration=0.5)
    source = Path(fixture['source'])
    source_bytes = source.read_bytes()
    clip = Clip(str(source), end=0.5, source_duration=0.5, id='clip-locked-test')
    editable = Layer(name='Editable', text='Remove from composition', clip_ids=[clip.id], group='g')
    locked = Layer(name='Locked', text='Keep in composition', locked=True, clip_ids=[clip.id], group='g')
    window = MainWindow(tmp_path / 'state')
    try:
        window.editor.set_composition(Composition(clips=[clip], layers=[editable, locked]))
        window.editor.select_ids([editable.id, locked.id])
        window.editor.cut_layers()
        assert [layer.id for layer in window.editor.composition.layers] == [locked.id]
        assert source.exists() and source.read_bytes() == source_bytes

        window.editor.undo.undo()
        assert [layer.id for layer in window.editor.composition.layers] == [editable.id, locked.id]
        window.editor.undo.redo()
        assert [layer.id for layer in window.editor.composition.layers] == [locked.id]
        assert source.exists() and source.read_bytes() == source_bytes
    finally:
        close(window)

def test_ui_layout_persists_and_restores_navigation_inspector_and_splitter(tmp_path):
    state = tmp_path / "state"
    window = MainWindow(state)
    window.resize(1280, 820)
    window.show()
    APP.processEvents()
    window.nav.setCurrentIndex(3)
    window.editor.inspector.setCurrentIndex(1)
    window.editor.splitter.setSizes([220, 680, 320])
    APP.processEvents()
    assert window.persist_ui_layout()
    saved = window.store.setting("ui_layout_v1")
    assert saved["version"] == 1
    assert saved["nav_index"] == 3
    assert saved["inspector_tab"] == 1
    assert len(saved["editor_splitter_sizes"]) == 3
    assert saved["geometry"] and saved["state"]
    close(window)

    restored = MainWindow(state)
    restored.show()
    APP.processEvents()
    assert restored.nav.currentIndex() == 3
    assert restored.editor.inspector.currentIndex() == 1
    assert restored._ui_geometry_restored is True
    sizes = restored.editor.splitter.sizes()
    assert len(sizes) == 3
    assert all(size > 0 for size in sizes)
    close(restored)


def test_ui_layout_restore_ignores_corrupt_or_out_of_range_settings(tmp_path):
    window = MainWindow(tmp_path / "state")
    window.store.set_setting("ui_layout_v1", {
        "version": 1,
        "geometry": "not-base64%%% ",
        "state": 123,
        "nav_index": 999,
        "inspector_tab": -2,
        "editor_splitter_sizes": [10, -1],
    })
    assert window.restore_ui_layout() is False
    assert 0 <= window.nav.currentIndex() < window.nav.count()
    assert 0 <= window.editor.inspector.currentIndex() < window.editor.inspector.count()
    assert len(window.editor.splitter.sizes()) == 3
    close(window)

def test_editor_global_shortcuts_are_suppressed_only_during_ime_preedit(tmp_path, monkeypatch):
    from PySide6.QtGui import QInputMethodEvent
    window = MainWindow(tmp_path / "state")
    window.show()
    window.nav.setCurrentWidget(window.editor)
    window.editor.add_layer("text")
    window.editor.inspector.setCurrentIndex(1)
    field = window.editor.fields["text"][0]
    window.activateWindow()
    field.setFocus()
    APP.processEvents()
    calls = []
    monkeypatch.setattr(window, "guard", lambda callback: lambda: calls.append(callback))
    try:
        APP.sendEvent(field, QInputMethodEvent("拼音", []))
        assert window.ime_composition_active(field)
        window.actions["Cài đặt"].trigger()
        assert calls == []

        APP.sendEvent(field, QInputMethodEvent("", []))
        assert not window.ime_composition_active(field)
        window.actions["Cài đặt"].trigger()
        assert len(calls) == 1
    finally:
        close(window)


def test_ime_preedit_state_clears_when_focus_leaves_composing_widget(tmp_path):
    from PySide6.QtGui import QInputMethodEvent
    window = MainWindow(tmp_path / "state")
    window.show()
    window.nav.setCurrentWidget(window.editor)
    window.editor.add_layer("text")
    window.editor.inspector.setCurrentIndex(1)
    field = window.editor.fields["text"][0]
    window.activateWindow()
    field.setFocus()
    APP.processEvents()
    try:
        APP.sendEvent(field, QInputMethodEvent("拼音", []))
        assert window.ime_composition_active(field)
        window.editor.property_search.setFocus()
        APP.processEvents()
        assert window._ime_composing_widget is None
        assert not window.ime_composition_active(field)
    finally:
        close(window)

def test_scan_search_filter_sort_preserves_original_selection_and_safe_urls(tmp_path):
    from PySide6.QtCore import Qt
    window = MainWindow(tmp_path / "state")
    window.scheduler.paused = True
    try:
        payload = {
            "url": "https://example.test/gallery",
            "folder": str(tmp_path / "output"),
            "engine": "gallery",
            "media": "both",
        }
        scan_id = window.store.submit("scan", payload)
        window.store.claim(allowed={"scan"})
        items = [
            {"id": "z1", "title": "Zebra cover", "kind": "images", "engine": "gallery",
             "url": "https://example.test/media/z.png", "selectable": True},
            {"id": "a2", "title": "Alpha trailer", "kind": "video", "engine": "video",
             "url": "https://example.test/media/a.mp4", "selectable": True},
            {"id": "a3", "title": "Alpha still", "kind": "images", "engine": "gallery",
             "url": "https://example.test/media/a.png", "selectable": True},
            {"id": "dup", "title": "Alpha duplicate", "kind": "images", "engine": "gallery",
             "url": "https://example.test/media/a.png", "selectable": True},
            {"id": "bad", "title": "Hidden unsafe", "kind": "images", "engine": "gallery",
             "url": None, "selectable": False, "reason": "No safe URL"},
        ]
        window.store.finish(scan_id, {
            "platform": "Generic", "items": items, "count": len(items), "complete": None
        })
        downloads = window.downloads
        downloads.scan_page_size = 2
        downloads.show_scan()

        downloads.scan_search.setText("alpha")
        APP.processEvents()
        root = downloads.scan_tree.topLevelItem(0)
        assert root.childCount() == 2
        assert [root.child(i).data(0, Qt.ItemDataRole.UserRole) for i in range(2)] == [1, 2]
        root.child(0).setCheckState(0, Qt.CheckState.Checked)  # original index 1

        downloads.scan_kind_filter.setCurrentIndex(downloads.scan_kind_filter.findData("images"))
        APP.processEvents()
        root = downloads.scan_tree.topLevelItem(0)
        assert [root.child(i).data(0, Qt.ItemDataRole.UserRole) for i in range(root.childCount())] == [2, 3]
        assert len(downloads.scan_selected[scan_id]) == 1  # hidden selected video is retained

        downloads.scan_kind_filter.setCurrentIndex(downloads.scan_kind_filter.findData("unselectable"))
        APP.processEvents()
        root = downloads.scan_tree.topLevelItem(0)
        assert root.childCount() == 1
        assert root.child(0).data(0, Qt.ItemDataRole.UserRole) == 3
        assert not (root.child(0).flags() & Qt.ItemFlag.ItemIsUserCheckable)
        assert "URL trùng" in root.child(0).text(2)

        downloads.scan_search.clear()
        downloads.scan_kind_filter.setCurrentIndex(downloads.scan_kind_filter.findData("all"))
        downloads.scan_sort.setCurrentIndex(downloads.scan_sort.findData("title"))
        APP.processEvents()
        root = downloads.scan_tree.topLevelItem(0)
        assert [root.child(i).data(0, Qt.ItemDataRole.UserRole) for i in range(root.childCount())] == [3, 2]
        downloads.change_scan_page(1)
        root = downloads.scan_tree.topLevelItem(0)
        assert root.child(0).data(0, Qt.ItemDataRole.UserRole) == 1
        assert root.child(0).checkState(0) == Qt.CheckState.Checked
        downloads.download_selected()
        jobs = [job for job in window.store.jobs() if job["kind"] == "download"]
        assert len(jobs) == 1
        assert jobs[0]["payload"]["url"] == "https://example.test/media/a.mp4"
        assert jobs[0]["payload"]["engine"] == "video"
    finally:
        close(window)

def test_bulk_scan_selection_spans_filtered_pages_and_clear_keeps_hidden_choices(tmp_path):
    window = MainWindow(tmp_path / "state")
    window.scheduler.paused = True
    try:
        payload = {"url": "https://example.test/gallery", "folder": str(tmp_path / "output"),
                   "engine": "gallery", "media": "images"}
        scan_id = window.store.submit("scan", payload)
        window.store.claim(allowed={"scan"})
        urls = [f"https://example.test/media/{name}.png" for name in ("a", "b", "c", "d", "e")]
        items = [{"id": str(i), "title": f"Image {i}", "kind": "images",
                  "engine": "gallery", "url": url, "selectable": True}
                 for i, url in enumerate(urls)]
        window.store.finish(scan_id, {"platform": "Generic", "items": items, "count": len(items), "complete": True})
        page = window.downloads
        page.scan_page_size = 2
        page.show_scan()
        page.select_all_filtered()
        assert page.scan_selected[scan_id] == set(range(5))
        page.scan_search.setText("Image 4")
        assert page.scan_selected[scan_id] == set(range(5))
        page.clear_all_filtered()
        assert page.scan_selected[scan_id] == {0, 1, 2, 3}
        page.scan_search.clear()
        page.change_scan_page(2)
        assert page.scan_tree.topLevelItem(0).child(0).checkState(0).name == "Unchecked"
    finally:
        close(window)


def test_bulk_scan_selection_over_cap_is_atomic_and_does_not_enqueue_partial_jobs(tmp_path):
    import pytest
    window = MainWindow(tmp_path / "state")
    window.scheduler.paused = True
    try:
        payload = {"url": "https://example.test/gallery", "folder": str(tmp_path / "output"),
                   "engine": "gallery", "media": "images"}
        scan_id = window.store.submit("scan", payload)
        window.store.claim(allowed={"scan"})
        items = [{"id": str(i), "title": f"Image {i}", "kind": "images",
                  "engine": "gallery", "url": f"https://example.test/media/{i}.png",
                  "selectable": True} for i in range(501)]
        window.store.finish(scan_id, {"platform": "Generic", "items": items, "count": len(items), "complete": True})
        page = window.downloads
        page.scan_page_size = 200
        page.show_scan()
        existing = set(range(500))
        page.scan_selected[scan_id] = set(existing)
        page.select_all_filtered()
        assert page.scan_selected[scan_id] == existing
        assert "chưa thay đổi" in window.status.text()
        page.scan_selected[scan_id] = set(range(501))
        with pytest.raises(ValueError, match="Tối đa 500"):
            page.download_selected()
        assert not [job for job in window.store.jobs() if job["kind"] == "download"]
    finally:
        close(window)




def test_scan_metadata_filters_keep_hidden_selections_and_validate_partial_input(tmp_path):
    from PySide6.QtCore import Qt
    window = MainWindow(tmp_path / "state")
    window.scheduler.paused = True
    try:
        payload = {"url": "https://example.test/channel", "folder": str(tmp_path / "files")}
        scan_id = window.store.submit("scan", payload)
        window.store.claim(allowed={"scan"})
        items = [
            {"id": "a", "title": "Older video", "kind": "video", "engine": "video",
             "url": "https://example.test/a", "selectable": True,
             "upload_date": "20240131", "duration": 59, "height": 1080},
            {"id": "b", "title": "Recent photo", "kind": "images", "engine": "gallery",
             "url": "https://example.test/b", "selectable": True,
             "upload_date": "20240229", "height": 720},
            {"id": "c", "title": "Oversize video", "kind": "video", "engine": "video",
             "url": "https://example.test/c", "selectable": True,
             "upload_date": "20240301", "duration": 120, "height": 2160},
            {"id": "d", "title": "Unknown metadata", "kind": "video", "engine": "video",
             "url": "https://example.test/d", "selectable": True},
            {"id": "e", "title": "Invalid metadata", "kind": "video", "engine": "video",
             "url": "https://example.test/e", "selectable": True,
             "upload_date": "20240230", "duration": -1, "height": "bad"},
        ]
        window.store.finish(scan_id, {"platform": "Generic", "items": items,
                                      "count": len(items), "complete": None})
        page = window.downloads
        page.scan_page_size = 2
        page.show_scan()
        first = page.scan_tree.topLevelItem(0).child(0)
        first.setCheckState(0, Qt.CheckState.Checked)
        assert page.scan_selected[scan_id] == {0}

        page.scan_after.setText("20240201")
        page.scan_before.setText("2024-03-01")
        page.scan_duration_min.setText("60")
        page.scan_height_max.setText("1080")
        assert page._scan_visible_indexes(items) == [1, 3, 4]
        assert page.scan_tree.topLevelItem(0).childCount() == 2
        page.change_scan_page(1)
        assert page.scan_tree.topLevelItem(0).child(0).data(
            0, Qt.ItemDataRole.UserRole) == 4
        assert page.scan_selected[scan_id] == {0}
        page.scan_include_missing.setChecked(False)
        assert page._scan_visible_indexes(items) == []
        assert page.scan_selected[scan_id] == {0}
        page.scan_duration_min.clear()
        assert page._scan_visible_indexes(items) == [1]
        page.scan_search.setText("photo")
        page.scan_kind_filter.setCurrentIndex(page.scan_kind_filter.findData("images"))
        page.select_all_filtered()
        assert page.scan_selected[scan_id] == {0, 1}

        page.scan_before.setText("2024-02-30")
        assert page._scan_visible_indexes(items) == []
        assert "Bộ lọc metadata không hợp lệ" in page.scan_note.text()
        assert page.scan_selected[scan_id] == {0, 1}
        page.scan_before.setText("20240229")
        page.scan_duration_min.setText("70")
        page.scan_duration_max.setText("10")
        assert page._scan_visible_indexes(items) == []
        assert "Thời lượng tối thiểu" in page.scan_note.text()
        page.scan_duration_min.clear()
        page.scan_duration_max.clear()
        page.download_selected()
        requests = [job['payload']['url'] for job in window.store.jobs()
                    if job['kind'] == 'download']
        assert set(requests) == {"https://example.test/a", "https://example.test/b"}
    finally:
        close(window)



def test_scan_chronological_sort_keeps_unknown_last_ties_stable_and_selection(tmp_path):
    from PySide6.QtCore import Qt
    window = MainWindow(tmp_path / "state")
    window.scheduler.paused = True
    try:
        payload = {"url": "https://example.test/gallery", "folder": str(tmp_path / "output"),
                   "engine": "gallery"}
        scan_id = window.store.submit("scan", payload)
        window.store.claim(allowed={"scan"})
        dates = ("20240201", "20240101", None, "20240230", "2024-02-01")
        items = []
        for i, day in enumerate(dates):
            item = {"id": str(i), "title": f"Item {i}", "kind": "images",
                    "engine": "gallery", "url": f"https://example.test/p/{i}",
                    "selectable": True}
            if day is not None:
                item["upload_date"] = day
            items.append(item)
        window.store.finish(scan_id, {"platform": "Generic", "items": items,
                                      "count": len(items), "complete": None})
        page = window.downloads
        page.scan_page_size = 2
        page.show_scan()
        page.scan_tree.topLevelItem(0).child(0).setCheckState(0, Qt.CheckState.Checked)
        assert page.scan_selected[scan_id] == {0}
        page.scan_sort.setCurrentIndex(page.scan_sort.findData("date_asc"))
        assert page._scan_visible_indexes(items) == [1, 0, 4, 2, 3]
        page.change_scan_page(1)
        assert page.scan_tree.topLevelItem(0).child(0).data(
            0, Qt.ItemDataRole.UserRole) == 4

        page.scan_sort.setCurrentIndex(page.scan_sort.findData("date_desc"))
        assert page._scan_visible_indexes(items) == [0, 4, 1, 2, 3]
        root = page.scan_tree.topLevelItem(0)
        assert root.child(0).checkState(0) == Qt.CheckState.Checked
        root.child(1).setCheckState(0, Qt.CheckState.Checked)
        assert page.scan_selected[scan_id] == {0, 4}
        page.change_scan_page(2)
        root = page.scan_tree.topLevelItem(0)
        assert [root.child(i).data(0, Qt.ItemDataRole.UserRole)
                for i in range(root.childCount())] == [3]

        page.scan_after.setText("20240201")
        assert page._scan_visible_indexes(items) == [0, 4, 2, 3]
        page.scan_include_missing.setChecked(False)
        assert page._scan_visible_indexes(items) == [0, 4]
        assert page.scan_selected[scan_id] == {0, 4}
        page.download_selected()
        urls = [job["payload"]["url"] for job in window.store.jobs()
                if job["kind"] == "download"]
        assert set(urls) == {"https://example.test/p/0", "https://example.test/p/4"}
    finally:
        close(window)



def test_bounded_scan_next_ui_is_idempotent_and_keeps_original_selection(tmp_path):
    from PySide6.QtCore import Qt
    from fonesi_edit.downloads import SCAN_WINDOW_MODE
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        payload={'url':'https://example.test/channel','folder':str(tmp_path/'files'),
                 'engine':'video','media':'videos','limit':2}
        parent_id=window.store.submit('scan',payload)
        window.store.claim(allowed={'scan'})
        first=[{'id':str(i),'title':f'Video {i}','kind':'video','engine':'video',
                'url':f'https://example.test/video/{i}','selectable':True}
               for i in range(2)]
        first_result={'platform':'Generic','items':first,'count':2,'complete':False,
                      'scan_window':{'mode':SCAN_WINDOW_MODE,'start':1,'limit':2,'next_start':3}}
        window.store.finish(parent_id,first_result)
        page=window.downloads
        page.scan_page_size=2
        page.show_scan()
        page.scan_tree.topLevelItem(0).child(0).setCheckState(0,Qt.CheckState.Checked)
        assert page.scan_selected[parent_id]=={0}
        page.continue_scan()
        next_id=page.scans.currentData()
        assert next_id!=parent_id and window.store.job(next_id)['state']=='pending'
        assert window.store.job(next_id)['payload']['scan_parent_id']==parent_id
        page.scans.setCurrentIndex(page.scans.findData(parent_id))
        page.continue_scan()
        assert page.scans.currentData()==next_id
        assert len([j for j in window.store.jobs() if j['kind']=='scan'])==2
        window.store.claim(allowed={'scan'})
        combined=first+[{'id':str(i),'title':f'Video {i}','kind':'video','engine':'video',
                         'url':f'https://example.test/video/{i}','selectable':True}
                        for i in (2,3)]
        window.store.finish(next_id,{'platform':'Generic','items':combined,'count':4,
                'complete':False,'scan_window':{
                    'mode':SCAN_WINDOW_MODE,'start':3,'limit':2,'next_start':5}})
        page.load_scan()
        assert page.scan_selected[next_id]=={0}
        page.scan_search.setText('Video 2')
        assert page._scan_visible_indexes(combined)==[2]
        page.select_all_filtered()
        assert page.scan_selected[next_id]=={0,2}
        page.download_selected()
        jobs=[job for job in window.store.jobs() if job['kind']=='download']
        assert len(jobs)==2
        assert {j['payload']['url'] for j in jobs}=={
            'https://example.test/video/0','https://example.test/video/2'}
        assert all('scan_parent_id' not in j['payload'] for j in jobs)
    finally:
        close(window)



def test_scan_subtitle_only_action_keeps_account_and_is_idempotent(tmp_path):
    from PySide6.QtCore import Qt
    from fonesi_edit.browser import create_profile,bind
    from fonesi_edit.downloads import selected_download_payloads
    import pytest
    window=MainWindow(tmp_path/'state')
    window.scheduler.paused=True
    try:
        p=create_profile(window.store,'Profile YouTube')
        account=bind(window.store,p,'YouTube')
        original={'url':'https://www.youtube.com/channel/test',
                  'folder':str(tmp_path/'output'),
                  'engine':'video','media':'videos','limit':2,
                  'account_ref':account,'expected_identity':None,
                  'languages':['vi','en'],'thumbnail':True,
                  'workflow':{'preset':{'clips':[]}}}
        scan=window.store.submit('scan',original)
        window.store.claim(allowed={'scan'})
        items=[{'id':'clip','title':'Video','kind':'video',
                'engine':'video','url':'https://www.youtube.com/watch?v=Abc_123-xyz',
                'selectable':True},
               {'id':'photo','title':'Image','kind':'images',
                'engine':'gallery','url':'https://www.youtube.com/shorts/abc-photo',
                'selectable':True}]
        window.store.finish(scan,{'platform':'YouTube','items':items,
                                  'count':2,'complete':None})
        page=window.downloads
        page.show_scan()
        page.scan_tree.topLevelItem(0).child(0).setCheckState(0,Qt.CheckState.Checked)
        page.download_subtitles_selected()
        page.download_subtitles_selected()
        jobs=[j for j in window.store.jobs() if j['kind']=='download']
        assert len(jobs)==1
        sub=jobs[0]['payload']
        assert sub['download_mode']=='subtitles_only'
        assert sub['url']==items[0]['url']
        assert sub['account_ref']==account and sub['folder']==original['folder']
        assert 'workflow' not in sub and sub['thumbnail'] is False
        page.download_selected()
        jobs=[j for j in window.store.jobs() if j['kind']=='download']
        assert len(jobs)==2
        assert sorted(x['payload'].get('download_mode','media') for x in jobs)==['media','subtitles_only']
        page.scan_tree.topLevelItem(0).child(1).setCheckState(0,Qt.CheckState.Checked)
        with pytest.raises(ValueError,match='Chỉ tải phụ đề'):
            page.download_subtitles_selected()
        assert len([j for j in window.store.jobs() if j['kind']=='download'])==2
    finally:
        close(window)
