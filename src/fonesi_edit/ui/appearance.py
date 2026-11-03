"""Persistent user appearance preferences; never stored in project files."""
from dataclasses import dataclass

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QFontDatabase, QPalette
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLabel,
    QComboBox, QPushButton,
)


THEMES=("system","light","dark")
FONT_SIZES=(9,10,11,12,14,16)
ZOOM_LEVELS=(100,110,125,150)


@dataclass(frozen=True)
class AppearancePreferences:
    theme: str="system"
    font_size_pt: int=10
    zoom_percent: int=100


class AppearanceSettingsError(ValueError):
    pass


class AppearanceSettingsStore:
    """Allow-listed QSettings persistence isolated to the appearance group."""
    def __init__(self,settings):
        self.settings=settings

    @staticmethod
    def _integer(value,default):
        try:
            return int(value)
        except (TypeError,ValueError,OverflowError):
            return default

    def load(self):
        theme=self.settings.value("appearance/theme","system")
        if not isinstance(theme,str) or theme not in THEMES:
            theme="system"
        font_size=self._integer(self.settings.value("appearance/font_size_pt",10),10)
        if font_size not in FONT_SIZES:
            font_size=10
        zoom=self._integer(self.settings.value("appearance/zoom_percent",100),100)
        if zoom not in ZOOM_LEVELS:
            zoom=100
        return AppearancePreferences(theme,font_size,zoom)

    def save(self,preferences):
        if (not isinstance(preferences,AppearancePreferences) or
                preferences.theme not in THEMES or
                preferences.font_size_pt not in FONT_SIZES or
                preferences.zoom_percent not in ZOOM_LEVELS):
            raise AppearanceSettingsError("Unsupported appearance preference")
        keys=("appearance/theme","appearance/font_size_pt","appearance/zoom_percent")
        previous={key:self.settings.value(key,None) for key in keys}
        self.settings.setValue(keys[0],preferences.theme)
        self.settings.setValue(keys[1],preferences.font_size_pt)
        self.settings.setValue(keys[2],preferences.zoom_percent)
        self.settings.sync()
        if self.settings.status()!=QSettings.Status.NoError:
            for key,value in previous.items():
                if value is None:
                    self.settings.remove(key)
                else:
                    self.settings.setValue(key,value)
            self.settings.sync()
            raise AppearanceSettingsError("Cannot persist appearance preferences")
        return preferences

    def reset(self):
        self.settings.remove("appearance")
        self.settings.sync()
        if self.settings.status()!=QSettings.Status.NoError:
            raise AppearanceSettingsError("Cannot reset appearance preferences")
        return AppearancePreferences()


def _palette_for(theme,app):
    palette=QPalette(app.style().standardPalette())
    if theme=="system":
        return palette
    if theme=="light":
        colors={
            QPalette.ColorRole.Window:"#f3f5f8",
            QPalette.ColorRole.WindowText:"#20242a",
            QPalette.ColorRole.Base:"#ffffff",
            QPalette.ColorRole.AlternateBase:"#edf0f4",
            QPalette.ColorRole.ToolTipBase:"#20242a",
            QPalette.ColorRole.ToolTipText:"#ffffff",
            QPalette.ColorRole.Text:"#20242a",
            QPalette.ColorRole.Button:"#e8ecf1",
            QPalette.ColorRole.ButtonText:"#20242a",
            QPalette.ColorRole.BrightText:"#c62828",
            QPalette.ColorRole.Highlight:"#286bd6",
            QPalette.ColorRole.HighlightedText:"#ffffff",
            QPalette.ColorRole.Link:"#175fc2",
        }
        for role,color in colors.items():
            palette.setColor(role,QColor(color))
        palette.setColor(QPalette.ColorGroup.Disabled,QPalette.ColorRole.Text,QColor("#8a929d"))
        palette.setColor(QPalette.ColorGroup.Disabled,QPalette.ColorRole.ButtonText,QColor("#8a929d"))
        return palette
    colors={
        QPalette.ColorRole.Window:"#252930",
        QPalette.ColorRole.WindowText:"#e8ebf0",
        QPalette.ColorRole.Base:"#1c2026",
        QPalette.ColorRole.AlternateBase:"#2d333c",
        QPalette.ColorRole.ToolTipBase:"#343b46",
        QPalette.ColorRole.ToolTipText:"#f7f9fc",
        QPalette.ColorRole.Text:"#e8ebf0",
        QPalette.ColorRole.Button:"#353c46",
        QPalette.ColorRole.ButtonText:"#e8ebf0",
        QPalette.ColorRole.BrightText:"#ff6666",
        QPalette.ColorRole.Highlight:"#3479d5",
        QPalette.ColorRole.HighlightedText:"#ffffff",
        QPalette.ColorRole.Link:"#82b4ff",
    }
    for role,color in colors.items():
        palette.setColor(role,QColor(color))
    palette.setColor(QPalette.ColorGroup.Disabled,QPalette.ColorRole.Text,QColor("#9aa3af"))
    palette.setColor(QPalette.ColorGroup.Disabled,QPalette.ColorRole.ButtonText,QColor("#9aa3af"))
    return palette


