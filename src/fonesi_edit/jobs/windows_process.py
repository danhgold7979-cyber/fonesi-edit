"""Windows 10+ owned nested job; atomic assignment at suspended process creation.

No breakaway, arbitrary PID termination, global inheritance or protection changes.
Win32 calls are loaded only on Windows; source/ABI tests are not runtime acceptance.
"""
from __future__ import annotations
import ctypes as C
import os
import subprocess
import time
from pathlib import Path
from .process import ProcessError, ProcessCanceled, ProcessResult, _begin_retirement, _confirm_retirement

DWORD=C.c_uint32
WORD=C.c_uint16
BOOL=C.c_int32
HANDLE=C.c_void_p
SIZE_T=C.c_size_t
LPVOID=C.c_void_p

class SECURITY_ATTRIBUTES(C.Structure):
    _fields_=[('nLength',DWORD),('lpSecurityDescriptor',LPVOID),('bInheritHandle',BOOL)]

class STARTUPINFOW(C.Structure):
    _fields_=[('cb',DWORD),('lpReserved',C.c_wchar_p),('lpDesktop',C.c_wchar_p),
              ('lpTitle',C.c_wchar_p),('dwX',DWORD),('dwY',DWORD),('dwXSize',DWORD),
              ('dwYSize',DWORD),('dwXCountChars',DWORD),('dwYCountChars',DWORD),
              ('dwFillAttribute',DWORD),('dwFlags',DWORD),('wShowWindow',WORD),
              ('cbReserved2',WORD),('lpReserved2',LPVOID),('hStdInput',HANDLE),
              ('hStdOutput',HANDLE),('hStdError',HANDLE)]

class STARTUPINFOEXW(C.Structure):
    _fields_=[('StartupInfo',STARTUPINFOW),('lpAttributeList',LPVOID)]

class PROCESS_INFORMATION(C.Structure):
    _fields_=[('hProcess',HANDLE),('hThread',HANDLE),('dwProcessId',DWORD),('dwThreadId',DWORD)]

class BASIC_LIMIT(C.Structure):
    _fields_=[('PerProcessUserTimeLimit',C.c_int64),('PerJobUserTimeLimit',C.c_int64),
              ('LimitFlags',DWORD),('MinimumWorkingSetSize',SIZE_T),('MaximumWorkingSetSize',SIZE_T),
              ('ActiveProcessLimit',DWORD),('Affinity',SIZE_T),('PriorityClass',DWORD),('SchedulingClass',DWORD)]

