# Fonesi Edit workflow

- Before starting any phase, read `docs/IMPLEMENTATION_PLAN.md`, the related requirements and current phase results.
- Write/update `docs/phases/Pxx_PLAN.md` before implementing that phase. Record master-plan alignment, task IDs, dependencies, artifacts, checks and external blockers.
- Finish and verify each phase against its gate before marking it complete. Record evidence in `docs/phases/Pxx_RESULTS.md`. A prototype, Linux result or missing credential is not Windows/platform acceptance.
- User steering: continue implementing all independent work across phases without stopping for external credentials/network/Windows/GPU. Read master and create each phase plan before its work. Keep blocked acceptance checks separate; never mark them complete or claim external verification.
- The user authorized implementation and pushing plans/code to the configured GitHub repository. Use normal commits and non-force pushes; preserve unrelated changes and never commit secrets, browser profiles, downloaded media or local runtime artifacts.
- Keep source media unchanged. Validate generated outputs before reporting success. Never weaken TLS, artifact checks or Chrome/OS protections.
- Test meaningful changes with the relevant checks. Keep unavailable, skipped and failed checks separate from passed checks.
- Do not delegate to sub-agents unless the user explicitly requests delegation.

## Clean generation 2026-11-01 (supersedes old implementation status)
- The active implementation is rebuilt from scratch. Do not import archived src/tests/scripts or dirty changes. Preserve canonical source requirements and licensing/reference artifacts.
- Work only in repository danhgold7979-cyber/fonesi-edit on the single integration branch develop/fonesi-full. Do not create/use phase-specific development branches; all phase work remains integrated in the same application. Keep main stable and never merge without explicit release authorization. Use ordinary commits, no force/history rewrite.
- Old CI/PASS is historical only. Current evidence lives in docs/evidence/records.json, with generation and exact new SHA. 95 requirement groups require child-level evidence, not one example per group.
- Before any source reset/removal verify recoverable archives/inventory; never reset/delete the separate old dirty checkout.
- All 94 task scopes remain mandatory; local/blocked/accepted distinct. Developer correctness checks are not Windows/Chrome/provider/GPU acceptance.
