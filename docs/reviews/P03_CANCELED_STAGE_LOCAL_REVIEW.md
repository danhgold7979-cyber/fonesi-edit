# Canceled stage cleanup — HOLD: quiescence uncertainty

2026-11-01. Read-only bounded review. All seven supplied SHA256 pins matched, including publication5e997406b4d2c71473e84fd9ce5f6f163d74926201402a300096690df7e5477c and canceled helper ebf5a338b1ccda54f9099f149a5abaf96154809c170ac33826de9d0c0d16f945. No aggregate/native test rerun.

## Blocking lifecycle defect
_staging_operation unconditionally clears its active latch in finally, including validate_media/run_owned exceptions whose meaning is explicitly unconfirmed process retirement. The canceled route can then accept a database cancellation acknowledgment and enter destructive cleanup, although neither acknowledgment nor Python stack unwind proves the writer/validator process is quiescent. This newly exposes a path that completed cleanup did not admit because completion requires successful staging.

Independent neutral control-flow reproduction: raise ProcessError('Process retirement unconfirmed') inside _staging_operation; afterward _staging=False and no sticky lifecycle-uncertainty field exists. This is control-flow proof, not an actual native retirement-failure claim.

Required fix: sticky fail-closed quiescence-unknown state for validator outcomes without confirmed retirement, consulted by both cleanup entry points even after job cancellation acknowledgment. Until a typed runner retirement outcome exists, conservatively treat validator exceptions as uncertain. Do not erase that state on later successful operations or DB acknowledgment. Add injected validator retirement-unknown→ack canceled→no native helper/no deletion causal regression. Ordinary canceled-and-confirmed-retired cases are not a substitute.

Other reviewed boundaries look consistent: exclusive-created original FD retained before producer failure; StageOwnership not publishable receipt; attempted/created mismatch retains unknown stage; exact live same-attempt canceled/prepared journal and no artifacts/history; no claimed/linked cleanup; native object-bound deletion only; entered-error UNKNOWN and session retired. Existing postflush test now observes completed writer instead of obsolete anchor timing, preserving actual cancellation boundary.

[cancel-cleanup] alone selects four targets/affected tests and skips unchanged aggregate/frozen/Qt installation. Native canceled-stage integration remains pending. No new requirement/phase acceptance recommended.

## Correction recheck 12:01 UTC — source CLEAR for affected native CI
Verified publicatione99d140b1d21d8eda09c7e271dfb44c5108d8d3048b68531597f9263cdf0cf64, tests29827d5c77cc61d64cb5a1a24cde7d4bdfe8f3d61af3a3b8ac71c1c410a088eb, contractf40d88e226530cb69cb687a6d6dc8347ee7d9942f1e2a27e4def697ca2e1504b. Other reviewed pins unchanged.
Any validator BaseException now sets sticky _quiescence_unknown, independently of active-call latch. Both cleanup entries and worker/claimed/canceled authority guards refuse it; DB cancellation acknowledgment cannot clear it. This conservatively retains stages for all validator failures until typed retirement evidence exists, not only a matched exception string.
Independent exact causal test1 PASS/18 deselected, exit0: injected unknown retirement then cancel acknowledgment refuses both cleanup methods/worker guard, native helper forbidden, original staged bytes retained. Initial test-selector typo selected no tests/exit5; corrected exact selector above, no full baseline repeated.
Lifecycle blocker closed. CLEAR permits scoped four-target canceled-stage CI only. Actual native canceled cleanup remains pending; no additional assertion/task/phase closure or general failed/restarted cleanup acceptance.