class IO_COUNTERS(C.Structure):
    _fields_=[(name,C.c_uint64) for name in ('ReadOperationCount','WriteOperationCount',
        'OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]

class EXTENDED_LIMIT(C.Structure):
    _fields_=[('BasicLimitInformation',BASIC_LIMIT),('IoInfo',IO_COUNTERS),
              ('ProcessMemoryLimit',SIZE_T),('JobMemoryLimit',SIZE_T),
              ('PeakProcessMemoryUsed',SIZE_T),('PeakJobMemoryUsed',SIZE_T)]


class BASIC_ACCOUNTING(C.Structure):
    _fields_=[('TotalUserTime',C.c_int64),('TotalKernelTime',C.c_int64),
              ('ThisPeriodTotalUserTime',C.c_int64),('ThisPeriodTotalKernelTime',C.c_int64),
              ('TotalPageFaultCount',DWORD),('TotalProcesses',DWORD),
              ('ActiveProcesses',DWORD),('TotalTerminatedProcesses',DWORD)]


def await_job_empty(kernel,job,*,timeout=5,clock=time.monotonic,sleep=time.sleep):
    """An owned handle, never a job name/PID, identifies the quiescence domain."""
    deadline=clock()+timeout
    while True:
        accounting=BASIC_ACCOUNTING()
        if not kernel.QueryInformationJobObject(job,1,C.byref(accounting),C.sizeof(accounting),None):
            error=getattr(C,'get_last_error',lambda:0)()
            raise ProcessError(f'Job quiescence query failed (Win32 {error})')
        if accounting.ActiveProcesses==0:return
        if clock()>=deadline:raise ProcessError('All-descendant retirement unconfirmed: job remains active')
        sleep(.005)


def _kernel():
    k=C.WinDLL('kernel32',use_last_error=True)
    signatures={
        'CreateJobObjectW':([LPVOID,C.c_wchar_p],HANDLE),
        'SetInformationJobObject':([HANDLE,C.c_int,LPVOID,DWORD],BOOL),
        'CreatePipe':([C.POINTER(HANDLE),C.POINTER(HANDLE),C.POINTER(SECURITY_ATTRIBUTES),DWORD],BOOL),
        'SetHandleInformation':([HANDLE,DWORD,DWORD],BOOL),
        'CreateFileW':([C.c_wchar_p,DWORD,DWORD,C.POINTER(SECURITY_ATTRIBUTES),DWORD,DWORD,HANDLE],HANDLE),
        'InitializeProcThreadAttributeList':([LPVOID,DWORD,DWORD,C.POINTER(SIZE_T)],BOOL),
        'UpdateProcThreadAttribute':([LPVOID,DWORD,SIZE_T,LPVOID,SIZE_T,LPVOID,LPVOID],BOOL),
        'DeleteProcThreadAttributeList':([LPVOID],None),
        'CreateProcessW':([C.c_wchar_p,C.c_wchar_p,LPVOID,LPVOID,BOOL,DWORD,LPVOID,C.c_wchar_p,C.POINTER(STARTUPINFOEXW),C.POINTER(PROCESS_INFORMATION)],BOOL),
        'IsProcessInJob':([HANDLE,HANDLE,C.POINTER(BOOL)],BOOL),
        'ResumeThread':([HANDLE],DWORD),
        'WaitForSingleObject':([HANDLE,DWORD],DWORD),
        'GetExitCodeProcess':([HANDLE,C.POINTER(DWORD)],BOOL),
        'PeekNamedPipe':([HANDLE,LPVOID,DWORD,LPVOID,C.POINTER(DWORD),LPVOID],BOOL),
        'ReadFile':([HANDLE,LPVOID,DWORD,C.POINTER(DWORD),LPVOID],BOOL),
        'TerminateJobObject':([HANDLE,DWORD],BOOL),
        'TerminateProcess':([HANDLE,DWORD],BOOL),
        'QueryInformationJobObject':([HANDLE,C.c_int,LPVOID,DWORD,LPVOID],BOOL),
        'CloseHandle':([HANDLE],BOOL),
    }
    for name,(args,result) in signatures.items():
        function=getattr(k,name);function.argtypes=args;function.restype=result
    return k


def run_windows_owned(argv, *, cancel=lambda:False, timeout=300,
                      max_output_bytes=4*1024*1024, grace_seconds=.2, on_stdout=None, _retirement=None):
    if on_stdout is not None and not callable(on_stdout):
        raise ValueError("stdout observer must be callable")
    if os.name!='nt':
        raise ProcessError('Windows Job Object adapter requires Windows')
    if isinstance(argv,(str,bytes)) or not argv or any(not isinstance(v,str) or '\0' in v for v in argv):
        raise ValueError('Nonempty argv sequence without NUL required')
    executable=Path(argv[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ProcessError('Explicit existing absolute executable path required')
    if timeout<=0 or max_output_bytes<1 or grace_seconds<0:
        raise ValueError('Invalid execution bounds')
    retirement_token=_begin_retirement(_retirement)
    if cancel():
        _confirm_retirement(_retirement,retirement_token,'NO_PROCESS')
        raise ProcessCanceled('Canceled before launch')
    k=_kernel();owned=[];attribute_list=None;initialized=False;job=None;pi=PROCESS_INFORMATION()
    outputs={'stdout':bytearray(),'stderr':bytearray()}
    retirement_errors=[]
    membership_verified=False;job_empty=False
    def checked(result,operation):
        if not result:raise ProcessError(f'{operation} failed (Win32 {C.get_last_error()})')
        return result
    def own(handle):
        if not handle or handle==C.c_void_p(-1).value:
            raise ProcessError(f'Handle creation failed (Win32 {C.get_last_error()})')
        owned.append(handle);return handle
    def close(handle):
        if handle in owned:
            if not k.CloseHandle(handle):retirement_errors.append(f'CloseHandle failed (Win32 {C.get_last_error()})')
            owned.remove(handle)
    def drain(pipes):
        for name,handle in list(pipes.items()):
            available=DWORD()
            if not k.PeekNamedPipe(handle,None,0,None,C.byref(available),None):
                if C.get_last_error()==109: # ERROR_BROKEN_PIPE: all writers closed
                    pipes.pop(name);continue
                checked(False,'PeekNamedPipe')
            if available.value:
                # Read at most limit+1 in memory, irrespective of child's write size.
                remaining=max_output_bytes-sum(map(len,outputs.values()))
                count=min(available.value,65536,remaining+1)
                buffer=C.create_string_buffer(count);read=DWORD()
                checked(k.ReadFile(handle,buffer,count,C.byref(read),None),'ReadFile')
                outputs[name].extend(buffer.raw[:read.value])
                if sum(map(len,outputs.values()))>max_output_bytes:
                    raise ProcessError('Owned process output exceeds limit')
                if name == 'stdout' and on_stdout is not None and read.value:
                    on_stdout(buffer.raw[:read.value])
    try:
        job=own(k.CreateJobObjectW(None,None))
        limits=EXTENDED_LIMIT();limits.BasicLimitInformation.LimitFlags=0x2000 # KILL_ON_JOB_CLOSE only
        checked(k.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)),'SetInformationJobObject')
        security=SECURITY_ATTRIBUTES(C.sizeof(SECURITY_ATTRIBUTES),None,True)
        stdin=own(k.CreateFileW('NUL',0x80000000,3,C.byref(security),3,0,None))
        pipes={};writes={}
        for name in outputs:
            reader,writer=HANDLE(),HANDLE()
            checked(k.CreatePipe(C.byref(reader),C.byref(writer),C.byref(security),0),'CreatePipe')
            pipes[name]=own(reader.value);writes[name]=own(writer.value)
            checked(k.SetHandleInformation(reader,1,0),'SetHandleInformation')
        size=SIZE_T()
        k.InitializeProcThreadAttributeList(None,2,0,C.byref(size))
        if not size.value:checked(False,'Attribute size query')
        attribute_buffer=C.create_string_buffer(size.value)
        attribute_list=C.cast(attribute_buffer,LPVOID)
        checked(k.InitializeProcThreadAttributeList(attribute_list,2,0,C.byref(size)),'InitializeProcThreadAttributeList');initialized=True
        handles=(HANDLE*3)(stdin,writes['stdout'],writes['stderr'])
        jobs=(HANDLE*1)(job)
        checked(k.UpdateProcThreadAttribute(attribute_list,0,0x20002,handles,C.sizeof(handles),None,None),'HANDLE_LIST')
        checked(k.UpdateProcThreadAttribute(attribute_list,0,0x2000D,jobs,C.sizeof(jobs),None,None),'JOB_LIST')
        startup=STARTUPINFOEXW();startup.StartupInfo.cb=C.sizeof(startup)
        startup.StartupInfo.dwFlags=0x100 # STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput=stdin;startup.StartupInfo.hStdOutput=writes['stdout'];startup.StartupInfo.hStdError=writes['stderr']
        startup.lpAttributeList=attribute_list
        command=C.create_unicode_buffer(subprocess.list2cmdline(list(argv)))
        # Atomic job assignment closes the crash gap of CreateSuspended + Assign.
        checked(k.CreateProcessW(str(executable),command,None,None,True,
            0x00080000|0x00000004|0x08000000,None,None,C.byref(startup),C.byref(pi)),'CreateProcessW')
        own(pi.hProcess);own(pi.hThread)
        in_job=BOOL()
        checked(k.IsProcessInJob(pi.hProcess,job,C.byref(in_job)),'IsProcessInJob')
        if not in_job.value:raise ProcessError('Child did not enter owned job; refusing resume')
        membership_verified=True
        for handle in writes.values():close(handle)
        close(stdin)
        if k.ResumeThread(pi.hThread)==0xFFFFFFFF:checked(False,'ResumeThread')
        close(pi.hThread)
        started=time.monotonic()
        while True:
            if cancel():raise ProcessCanceled('Canceled during execution')
            if time.monotonic()-started>timeout:raise ProcessError('Owned process timed out')
            drain(pipes)
            wait=k.WaitForSingleObject(pi.hProcess,10)
            if wait==0:break
            if wait!=258:checked(False,'WaitForSingleObject')
        exit_code=DWORD();checked(k.GetExitCodeProcess(pi.hProcess,C.byref(exit_code)),'GetExitCodeProcess')
        # Completed leader cannot leave silent descendants behind.
        checked(k.TerminateJobObject(job,130),'TerminateJobObject')
        drain_deadline=time.monotonic()+5
        while pipes:
            drain(pipes)
            if time.monotonic()>drain_deadline:raise ProcessError('Pipe retirement timed out')
            if pipes:time.sleep(.005)
        return ProcessResult(exit_code.value,bytes(outputs['stdout']),bytes(outputs['stderr']))
    finally:
        # Immediate termination is the Windows safety policy here. Cooperative tool-
        # specific soft cancellation is a higher-level worker gate, not provided by
        # the shared grace_seconds argument in this low-level Windows adapter.
        if job:
            if not k.TerminateJobObject(job,130):
                retirement_errors.append(f'TerminateJobObject failed (Win32 {C.get_last_error()})')
        if pi.hProcess and not membership_verified:
            # Still suspended: directly terminate our exact created handle on setup failure.
            if not k.TerminateProcess(pi.hProcess,130):
                retirement_errors.append(f'Suspended-child retirement failed (Win32 {C.get_last_error()})')
        if pi.hProcess:
            wait=k.WaitForSingleObject(pi.hProcess,5000)
            if wait!=0:retirement_errors.append(f'Process retirement unconfirmed (wait={wait})')
            close(pi.hProcess)
        if pi.hThread:close(pi.hThread)
        if job:
            try:
                await_job_empty(k,job);job_empty=True
            except ProcessError as exc:retirement_errors.append(str(exc))
            close(job) # crash/exception fail-safe; handle was never inherited
        if initialized:k.DeleteProcThreadAttributeList(attribute_list)
        for handle in list(reversed(owned)):close(handle)
        if retirement_errors:
            raise ProcessError('; '.join(retirement_errors))

        if job and job_empty:_confirm_retirement(_retirement,retirement_token,'WINDOWS_JOB_EMPTY')
        elif not job and not pi.hProcess:_confirm_retirement(_retirement,retirement_token,'NO_PROCESS')
