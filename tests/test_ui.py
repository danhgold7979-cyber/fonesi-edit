from pathlib import Path
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from fonesi_edit.core.model import Project,Layer,CommandHistory,US
from fonesi_edit.ui.canvas import Canvas
from fonesi_edit.ui.window import MainWindow


def test_canvas_drag_one_undo_zoom_and_cancel(qapp):
    p=Project(width=320,height=180,layers=[Layer(x=.2,y=.2,width=.3,height=.3,text='test',end=US,style={'font_size':16,'overflow':'shrink'})]);h=CommandHistory(p)
    w=Canvas(p,h);w.resize(680,400);w.show();qapp.processEvents();rect,scale=w.viewport()
    center=QPoint(round(rect.x()+.3*320*scale),round(rect.y()+.3*180*scale))
    QTest.mousePress(w,Qt.MouseButton.LeftButton,pos=center);QTest.mouseMove(w,center+QPoint(40,20));QTest.mouseRelease(w,Qt.MouseButton.LeftButton,pos=center+QPoint(40,20))
    assert len(h.undo_items)==1;assert p.layers[0].x>.2
    old=p.layers[0].x;w.zoom=2;w.update();qapp.processEvents();assert p.layers[0].x==old
    h.undo();assert p.layers[0].x==.2
    w.close()


def test_canvas_locked_and_delete_only_object(qapp,tmp_path):
    file=tmp_path/'logo.png';file.write_bytes(b'preserved')
    p=Project(layers=[Layer(locked=True,asset_path=str(file))]);h=CommandHistory(p);w=Canvas(p,h);w.show();w.selection={p.layers[0].id}
    QTest.keyClick(w,Qt.Key.Key_Delete);assert len(p.layers)==1
    p.layers[0].locked=False;QTest.keyClick(w,Qt.Key.Key_Delete);assert not p.layers;assert file.read_bytes()==b'preserved';w.close()


def test_window_eight_tabs_autosave_and_text_focus(qapp,tmp_path,monkeypatch):
    monkeypatch.setattr(MainWindow,'scan_tools_async',lambda self:None)
    w=MainWindow(tmp_path);w.show();qapp.processEvents();assert w.tabs.count()==8
    w.editor.add_text();w.editor.canvas.selection={w.project.layers[0].id};w.editor.refresh();w.editor.text.setFocus();w.editor.text.setText('Tiếng Việt 中文')
    QTest.keyClick(w.editor.text,Qt.Key.Key_Space);assert len(w.project.layers)==1
    w.autosave_now();assert (tmp_path/'recovery.json').exists();w.close();qapp.processEvents()
