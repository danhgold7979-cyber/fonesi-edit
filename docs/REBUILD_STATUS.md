# Trạng thái làm lại Fonesi Edit

## Hiện tại — early frozen startup proof

- Repo: danhgold7979-cyber/fonesi-edit; nhánh rebuild. Main và develop/fonesi-full không đổi.
- 12 phase / 94 task / 95 nhóm yêu cầu; chưa nghiệm thu trọn phase hoặc task đầy đủ. Không dùng số test để suy ra phần trăm sản phẩm.
- Code mới đã có: rational timing, immutable intent, SQLite lease ledger, probe/render CPU, Qt import/preview/trim-speed/export, project save-as/open, SRT editor, thuật toán matrix và batch local.
- Kiểm tra local: 105/105 tests PASS; Ruff check/format PASS. CI checkpoint 0e5d398 (run 41107887718) SUCCESS; batch/Escape checkpoint f70f64b CI41112455704 SUCCESS; frozen Windows checkpoint dceeb5b/run41113327409 job124261038897 build + sáu startup checks PASS; selection-fix increment chưa có CI.
- Đã có CI Windows/Linux Python 3.12/3.13, không đồng nghĩa nghiệm thu máy Windows người dùng, installer hoặc GPU.
- UI/real CPU output có bằng chứng riêng; các workspace chưa triển khai vẫn bị vô hiệu hóa. Matrix chưa tích hợp UI; batch có dialog CPU độc lập nhưng chưa có durable queue; ledger chưa nối production worker.
- Còn mở: full timeline/layers/preview parity, VTT/ASS/translation/burn-in, download/browser auth, durable queue recovery, matrix integration, Windows packaging/live acceptance.
- Backup toàn bộ lịch sử đã verify restore; implementation cũ được loại trong commit riêng có thể khôi phục. Các báo cáo cũ có nhãn lịch sử, không chứng nhận rebuild.
- Tiếp tục phần độc lập theo plan trước code; không đoán cổng bên ngoài là PASS.

## Nhật ký các checkpoint trước

Các số test và trạng thái pending dưới đây mô tả thời điểm từng increment, không phải trạng thái hiện tại. Xem tóm tắt ở trên và CI đúng commit.

## UI increment and Windows failure correction

- Added app.py, Qt UI tests, PRODUCT.md, DESIGN.md and UI slice plan. Real import/preview/export, busy/cancel/close protection; unimplemented workspaces visibly disabled.
- Local 41 tests PASS under Python3.12.14, PySide6 6.8.3, FFmpeg7.1.5; two inspected synthetic screenshots1280/1600.
- CI41099091424: Linux3.12/3.13 PASS38; Windows3.12/3.13 FAIL1/38 at fsync on read-only staged descriptor (Errno9). Fix opens ONLY owned staged output r+b before fsync; source remains read-only and no-overwrite unchanged. Windows rerun pending.
- Source proof does not establish Windows user-machine acceptance, installer, complete timeline/editor, live download/auth or provider translation.

## Trim/speed increment

- One immutable ClipMap can drive real video/audio trim and speed0.5–2, with explicit duration policy. Real2s audio/video fixture -> one-second interval at2x -> approximately0.5s verified.
- Qt start/end/speed controls preserve per-row edits; invalid/beyond-source interval disables export. Source preview remains clearly distinct from output.
- Local43 tests PASS; Windows/Python3.12 run41099958032 passed41 tests on prior UI/fsync checkpoint, other matrix jobs awaited. New trim/speed increment not yet CI-verified.

## Project persistence slice

New strict project schema/save-as/open, no media auto-probe on load, missing references retained and exact rational edits preserved until explicit numeric edit. Existing destination never overwritten. UI replacement requires confirmation. Current schema rejects unsupported nonzero timeline offsets. Local54 tests PASS. Saves are bounded-size local filesystem work; no claim of interruptible network-filesystem flush or autosave/migration acceptance. Project code not yet Windows CI-verified.

## SRT editor slice

- Strict UTF-8 SRT parser/exporter, exact cue time maps, overlap/order diagnostics, literal text retained. VTT/ASS/translation/burn-in NOT_IMPLEMENTED.
- Native virtual table edits text/times/lock, bounded100-command undo/redo, asynchronous new-file save/open, no overwrite. SRT does not persist manual-lock metadata; UI states this explicitly.
- Plain-text user-controlled labels prevent accidental rich-text interpretation.
- Local72 tests PASS, Python3.12.14/Qt6.8.3/Linux/FFmpeg7.1.5. All4 jobs CI41099958032 passed41 tests on prior UI/fsync checkpoint; newer increments await CI.

