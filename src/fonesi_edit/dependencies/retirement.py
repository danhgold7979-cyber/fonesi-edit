"""Single pair-check operation composes existing bounded validator receipts."""
from contextlib import contextmanager
from threading import get_ident
from fonesi_edit.media.retirement import ValidationLifecycle


class PairRetirement:
    ORDER=('versions','media','frame')
    COUNTS=(2,2,1)
    def __init__(self,operation):
        self._operation=operation;self._thread=get_ident();self._entered=False
        self._active=False;self._sealed=False;self._revoked=False;self._inside=False;self._stages=[]
    def _owner(self):
        if get_ident()!=self._thread:
            self._revoked=True;raise RuntimeError('Pair receipt belongs to another thread')
    @contextmanager
    def check_body(self):
        self._owner()
        if self._entered or self._revoked:
            self._revoked=True;raise RuntimeError('Pair receipt cannot be reused')
        self._entered=True;self._active=True
        try:yield
        finally:self._active=False;self._sealed=True
    @contextmanager
    def stage(self,name):
        self._owner();index=len(self._stages)
        if self._revoked or not self._active or self._sealed or self._inside or index>=3 or name!=self.ORDER[index]:
            self._revoked=True;raise RuntimeError('Invalid pair stage order or reuse')
        operation=object();lifecycle=ValidationLifecycle(operation)
        self._stages.append((name,operation,lifecycle)) # UNKNOWN before delegate entry
        self._inside=True
        try:yield lifecycle
        finally:self._inside=False
    def confirmed_for(self,operation):
        self._owner()
        return (not self._revoked and operation is self._operation and self._entered and self._sealed
                and not self._active and not self._inside
                and all(lifecycle.confirmed_for(token) for _,token,lifecycle in self._stages))
    def complete_for(self,operation):
        return (self.confirmed_for(operation) and len(self._stages)==3 and
            all(name==self.ORDER[i] and len(lifecycle.mechanisms)==self.COUNTS[i]
                and all(m in {'WINDOWS_JOB_EMPTY','POSIX_GROUP_RETIRED'} for m in lifecycle.mechanisms)
                for i,(name,_,lifecycle) in enumerate(self._stages)))
    @property
    def mechanisms(self):return tuple(m for _,_,scope in self._stages for m in scope.mechanisms)
