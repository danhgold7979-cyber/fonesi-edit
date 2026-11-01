# Local queue observation review

Functional verdict: CLEAR for bounded read-only queue UI. Base local HEAD 5535e56; reviewed dirty files, not a new commit.

Verified SHA256:
- jobs/view.py 480630b412cfd759b5c2ec49ed931f865d148a44d1169a4f1bc1891bcd2f7021
- ui/queue.py 56657d876f26a6feb59eba4029315fd7a472c6327783e06c71aed0bf241b9193
- ui/shell.py 07db441299bf5830f46fc5efe56eb9cf46d6ce0fb1212758d0c437f5014b9b50
- tests/test_queue_view.py 872693b4ee4e883b6d7f25f504154c85014fa887479b7fe40dc100d3198244c4
- QUEUE_VIEW.md cd4051c00a013365ec5442c4b1b022fc45f96b6050a811fc6103797c74e65095

Independent targeted run: 4 PASS, 3 deselected (bounded immutable actual rows, foreign/malformed store, cooperative close, stale previous rows). No prior baseline repeated.

Reader opens its own mode=ro connection on worker thread after physical/receipt checks, verifies exact current schema and selects only display-safe closed fields. Missing DB remains missing. SQLite resources close in worker finally; no migration/admission/job mutation or snapshot/request-key selection. UI retains but labels stale rows on error, displays unknown progress and defers MainWindow close until QThread finishes. No forced terminate or cross-thread SQLite close.

Requirements attribution correction requested: prior user red-circle Edit request was a chat/status marker; absent a newer explicit app-icon request, document the window icon as provisional design choice rather than user-mandated branding. Author can polish column sizing/tooltips without changing reviewed data/worker logic.

No native Windows GUI evidence, queue commands, telemetry/progress or whole criterion completion claimed. Read-only WAL may use SHM metadata; no business-data mutation is the actual guarantee. Remote publication/CI hold remains separate; no reviewer commits or remote actions.
