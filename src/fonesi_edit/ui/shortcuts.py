"""User-remappable, focus-scoped shortcut registry and searchable settings panel."""
from PySide6.QtCore import QObject, QSettings, Qt, Signal, QEvent
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QListWidget,QListWidgetItem,
    QKeySequenceEdit,QPushButton,QFormLayout,QPlainTextEdit,QTextEdit,QApplication,QAbstractSpinBox,
)


class ShortcutError(ValueError):
    pass


class ShortcutConflictError(ShortcutError):
    def __init__(self,sequence,other_id,other_label):
        super().__init__(f"{sequence} is already assigned to {other_label}")
        self.sequence=sequence;self.other_id=other_id;self.other_label=other_label


DEFAULT_SHORTCUTS=(
    ('app.settings','Mở Cài đặt','Ứng dụng','Ctrl+,'),
    ('tools.rescan','Quét lại công cụ','Danh sách công cụ','F5'),
    ('layer.undo','Hoàn tác layer','Canvas / Layer','Ctrl+Z'),
    ('layer.redo','Làm lại layer','Canvas / Layer','Ctrl+Shift+Z'),
    ('layer.delete','Xóa layer đã chọn','Canvas / Layer','Delete'),
    ('layer.group','Nhóm layer','Canvas / Layer','Ctrl+G'),
    ('layer.ungroup','Bỏ nhóm layer','Canvas / Layer','Ctrl+Shift+G'),
    ('layer.raise','Đưa layer lên','Canvas / Layer','Alt+Up'),
    ('layer.lower','Đưa layer xuống','Canvas / Layer','Alt+Down'),
    ('timeline.previous_frame','Lùi một frame','Timeline','Left'),
    ('timeline.next_frame','Tiến một frame','Timeline','Right'),
    ('timeline.previous_10','Lùi mười frame','Timeline','Shift+Left'),
    ('timeline.next_10','Tiến mười frame','Timeline','Shift+Right'),
    ('timeline.start','Về frame đầu','Timeline','Home'),
    ('timeline.end','Tới frame cuối','Timeline','End'),
    ('timeline.mark_in','Đặt điểm In','Timeline','I'),
    ('timeline.mark_out','Đặt điểm Out','Timeline','O'),
    ('timeline.clear_range','Xóa vùng In/Out','Timeline','Escape'),
)


def _portable(sequence):
    if isinstance(sequence,QKeySequence):
        value=sequence
    elif isinstance(sequence,str):
        value=QKeySequence(sequence)
    else:
        raise ShortcutError('A Qt key sequence or text sequence is required')
    if value.isEmpty():
        raise ShortcutError('Shortcut cannot be empty')
    if value.count()!=1:
        raise ShortcutError('Only one key chord per shortcut is supported in this editor slice')
    normalized=value.toString(QKeySequence.SequenceFormat.PortableText)
    if not normalized:
        raise ShortcutError('Shortcut cannot be empty')
    return normalized


