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

def test_peer_snap_aligns_edges_and_centres_within_tolerance():
    from fonesi_edit.ui.canvas import snap_layer_to_peers
    peers = [(0.4, 0.4, 0.2, 0.2)]
    # Moving left edge aligns to peer right edge; moving bottom aligns to peer top.
    assert snap_layer_to_peers(.603, .303, .1, .1, peers) == pytest.approx((.6, .3))
    # Moving centre aligns to peer centre on both axes.
    assert snap_layer_to_peers(.442, .442, .1, .1, peers) == pytest.approx((.45, .45))


def test_peer_snap_respects_tolerance_and_alt_override():
    from fonesi_edit.ui.canvas import snap_layer_to_peers
    peers = [(0.4, 0.4, 0.2, 0.2)]
    assert snap_layer_to_peers(.625, .625, .1, .1, peers) == (.625, .625)
    assert snap_layer_to_peers(.603, .303, .1, .1, peers, enabled=False) == (.603, .303)


def test_peer_snap_rejects_nonfinite_geometry_and_ignores_out_of_canvas_peers():
    from fonesi_edit.ui.canvas import snap_layer_to_peers
    with pytest.raises(ValueError, match="finite"):
        snap_layer_to_peers(float("nan"), .2, .1, .1, [])
    assert snap_layer_to_peers(.603, .303, .1, .1, [(1.2, .4, .2, .2)]) == (.603, .303)

def test_peer_snap_reports_visible_guide_coordinates():
    from fonesi_edit.ui.canvas import snap_layer_to_peers_with_guides
    peers = [(0.4, 0.4, 0.2, 0.2)]
    x, y, vertical, horizontal = snap_layer_to_peers_with_guides(
        .603, .303, .1, .1, peers
    )
    assert (x, y, vertical, horizontal) == pytest.approx((.6, .3, .6, .4))
    x, y, vertical, horizontal = snap_layer_to_peers_with_guides(
        .442, .442, .1, .1, peers
    )
    assert (x, y, vertical, horizontal) == pytest.approx((.45, .45, .5, .5))


def test_peer_snap_guides_are_absent_when_no_snap_occurs_or_alt_is_held():
    from fonesi_edit.ui.canvas import snap_layer_to_peers_with_guides
    peers = [(0.4, 0.4, 0.2, 0.2)]
    assert snap_layer_to_peers_with_guides(.625, .625, .1, .1, peers) == (
        .625, .625, None, None
    )
    x, y, vertical, horizontal = snap_layer_to_peers_with_guides(
        .603, .303, .1, .1, peers, enabled=False
    )
    assert (x, y) == pytest.approx((.603, .303))
    assert vertical is None and horizontal is None


def test_canvas_clears_peer_guides_when_rebuilt():
    host = Host()
    editor = Editor(host)
    try:
        editor.canvas.set_peer_snap_guides(.5, .4)
        assert editor.canvas._peer_snap_guides == (.5, .4)
        editor.canvas.rebuild()
        assert editor.canvas._peer_snap_guides == (None, None)
    finally:
        editor.close()
        host.workspace.cleanup()

def test_layer_clipboard_paste_remaps_ids_and_groups_and_supports_undo_redo():
    host = Host()
    editor = Editor(host)
    try:
        first = Layer(text="A", x=.1, group="shared", clip_ids=["clip-a"],
                      style={"font_family": "Arial", "color": "#fefefe"},
                      keyframes={"x": [{"time": 0, "value": .1}]})
        second = Layer(text="B", x=.3, group="shared", clip_ids=["clip-a"],
                       style={"font_family": "Arial", "color": "#ff0000"},
                       keyframes={"x": [{"time": 0, "value": .3}]})
        unrelated = Layer(text="Unrelated", x=.7, group="unrelated")
        editor.set_composition(Composition(clips=[Clip('unused.mp4', id='clip-a')], layers=[first, second, unrelated]))
        editor.select_ids([first.id, second.id])
        editor.copy_layers()
        editor.paste_layers()

        assert len(editor.composition.layers) == 5
        pasted = editor.composition.layers[3:]
        assert all(layer.id not in {first.id, second.id, unrelated.id} for layer in pasted)
        assert pasted[0].group == pasted[1].group
        assert pasted[0].group != "shared"
        assert editor.composition.layers[2].group == "unrelated"
        assert [layer.clip_ids for layer in pasted] == [["clip-a"], ["clip-a"]]
        assert pasted[0].style == first.style and pasted[1].style == second.style
        assert pasted[0].keyframes == first.keyframes and pasted[1].keyframes == second.keyframes
        assert pasted[0].x == pytest.approx(.12)
        assert pasted[1].x == pytest.approx(.32)
        assert editor.undo.count() == 1

        editor.undo.undo()
        assert len(editor.composition.layers) == 3
        editor.undo.redo()
        assert len(editor.composition.layers) == 5
    finally:
        editor.close()
        host.workspace.cleanup()


