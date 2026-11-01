# Backup restore + CLI — corrected source CLEAR for scoped CI

2026-11-01. Bounded review, no aggregate/native rerun.

## Blocker
_validate_copy uses SQLite substr(TEXT) for id/name/origin. SQLite TEXT substring stops at embedded NUL, so it can validate a truncated prefix rather than the stored row. Independent actual exact-schema v1 backup with row id UUID + NUL + HIDDEN and document.project_id UUID successfully restored and registered ownership, then reopening ProjectStore and load(UUID) raised KeyError. This violates complete row/document consistency validation.

Use bounded BLOB projections/type checks for metadata, strict UTF-8 decode and full original-value comparison; reject over-bound values before parsing. Avoid reducing existing Project model scope: it accepts noncanonical UUID spellings (e.g. braces) and matching embedded-NUL names; restore must not reject otherwise supported backups merely because a fixed 36-character UUID or NUL-free name was assumed. ID NUL itself fails UUID validation; origin NUL fails _origin. Add negatives for mismatched NUL-suffix id/name and invalid origin plus supported metadata positives.

## Other result
Source no-SQLite read, original FD/per-API signatures, bounded copy/hash, exclusive target, receipt-last registration and post-registration UNKNOWN classification are sound in reviewed cooperating namespace scope. Failed new destinations are retained; no path deletion/overwrite/retry. CLI remains mutually exclusive/headless/sanitized. No additional blocker found.

Independent meaningful tests: real migration-generated v1 backup restore/reopen; post-validation target hash drift; four fault boundaries (including post-registration) — **6 PASS / 19 deselected, exit 0**. No unchanged aggregate run.

Workflow [project-restore] ALONE source review: four default targets, exact restore/projects/project-identity/subtitle-CLI files, Linux Qt apt and unrelated aggregate/plan/schema/frozen excluded; normal default unchanged. Workflow itself is suitable, but source publication remains HOLD pending metadata correction. No native proof or criterion closure inferred.

## Targeted correction recheck, 13:41 UTC
Final restore SHA256 `17b20f9edbdfc2cfefcc559421a18818624098ff64a6f71462a95b3e0330ddae`, tests `124f26ec1c30543bccee79d2beecc89845013a2f0b81221d600286e195b7d276`. Bounded BLOB projections plus strict decoding now compare complete IDs/names/origin, preventing SQLite NUL-prefix truncation. Supported urn:uuid and matching NUL/Unicode name retained. Blocker closed.

Independent metadata/origin selection: 5 PASS /24 deselected (includes existing real migration-original-rows test because its name matched origin); separately exact supported-spelling test 1 PASS /31 deselected. All exit0. Earlier six-test pass ran while author correction was being installed; do not attribute it to the obsolete initial source pin. No aggregate repeat.

Source and workflow CLEAR for target CI. Explicit limitation: rollback-format v1 actual migration backup is supported; current WAL-format v2 _backup output is refused without touching source. The v2-origin test prepares an offline DELETE-format fixture using SQLite first, so it proves origin preservation in supported format, NOT direct import of untouched WAL-format backup. This distinction must remain in contract/evidence and later criterion assessment; no automatic conversion or all-backup claim. No criterion closure yet.

Final type-preservation correction: verified restore `a821b35821764bb136c03c09174dce7cc7166f155d6b52e800cde6cdce48fdaa`, tests `7657f1a0a15512bf188e73fbbe89744e9fe530320ac5e24563d4778cf225fcbf`. typeof(TEXT) gates prevent BLOB IDs from decoding to valid UUID yet failing text lookup, and BLOB origin from passing text validation then failing normal load. Independently 3 new BLOB negatives PASS /29 deselected, exit0. Final source CLEAR; CLI/workflow unchanged. Supported-spelling run immediately preceded pin announcement while new tests were present (31 deselected); reported count corrected above.
