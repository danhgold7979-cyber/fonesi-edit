# Durable explicit tool preferences — initial source review, correction pending

2026-11-01 16:19 UTC. Source preferences41345ce1…/worker88d4d1a6…/inventory4574602a…/shell eed4ea30… reviewed. No remote/native/aggregate execution.

## Blocking causal finding
`save_preferences` returns `connection.snapshot()` AFTER COMMIT and receipt validation. A cooperating writer can commit a newer version/value after this transaction releases its lock but before readback. Outer Save then returns the OTHER writer's snapshot as its own successful save; UI claims that unrelated version saved and adopts its CAS baseline while displaying original requested fields.

Independent minimal reproduction using provided after_commit fault: existingv1; outer requestsA/v2; callback opens legitimate second save using currentv2 and commitsB/v3; outer returnsB/v3. Assertion confirmed. No malicious namespace race needed.

Fix: return own exact captured committed version/value/token after continuity validation (stale future CAS will correctly conflict), OR require readback exact intended version/value and classify divergence UNKNOWN/conflict. Never equate any successful postcommit read with own save success. Add deterministic cooperating-writer regression. Source clearance pending this fix.

## Other reviewed boundaries
Missing read no parent/file creation; foreign/empty/newer/receipt/header rejection before SQLite mutation; rollback header preflight prevents read-created WAL sidecars; exclusive initialization; original-FD continuity; complete schema checks; bounded full BLOB projection + TEXT types; same-store token and version/value CAS; no trust/readiness persisted. Existing-store unknown commit readback requires exact same token plus old or intended next snapshot. UI stale load preserves newer edits, unknown state survives stale results, workers waited before release. No execution/scan/activation on preference load. Initial create/receipt gap cannot be reconciled with absent prior token and must remain explicit recovery-needed, not promised automatic reload resolution.

Independent targeted tests:3PASS/22deselected exit0 (WAL preflight prevents SQLite access/sidecars; replacement cannot clear unknown; stale load/close waits). No unchanged full suite rerun.

## Correction verified — final source/workflow CLEAR,16:19 UTC
Final preferences `f01aa76d3ce27d86359bb0209d9a15ef4da10cc8e02d90d4c40c2008dc51ad4b` and tests `c5833b0f68ce467b45bfbe5e30632cd99842ab7e20302ca8f2ec26a71cc7b18b`: postcommit readback now requires intended version/value and original token when known, else UNKNOWN, preserving the concurrent writer's data without false save attribution. Independent exact causal test **1PASS exit0**. An initial selector matched no tests (21deselected/exit5), corrected to exact node; not a product failure or PASS claim. No baseline repeated.

Initial creation without prior token remains unreconciled within session by explicit design, no adoption/replay. Existing four UI/source pins unchanged. Workflow `e18415b7ffe1f9e78896f9f9d32ab353cd3d490b2247441f03091f6cc9f5467e`: `[tool-preferences]` alone selects four targets/eight affected files; Linux Qt retained, aggregate/schema/frozen excluded and no native FFmpeg marker. Defaults/permissions unchanged. Source and scoped workflow CLEAR; actual native receipt/criterion closure still pending. No new criterion accepted from local tests.
