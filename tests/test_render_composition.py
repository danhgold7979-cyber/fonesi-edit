from copy import deepcopy
import math
import pytest
from fonesi_edit.domain import Composition,Clip,Layer
from fonesi_edit.motion import transforms
from fonesi_edit.render import render_composition,reference_frame
from fonesi_edit.prototypes.media import create_fixture,probe


@pytest.mark.parametrize('preset',['fixed','left-right','right-left','top-bottom','bottom-top','diagonal','pingpong','bounce','corners','random','zoom','a-b'])
def test_motion_shared_expression_is_finite_reproducible_and_numeric(preset):
    layer=Layer(motion={'preset':preset,'speed':20,'duration':3,'repeat':True,'easing':'ease-in-out'})
    first=transforms(layer,320,180,123);second=transforms(layer,320,180,123)
    for key,value in first.items():
        assert value.ffmpeg()==second[key].ffmpeg()
        assert all(math.isfinite(value.value(t)) for t in (0,.5,3,10))


def test_real_multi_clip_alpha_mask_text_subtitle_audio_and_reuse(tmp_path):
    f=create_fixture(tmp_path/'media',duration=1)
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[
        Clip(str(f['source']),end=.5,subtitles=str(f['subtitles'])),Clip(str(f['source']),start=.5,end=1,speed=1)],layers=[
        Layer(kind='mask',x=.1,y=.7,width=.8,height=.15,style={'mode':'blur','radius':5}),
        Layer(kind='image',path=str(f['logo']),width=.15,height=.2,x=.8,y=.05),
        Layer(text='Fonesi Việt',style={'font_size':18,'color':'#ffffff','outline':1},keyframes={'x':[{'time':0,'value':.05},{'time':1,'value':.2}]})],
        audio=[{'path':str(f['source']),'volume':.1,'loop':True,'fade_out':.1}])
    output=tmp_path/'output.mp4'
    result=render_composition(c,output)
    assert result['validated'] and result['encoder']=='libx264'
    assert (probe(output).width,probe(output).height)==(320,180)
    assert render_composition(c,output)['reused']
    changed=deepcopy(c);changed.layers[-1].text='Different'
    with pytest.raises(FileExistsError):render_composition(changed,output)


def test_clip_crop_defaults_keep_legacy_project_payload_compatible():
    legacy = Composition.from_dict({"clips": [{"path": "legacy.mp4"}]})
    clip = legacy.clips[0]
    assert (clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height) == (0, 0, 1, 1)
    assert Composition.from_dict(legacy.to_dict()).clips[0].crop_width == 1


@pytest.mark.parametrize("values", [
    {"crop_x": -0.01},
    {"crop_y": 1.01},
    {"crop_width": 0},
    {"crop_height": -0.1},
    {"crop_x": 0.8, "crop_width": 0.3},
    {"crop_y": 0.8, "crop_height": 0.3},
    {"crop_x": float("nan")},
    {"crop_width": True},
])
def test_clip_crop_rejects_invalid_normalized_regions(values):
    with pytest.raises(ValueError, match="Crop region"):
        Composition(clips=[Clip("unused.mp4", **values)]).validate()


def test_crop_rect_pixels_uses_even_source_pixel_bounds():
    from fonesi_edit.render import crop_rect_pixels
    clip = Clip("unused.mp4", crop_x=0.25, crop_y=0.1,
                crop_width=0.5, crop_height=0.8)
    assert crop_rect_pixels(clip, 640, 360) == (320, 288, 160, 36)
    assert crop_rect_pixels(Clip("unused.mp4"), 640, 360) is None
    # Odd source dimensions are clamped to safe even boundaries.
    assert crop_rect_pixels(Clip("unused.mp4", crop_x=0.99, crop_y=0.99,
                                 crop_width=0.01, crop_height=0.01), 641, 361) == (6, 4, 634, 356)


