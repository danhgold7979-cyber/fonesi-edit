# P11-08 / AUTH-06…AUTH-11 — Browser session expiry, identity and profile isolation

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 2df51cc4a6e3c02632415885eb20e24dfb8128a9
- Alignment: P03-09 (account/profile-scoped sessions), P05-09/P05-10 (session readiness and account-bound jobs), P10-07 (resume must retain original account), P11-08 (Chrome A/B, expiry, mismatch, bridge), AUTH-06…AUTH-11.

## 1. Evidence reviewed

Read AGENTS.md, README.md, the master implementation plan, Settings/browser specification sections 3–8, requirements traceability, implementation coverage, current status, execution ledger and P11 results. Inspected `browser.py`, `downloads.py`, Settings profile display, `test_browser.py` and `test_downloads_sessions.py`.

Existing coverage proves independent Chrome profile directories, per-profile pairing revocation, single-use/concurrent pairing codes, Linux DPAPI fail-closed behavior, account-bound download snapshots and refusal to silently switch identities. However, the session lifecycle has no direct regression for successful synthetic handoff into two profiles for the same platform, identity-mismatch preservation of the old encrypted snapshot, partitioned/foreign-domain cookie rejection, or expiry state transition.

## 2. Gaps

1. `cookie_jar` filters expired cookies and raises `Session expired` when no usable cookie remains, but it leaves the binding marked `available` and retains the stale encrypted snapshot. Settings can therefore display a stale session as available after the download detects expiry.
2. No test currently proves that Chrome A and Chrome B can hold different identities for the same platform without crossing cookies.
3. No direct test proves that an incoming different identity is rejected without replacing the existing encrypted snapshot, or that foreign-domain/CHIPS cookies are excluded from the connector jar.

## 3. Implementation

1. When `cookie_jar` finds no non-expired cookies, atomically delete only that binding's stale `session:<binding_id>` secret and set the binding to `login_required` with a fresh checked timestamp before raising the existing explicit expiry error.
2. Preserve current behavior for expected-identity mismatch: reject the job without mutating the binding or replacing/deleting the stored session.
3. Add synthetic tests with a reversible test-only `protect` stub (never a production fallback) to exercise successful receive/decrypt for Chrome A/B with different same-platform identities.
4. Verify account mismatch leaves the old secret bytes, binding identity/status and old cookie jar unchanged.
5. Verify foreign-domain and partitionKey cookies never enter the jar; if no transferable cookies remain, fail closed and do not store a session.
6. Verify expired snapshots are removed from the secret store and transition the binding from `available` to `login_required`; re-pair/relogin remains explicit.
7. Keep the real `protect` implementation and existing Linux no-plaintext fallback test unchanged. Do not inspect/decrypt real Chrome databases or use live accounts/tokens.
8. Run phase reference checker, complete source suite, Batch/Matrix benchmarks, production desktop/native-host builds and frozen packaged proof on Linux and Windows. Update AUTH traceability and P11 results only after exact-HEAD CI passes.

## 4. Acceptance criteria

- [ ] Chrome A and Chrome B can hold distinct same-platform identities and cookie jars without cross-profile leakage.
- [ ] Incoming account mismatch is rejected without mutating the old encrypted session, identity or status.
- [ ] Foreign-domain and partitionKey cookies are excluded; no transferable cookies means no session is stored.
- [ ] Expired cookie jars fail with an explicit relogin message, delete only the stale binding secret and set that binding to `login_required`.
- [ ] A later explicit relogin/bridge handoff can restore the binding to `available` without affecting another profile.
- [ ] Job snapshots retain only account/profile references and expected identity, never cookie values or session tokens.
- [ ] Existing pairing, revoke, DPAPI fail-closed, job-account binding, download and complete-suite regressions remain passing.
- [ ] Exact-HEAD Linux and Windows CI, production builds and frozen packaged proof pass.

## 5. Limits

All new tests use synthetic cookie dictionaries and a test-only reversible protection stub. They do not certify real Chrome login, DPAPI persistence on a user's Windows account, Chrome profile lock/challenge flows, live connector acceptance, website policy/rate limits or all platform-specific cookie semantics. Do not merge to main or force-push.
