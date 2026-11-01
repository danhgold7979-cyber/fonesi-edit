# Completed cleanup integration — HOLD for uncertainty classification

2026-11-01. Read-only review, no unchanged tests rerun.
Verified five supplied pins: filesystem e6ef599e43d2da3118709dcd915c4964e5c65b0233d7b3295c2713e01f200a69; completed_cleanup93b6052a38ddf33fb2e4a9657cac21d9b1403bb23b1935c69f7704a875be99cb; publicatione7da9f0b3c2da6d4b00c3b55e27639fc79e067ca66aa16674dab891f78452c45; tests7ddc5cd8bd9bd546b24d31b9e1bb4b1be1862b4a2e0ec50d0be74217a9c0ac9f; workflow1e575db852b7ce1a5c7e06f6d4f85c4d53f6ce969d4357db2767cbc3a6415e3b.

## Blocking classification gap
PublicationSession.cleanup_completed re-raises every JobConflict/PublicationError unchanged, including after one or more native effects. If a payload/member was disposed then current history/epoch guard fails before directory/next-member deletion, caller receives known-conflict form rather than promised partial-cleanup UNKNOWN. Session closure prevents replay, but does not fix outcome classification.
Track effect/transfer phase or conservatively wrap exceptions after entering native cleanup as PublicationUnknown, preserving cause. Only provably pre-effect preflight may retain ordinary refusal. Add causal post-effect authority failure regression with exact UNKNOWN assertion, completed state preserved, no automatic replay.

No other blocker found in bounded source review. Original file and directory capabilities persist from creation; mutable close-once ownership avoids stale raw-close callbacks. Final bridge continuously retains object while deletion handle retires, then strong final pin protects subsequent directory disposition/readback. Exact journal/history/epoch callbacks and no POSIX/path-delete fallback remain. Actual Windows delete-pending/final-bridge interaction is NOT established by prior primitive success; this integration must prove it or fail closed. [worker-cleanup] alone preserves four targets and runs five affected files, without unchanged aggregate/frozen repeats.

## Independently verified primitive evidence
GitHub run https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41301972313 has two completed SUCCESS jobs. Exact source ccfa0b1de7b6929c9909b0dc1b498b65ef5b00f1, tree94399c9697a0c9613a197faa9cd6cd196f66837a. Both local ZIPs match API digests, all4 retained source/JUnit members match ZIP bytes/hash manifest.
Windows3.12.10/SQLite3.49.1 and Windows3.13.16/SQLite3.50.4 each:9 native PASS +1 platform-neutral control PASS +1 non-Windows branch SKIP. Non-skipped native cases cover final-hardlink survival, file/directory swap refusal, empty/nonempty/late-child directory handling, authority-loss/no-replay, conflicting DELETE handle, unmarked close and20-cycle handle plateau. Not production integration, latest aggregate, power-loss or full-P03 acceptance.

## Progress follow-up
Read added real SQLite/owned subprocess callback test: repository lives on runner thread; end leaves exact job unchanged; cancellation suppresses subsequent event. Provenance hash receipt and thread-affinity clarification are consistent with unchanged reviewed progress source. No duplicate test/real FFmpeg execution performed.

## Final correction 11:44 UTC — source CLEAR for scoped affected CI

Verified final publication SHAa1e86b35cf86686deb14c917111c17c1a96a4122990c21f9e691a717cc06dcc0, tests63f3d84061afec0d74f7dd0b2bffa195bb43f549dd851887c1dc4fcc3674f6fe, workflow1c964255add731bf58964ebee3493258f2f97f1d95411db8f5e4bc40ea0a7353. Other previously inspected integration pins unchanged.
entered_cleanup is latched before native helper entry. Later known-conflict/publication errors become PublicationUnknown preserving cause; true preflight refusal remains distinct. Close errors still become UNKNOWN and session retires. Independent platform-neutral causal classification test:1 PASS/12 deselected, exit0. Fake helper explicitly tests control flow, not native deletion proof. Additional native first-member-deleted then authority-failure test awaits Windows CI.

Classification blocker closed. [worker-cleanup] alone runs four targets/five affected files, skips unused Linux Qt apt plus unchanged frozen/aggregate/plan/schema; ordinary aggregate unchanged. CLEAR is source readiness for this scoped checkpoint only. Critical classic-disposition/final-read-bridge interaction must still pass actual Windows integration or safely refuse; no inference from earlier primitive evidence, no new requirement/phase acceptance.