## Windows project reference correction

CI41101541228 Linux PASS54, Windows FAIL1/54: UI converted a preserved POSIX reference into a drive-qualified Windows path. Fix separates original reference strings from native Path objects, preserves exact reference on save, and refuses foreign paths before probe instead of guessing a drive. New OS-dependent negative test complements the existing failing roundtrip test. Local73 tests PASS; Windows rerun pending.

## Matrix planning slice

New pure mixed-radix planner, unique combinations/history scope, W/K, seeded coprime traversal and heuristic lookahead balance. Candidate+wall-clock budgets/cancellation return SEARCH_LIMIT/CANCELED, never false infeasibility proof. Exact small-product and huge logical-space tests included. Local84 tests PASS. No reservation/database/render/UI matrix integration claimed yet.

## Local batch slice

Bounded/no-follow folder scan, output subtree exclusion/dedup, real per-file CPU render preserving source; failures/collisions isolated and never called verified reuse. Real two-video+corrupt fixture and collision rerun pass. Local90 tests PASS. Batch UI, immutable source snapshots and durable queue recovery remain open; not a hostile-filesystem isolation guarantee.

## Regression and UI consistency checkpoint

Scan-limit now retains already visited candidates before returning PARTIAL; invalid checkbox state cannot unlock a cue; randomized interval sweep matches a pairwise oracle. Shared native theme keeps subtitle table/header contrast consistent with the main app. Local92 tests PASS; fresh screenshots inspected with synthetic data only. Full design/interaction acceptance remains open.

## Readability/static gate

Ruff0.17.3 added as locked developer tool from PyPI; newly authored source/tests formatted, imports cleaned. Intentional sanitized Qt thread catch boundaries and stable ValueError contracts explicitly documented at their lint exceptions, not runtime-test exemptions. Qt model root-index default made explicit. Static+format checks and unchanged92-test suite pass locally; CI now enforces both.


## Ledger schema hardening

Opening a ledger now refuses nonempty unversioned databases and exact-schema drift, including extra triggers/indexes, changed constraints/defaults and missing version1 table. Transactional initialization and rejection preserve existing schema/data/version; constructor failures close their connection. Original rebuild schema indentation remains compatible. 96 local tests PASS including rejection/no-mutation and all prior lease checks; no migrations or production queue acceptance implied.


## Native batch UI slice

New batch_editor.py + shared worker.py, main-app launcher and child-worker close guard. One folder/output pair, asynchronous scan and per-file CPU render, checkbox/output-name review, invalidation on folder change, partial scans blocked from export, immutable selected tuple, cancel/close waits. Full batch presets/multifolder/filter tree/durable recovery are still open. Synthetic actual UI scan/export/collision preserves source; parent close and selection capture regressions included. 101 local tests PASS. Native dialog screenshot inspected with explicitly synthetic rows; runtime acceptance Windows remains separate.

Escape/reject batch interruption now follows window Close cancellation/wait; 102 local tests PASS.


## Early frozen startup proof — P02-06

Pinned developer-only PyInstaller6.22.3 with public-PyPI hashes in uv.lock. Explicit CLI smoke starts real Editor/SRT/batch windows and verifies six booleans, idle workers and frozen identity. Owned child timeout60/output16KiB; PATH cleared so external media tools are not required for startup. Linux one-folder build and frozen smoke PASS; 104 source tests and Ruff PASS. Windows3.12 CI build/smoke added but not yet run for this commit. No binary upload, installer, signing, bundled FFmpeg, release or user-machine acceptance. Local frozen output is ignored.

Deselection regression clears the implicit export source and preview without removing media/edits; explicit reselection restores it. 105 local tests PASS. Frozen Windows checkpoint remains separately pending.


Hosted Windows packaging evidence: exact remote dceeb5ba50272c1524a03775e117e32c9a9d6a6b, run41113327409/job124261038897. Python3.12.10 Windows x64, PyInstaller6.22.3/PySide6.8.3. Actual one-folder EXE launched with cleared tool PATH; all six window/idle/empty-state checks true and frozen=true, exit0. Verified logs, not inferred from source tests. This does not certify installer/signing/media/fonts/GPU or target Windows10/11 user hardware.
