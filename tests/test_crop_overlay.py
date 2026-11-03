"""Interactive normalized crop overlay geometry; no crop renderer is implied."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import Qt, QPoint, QCoreApplication, QEvent
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtTest import QTest

from fonesi_edit.ui.timeline import CropEditorView


def _view(qt_app):
    view=CropEditorView()
    view.resize(500,300)
    pixmap=QPixmap(400,200);pixmap.fill(QColor('#808080'))
    view.setPixmap(pixmap)
    view.set_crop({'left':[1,5],'top':[1,5],'width':[2,5],'height':[2,5]})
    view.set_editing(True)
    view.show();qt_app.processEvents()
    return view


def test_crop_overlay_move_is_normalized_and_staged(qt_app):
    view=_view(qt_app);changes=[]
    view.crop_changed.connect(changes.append)
    rect=view._crop_rect();center=rect.center()
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    QTest.mouseMove(view,QPoint(round(center.x()+24),round(center.y()+12)))
    QTest.mouseRelease(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()+24),round(center.y()+12)))
    assert len(changes)==1
    assert abs(changes[0]['left']-.25)<.01
    assert abs(changes[0]['top']-.25)<.01
    assert changes[0]['width']==.4 and changes[0]['height']==.4
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)


def test_crop_overlay_corner_resize_respects_locked_ratio(qt_app):
    view=_view(qt_app);view.set_ratio_locked(True)
    changes=[];view.crop_changed.connect(changes.append)
    rect=view._crop_rect();handle=view._handles(rect)['se']
    start=QPoint(round(handle.x()),round(handle.y()))
    end=QPoint(start.x()+24,start.y()+12)
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=start)
    QTest.mouseMove(view,end)
    QTest.mouseRelease(view,Qt.MouseButton.LeftButton,pos=end)
    assert len(changes)==1
    assert abs(changes[0]['width']-changes[0]['height'])<1e-9
    assert abs(changes[0]['width']-.45)<.02
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)


def test_crop_overlay_clamps_move_to_source_frame(qt_app):
    view=_view(qt_app);changes=[];view.crop_changed.connect(changes.append)
    rect=view._crop_rect();center=rect.center()
    end=QPoint(round(view._image_rect.right()+100),round(view._image_rect.bottom()+100))
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    QTest.mouseMove(view,end)
    QTest.mouseRelease(view,Qt.MouseButton.LeftButton,pos=end)
    assert len(changes)==1
    crop=changes[0]
    assert crop['left']>=0 and crop['top']>=0
    assert crop['left']+crop['width']<=1+1e-9
    assert crop['top']+crop['height']<=1+1e-9
    assert crop['width']>0 and crop['height']>0
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)


def test_crop_overlay_escape_cancels_active_drag_without_emitting(qt_app):
    view=_view(qt_app);changes=[];view.crop_changed.connect(changes.append)
    original=dict(view.crop)
    rect=view._crop_rect();center=rect.center()
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    QTest.mouseMove(view,QPoint(round(center.x()+30),round(center.y()+15)))
    assert view.crop!=original
    QTest.keyClick(view,Qt.Key.Key_Escape)
    assert view.crop==original
    assert changes==[]
    assert view._active_handle is None and view._start_crop is None
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)


def test_disabling_crop_edit_cancels_pointer_gesture(qt_app):
    view=_view(qt_app);changes=[];view.crop_changed.connect(changes.append)
    original=dict(view.crop)
    rect=view._crop_rect();center=rect.center()
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    QTest.mouseMove(view,QPoint(round(center.x()+30),round(center.y()+15)))
    assert view.crop!=original
    view.set_editing(False)
    assert view.crop==original
    QTest.mouseRelease(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()+30),round(center.y()+15)))
    assert changes==[]
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)


def test_crop_overlay_click_without_drag_is_a_noop(qt_app):
    view=_view(qt_app);changes=[];view.crop_changed.connect(changes.append)
    rect=view._crop_rect();center=rect.center()
    QTest.mousePress(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    QTest.mouseRelease(view,Qt.MouseButton.LeftButton,pos=QPoint(round(center.x()),round(center.y())))
    assert changes==[]
    assert view.crop=={'left':.2,'top':.2,'width':.4,'height':.4}
    view.close();view.deleteLater();QCoreApplication.sendPostedEvents(view,QEvent.Type.DeferredDelete)