def test_cut_layer_copies_only_unlocked_layers_and_undo_restores_them():
    host = Host()
    editor = Editor(host)
    try:
        editable = Layer(text="Editable")
        locked = Layer(text="Locked", locked=True)
        editor.set_composition(Composition(layers=[editable, locked]))
        editor.select_ids([editable.id, locked.id])
        editor.cut_layers()
        assert [layer.id for layer in editor.composition.layers] == [locked.id]
        assert [layer.text for layer in editor._layer_clipboard] == ["Editable"]
        assert editor.undo.count() == 1
        editor.undo.undo()
        assert {layer.id for layer in editor.composition.layers} == {editable.id, locked.id}
        editor.undo.redo()
        assert [layer.id for layer in editor.composition.layers] == [locked.id]
    finally:
        editor.close()
        host.workspace.cleanup()


def test_select_all_layers_selects_every_layer_in_canvas():
    host = Host()
    editor = Editor(host)
    try:
        layers = [Layer(text="A"), Layer(text="B", locked=True)]
        editor.set_composition(Composition(layers=layers))
        editor.select_all_layers()
        assert editor.selected_ids == {layer.id for layer in layers}
        assert len(editor.selected_layers()) == 2
    finally:
        editor.close()
        host.workspace.cleanup()

def test_escape_cancels_canvas_drag_and_mouse_release_does_not_commit():
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt, QPoint, QPointF
    host = Host()
    editor = Editor(host)
    try:
        layer = Layer(x=.1, y=.2, width=.2, height=.15)
        editor.set_composition(Composition(layers=[layer]))
        editor.select_id(layer.id)
        editor.resize(1300, 850)
        editor.show()
        editor.canvas.setFocus()
        APP.processEvents()

        start = editor.canvas.mapFromScene(QPointF(.17 * 1280, .27 * 720))
        end = start + QPoint(55, 30)
        QTest.mousePress(editor.canvas.viewport(), Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, start)
        QTest.mouseMove(editor.canvas.viewport(), end, 20)
        APP.processEvents()
        assert editor.composition.layers[0].x > .1

        QTest.keyClick(editor.canvas, Qt.Key.Key_Escape)
        APP.processEvents()
        QTest.mouseRelease(editor.canvas.viewport(), Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier, end)
        APP.processEvents()

        assert editor.composition.layers[0].x == pytest.approx(.1)
        assert editor.composition.layers[0].y == pytest.approx(.2)
        assert editor.undo.count() == 0
    finally:
        editor.close()
        host.workspace.cleanup()

def test_paste_layer_clamps_offset_to_canvas_bounds():
    host = Host()
    editor = Editor(host)
    try:
        edge = Layer(text="Edge", x=.69, y=.84, width=.3, height=.15)
        editor.set_composition(Composition(layers=[edge]))
        editor.select_id(edge.id)
        editor.copy_layers()
        editor.paste_layers()
        pasted = editor.composition.layers[-1]
        assert pasted.x == pytest.approx(.7)
        assert pasted.y == pytest.approx(.85)
        assert pasted.x + pasted.width <= 1.0 + 1e-9
        assert pasted.y + pasted.height <= 1.0 + 1e-9
    finally:
        editor.close()
        host.workspace.cleanup()

@pytest.mark.parametrize("step,x0,y0,expected", [
    (.05, .101, .301, (.1, .3)),
    (.1, .101, .301, (.1, .3)),
    (.2, .199, .399, (.2, .4)),
])
def test_canvas_grid_snap_uses_selected_spacing(step, x0, y0, expected):
    from fonesi_edit.ui.canvas import snap_layer_position
    x, y = snap_layer_position(x0, y0, .1, .1, grid=True, grid_step=step)
    assert (x, y) == pytest.approx(expected)


@pytest.mark.parametrize("step", [0, -0.1, .005, .75, 1.1, float("nan"), True])
def test_canvas_grid_snap_rejects_invalid_spacing(step):
    from fonesi_edit.ui.canvas import snap_layer_position
    with pytest.raises(ValueError, match="Grid spacing"):
        snap_layer_position(.1, .1, .2, .2, grid=True, grid_step=step)


def test_canvas_grid_spacing_is_saved_undoable_and_falls_back_for_unknown_values():
    host = Host()
    editor = Editor(host)
    try:
        assert editor.composition.adjustments.get("canvas_grid_spacing", .05) == .05
        editor.set_canvas_grid_spacing(.2)
        assert editor.composition.adjustments["canvas_grid_spacing"] == .2
        serialized = editor.composition.to_dict()
        assert Composition.from_dict(serialized).adjustments["canvas_grid_spacing"] == .2
        editor.undo.undo()
        assert editor.composition.adjustments.get("canvas_grid_spacing", .05) == .05
        editor.composition.adjustments["canvas_grid_spacing"] = .75
        editor.refresh()
        assert all(
            action.isChecked() == (value == .05)
            for value, action in editor.grid_spacing_actions.items()
        )
    finally:
        editor.close()
        host.workspace.cleanup()

