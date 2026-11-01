"""One validation operation's internal process-retirement ledger, not validation."""
from contextlib import contextmanager
from threading import get_ident
from fonesi_edit.jobs.process import _RetirementObservation


class ValidationLifecycle:
    """Unknown until actual trusted validator entry/unwind and every owned attempt.

    No process creation here: actual adapters alone confirm their own token after
    checked retirement. POSIX_GROUP_RETIRED means its existing group policy, NOT a
    Windows ActiveProcesses0 proof; POSIX destructive staging cleanup stays absent.
    """
    def __init__(self,operation):
        self._operation=operation;self._thread=get_ident()
        self._entered=False;self._active=False;self._sealed=False;self._revoked=False
        self._invoking=False;self._observations=[]

    def _owner(self):
        if get_ident()!=self._thread:
            self._revoked=True
            raise RuntimeError('Validation lifecycle belongs to another thread')

    @contextmanager
    def validation_body(self):
        self._owner()
        if self._entered or self._revoked:
            self._revoked=True
            raise RuntimeError('Validation lifecycle cannot be reused')
        self._entered=True;self._active=True
        try:yield
        finally:self._active=False;self._sealed=True

    def run(self,runner,argv,**kwargs):
        self._owner()
        if self._revoked or not self._active or self._sealed or self._invoking or len(self._observations)>=2:
            self._revoked=True
            raise RuntimeError('Invalid or unbounded validation invocation')
        observation=_RetirementObservation()
        self._observations.append(observation) # UNKNOWN BEFORE any launcher entry.
        self._invoking=True
        try:return runner(argv,_retirement=observation,**kwargs)
        finally:self._invoking=False # Never confirms an invocation, even on success.

    def confirmed_for(self,operation):
        self._owner()
        return (not self._revoked and operation is self._operation and self._entered and self._sealed
                and not self._active and not self._invoking
                and all(o.mechanism in {'NO_PROCESS','POSIX_GROUP_RETIRED','WINDOWS_JOB_EMPTY'}
                        for o in self._observations))

    @property
    def mechanisms(self):
        return tuple(o.mechanism for o in self._observations)
