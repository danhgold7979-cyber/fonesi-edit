# Local selected-job command review

Base local HEAD 5cbb079, seven dirty paths. Initial hashes recorded in P03_QUEUE_COMMAND_INITIAL_HASHES.txt, matching supplied review pin.

Verdict: backend scope clear; UI HOLD pending actual-selection fix.

Independent offscreen repro: selectRow(0), then clearSelection leaves selectedRows empty but currentRow=0. _selected() returns that old job and pause button remains enabled. This violates selected-job intent and allows a visually unselected target to be mutated. Require exactly one selectedRows entry, no-op/disable when none. On snapshot replacement clear selection or restore by same UUID, never silently retarget by table index.

Author also identified action notices being overwritten by automatic refresh; preserve cancellation-request-only and unknown-outcome/refusal notices separately from data refresh status.

Independently ran six backend stale-version/store-token/unknown-COMMIT/existing-only-old-or-foreign-store/busy-lock tests: 6 PASS, 4 deselected. Existing-only open uses mode=rw, no creation/migration/adoption; store receipt token checked before owner epoch and again under transaction. CAS protects captured job version; coordinator contention is not bypassed; unknown COMMIT does not automatically replay. Command thread owns its connection and closes before UI completes shutdown.

No generic running-process stop guarantee; cancellation only requests flag. Active-coordinator routing, Windows GUI and full phase acceptance remain open. No remote commit/push/CI performed.

## Corrected selection/lifecycle batch — native teardown remains BLOCKED

Verified supplied correction hashes: ui/queue.py 9da88c233e9bf2793c958fc59b10e4b37ff15d2c70e2cd72ae93d28410e57c49; test_queue_commands.py c0e0853c5030ee75d30959939507bef53a6f3f9e14010ae8ca47bdd4aa88fcfd; conftest 40c8f78e9e24474bcee0cffc117feedb4fb19d07efc05072a9aeb959382172d9; shell test a4bc360ac78d8ccc0f79bb50135761944bdfb401ec58c08aa29f0e6f90b6e9a1; queue view test 369b1ab6b38dc4a29b6900ecc95d8152fed55d89a68ced7c3ffd48f1f8cbc19c; contract 66d480e3f8656d49e7a64a71e4c7d3c364117e7f1ba4606c1dc3b516766eec5e.

Source now correctly requires one selectedRows entry, clears old selection on refreshed rows and preserves action notices separately. QThread retirement uses wait(0) and timer polling before releasing busy state; reviewed official https://doc.qt.io/qt-6/qthread.html#isFinished (finished may precede remaining thread cleanup). This is reasonable hardening but does not establish the prior crash root cause.

Independent exact command: PYTHONFAULTHANDLER=1 .venv/bin/python -m pytest -q tests/test_queue_commands.py -k 'visibly_deselected or snapshot_refresh or finished_signal'. Three assertions PASS, thirteen deselected, followed by process exit135 / Fatal Python error: Bus error; current thread had no Python frame, extensions Shiboken/QtCore/QtGui/QtWidgets. This run is NOT PASS. Two selected tests start no real worker and the third uses a fake worker, narrowing investigation to Qt/application/object teardown rather than proving a real worker TLS cause. Author and parent informed. UI checkpoint remains HOLD pending causal resolution and clean process exit; backend evidence unchanged.

## Final local correction — scoped CLEAR

Verified further hashes: __main__.py 0d9201e7571d8978297cfbb126d198326ecb556ba49171a1fffd9e8b5e0000e0; conftest 50e2ebbc364c833fce4b135189602108d0c38ffe0acfb1d59248e4ebf33f6dcb; test_queue_commands.py 9648eaec6f6150dd78e25d92917c5a1e7c5837c39a7101877ffa959613a48aca; contract c242c3798f21534050c1ca56ff22fe24aec7fde004f4a2dc6c7230307cabd8ce. Other corrected source hashes above unchanged.

Fixture now explicitly retires child QThreads and destroys top-level widgets while QApplication remains alive. Production main likewise cooperatively retires queue workers and delivers owned window deferred deletion before releasing QApplication/project store. No forced thread termination is introduced. An OS-blocked operation can still defer exit: not a hard deadline claim.

Independently repeated ONLY the previously failing three-case subset: 3 PASS, 14 deselected, process exit0. Separately ran actual GUI-entrypoint subprocess closure: 1 PASS, 16 deselected, process exit0. No aggregate/baseline repetition. Original reviewer exit135 remains retained above, not erased. Author's isolation and fixture-order intervention support an object teardown-order diagnosis; exact native C++ failure mechanism is not proven.

Selected-row source defect and persistent notice/lifecycle gaps are closed for this bounded local checkpoint. No remaining identified blocker; native Windows GUI shutdown/commands and full queue integration still require evidence. Remote hold, no new criterion/phase acceptance, no automatic retry after unknown COMMIT all remain unchanged.