def test_custom_canvas_grid_spacing_aligns_snap_to_exact_step():
    from fonesi_edit.ui.canvas import snap_layer_position
    x, y = snap_layer_position(.071, .141, .1, .1, grid=True, grid_step=.07)
    assert (x, y) == pytest.approx((.07, .14))


def test_custom_canvas_grid_spacing_is_persisted_and_shown_in_menu():
    host = Host()
    editor = Editor(host)
    try:
        editor.set_canvas_grid_spacing(.07)
        assert editor.composition.adjustments["canvas_grid_spacing"] == pytest.approx(.07)
        assert editor.grid_spacing_custom_action.text() == "Tùy chỉnh (7%)"
        assert not any(action.isChecked() for action in editor.grid_spacing_actions.values())
        serialized = editor.composition.to_dict()
        assert Composition.from_dict(serialized).adjustments["canvas_grid_spacing"] == pytest.approx(.07)
        editor.undo.undo()
        assert editor.composition.adjustments.get("canvas_grid_spacing", .05) == .05
        assert editor.grid_spacing_actions[.05].isChecked()
    finally:
        editor.close()
        host.workspace.cleanup()


def test_custom_canvas_grid_spacing_rejects_out_of_range_values():
    host = Host()
    editor = Editor(host)
    try:
        editor.set_canvas_grid_spacing(.75)
        assert editor.composition.adjustments.get("canvas_grid_spacing", .05) == .05
        assert any("1–50%" in message for message in host.errors)
    finally:
        editor.close()
        host.workspace.cleanup()

def test_inspector_property_search_filters_rows_case_insensitively_without_project_mutation():
    host = Host()
    editor = Editor(host)
    try:
        editor.add_layer('text')
        before = editor.composition.to_dict()
        editor.property_search.setText("FONT")
        font_row, _ = editor.field_forms["style.font_family"].getWidgetPosition(
            editor.fields["style.font_family"][0]
        )
        x_row, _ = editor.field_forms["x"].getWidgetPosition(editor.fields["x"][0])
        assert editor.field_forms["style.font_family"].isRowVisible(font_row)
        assert not editor.field_forms["x"].isRowVisible(x_row)
        assert editor.composition.to_dict() == before
        editor.property_search.clear()
        assert editor.field_forms["x"].isRowVisible(x_row)
        assert editor.composition.to_dict() == before
    finally:
        editor.close()
        host.workspace.cleanup()


def test_reset_layer_properties_preserves_identity_content_and_is_one_undo_step():
    from fonesi_edit.domain import Layer
    host = Host()
    editor = Editor(host)
    try:
        layer = Layer(
            kind="text", name="Custom title", text="Keep this text",
            x=.4, y=.3, width=.6, height=.2, rotation=45, opacity=.4,
            style={"font_size": 48, "color": "#ff0000", "outline": 4},
            motion={"preset": "zoom", "zoom_min": .5, "zoom_max": 2},
            keyframes={"x": [{"time": 0.0, "value": .4}]},
            group="group-keep", clip_ids=["clip-keep"],
        )
        editor.composition.layers.append(layer)
        editor.selected_id = layer.id
        editor.selected_ids = {layer.id}
        editor.refresh()
        editor.undo.clear()
        editor.reset_layer_properties()
        restored = editor.layer()
        assert restored is not None
        assert restored.id == layer.id
        assert restored.name == "Custom title"
        assert restored.text == "Keep this text"
        assert restored.path is None
        assert restored.group == "group-keep"
        assert restored.clip_ids == ["clip-keep"]
        assert (restored.x, restored.y, restored.width, restored.height, restored.rotation, restored.opacity) == pytest.approx((.05, .08, .3, .1, 0, 1))
        assert restored.style == {"font_size": 32, "color": "#ffffff", "outline": 2, "outline_color": "#000000"}
        assert restored.motion == {"preset": "fixed", "speed": 20, "duration": 5, "delay": 0, "repeat": True, "easing": "linear"}
        assert restored.keyframes == {}
        assert editor.undo.count() == 1
        editor.undo.undo()
        restored = editor.layer()
        assert restored.rotation == 45
        assert restored.text == "Keep this text"
        assert restored.keyframes["x"][0]["value"] == .4
        editor.undo.redo()
        assert editor.layer().rotation == 0
    finally:
        editor.close()
        host.workspace.cleanup()


def test_reset_layer_properties_requires_unlocked_selected_layer():
    from fonesi_edit.domain import Layer
    host = Host()
    editor = Editor(host)
    try:
        layer = Layer(kind="text", locked=True, rotation=45)
        editor.composition.layers.append(layer)
        editor.selected_id = layer.id
        editor.refresh()
        editor.undo.clear()
        editor.reset_layer_properties()
        assert editor.layer().rotation == 45
        assert editor.undo.count() == 0
        assert any("mở khóa" in message for message in host.errors)
    finally:
        editor.close()
        host.workspace.cleanup()

