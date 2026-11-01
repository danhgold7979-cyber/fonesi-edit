# P03 checkpoint evidence reconciliation — verified, scoped PASS

2026-11-01. No tests rerun. Independently verified all 21 source/JUnit/frozen receipt member hashes across runs 41295642110, 41296135792 and 41296433758. Final two local ZIP hashes match GitHub artifact API digests; ZIP member bytes equal all five retained final files. GitHub latest job steps confirm both final jobs completed SUCCESS and Windows312 PyInstaller build plus frozen checks actually ran successfully.

Final public source: 61622936684fbbd7faa56eaeb332cc877170b619
Final tree: c8580226a98f022a2001bf924ed18359a2a71a49
https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41296433758

## Counts independently parsed from JUnit

| Run/scope | Runtime | PASS | SKIP | FAIL |
|---|---|---:|---:|---:|
| 41295642110 full source | Ubuntu Python3.12.15 |491|13|1|
| same | Ubuntu Python3.13.17 |491|13|1|
| same | Windows Python3.12.10 |475|22|8|
| same | Windows Python3.13.16 |475|22|8|
| 41296135792 affected repair | Ubuntu Python3.12.15 |48|0|0|
| same | Ubuntu Python3.13.17 |48|0|0|
| same | Windows Python3.12.10 |47|0|1|
| same | Windows Python3.13.17 |47|0|1|
| 41296433758 final boundary | Windows Python3.12.10 / SQLite3.49.1 |4|0|0|
| same | Windows Python3.13.16 / SQLite3.50.4 |4|0|0|

Each original full run had 505 cases. The original failures were receipt-error wording (all targets), six media-discovery identity cases and the empty-host-candidate test assumption (Windows). Intermediate repair closes wording/media cases; final boundary tests correct and pass the no-fallback/unchecked-candidate contract. Do NOT add the above counts into a new aggregate or call latest full suite green. Python313 patch versions differ: original full Windows .16, repair .17, final .16.

## Non-skipped native/UI/publication evidence

Original full Windows jobs each actually passed: 11 windows_process cases, 17 queue_commands cases, 7 root_relink cases, 5 project_recovery_ui cases, 13 coordinator_ownership cases, 9 publication_recovery cases, and 32/33 publication_session cases. The remaining publication_session integration was SKIPPED because actual FFmpeg was unavailable. Qt evidence is automated/offscreen, not interactive desktop usability proof. Other Windows skips include POSIX-only process/probe fixtures and real FFmpeg-dependent validation/probe. These are not promoted to PASS by the final boundary run.

Verified local ancestry deltas f996800→f54ff07→0034d51: application files changed only jobs/repository.py (message text) and media/discovery.py (fresh nofollow physical stat); latter received affected native tests. Final delta changes tests/harness/workflow/docs only. Unchanged native/UI/publication tests retain prior exact-source evidence; they were NOT rerun at final commit. This supports reviewed delta carry-forward, not a fictitious latest aggregate.

## Frozen boundary

Actual Windows312 onedir build and five frozen cases PASS: schema, valid subtitle, invalid timestamp refusal, explicit-empty-encoding refusal, candidate discovery with explicit missing Chrome/no fallback. Host Chrome may be listed UNCHECKED while selected explicit Chrome remains INVALID_EXPLICIT_PATH/candidate null. Report confirms exact MIT bytes and input/application-data nonmutation checks.

Harness-reported executable SHA256: f9befc6a9941dc22fed7d8b86bc9c8dfacafea7f83e4aae50d1b21302804f6ef.
MIT SHA256: 93d82c4caf14f9ac8845377399860ee8e3628481d8017ebe33febb8bf7236211.
Binary itself was not downloaded or independently rehashed. No frozen Windows313, GUI/media/GPU/provider/release readiness inferred. No new requirement child or whole-phase acceptance closure.
