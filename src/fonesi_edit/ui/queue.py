"""Actual durable queue observations on a worker thread, no simulated progress."""
from PySide6.QtCore import QThread,Signal,Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView
from fonesi_edit.jobs.view import read_queue,QueueReadError
from fonesi_edit.jobs.commands import QueueCommand,apply_queue_command


class QueueCommander(QThread):
    applied=Signal(object)
    refused=Signal(str)
    def __init__(self,path,command,parent=None):super().__init__(parent);self.path=path;self.command=command
    def run(self):
        try:self.applied.emit(apply_queue_command(self.path,self.command,cancel=self.isInterruptionRequested))
        except Exception:self.refused.emit('Yêu cầu chưa được xác nhận. Đọc lại trạng thái; không tự gửi lại thao tác.')


class QueueReader(QThread):
    observed=Signal(object)
    refused=Signal(str)
    def __init__(self,path,parent=None):super().__init__(parent);self.path=path
    def run(self):
        try:self.observed.emit(read_queue(self.path,cancel=self.isInterruptionRequested))
        except QueueReadError:self.refused.emit('Không thể đọc hàng đợi. Dữ liệu hiện có không bị thay đổi.')


class QueuePage(QWidget):
    idle=Signal()
    def __init__(self,path,parent=None):
        super().__init__(parent);self.path=path;self.reader=None;self.commander=None;self.stopping=False;self.store_token=None
        layout=QVBoxLayout(self)
        self.message=QLabel('Chưa đọc dữ liệu hàng đợi. Không có số liệu giả lập.')
        self.message.setTextFormat(Qt.PlainText);layout.addWidget(self.message)
        self.command_notice=QLabel('');self.command_notice.setTextFormat(Qt.PlainText)
        self.command_notice.setWordWrap(True);layout.addWidget(self.command_notice)
        self.refresh_button=QPushButton('Đọc lại hàng đợi');self.refresh_button.clicked.connect(self.refresh);layout.addWidget(self.refresh_button)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Mã tác vụ','Trạng thái','Lần thử','Hủy đã yêu cầu','Xuất tệp / Tiến độ'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self._actions)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        for column,width in enumerate((280,130,70,145)):self.table.setColumnWidth(column,width)
        layout.addWidget(self.table)
        actions=QHBoxLayout();self.action_buttons={}
        for action,label in (('pause','Tạm dừng chờ'),('resume','Tiếp tục chờ'),('cancel','Yêu cầu hủy')):
            button=QPushButton(label);button.clicked.connect(lambda checked=False,action=action:self.command(action));actions.addWidget(button);self.action_buttons[action]=button
        layout.addLayout(actions);self._actions()
        note=QLabel('Chỉ thao tác tác vụ đã chọn. Hủy đang chạy chỉ là yêu cầu, chưa xác nhận tiến trình đã dừng. Tiến độ công đoạn chưa được nối.')
        note.setWordWrap(True);layout.addWidget(note)
    def refresh(self):
        if self.busy or self.stopping:return
        self.message.setText('Đang đọc dữ liệu…');self.refresh_button.setEnabled(False)
        self.reader=QueueReader(self.path,self)
        self.reader.observed.connect(self.show_snapshot);self.reader.refused.connect(self.show_error)
        self.reader.finished.connect(self._finished);self._actions();self.reader.start()
    def show_error(self,message):
        self.message.setText(message+' Bảng đang giữ lần đọc trước, không phải trạng thái mới nhất.')
    def show_snapshot(self,snapshot):
        self.table.clearSelection();self.table.setCurrentCell(-1,-1)
        self.store_token=snapshot.store_token
        self.table.setRowCount(len(snapshot.rows))
        for index,row in enumerate(snapshot.rows):
            values=(row.id,row.state,str(row.attempt),'Có' if row.cancel_requested else 'Không',
                    'Chưa hoàn tất đối soát tệp' if row.unresolved_publication else 'Chưa có dữ liệu tiến độ')
            for column,value in enumerate(values):
                item=QTableWidgetItem(value);item.setToolTip(value);item.setData(Qt.UserRole,row);self.table.setItem(index,column,item)
        self.message.setText(('Hiển thị tối đa 500 tác vụ gần nhất; còn dữ liệu khác.' if snapshot.truncated else f'{len(snapshot.rows)} tác vụ từ dữ liệu ứng dụng.') if snapshot.store_exists else 'Chưa có kho tác vụ; không tạo dữ liệu giả.')
    def _finished(self):
        if self.reader is not None and not self.reader.wait(0):
            QTimer.singleShot(10,self._finished);return
        old=self.reader;self.reader=None
        if old is not None:old.deleteLater()
        self.refresh_button.setEnabled(not self.stopping and not self.busy);self._actions();self.idle.emit()
    def request_stop(self):
        self.stopping=True;self.refresh_button.setEnabled(False)
        if self.reader is not None:self.reader.requestInterruption()
        if self.commander is not None:self.commander.requestInterruption()
        self._actions()
    @property
    def busy(self):return self.reader is not None or self.commander is not None

    def _selected(self):
        selected=self.table.selectionModel().selectedRows()
        if len(selected)!=1:return None
        index=selected[0].row()
        item=self.table.item(index,0)
        return item.data(Qt.UserRole) if item is not None else None

    def _actions(self):
        if not hasattr(self,'action_buttons'):return
        row=self._selected();available=row is not None and self.store_token is not None and not self.busy and not self.stopping
        allowed={'pause':{'pending'},'resume':{'paused'},'cancel':{'pending','paused','running','validating'}}
        for action,button in self.action_buttons.items():button.setEnabled(available and row.state in allowed[action])

    def command(self,action):
        row=self._selected()
        if row is None or self.store_token is None or self.busy or self.stopping:return
        self.commander=QueueCommander(self.path,QueueCommand(action,row.id,row.version,self.store_token),self)
        self.commander.applied.connect(self._applied);self.commander.refused.connect(self._command_refused)
        self.commander.finished.connect(self._command_finished)
        self.command_notice.setText('Đang gửi yêu cầu cho tác vụ đã chọn…')
        self.refresh_button.setEnabled(False);self._actions();self.commander.start()

    def _applied(self,result):
        self.command_notice.setText('Đã ghi yêu cầu hủy; chưa xác nhận tiến trình đã dừng.' if result.cancel_requested and result.state in {'running','validating'} else 'Đã ghi trạng thái tác vụ.')

    def _command_refused(self,message):
        self.command_notice.setText(message)

    def _command_finished(self):
        if self.commander is not None and not self.commander.wait(0):
            QTimer.singleShot(10,self._command_finished);return
        old=self.commander;self.commander=None
        if old is not None:old.deleteLater()
        self._actions();self.refresh_button.setEnabled(not self.stopping)
        if not self.stopping:self.refresh()
        self.idle.emit()
