# Native cleanup primitive review — HOLD for failure-latch correction

2026-11-01. Source-only plus platform-neutral causal probe; no actual Windows execution.
Verified source SHA521ce04ca9730627e1fbd8973ceaa168ca93b8c1b995bc6b3ed7a469d506d0ab and test SHAe05683aacdb3c9c65b79b70628a4451d33ecb96bbc8072d0eeda9b0f0022aad8.

## Blocker: failed authority callback does not retire mark capability
DeleteCapability.mark sets mark_attempted only after both guards and before_effect callback. If callback raises PublicationUnknown (lost authority), the same capability can be marked again with another callback. This violates failed-operation/no-replay contract and can revive deletion authority after an observed loss.

Independent neutral control-flow repro: allocate capability with mock guard, first mark callback raises PublicationUnknown; second mark reaches second callback, while mark_attempted remains False. No Windows call or deletion performed.

Fix: latch one-shot attempt before any guard/callback, or permanently revoke on any exception. Do not reset after authority/continuity failure. Add authority-loss then second-mark refusal/no-delete regression. Test must not call a second arbitrary callback or disposition.

No other source blocker found in bounded primitive review. OPEN_EXISTING, OPEN_REPARSE_POINT, directory BACKUP_SEMANTICS, original-to-bridge identity chain, parent identity check, deny-write/delete target sharing, one-byte BOOLEAN and pointer-width HANDLE declarations are consistent with proposed design. Native execution remains necessary to establish CRT attribute-only fstat support, reciprocal-sharing behavior, exact hardlink deletion, nonempty-directory refusal, inheritance and handle plateau. Safe refusal is not cleanup success. Production journal/quiescence/final-hash integration remains intentionally absent and requires separate review; no acceptance closure.

## Correction recheck 11:21 UTC — CLEAR for native prototype CI

Verified source691081bbe55162d11cb24c4de355ca507494dff44fe2d29175d82ecb87bda923, tests297a01631ba31a580064450892eeea97742b2e8ea3d472f33e8dab7e04c6a73f, workflow507a5256dca47c8bf16f598e8ab9ee0c3cdcb42ebb96c48bdcd93c62db9aedaf.
Attempt latch now precedes first guard/callback; guard/callback failures permanently revoke, any second mark refuses. Independent causal control-flow regression 1 PASS / 10 deselected, exit0. Blocker closed.
[windows-cleanup] alone selects Windows312/313 and primitive tests, excludes unchanged aggregate/frozen/plan/schema runs, labels non-integration evidence. Contract accurately keeps production cleanup absent and live journal/quiescence/final-hash integration pending. Source CLEAR permits scoped capability CI, not actual native/runtime acceptance. No additional baseline run.