def apply_appearance(app,preferences):
    """Apply app-local theme/font/zoom; Qt retains OS-managed device pixel ratio."""
    app.setPalette(_palette_for(preferences.theme,app))
    font=QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSizeF(float(preferences.font_size_pt*preferences.zoom_percent)/100.0)
    app.setFont(font)
    pad=max(3,round(4*preferences.zoom_percent/100))
    tab_y=max(4,round(6*preferences.zoom_percent/100))
    tab_x=max(6,round(8*preferences.zoom_percent/100))
    if preferences.zoom_percent==100:
        app.setStyleSheet("")
    else:
        app.setStyleSheet(
            "QPushButton, QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { "
            f"padding: {pad}px; "
            "}"
            "QTabBar::tab { "
            f"padding: {tab_y}px {tab_x}px; "
            "}"
        )


class AppearanceSettingsPanel(QWidget):
    """Live preview and persistent theme/font/zoom controls."""
    def __init__(self,settings,parent=None):
        super().__init__(parent)
        self.app=QApplication.instance()
        if self.app is None:
            raise RuntimeError("Appearance settings require QApplication")
        self.store=AppearanceSettingsStore(settings)
        self.preferences=self.store.load()
        apply_appearance(self.app,self.preferences)

        layout=QVBoxLayout(self)
        form=QFormLayout()
        self.theme_combo=QComboBox()
        self.theme_combo.addItem("Theo hệ điều hành","system")
        self.theme_combo.addItem("Sáng","light")
        self.theme_combo.addItem("Tối","dark")
        self.theme_combo.setAccessibleName("Chủ đề giao diện")
        self.theme_combo.setToolTip("Áp dụng chủ đề cho toàn bộ cửa sổ ứng dụng.")
        form.addRow("Chủ đề",self.theme_combo)

        self.font_size_combo=QComboBox()
        for size in FONT_SIZES:
            self.font_size_combo.addItem(f"{size} pt",size)
        self.font_size_combo.setAccessibleName("Cỡ chữ giao diện")
        self.font_size_combo.setToolTip("Cỡ chữ cơ sở của ứng dụng, không thay đổi font trong project.")
        form.addRow("Cỡ chữ",self.font_size_combo)

        self.zoom_combo=QComboBox()
        for zoom in ZOOM_LEVELS:
            self.zoom_combo.addItem(f"{zoom}%",zoom)
        self.zoom_combo.setAccessibleName("Tỷ lệ giao diện")
        self.zoom_combo.setToolTip("Phóng chữ và khoảng đệm điều khiển trong ứng dụng.")
        form.addRow("Phóng giao diện",self.zoom_combo)
        layout.addLayout(form)

        self.hidpi_note=QLabel(
            "Qt 6 tự nhận DPI/HiDPI từ hệ điều hành và màn hình. "
            "Tùy chọn này chỉ phóng giao diện bên trong Fonesi Edit; "
            "không thay đổi thiết lập hiển thị Windows.")
        self.hidpi_note.setWordWrap(True)
        layout.addWidget(self.hidpi_note)

        self.status=QLabel("Thay đổi được xem trước ngay và lưu vào cài đặt người dùng.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.reset_button=QPushButton("Đặt lại giao diện")
        self.reset_button.setToolTip("Chỉ đặt lại chủ đề, cỡ chữ và tỷ lệ giao diện; không xóa phím tắt hoặc bố cục cửa sổ.")
        self.reset_button.clicked.connect(self.reset_preferences)
        layout.addWidget(self.reset_button)
        layout.addStretch()

        self._set_controls(self.preferences)
        self.theme_combo.currentIndexChanged.connect(self._save_controls)
        self.font_size_combo.currentIndexChanged.connect(self._save_controls)
        self.zoom_combo.currentIndexChanged.connect(self._save_controls)

    def _set_controls(self,preferences):
        controls=(
            (self.theme_combo,self.theme_combo.findData(preferences.theme)),
            (self.font_size_combo,self.font_size_combo.findData(preferences.font_size_pt)),
            (self.zoom_combo,self.zoom_combo.findData(preferences.zoom_percent)),
        )
        for control,index in controls:
            control.blockSignals(True)
            control.setCurrentIndex(max(0,index))
            control.blockSignals(False)

    def _save_controls(self,*_):
        preferences=AppearancePreferences(
            str(self.theme_combo.currentData()),
            int(self.font_size_combo.currentData()),
            int(self.zoom_combo.currentData()),
        )
        try:
            self.store.save(preferences)
        except AppearanceSettingsError:
            self.preferences=self.store.load()
            self._set_controls(self.preferences)
            apply_appearance(self.app,self.preferences)
            self.status.setText("Không lưu được cài đặt giao diện; đã giữ lại cấu hình trước.")
            return
        self.preferences=preferences
        apply_appearance(self.app,preferences)
        self.status.setText(
            f"Đã lưu: {preferences.theme}, {preferences.font_size_pt} pt, "
            f"phóng giao diện {preferences.zoom_percent}%. "
            "Thay đổi chỉ áp dụng trong ứng dụng.")

    def reset_preferences(self):
        try:
            preferences=self.store.reset()
        except AppearanceSettingsError:
            self.status.setText("Không thể đặt lại giao diện; cài đặt trước được giữ nguyên.")
            return
        self.preferences=preferences
        self._set_controls(preferences)
        apply_appearance(self.app,preferences)
        self.status.setText("Đã đặt lại chủ đề, cỡ chữ và tỷ lệ giao diện. Phím tắt và bố cục cửa sổ được giữ nguyên.")
