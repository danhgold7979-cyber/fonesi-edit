import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
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