def test_clip_crop_compiles_before_flip_rotation_and_renders(tmp_path):
    from fonesi_edit.render import compile_graph
    f = create_fixture(tmp_path / "media", duration=0.6)
    source = str(f["source"])
    clip = Clip(source, end=0.5, flip=True, rotation=90,
                crop_x=0.25, crop_y=0.1, crop_width=0.5, crop_height=0.8)
    composition = Composition(width=320, height=180, fps=25, encoder="cpu",
                              clips=[clip], mute_original=True)
    stage = tmp_path / "crop-stage"
    stage.mkdir()
    _, graph, _ = compile_graph(composition, stage)
    joined = graph
    # Derive the expected geometry from the same probed source dimensions as
    # the compositor; this also catches incorrect metadata/orientation handling.
    from fonesi_edit.render import crop_rect_pixels
    info = probe(f["source"])
    rect = crop_rect_pixels(clip, info.width, info.height)
    assert rect is not None
    crop_filter = "crop=" + ":".join(str(value) for value in rect)
    assert crop_filter in joined, f"Missing source crop filter {crop_filter!r} in graph: {joined}"
    crop_at = joined.index(crop_filter)
    assert crop_at < joined.index("hflip") < joined.index("rotate=")
    output = tmp_path / "cropped.mp4"
    assert render_composition(composition, output)["validated"]
    assert (probe(output).width, probe(output).height) == (320, 180)


def test_crop_dialog_has_preview_controls_and_cancel_preserves_clip(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.ui.dialogs import CropDialog
    from fonesi_edit.prototypes.media import MediaInfo
    app = QApplication.instance()
    source = tmp_path / "dummy.mp4"
    source.write_bytes(b"test")
    clip = Clip(str(source))
    monkeypatch.setattr("fonesi_edit.ui.dialogs.probe", lambda path: MediaInfo(640, 360, 1, "25/1", "h264", None))
    from PySide6.QtGui import QPixmap, QColor
    def write_white_frame(source, dest, second=0):
        pixmap = QPixmap(640, 360)
        pixmap.fill(QColor("#ffffff"))
        return pixmap.save(str(dest))
    monkeypatch.setattr("fonesi_edit.ui.dialogs.extract_frame", write_white_frame)
    dialog = CropDialog(clip)
    before = (clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height)
    dialog.rect = [0.25, 0.25, 0.5, 0.5]
    dialog._paint_crop()
    preview = dialog.canvas.pixmap().toImage()
    inside = preview.pixelColor(preview.width() // 2, preview.height() // 2)
    outside = preview.pixelColor(2, 2)
    assert inside.lightness() > 220
    assert outside.lightness() < 180

    # Verify that a real Qt drag moves the normalized crop rectangle.
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    dialog.show()
    app.processEvents()
    dialog.rect = [0.25, 0.25, 0.5, 0.5]
    dialog._paint_crop()
    shown = dialog.canvas.pixmap()
    offset_x = (dialog.canvas.width() - shown.width()) // 2
    offset_y = (dialog.canvas.height() - shown.height()) // 2
    start = QPoint(offset_x + int(0.45 * shown.width()), offset_y + int(0.45 * shown.height()))
    end = QPoint(start.x() + 24, start.y() + 8)
    original_x = dialog.rect[0]
    QTest.mousePress(dialog.canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(dialog.canvas, end, delay=10)
    QTest.mouseRelease(dialog.canvas, Qt.MouseButton.LeftButton, pos=end)
    app.processEvents()
    assert dialog.rect[0] > original_x

    dialog.rect = [0.1, 0.1, 0.6, 0.6]
    dialog.reject()
    dialog.close()
    assert (clip.crop_x, clip.crop_y, clip.crop_width, clip.crop_height) == before
    assert dialog.lock_ratio.text() == "Khóa tỷ lệ crop"
    dialog.reset_crop()
    assert dialog.rect == [0.0, 0.0, 1.0, 1.0]


def test_clip_dialog_crop_button_commits_crop_as_one_undo_step(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QDialog
    from fonesi_edit.ui.dialogs import ClipDialog, CropDialog
    from fonesi_edit.prototypes.media import MediaInfo
    from fonesi_edit.ui.editor import Editor
    from tempfile import TemporaryDirectory
    app = QApplication.instance()
    source = tmp_path / "source.mp4"
    source.write_bytes(b"fixture")
    host = type("Host", (), {"workspace": TemporaryDirectory(), "message": lambda *args: None})()
    editor = Editor(host)
    editor.set_composition(Composition(clips=[Clip(str(source), end=1)]))
    monkeypatch.setattr("fonesi_edit.ui.dialogs.probe", lambda path: MediaInfo(640, 360, 1, "25/1", "h264", None))
    from PySide6.QtGui import QPixmap
    monkeypatch.setattr("fonesi_edit.ui.dialogs.extract_frame", lambda source, dest, second=0: QPixmap(640, 360).save(str(dest)))
    dialog = ClipDialog(editor, 0)
    monkeypatch.setattr(CropDialog, "exec", lambda self: (setattr(self, "rect", [0.1, 0.1, 0.7, 0.7]) or QDialog.DialogCode.Accepted))
    dialog.edit_crop()
    dialog.apply()
    assert editor.composition.clips[0].crop_x == 0.1
    assert editor.composition.clips[0].crop_width == 0.7
    assert editor.undo.count() == 1
    editor.undo.undo()
    assert editor.composition.clips[0].crop_width == 1.0
    editor.close()
    host.workspace.cleanup()


def test_crossfade_speed_crop_and_reference_use_real_export(tmp_path):
    f=create_fixture(tmp_path/'media',duration=1)
    c=Composition(width=180,height=320,fps=25,encoder='cpu',fit='crop',transition=.1,
        clips=[Clip(str(f['source']),end=1,speed=2),Clip(str(f['source']),end=.5)],mute_original=True)
    result=render_composition(c,tmp_path/'out.mp4')
    assert abs(probe(tmp_path/'out.mp4').duration-.9)<.15
    frame=reference_frame(c,tmp_path/'reference',second=.2)
    assert frame.is_file() and frame.stat().st_size>1000


def test_dynamic_rotated_feathered_mask_and_ducking_normalization(tmp_path):
    f=create_fixture(tmp_path/'media',duration=.5)
    mask=Layer(kind='mask',x=.1,y=.2,width=.4,height=.3,rotation=20,style={'mode':'mosaic','radius':3,'corner_radius':8,'feather':3},keyframes={'x':[{'time':0,'value':.1},{'time':.5,'value':.3}]})
    c=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(f['source']),end=.5)],layers=[mask],
        audio=[{'path':str(f['source']),'mode':'main','volume':.5},{'path':str(f['source']),'mode':'music','loop':True,'volume':.1}],adjustments={'ducking':True,'normalize':True})
    result=render_composition(c,tmp_path/'dynamic.mp4')
    assert result['validated']


def test_draggable_subtitle_layer_maps_source_trim_speed_and_output_time(tmp_path):
    from fonesi_edit.render import compile_graph
    f=create_fixture(tmp_path/'media',duration=1)
    sub=tmp_path/'timed.srt';sub.write_text('1\n00:00:00,200 --> 00:00:00,800\nĐúng thời gian\n',encoding='utf-8')
    clip=Clip(str(f['source']),start=.2,end=1,speed=2)
    layer=Layer(kind='subtitle',path=str(sub),clip_ids=[clip.id],x=.2,y=.5,style={'font_size':18})
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[clip],layers=[layer])
    stage=tmp_path/'graph';stage.mkdir();compile_graph(comp,stage)
    import pysubs2
    cue=pysubs2.load(str(stage/'layer-0.ass'))[0]
    assert cue.start==0 and cue.end==300
    assert render_composition(comp,tmp_path/'subtitle.mp4')['validated']


