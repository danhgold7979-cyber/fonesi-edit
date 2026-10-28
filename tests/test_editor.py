import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from fonesi_edit.domain import Clip,Layer,Composition
from fonesi_edit.ui.editor import Editor

APP=QApplication.instance() or QApplication([])


class Host:
    def __init__(self):self.workspace=TemporaryDirectory();self.errors=[]
    def message(self,message):self.errors.append(message)


def test_layer_inspector_undo_redo_and_snapshot_roundtrip():
    host=Host();editor=Editor(host)
    editor.add_layer('text');layer=editor.layer()
    assert layer is not None
    editor.fields['text'][0].setText('Tiếng Việt 中文')
    editor.field_changed('text')
    assert editor.layer().text=='Tiếng Việt 中文'
    editor.undo.undo();assert editor.layer().text=='Fonesi Edit'
    editor.undo.redo();assert editor.layer().text=='Tiếng Việt 中文'
    editor.duplicate();assert len(editor.composition.layers)==2
    editor.delete_layer();assert len(editor.composition.layers)==1
    assert Composition.from_dict(editor.composition.to_dict()).to_dict()==editor.composition.to_dict()
    editor.close();host.workspace.cleanup()


def test_split_preserves_source_time_and_undo():
    host=Host();editor=Editor(host)
    editor.set_composition(Composition(clips=[Clip('fixture.mp4',start=1,end=5,speed=2,source_duration=6)]))
    editor.timeline.playhead=1
    editor.split()
    left,right=editor.composition.clips
    assert left.end==3 and right.start==3 and right.end==5 and right.offset==1
    editor.undo.undo();assert len(editor.composition.clips)==1
    editor.close();host.workspace.cleanup()


def test_multi_layer_group_alignment_lock_and_undo_are_atomic():
    host=Host();editor=Editor(host)
    editor.set_composition(Composition(layers=[Layer(x=.1),Layer(x=.2),Layer(x=.8,locked=True)]))
    ids=[l.id for l in editor.composition.layers];editor.select_ids(ids);editor.group()
    a,b,locked=editor.composition.layers
    assert a.group==b.group and a.group and locked.group is None
    editor.align('x');assert editor.composition.layers[0].x==.35 and editor.composition.layers[-1].x==.8
    editor.undo.undo();assert editor.composition.layers[0].x==.1
    editor.select_ids(ids);editor.delete_layer();assert len(editor.composition.layers)==1 and editor.composition.layers[0].locked
    editor.undo.undo();assert len(editor.composition.layers)==3
    editor.close();host.workspace.cleanup()


def test_split_keeps_subtitle_scope_and_in_out_use_source_time():
    host=Host();editor=Editor(host);clip=Clip('source.mp4',start=1,end=5,speed=2,source_duration=5)
    editor.set_composition(Composition(clips=[clip],layers=[Layer(kind='subtitle',path='sub.srt',clip_ids=[clip.id])]))
    editor.timeline.playhead=1;editor.split()
    assert set(editor.composition.layers[0].clip_ids)=={c.id for c in editor.composition.clips}
    editor.in_point=.25;editor.out_point=.75;editor.trim_in_out();left=editor.composition.clips[0]
    assert left.start==1.5 and left.end==2.5
    editor.undo.undo();assert editor.composition.clips[0].start==1
    editor.close();host.workspace.cleanup()


def test_mouse_drag_on_preview_updates_model_and_has_one_undo_step():
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt,QPointF,QPoint
    host=Host();editor=Editor(host);layer=Layer(x=.1,y=.2,width=.2,height=.15)
    editor.set_composition(Composition(layers=[layer]));editor.select_id(layer.id);editor.resize(1300,850);editor.show();APP.processEvents()
    start=editor.canvas.mapFromScene(QPointF(.17*1280,.27*720));end=start+QPoint(55,30)
    QTest.mousePress(editor.canvas.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,start)
    QTest.mouseMove(editor.canvas.viewport(),end,20)
    QTest.mouseRelease(editor.canvas.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,end);APP.processEvents()
    assert editor.composition.layers[0].x>.1 and editor.undo.count()==1
    editor.undo.undo();assert editor.composition.layers[0].x==.1
    editor.close();host.workspace.cleanup()


def test_canvas_snap_uses_layer_centre_and_supports_alt_override():
    from fonesi_edit.ui.canvas import snap_layer_position
    x, y = snap_layer_position(.396, .405, .2, .2)
    assert abs(x-.4)<1e-9 and abs(y-.4)<1e-9
    # Top-left at .5 is not a centred .2-wide layer: no false snap.
    x, y = snap_layer_position(.488, .4, .2, .2)
    assert abs(x-.488)<1e-9
    assert snap_layer_position(.396,.405,.2,.2,enabled=False)==(.396,.405)
    assert snap_layer_position(.054,.749,.2,.2)==(.05,.75)
    # The grid snaps on the same normalized basis as canvas coordinates.
    grid_x, grid_y = snap_layer_position(.101,.301,.2,.2,grid=True)
    assert abs(grid_x-.1)<1e-9 and abs(grid_y-.3)<1e-9


