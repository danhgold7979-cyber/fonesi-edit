# Fonesi Edit workflow

- Before starting any phase, read `docs/IMPLEMENTATION_PLAN.md`, the related requirements and current phase results.
- Write/update `docs/phases/Pxx_PLAN.md` before implementing that phase. Record master-plan alignment, task IDs, dependencies, artifacts, checks and external blockers.
- Finish and verify each phase against its gate before marking it complete. Record evidence in `docs/phases/Pxx_RESULTS.md`. A prototype, Linux result or missing credential is not Windows/platform acceptance.
- Continue independent tasks inside the current phase when a prerequisite is blocked. Do not silently skip a gate or mark blocked work complete.
- The user authorized implementation and pushing plans/code to the configured GitHub repository. Use normal commits and non-force pushes; preserve unrelated changes and never commit secrets, browser profiles, downloaded media or local runtime artifacts.
- Keep source media unchanged. Validate generated outputs before reporting success. Never weaken TLS, artifact checks or Chrome/OS protections.
- Test meaningful changes with the relevant checks. Keep unavailable, skipped and failed checks separate from passed checks.
- Do not delegate to sub-agents unless the user explicitly requests delegation.