def test_solo_track_excludes_original_audio_in_actual_output(tmp_path):
    import subprocess
    from fonesi_edit.prototypes.tools import locate_tool
    from array import array
    f=create_fixture(tmp_path/'media',duration=.5)
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',clips=[Clip(str(f['source']),end=.5)],audio=[{'path':str(f['source']),'mode':'music','solo':True,'volume':0}])
    output=tmp_path/'solo.mp4';render_composition(comp,output)
    data=subprocess.run([locate_tool('ffmpeg'),'-v','error','-i',str(output),'-vn','-f','s16le','-'],capture_output=True,check=True).stdout
    samples=array('h');samples.frombytes(data)
    assert samples and max(abs(value) for value in samples)==0


@pytest.mark.parametrize('bad_gain',[float('nan'),float('inf'),-1,5])
def test_clip_gain_rejects_nonfinite_and_out_of_bounds(bad_gain):
    with pytest.raises(ValueError,match='rotation/volume'):
        Composition(clips=[Clip('synthetic.mp4',volume=bad_gain)]).validate()


@pytest.mark.parametrize('changes',[
    {'width':320.0},
    {'height':True},
    {'fps':30.5},
    {'fps':True},
    {'width':321},
])
def test_output_geometry_requires_even_integer_dimensions_and_integer_fps(changes):
    values={'width':320,'height':180,'fps':25,**changes}
    with pytest.raises(ValueError):
        Composition(**values).validate()
    Composition(width=320,height=180,fps=25).validate()