def test_group_translation_clamps_original_union_not_member_positions():
    from fonesi_edit.ui.canvas import constrained_group_delta
    bounds=[(.1,.2,.2,.15),(.65,.6,.3,.2)]
    dx,dy=constrained_group_delta(bounds,.4,.4)
    assert abs(dx-.05)<1e-9 and abs(dy-.2)<1e-9
    moved=[(x+dx,y+dy,w,h) for x,y,w,h in bounds]
    assert abs(moved[1][0]-moved[0][0]-.55)<1e-9
    assert max(x+w for x,y,w,h in moved)<=1
    assert max(y+h for x,y,w,h in moved)<=1
    assert constrained_group_delta(bounds,-.5,-.5)==(-.1,-.2)


def test_canvas_grid_is_view_only_project_persistent_and_undoable():
    from PySide6.QtWidgets import QGraphicsLineItem
    host=Host();editor=Editor(host)
    try:
        assert not editor.composition.adjustments.get('canvas_grid')
        editor.set_canvas_grid(True)
        assert editor.grid_action.isChecked()
        assert editor.composition.adjustments['canvas_grid'] is True
        assert len([item for item in editor.canvas.scene().items()
                    if isinstance(item,QGraphicsLineItem)])==38
        serialized=editor.composition.to_dict()
        assert Composition.from_dict(serialized).adjustments['canvas_grid'] is True
        editor.undo.undo()
        assert not editor.grid_action.isChecked()
        assert not editor.composition.adjustments.get('canvas_grid')
        assert editor.undo.count()==1
        editor.undo.redo()
        assert editor.grid_action.isChecked()
    finally:
        editor.close();host.workspace.cleanup()


def test_multiselection_drag_preserves_offsets_and_has_one_undo():
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPointF,QPoint,Qt
    host=Host();editor=Editor(host)
    first=Layer(x=.1,y=.2,width=.2,height=.15)
    second=Layer(x=.4,y=.3,width=.2,height=.15)
    try:
        editor.set_composition(Composition(layers=[first,second]))
        editor.select_ids([first.id,second.id])
        editor.canvas.rebuild()
        editor.resize(1300,850);editor.show();APP.processEvents()
        start=editor.canvas.mapFromScene(QPointF(.16*1280,.27*720))
        destination=start+QPoint(50,23)
        QTest.mousePress(editor.canvas.viewport(),Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier,start)
        QTest.mouseMove(editor.canvas.viewport(),destination,20)
        QTest.mouseRelease(editor.canvas.viewport(),Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier,destination)
        APP.processEvents()
        a,b=editor.composition.layers
        assert a.x>.1 and b.x>.4
        assert abs((b.x-a.x)-.3)<1e-9
        assert abs((b.y-a.y)-.1)<1e-9
        assert editor.undo.count()==1
        editor.undo.undo()
        a,b=editor.composition.layers
        assert abs(a.x-.1)<1e-9 and abs(b.x-.4)<1e-9
    finally:
        editor.close();host.workspace.cleanup()


def test_rendered_preview_loop_requires_valid_in_out_and_matching_composition():
    from fonesi_edit.ui.editor import loop_seek_target
    assert loop_seek_target(1200,.5,1.2,enabled=True,verified=True)==500
    assert loop_seek_target(1100,.5,1.2,enabled=True,verified=True) is None
    for kwargs in ({'enabled':False,'verified':True},
                   {'enabled':True,'verified':False}):
        assert loop_seek_target(1200,.5,1.2,**kwargs) is None
    for start,end in ((None,1.2),(1,1),(1.2,.5),(-1,1),(0,float('nan')),(0,.01)):
        assert loop_seek_target(2000,start,end,enabled=True,verified=True) is None


def test_loop_action_validates_range_and_is_invalidated_by_composition_edit():
    from fonesi_edit.domain import canonical
    host=Host();editor=Editor(host)
    try:
        editor.set_composition(Composition(clips=[Clip('fixture.mp4',end=4)]))
        editor.loop_action.setChecked(True)
        assert not editor.loop_action.isChecked()
        assert any('In và Out' in error for error in host.errors)
        editor.in_point=.25;editor.out_point=1.75
        editor.preview_fingerprint=canonical(editor.composition.to_dict())
        editor.loop_action.setChecked(True)
        assert editor.loop_action.isChecked()
        editor.set_composition(Composition(clips=[Clip('different.mp4',end=3)]))
        assert editor.preview_fingerprint is None
        editor.out_point=10
        editor.loop_action.setChecked(False)
        editor.loop_action.setChecked(True)
        assert not editor.loop_action.isChecked()
        assert any('vượt thời lượng' in error for error in host.errors)
    finally:
        editor.close();host.workspace.cleanup()


