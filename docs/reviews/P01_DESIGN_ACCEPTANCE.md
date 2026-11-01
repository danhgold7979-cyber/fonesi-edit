# P01 targeted design acceptance — dbc3f30

Reviewed exact commit `dbc3f30ed9122313c6aa7906fde74a5120651b3d`, tree `e515afcfefe877a369a2b4326b8d7e4ef29c4fbc`, clean worktree on inspection, 2026-11-01 UTC. Scope: remaining R1/R2 only; six previously closed findings retain their earlier design disposition. Original-spec/reference preservation checks reused because unchanged.

## Verdict: READY FOR P01 DESIGN ACCEPTANCE

Both remaining findings are closed at design level. The master/per-phase plans and contracts are sufficiently explicit to begin the planned P02 experiments and subsequent independently gated fresh implementation. No remaining blocker from this review requires further planning before starting that work. This does not certify all future design choices or implementation; P02 decisions and per-phase contracts/tests remain enforceable gates.

### R1 closed

Probe now contains container summary plus discriminated video/audio/subtitle/image stream records; stream-specific geometry/SAR/rotation/PTS and audio format are no longer ambiguous global metadata. Subtitle stream can exist and selected indices bind by type. Explicit source-relative vs decoder-PTS/output-placement formulas apply stream offset once; sidecar origin and cue segment binding are stated. New nonempty example includes two video, two audio and subtitle tracks with differing metadata and explicit selections. Runtime validators must enforce reference/type/semantic rules; schema design does not pretend these validators already exist.

### R2 closed

Exact affected assertions expanded to retain all seven reported conjunctions: no machine-wide PATH mutation; explicit click/auto-update opt-in before download/install; same-auth multiple page/channel profile sharing; fit/preset/custom zoom; keyframe recording-OFF base/scope behavior; easing curve display/preview; profile color/label/version/check. Original source links remain, count438 unchanged because existing assertions were strengthened rather than artificial criteria inflation.

## Verification

- `python scripts/check_plan.py`: PASS12phases/94tasks/95groups/438child assertions/392source records/101acyclic artifact milestones/0runtime evidence.
- `python scripts/check_schema_design.py`: PASS2valid structural examples/22negative structural cases; semantic R01–R15 NOT_IMPLEMENTED; runtime NOT_RUN.
- Reviewed targeted contract/schema/criterion diff and nonempty stream/cue selections. No contradictory regression observed within targeted scope.

## Acceptance boundary

This is P01 DESIGN readiness, not runnable tool completion or runtime100%. Author may record independent P01 design review against this SHA/document and update P01 results. Do not turn NOT_RUN feature criteria into PASS. P02 engine/toolchain/provider/Chrome/GPU/Windows experiments, fresh runtime semantic validators, actual media tests, publication crash proofs and target acceptance remain future work. No old implementation/test evidence transfers to the clean generation. Root retains remote publication/branch-cleanup responsibility.
