from PySide6.QtCore import QObject,QRunnable,Signal,Slot,QThreadPool
import threading
from ..core.process import Cancelled

class Signals(QObject):
    done=Signal(object)
    failed=Signal(str)
    progress=Signal(str,object)

class Task(QRunnable):
    def __init__(self,function,with_progress=False):
        super().__init__();self.function=function;self.with_progress=with_progress;self.signals=Signals();self.cancelled=threading.Event()
    @Slot()
    def run(self):
        try:self.signals.done.emit(self.function(self.cancelled.is_set,self.signals.progress.emit) if self.with_progress else self.function(self.cancelled.is_set))
        except Exception as exc:self.signals.failed.emit(f'{type(exc).__name__}: {exc}')

class TaskRunner(QObject):
    def __init__(self,parent=None):super().__init__(parent);self.active=[]
    def submit(self,function,done,error,progress=None):
        task=Task(function,with_progress=progress is not None);self.active.append(task)
        def finished():
            if task in self.active:self.active.remove(task)
        if progress:task.signals.progress.connect(progress)
        task.signals.done.connect(done);task.signals.done.connect(finished)
        task.signals.failed.connect(error);task.signals.failed.connect(finished)
        QThreadPool.globalInstance().start(task);return task
    def cancel_all(self):
        for task in self.active:task.cancelled.set()