def test_timeline_thumbnail_toggle_is_undoable_and_displays_verified_cached_frames(tmp_path):
    from fonesi_edit.prototypes.media import create_fixture
    from fonesi_edit.thumbnails import thumbnail_strip
    from fonesi_edit.ui.timeline import Segment
    host=Host();editor=Editor(host)
    media=create_fixture(tmp_path/'source',duration=.5)
    clip=Clip(str(media['source']),end=.5,source_duration=.5)
    try:
        editor.set_composition(Composition(clips=[clip]))
        assert editor.clips.currentRow()==0
        assert editor.thumbnail_assets(clip)==[]
        assert not editor.thumbnail_action.isChecked()
        editor.thumbnail_action.setChecked(True)
        assert editor.composition.adjustments['timeline_thumbnails'] is True
        assert editor.undo.count()==1
        tiles=thumbnail_strip(clip,tmp_path/'cache')
        editor.thumbnails[clip.id]=tiles
        editor.timeline.rebuild()
        segments=[item for item in editor.timeline.scene().items()
                  if isinstance(item,Segment) and item.is_clip]
        assert len(segments)==1 and len(segments[0].thumbnail_pixmaps)==3
        editor.undo.undo()
        assert editor.composition.adjustments.get('timeline_thumbnails') is None
        assert not editor.thumbnail_action.isChecked()
        editor.timeline.rebuild()
        segment=next(item for item in editor.timeline.scene().items()
                     if isinstance(item,Segment) and item.is_clip)
        assert not segment.thumbnail_pixmaps
        editor.undo.redo()
        assert editor.thumbnail_action.isChecked()
        assert editor.thumbnail_assets(editor.composition.clips[0])==tiles['frames']
    finally:
        editor.close();host.workspace.cleanup()



def test_anchor_group_delta_supports_all_nine_safe_positions():
    from fonesi_edit.ui.canvas import anchor_group_delta

    rectangles = [(.2, .2, .2, .1), (.5, .4, .2, .2)]
    horizontal_targets = {'left': .05, 'center': .25, 'right': .45}
    vertical_targets = {'top': .05, 'center': .3, 'bottom': .55}
    for horizontal, target_x in horizontal_targets.items():
        for vertical, target_y in vertical_targets.items():
            dx, dy = anchor_group_delta(rectangles, horizontal, vertical)
            assert abs((.2 + dx) - target_x) < 1e-9
            assert abs((.2 + dy) - target_y) < 1e-9


def test_anchor_group_delta_handles_large_groups_and_invalid_inputs():
    from fonesi_edit.ui.canvas import anchor_group_delta

    # The 5% margin shrinks to 2.5% when a 95%-wide group still fits.
    dx, dy = anchor_group_delta([(0, 0, .95, .5)], 'right', 'bottom')
    assert abs(dx - .025) < 1e-9
    assert abs(dy - .45) < 1e-9
    assert anchor_group_delta([(0, 0, 1.01, .5)], 'center', 'center') is None
    with pytest.raises(ValueError):
        anchor_group_delta([(0, 0, .2, .2)], 'outside', 'center')
    with pytest.raises(ValueError):
        anchor_group_delta([(0, 0, float('nan'), .2)], 'left', 'top')


def test_nine_point_anchor_moves_group_atomically_and_respects_locked_layers():
    host = Host()
    editor = Editor(host)
    first = Layer(x=.2, y=.3, width=.1, height=.1, group='pair')
    second = Layer(x=.4, y=.5, width=.2, height=.1, group='pair')
    locked = Layer(x=.8, y=.8, width=.1, height=.1, group='pair', locked=True)
    unrelated = Layer(x=.1, y=.1, width=.1, height=.1)
    try:
        editor.set_composition(Composition(layers=[first, second, locked, unrelated]))
        editor.select_id(first.id)
        editor.anchor_selected('right', 'bottom')
        by_id = {layer.id: layer for layer in editor.composition.layers}
        assert abs(by_id[first.id].x - .55) < 1e-9
        assert abs(by_id[first.id].y - .65) < 1e-9
        assert abs(by_id[second.id].x - .75) < 1e-9
        assert abs(by_id[second.id].y - .85) < 1e-9
        assert (by_id[locked.id].x, by_id[locked.id].y) == (.8, .8)
        assert (by_id[unrelated.id].x, by_id[unrelated.id].y) == (.1, .1)
        assert abs((by_id[second.id].x - by_id[first.id].x) - .2) < 1e-9
        assert editor.undo.count() == 1

        editor.undo.undo()
        by_id = {layer.id: layer for layer in editor.composition.layers}
        assert abs(by_id[first.id].x - .2) < 1e-9
        assert abs(by_id[second.id].y - .5) < 1e-9
        editor.undo.redo()
        by_id = {layer.id: layer for layer in editor.composition.layers}
        assert abs(by_id[first.id].x - .55) < 1e-9
        assert abs(by_id[second.id].y - .85) < 1e-9
    finally:
        editor.close()
        host.workspace.cleanup()