@pytest.mark.parametrize(('placement','extra','expected'),[
    ('absolute',{'offset':.4},.4),
    ('percent',{'position_pct':50,'offset':.1},.65),
    ('video_end',{'offset':.2},.9),
    ('scene_start',{'scene_index':2,'offset':.1},.4),
    ('scene_end',{'scene_index':1,'offset':.1},.3),
])
def test_sfx_placement_anchors_follow_real_clip_timing(placement,extra,expected,tmp_path):
    from fonesi_edit.render import compile_graph,audio_timeline_offset
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    c=Composition(width=320,height=180,fps=25,encoder='cpu',transition=.1,
                  mute_original=True,clips=[
                      Clip(source,end=.8,speed=2),
                      Clip(source,end=.8)],
                  audio=[{'path':source,'mode':'sfx','placement':placement,**extra}])
    stage=tmp_path/'graph';stage.mkdir()
    args,graph,total=compile_graph(c,stage)
    assert abs(total-1.1)<1e-6
    assert f'adelay={round(expected*1000)}:all=1' in graph
    ranges={c.clips[0].id:(0,.4),c.clips[1].id:(.3,.8)}
    assert abs(audio_timeline_offset(c.audio[0],total,c.clips,ranges)-expected)<1e-6


@pytest.mark.parametrize('invalid',[
    {'placement':'unsupported'},
    {'placement':'percent'},
    {'placement':'percent','position_pct':-1},
    {'placement':'percent','position_pct':101},
    {'placement':'percent','position_pct':float('nan')},
    {'placement':'percent','position_pct':True},
    {'placement':'scene_start'},
    {'placement':'scene_start','scene_index':0},
    {'placement':'scene_end','scene_index':2},
    {'placement':'scene_start','scene_index':1.5},
])
def test_invalid_sfx_placement_is_rejected_in_domain(invalid):
    c=Composition(clips=[Clip('unused.mp4',end=1)],audio=[
        {'path':'unused.mp4','mode':'sfx',**invalid}])
    with pytest.raises(ValueError,match='SFX'):
        c.validate()
    with pytest.raises(ValueError,match='Relative placement'):
        Composition(clips=[Clip('a.mp4',end=1)],audio=[
            {'path':'b.wav','mode':'music','placement':'video_end'}]).validate()


def test_sfx_anchor_rejects_out_of_range_onset_without_silent_fallback(tmp_path):
    from fonesi_edit.render import compile_graph
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    for placement,extra in [
        ('video_end',{'offset':0}),
        ('video_end',{'offset':2}),
        ('percent',{'position_pct':100}),
        ('scene_start',{'scene_index':1,'offset':2}),
        ('scene_end',{'scene_index':1,'offset':2}),
    ]:
        c=Composition(width=320,height=180,fps=25,encoder='cpu',
            clips=[Clip(source,end=1)],audio=[
                {'path':source,'mode':'sfx','placement':placement,**extra}])
        folder=tmp_path/(placement+str(len(extra))+'_'+str(extra.get('offset',0)).replace('-','n'))
        folder.mkdir(exist_ok=True)
        with pytest.raises(ValueError,match='outside the output timeline'):
            compile_graph(c,folder)


def test_exported_sfx_is_audible_only_after_percent_anchor(tmp_path):
    from array import array
    import subprocess
    from fonesi_edit.prototypes.tools import locate_tool
    media=create_fixture(tmp_path/'media',duration=1)
    source=str(media['source'])
    c=Composition(width=320,height=180,fps=25,encoder='cpu',
        clips=[Clip(source,end=1)],mute_original=True,audio=[
            {'path':source,'mode':'sfx','volume':1,'placement':'percent',
             'position_pct':50,'offset':0}])
    out=tmp_path/'sfx-at-half.mp4'
    assert render_composition(c,out)['validated']
    result=subprocess.run([locate_tool('ffmpeg'),'-v','error','-i',str(out),
                           '-vn','-ac','1','-ar','48000','-f','s16le','-'],
                          capture_output=True,check=True)
    samples=array('h');samples.frombytes(result.stdout)
    assert len(samples)>40000
    assert max(abs(value) for value in samples[4800:14400])<20
    assert max(abs(value) for value in samples[30000:42000])>100



