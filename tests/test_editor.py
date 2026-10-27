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