class ShortcutRegistry(QObject):
    """Persists only user preferences; project files never contain shortcuts."""
    changed=Signal(str)

    def __init__(self,parent=None,settings=None):
        super().__init__(parent)
        self.settings=settings if settings is not None else QSettings('Fonesi','Fonesi Edit')
        self._specs={key:(label,scope,default) for key,label,scope,default in DEFAULT_SHORTCUTS}

    def definitions(self):
        return tuple((key,label,scope,self.sequence(key),default)
                     for key,(label,scope,default) in self._specs.items())

    def sequence(self,action_id):
        if action_id not in self._specs:raise ShortcutError('Unknown shortcut action')
        _label,_scope,default=self._specs[action_id]
        raw=self.settings.value(f'shortcuts/{action_id}',default)
        try:return _portable(str(raw))
        except ShortcutError:return _portable(default)

    def _overlap(self,first,second):
        a=self._specs[first][1];b=self._specs[second][1]
        return a==b or a=='Ứng dụng' or b=='Ứng dụng'

    def set_sequence(self,action_id,sequence):
        if action_id not in self._specs:raise ShortcutError('Unknown shortcut action')
        normalized=_portable(sequence)
        for other,(label,_scope,_default) in self._specs.items():
            if other==action_id or not self._overlap(action_id,other):continue
            if self.sequence(other)==normalized:
                raise ShortcutConflictError(normalized,other,label)
        self.settings.setValue(f'shortcuts/{action_id}',normalized)
        self.settings.sync()
        if self.settings.status()!=QSettings.Status.NoError:
            raise ShortcutError('Cannot persist shortcut preferences')
        self.changed.emit(action_id)
        return normalized

    def reset(self,action_id):
        if action_id not in self._specs:raise ShortcutError('Unknown shortcut action')
        self.settings.remove(f'shortcuts/{action_id}')
        self.settings.sync()
        if self.settings.status()!=QSettings.Status.NoError:
            raise ShortcutError('Cannot persist shortcut reset')
        self.changed.emit(action_id)

    def reset_all(self):
        for action_id in self._specs:self.settings.remove(f'shortcuts/{action_id}')
        self.settings.sync()
        if self.settings.status()!=QSettings.Status.NoError:
            raise ShortcutError('Cannot persist shortcut reset')
        for action_id in self._specs:self.changed.emit(action_id)

    def matches(self,action_id,event):
        if action_id not in self._specs:return False
        modifiers=(Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.ShiftModifier|
                   Qt.KeyboardModifier.AltModifier|Qt.KeyboardModifier.MetaModifier)
        combined=(event.modifiers() & modifiers).value|int(event.key())
        actual=QKeySequence(combined).toString(QKeySequence.SequenceFormat.PortableText)
        return bool(actual) and actual==self.sequence(action_id)


class ShortcutEventRouter(QObject):
    """Dispatch shared-registry shortcuts only from explicitly installed focus scopes."""
    def __init__(self,registry,bindings,parent=None,*,ignore_text_entry=False,repeatable=()):
        super().__init__(parent)
        self.registry=registry
        self.bindings=tuple(bindings)
        self.ignore_text_entry=ignore_text_entry
        self.repeatable=frozenset(repeatable)

    def _is_text_entry(self,watched):
        if not self.ignore_text_entry:return False
        text_types=(QLineEdit,QTextEdit,QPlainTextEdit,QKeySequenceEdit)
        # Inspect both the event receiver and actual focus widget: Qt may propagate
        # an unhandled key to a parent after the child filter has returned False.
        for candidate in (watched,QApplication.focusWidget()):
            current=candidate;found_text_entry=False
            while current is not None:
                if isinstance(current,QAbstractSpinBox):
                    # Its internal QLineEdit is a numeric editor, not a text document.
                    found_text_entry=False
                    break
                if isinstance(current,text_types):found_text_entry=True
                parent=getattr(current,'parentWidget',None)
                current=parent() if parent is not None else None
            if found_text_entry:return True
        return False

    def eventFilter(self,watched,event):
        if event.type()!=QEvent.Type.KeyPress or self._is_text_entry(watched):return False
        for action_id,callback in self.bindings:
            if not self.registry.matches(action_id,event):continue
            if event.isAutoRepeat() and action_id not in self.repeatable:
                event.accept();return True
            callback()
            event.accept()
            return True
        return False