@pytest.mark.parametrize('track',[
    {'mode':'music','loop':True,'loop_crossfade':-1},
    {'mode':'music','loop':True,'loop_crossfade':float('nan')},
    {'mode':'music','loop':True,'loop_crossfade':11},
    {'mode':'music','loop':False,'loop_crossfade':.1},
    {'mode':'main','loop':True,'loop_crossfade':.1},
    {'mode':'sfx','loop':True,'loop_crossfade':.1},
])
def test_music_loop_crossfade_invalid_inputs_are_rejected(track):
    comp=Composition(clips=[Clip('unused.mp4',end=1)],
        audio=[{'path':'unused.mp4',**track}])
    with pytest.raises(ValueError,match='crossfade'):
        comp.validate()


def test_music_loop_crossfade_compiles_and_exports_real_audio(tmp_path):
    from pathlib import Path
    from fonesi_edit.render import compile_graph
    source=str(create_fixture(tmp_path/'fixture',duration=.6)['source'])
    comp=Composition(width=320,height=180,fps=25,encoder='cpu',mute_original=True,
        clips=[Clip(source,end=.5) for _ in range(4)],
        audio=[{'path':source,'mode':'music','loop':True,'loop_crossfade':.1,
                'volume':.3,'fade_in':.03,'fade_out':.05}])
    args,graph,total=compile_graph(comp,tmp_path/'stage')
    assert abs(total-2)<.01
    assert 'asplit=' not in graph and graph.count('acrossfade=d=0.1')>=2
    assert args.count(source)>len(comp.clips)+1  # Separate music inputs per repeat
    assert 'adelay=0:all=1' in graph
    assert '-stream_loop' not in args
    result=render_composition(comp,tmp_path/'with-crossfade.mp4')
    assert result['validated']
    media=probe(Path(result['output']))
    assert media.audio_codec is not None and abs(media.duration-2)<.15
    invalid=deepcopy(comp)
    invalid.audio[0]['loop_crossfade']=.35  # Too long for a ~.6 s segment.
    with pytest.raises(ValueError,match='dài hơn hai lần'):
        compile_graph(invalid,tmp_path/'invalid')



@pytest.mark.parametrize('track',[
    {'mode':'sfx','repeat_count':0},
    {'mode':'sfx','repeat_count':33},
    {'mode':'sfx','repeat_count':2.5,'repeat_interval':.1},
    {'mode':'sfx','repeat_count':True},
    {'mode':'sfx','repeat_count':2,'repeat_interval':0},
    {'mode':'sfx','repeat_count':2,'repeat_interval':-1},
    {'mode':'sfx','repeat_count':2,'repeat_interval':float('nan')},
    {'mode':'sfx','repeat_count':1,'repeat_interval':.2},
    {'mode':'music','repeat_count':2,'repeat_interval':.2},
    {'mode':'main','repeat_count':2,'repeat_interval':.2},
    {'mode':'sfx','loop':True,'repeat_count':2,'repeat_interval':.2},
])
def test_repeated_sfx_invalid_configuration_is_rejected(track):
    composition=Composition(clips=[Clip('unused.mp4',end=1)],
        audio=[{'path':'sfx.wav',**track}])
    with pytest.raises(ValueError,match='SFX repeat'):
        composition.validate()


