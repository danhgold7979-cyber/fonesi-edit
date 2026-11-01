import ctypes as C
import pytest
from fonesi_edit.jobs.windows_process import BASIC_ACCOUNTING, await_job_empty
from fonesi_edit.jobs.process import ProcessError

class AccountingSequence:
    def __init__(self,values):self.values=iter(values);self.observed=[]
    def QueryInformationJobObject(self,handle,kind,pointer,size,length):
        assert handle==123 and kind==1 and size==48
        value=next(self.values);self.observed.append(value)
        if value is None:return 0
        C.cast(pointer,C.POINTER(BASIC_ACCOUNTING)).contents.ActiveProcesses=value
        return 1

def test_waits_for_all_descendants_not_leader_only():
    api=AccountingSequence([3,2,1,0])
    await_job_empty(api,123,clock=lambda:0,sleep=lambda _:None)
    assert api.observed==[3,2,1,0]

def test_timeout_does_not_claim_quiescence():
    api=AccountingSequence([1,1]);ticks=iter([0,1,2])
    with pytest.raises(ProcessError,match='unconfirmed'):
        await_job_empty(api,123,timeout=2,clock=lambda:next(ticks),sleep=lambda _:None)

def test_query_failure_does_not_claim_quiescence():
    with pytest.raises(ProcessError,match='query failed'):
        await_job_empty(AccountingSequence([None]),123)