class ShortcutSettingsPanel(QWidget):
    """Search, inspect and remap the implemented shortcut subset."""
    def __init__(self,registry:ShortcutRegistry,parent=None):
        super().__init__(parent)
        self.registry=registry;self._selected_id=None
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Phím tắt đang hoạt động. Chỉ các hành động đã triển khai mới xuất hiện; vùng focus và ô nhập vẫn được ưu tiên.'))
        self.search=QLineEdit();self.search.setPlaceholderText('Tìm hành động hoặc vùng focus…')
        self.search.textChanged.connect(self.refresh_list);layout.addWidget(self.search)
        self.items=QListWidget();self.items.currentRowChanged.connect(self.select_row)
        layout.addWidget(self.items)
        form=QFormLayout()
        self.action_label=QLabel('Chọn một hành động.')
        self.scope_label=QLabel('—')
        self.sequence_edit=QKeySequenceEdit()
        form.addRow('Hành động',self.action_label)
        form.addRow('Vùng focus',self.scope_label)
        form.addRow('Phím tắt mới',self.sequence_edit)
        layout.addLayout(form)
        buttons=QHBoxLayout()
        self.save_button=QPushButton('Lưu phím tắt')
        self.reset_button=QPushButton('Đặt lại hành động')
        self.reset_all_button=QPushButton('Đặt lại tất cả')
        for button in (self.save_button,self.reset_button,self.reset_all_button):buttons.addWidget(button)
        layout.addLayout(buttons)
        self.status=QLabel('Thay đổi chỉ lưu trong cài đặt người dùng, không ghi vào project.')
        self.status.setWordWrap(True);layout.addWidget(self.status)
        self.save_button.clicked.connect(self.save_selected)
        self.reset_button.clicked.connect(self.reset_selected)
        self.reset_all_button.clicked.connect(self.reset_all)
        self.registry.changed.connect(self._registry_changed)
        self.refresh_list()

    def refresh_list(self):
        query=self.search.text().strip().casefold()
        current=self._selected_id
        self.items.blockSignals(True)
        self.items.clear()
        for action_id,label,scope,sequence,default in self.registry.definitions():
            haystack=' '.join((action_id,label,scope,sequence,default)).casefold()
            if query and query not in haystack:continue
            item=QListWidgetItem(f'{label} — {sequence} [{scope}]')
            item.setData(Qt.ItemDataRole.UserRole,action_id)
            self.items.addItem(item)
            if action_id==current:self.items.setCurrentItem(item)
        self.items.blockSignals(False)
        if self.items.currentRow()<0 and self.items.count():
            self.items.setCurrentRow(0)
        elif self.items.currentRow()>=0:
            self.select_row(self.items.currentRow())
        if not self.items.count():
            self._selected_id=None
            self.action_label.setText('Không có kết quả.')
            self.scope_label.setText('—')
            self.sequence_edit.setKeySequence(QKeySequence())
            self.save_button.setEnabled(False);self.reset_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True);self.reset_button.setEnabled(True)

    def select_row(self,row):
        item=self.items.item(row) if row>=0 else None
        if item is None:return
        action_id=item.data(Qt.ItemDataRole.UserRole)
        spec=next(x for x in self.registry.definitions() if x[0]==action_id)
        self._selected_id=action_id
        self.action_label.setText(spec[1]);self.scope_label.setText(spec[2])
        self.sequence_edit.setKeySequence(QKeySequence(spec[3]))
        self.save_button.setEnabled(True);self.reset_button.setEnabled(True)

    def save_selected(self):
        if self._selected_id is None:return
        try:
            sequence=self.registry.set_sequence(self._selected_id,self.sequence_edit.keySequence())
        except ShortcutConflictError as exc:
            self.status.setText(f'Xung đột: {sequence_text(exc.sequence)} đã dùng cho {exc.other_label}. Chưa lưu thay đổi.')
            return
        except ShortcutError as exc:
            self.status.setText(str(exc));return
        self.status.setText(f'Đã lưu {sequence}. Thay đổi có hiệu lực ngay trong vùng focus tương ứng.')

    def reset_selected(self):
        if self._selected_id is None:return
        self.registry.reset(self._selected_id)
        self.status.setText('Đã đặt lại phím tắt của hành động đang chọn.')

    def reset_all(self):
        self.registry.reset_all()
        self.status.setText('Đã đặt lại toàn bộ phím tắt về mặc định.')

    def _registry_changed(self,_action_id):
        self.refresh_list()


def sequence_text(value):
    return str(value)