def test_sfx_repeat_anchors_render_two_audible_events_without_leaking_outside(tmp_path):
    from array import array
    import subprocess
    from fonesi_edit.render import compile_graph
    from fonesi_edit.prototypes.tools import locate_tool
    source=str(create_fixture(tmp_path/'media',duration=1)['source'])
    composition=Composition(width=320,height=180,fps=25,encoder='cpu',
        clips=[Clip(source,end=1)],mute_original=True,audio=[{
            'path':source,'mode':'sfx','placement':'percent','position_pct':20,
            'repeat_count':2,'repeat_interval':.4,'trim_end':.12,'volume':1}])
    args,graph,total=compile_graph(composition,tmp_path/'graph')
    assert abs(total-1)<.01
    assert 'adelay=200:all=1' in graph and 'adelay=600:all=1' in graph
    assert 'amix=inputs=2:normalize=0:duration=longest[sfxrepeated0]' in graph
    assert args.count(source)==3  # Video input plus two independent SFX inputs.
    result=render_composition(composition,tmp_path/'two-sfx.mp4')
    assert result['validated']
    decoded=subprocess.run([locate_tool('ffmpeg'),'-v','error',
        '-i',str(tmp_path/'two-sfx.mp4'),'-vn','-ac','1','-ar','48000',
        '-f','s16le','-'],capture_output=True,check=True).stdout
    samples=array('h');samples.frombytes(decoded)
    assert len(samples)>43000
    def peak(start,end):
        return max(abs(sample) for sample in samples[round(start*48000):round(end*48000)])
    assert peak(.05,.12)<20 and peak(.40,.50)<20
    assert peak(.23,.30)>100 and peak(.63,.70)>100
    invalid=deepcopy(composition);invalid.audio[0]['repeat_interval']=.81
    with pytest.raises(ValueError,match='outside the output timeline'):
        compile_graph(invalid,tmp_path/'invalid')

@pytest.mark.parametrize("handle,start,current", [
    ("left_top", (0.2, 0.2), (0.1, 0.1)),
    ("left_bottom", (0.2, 0.4), (0.1, 0.5)),
    ("right_top", (0.6, 0.2), (0.7, 0.1)),
    ("right_bottom", (0.6, 0.4), (0.7, 0.5)),
    ("left", (0.2, 0.3), (0.1, 0.3)),
    ("right", (0.6, 0.3), (0.7, 0.3)),
    ("top", (0.4, 0.2), (0.4, 0.1)),
    ("bottom", (0.4, 0.4), (0.4, 0.5)),
])
def test_crop_drag_ratio_lock_preserves_aspect_for_all_handles(handle, start, current):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    rect = crop_drag_rect((0.2, 0.2, 0.4, 0.2), handle, start, current, ratio_locked=True)
    x, y, width, height = rect
    assert width / height == pytest.approx(2.0)
    assert 0 <= x < 1 and 0 <= y < 1
    assert 0 < width <= 1 and 0 < height <= 1
    assert x + width <= 1.0 + 1e-9
    assert y + height <= 1.0 + 1e-9


@pytest.mark.parametrize("handle,start,current", [
    ("right_bottom", (0.6, 0.4), (1.0, 1.0)),
    ("left_top", (0.2, 0.2), (0.0, 0.0)),
    ("top", (0.4, 0.2), (0.4, 0.0)),
    ("new", (0.8, 0.8), (0.2, 0.2)),
])
def test_crop_ratio_lock_stays_in_bounds_at_canvas_edges(handle, start, current):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    rect = crop_drag_rect((0.2, 0.2, 0.4, 0.2), handle, start, current, ratio_locked=True)
    x, y, width, height = rect
    assert width / height == pytest.approx(2.0)
    assert x >= 0 and y >= 0 and x + width <= 1.0 + 1e-9 and y + height <= 1.0 + 1e-9


def test_crop_drag_free_ratio_keeps_independent_edge_resize_and_move_behavior():
    from fonesi_edit.ui.dialogs import crop_drag_rect
    assert crop_drag_rect((0.2, 0.2, 0.4, 0.2), "right", (0.6, 0.3), (0.7, 0.3)) == pytest.approx(
        (0.2, 0.2, 0.5, 0.2)
    )
    assert crop_drag_rect((0.2, 0.2, 0.4, 0.2), "move", (0.4, 0.3), (0.5, 0.4)) == pytest.approx(
        (0.3, 0.3, 0.4, 0.2)
    )

