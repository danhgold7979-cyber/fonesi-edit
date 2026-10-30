# P11 — Profile handoff and revocation ordering plan

- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 76924228bc949373d7d0d5de2a1ef48203671464
- Scope: P03-09, P05-09/P05-10, P10-07, P11-08; AUTH-06, AUTH-08, AUTH-09.

## Evidence reviewed
Read AGENTS.md, README.md, master plan, product requirements, traceability, coverage, current status, execution ledger, browser lifecycle plan, browser implementation and session integration tests.

## Gap
The profile bridge is looked up before the write transaction in receive_session. Revocation can occur after that lookup and before the session update. The request must verify the current bridge record while holding the same SQLite writer lock used by revocation.

## Implementation
1. Move the authoritative bridge lookup into the BEGIN IMMEDIATE transaction in receive_session.
2. Confirm the bridge still maps to the same profile used by the platform binding before changing the binding or session record.
3. Keep the account identity comparison, encrypted session write and binding status update in that transaction.
4. Add deterministic tests for revocation-first and handoff-first ordering. Rejected requests must not create a binding or change an existing binding.
5. Preserve single-use pairing, account mismatch protection, profile isolation, expiry handling and job snapshot references.
6. Run phase checker, full test suite, Batch/Matrix benchmarks, production/native-host builds and packaged proof on Linux and Windows.
7. Update AUTH traceability, P11 results, coverage, current status and ledger only after exact-HEAD CI passes.

## Acceptance
- [x] Revocation-first ordering rejects the stale bridge request without changing profile binding state.
- [x] Handoff-first ordering commits the complete update before revocation.
- [x] Existing account isolation, mismatch, expiry, pairing and job snapshot tests pass.
- [x] Exact-HEAD Linux and Windows CI, production builds and packaged proof pass.

## Limits
This is synthetic database/integration evidence. It does not certify live browser delivery, OS credential storage, provider login or physical Windows acceptance. P11/P12 remain open until all master gates are evidenced. Do not merge to main.


## Execution result — PASS (30/10/2026)

Plan d684602 → implementation e4f7b3d → ordering compatibility fix 683f532 → exact-HEAD CI 41088435585 SUCCESS.

receive_session revalidates the bridge only after BEGIN IMMEDIATE; profile existence, binding creation, identity comparison, protected session write and binding status update share that transaction. revoke_pairing uses the same writer lock. Two deterministic concurrency tests prove revoke-first rejects the stale bridge without creating binding/session state, and handoff-first commits the complete session before revocation.

Linux: 892 passed, 0 skipped, 0 failures/errors. Windows: 888 passed, 4 intentional platform skips, 0 failures/errors. Both runners passed Batch 128-source dry-run (failed_count=0; 5.873457 s Linux / 7.603461 s Windows), Matrix 2,000 logical outputs (complete=true, max spread 5; 11.955144 s Linux / 9.672810 s Windows), production desktop/native-host build and frozen packaged proof (6.419 s Linux / 9.937 s Windows). Windows development artifact: 197,426,877 bytes.

Separate follow-up remains: pairing_code still inserts a pending code outside the revocation writer transaction. Serialize code issuance with the same lock and add a deterministic regression before claiming the full pending/active pairing lifecycle is closed.

## Limits
