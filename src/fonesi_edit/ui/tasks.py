from PySide6.QtCore import QObject,QRunnable,Signal,Slot,QThreadPool
import threading
from ..core.process import Cancelled

class Signals(QObject):
    done=Signal(object)
    failed=Signal(str)

class Task(QRunnable):
    def __init__(self,function):
        super().__init__();self.function=function;self.signals=Signals();self.cancelled=threading.Event()
    @Slot()
    def run(self):
        try:self.signals.done.emit(self.function(self.cancelled.is_set))
        except Exception as exc:self.signals.failed.emit(f'{type(exc).__name__}: {exc}')

class TaskRunner(QObject):
    def __init__(self,parent=None):super().__init__(parent);self.active=[]
    def submit(self,function,done,error):
        task=Task(function);self.active.append(task)
        def finished():
            if task in self.active:self.active.remove(task)
        task.signals.done.connect(done);task.signals.done.connect(finished)
        task.signals.failed.connect(error);task.signals.failed.connect(finished)
        QThreadPool.globalInstance().start(task);return task
    def cancel_all(self):
        for task in self.active:task.cancelled.set()