@pytest.mark.parametrize("handle,start,current,anchor", [
    ("left_top", (0.2, 0.2), (0.1, 0.1), (0.6, 0.4)),
    ("left_bottom", (0.2, 0.4), (0.1, 0.5), (0.6, 0.2)),
    ("right_top", (0.6, 0.2), (0.7, 0.1), (0.2, 0.4)),
    ("right_bottom", (0.6, 0.4), (0.7, 0.5), (0.2, 0.2)),
])
def test_crop_ratio_locked_corner_keeps_opposite_corner_fixed(handle, start, current, anchor):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    x, y, width, height = crop_drag_rect(
        (0.2, 0.2, 0.4, 0.2), handle, start, current, ratio_locked=True
    )
    expected_x, expected_y = anchor
    fixed_x = x + width if "left" in handle else x
    fixed_y = y + height if "top" in handle else y
    assert fixed_x == pytest.approx(expected_x)
    assert fixed_y == pytest.approx(expected_y)


@pytest.mark.parametrize("handle,start,current,anchor", [
    ("left", (0.2, 0.3), (0.1, 0.3), ("right", 0.6)),
    ("right", (0.6, 0.3), (0.7, 0.3), ("left", 0.2)),
    ("top", (0.4, 0.2), (0.4, 0.1), ("bottom", 0.4)),
    ("bottom", (0.4, 0.4), (0.4, 0.5), ("top", 0.2)),
])
def test_crop_ratio_locked_side_keeps_opposite_edge_and_centres_other_axis(handle, start, current, anchor):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    x, y, width, height = crop_drag_rect(
        (0.2, 0.2, 0.4, 0.2), handle, start, current, ratio_locked=True
    )
    edge, value = anchor
    if edge == "right":
        assert x + width == pytest.approx(value)
        assert y + height / 2 == pytest.approx(0.3)
    elif edge == "left":
        assert x == pytest.approx(value)
        assert y + height / 2 == pytest.approx(0.3)
    elif edge == "bottom":
        assert y + height == pytest.approx(value)
        assert x + width / 2 == pytest.approx(0.4)
    else:
        assert y == pytest.approx(value)
        assert x + width / 2 == pytest.approx(0.4)

@pytest.mark.parametrize("handle,start,current", [
    ("left", (.2, .35), (.1, .35)),
    ("right", (.6, .35), (.7, .35)),
    ("top", (.4, .2), (.4, .1)),
    ("bottom", (.4, .5), (.4, .6)),
    ("left_top", (.2, .2), (.1, .1)),
    ("left_bottom", (.2, .5), (.1, .6)),
    ("right_top", (.6, .2), (.7, .1)),
    ("right_bottom", (.6, .5), (.7, .6)),
])
def test_crop_ratio_lock_preserves_normalized_ratio_for_every_handle(handle, start, current):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    initial = (.2, .2, .4, .3)
    result = crop_drag_rect(initial, handle, start, current, ratio_locked=True)
    x, y, width, height = result
    assert width / height == pytest.approx(initial[2] / initial[3], abs=1e-9)
    assert 0 <= x <= 1 and 0 <= y <= 1
    assert 0 < width <= 1 and 0 < height <= 1
    assert x + width <= 1 + 1e-9
    assert y + height <= 1 + 1e-9


@pytest.mark.parametrize("handle,start,current", [
    ("right_bottom", (.9, .9), (1.0, 1.0)),
    ("left_top", (.5, .5), (0.0, 0.0)),
    ("right", (.9, .7), (1.0, .7)),
    ("bottom", (.7, .9), (.7, 1.0)),
])
def test_ratio_locked_crop_handles_clamp_at_source_boundaries(handle, start, current):
    from fonesi_edit.ui.dialogs import crop_drag_rect
    initial = (.5, .5, .4, .4)
    x, y, width, height = crop_drag_rect(
        initial, handle, start, current, ratio_locked=True
    )
    assert x >= 0 and y >= 0 and width > 0 and height > 0
    assert x + width <= 1 + 1e-9 and y + height <= 1 + 1e-9
    assert width / height == pytest.approx(initial[2] / initial[3], abs=1e-9)


def test_free_ratio_crop_edge_resize_keeps_orthogonal_dimension():
    from fonesi_edit.ui.dialogs import crop_drag_rect
    initial = (.2, .2, .4, .3)
    x, y, width, height = crop_drag_rect(
        initial, "right", (.6, .35), (.7, .35), ratio_locked=False
    )
    assert x == pytest.approx(.2)
    assert y == pytest.approx(.2)
    assert width == pytest.approx(.5)
    assert height == pytest.approx(.3)

