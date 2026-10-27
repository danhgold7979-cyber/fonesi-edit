from threading import Event
from PySide6.QtCore import QThread, Signal


class Task(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(float)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function, self.cancel = function, Event()

    def run(self):
        try:
            self.result.emit(self.function(self.progress.emit, self.cancel))
        except Exception as exc:
            self.error.emit(str(exc))
