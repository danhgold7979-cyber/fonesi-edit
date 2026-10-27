from threading import Event
import time
from PySide6.QtCore import QThread, Signal


class Task(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(float)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function, self.cancel = function, Event()
        self.started=None;self.ratio=0

    def report(self,value):self.ratio=value;self.progress.emit(value)

    def run(self):
        try:
            self.started=time.monotonic();self.result.emit(self.function(self.report, self.cancel))
        except Exception as exc:
            self.error.emit(str(exc))
