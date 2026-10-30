# P11-08 / AUTH-06 — Serialize pairing-code issuance with profile revocation

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: fc3d70dd3a93923df1a00dcc01c1357704bbf60e
- Alignment: P03-09 profile/session lifecycle, P05-09 session handoff, P11-08 bridge revocation, AUTH-06/AUTH-08.

## Evidence reviewed
Read AGENTS.md, README.md, master plan, product requirements, traceability, coverage, current status, execution ledger, browser lifecycle and bridge revocation plans, browser implementation and session tests.

The previous exact-HEAD source/test commit 683f532 passed [CI 41088435585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41088435585): Linux 892 passed; Windows 888 passed + 4 intentional skips; both production/native-host builds and frozen proofs passed.

## Gap
revoke_pairing and receive_session now serialize using BEGIN IMMEDIATE, and pair consumes a pending code under that lock. pairing_code still checks the profile and writes a pending code in separate operations. If issuance overlaps revocation, the pending code can be inserted after the revocation sweep and remain usable.

## Implementation
1. Generate the one-time code and validate the profile inside one BEGIN IMMEDIATE transaction.
2. Store only the SHA-256-derived setting key and profile/expiry metadata; return the raw code only to the caller.
3. Keep pair consumption and revoke_pairing on the same writer lock.
4. Add a deterministic race test where issuance owns the writer lock, revocation waits, and then removes the newly committed pending code.
5. Add a control test that a new explicit pairing-code request after a completed revocation is still allowed.
6. Preserve single-use pairing, profile-scoped revoke, session handoff, identity mismatch, expiry and DPAPI behavior.
7. Run phase checker, full suite, Batch/Matrix benchmarks, production/native-host builds and frozen packaged proof on Linux and Windows.
8. Update AUTH traceability, browser lifecycle plan, P11 results, coverage, current status and ledger only after exact-HEAD CI passes.

## Acceptance
- [ ] Pairing-code profile validation and pending-code insert occur in one writer transaction.
- [ ] Revocation waits for in-flight issuance and removes its pending code when issuance commits first.
- [ ] A fresh explicit code requested after revocation remains usable.
- [ ] Existing pairing, revoke/handoff ordering, profile isolation, session expiry, mismatch and job snapshot tests pass.
- [ ] Exact-HEAD Linux and Windows CI, production builds and frozen packaged proof pass.

## Limits
This is synthetic SQLite lifecycle evidence. It does not certify live extension delivery, real Chrome/DPAPI, provider login or physical Windows acceptance. Do not merge to main or force-push.
