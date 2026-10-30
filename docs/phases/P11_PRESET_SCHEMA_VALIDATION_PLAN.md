# P11-05 / OPS-07 — Strict preset file contract and resource diagnostics

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: ffc612c5eee838e11dd1355ff9f6a3a8a27cc18c
- Master alignment: P11-05 (preset migration/options and traceability), OPS-07 (preset import/export/copy groups/resources missing), P11-07 (data/privacy diagnostics).

## 1. Evidence reviewed

Read AGENTS.md, README.md, docs/IMPLEMENTATION_PLAN.md, docs/PRODUCT_REQUIREMENTS.md, docs/IMPLEMENTATION_COVERAGE.md, docs/REQUIREMENTS_TRACEABILITY.md, docs/CURRENT_STATUS.md, docs/PHASE_EXECUTION_LEDGER.md, docs/phases/P11_PLAN.md, docs/phases/P11_RESULTS.md, docs/phases/P12_PLAN.md, docs/phases/P12_RESULTS.md, src/fonesi_edit/app.py, src/fonesi_edit/domain.py, src/fonesi_edit/storage.py, src/fonesi_edit/browser.py, src/fonesi_edit/ui/pages.py, tests/test_app_integration.py, tests/test_editor.py, tests/test_shortcuts.py, and tests/test_browser.py.

## 2. Current gap

- MainWindow.export_preset writes schema version 1 and strips source clips/clip bindings, but it has no shared format validator.
- MainWindow.import_preset reads arbitrary-size JSON, checks only the outer version, and immediately passes the nested composition to Composition.from_dict. It does not reject duplicate JSON keys, unexpected envelope keys, non-empty source clips or layer clip bindings, or malformed/unsafe preset names before persistence.
- The domain composition validator checks rendering fields, but it is not a strict preset-envelope validator and does not provide missing-resource diagnostics.
- There is no focused preset import/export regression module.
- Profile-scoped extension pairing revocation already exists in browser.revoke_pairing and Settings UI; it removes only the selected profile's bridge/pair records and explicitly preserves the Chrome profile.
- App-level Undo/Redo already yields to focused native text controls, and subtitle table undo is separately covered. Do not rewrite these completed paths in this slice.

## 3. Scope and implementation

1. Add a UI-independent presets.py module with one canonical schema-v1 builder/parser and explicit name validation.
2. Bound imported files to 2 MiB; decode UTF-8 safely; reject malformed JSON, duplicate object keys, non-object roots, unsupported/non-integer schema versions, unknown envelope fields, invalid names, and invalid composition payloads.
3. Require preset compositions to contain no source clips and no layer-to-clip bindings. Validate the composition with the existing domain model and secret-key guard before any database write.
4. Preserve referenced logo/font/audio asset paths; report missing local resources without silently copying, deleting, relinking, or changing those files.
5. Route MainWindow import/export through the shared contract. Import must validate completely before Store.save_named; it must not mutate the active composition/project.
6. Add focused unit tests for valid round-trip, source stripping, asset references, missing resources, duplicate keys, malformed/oversized payloads, unknown fields, unsupported versions, secret fields and invalid clip bindings. Add Qt integration tests proving failed import does not create a saved preset and valid import creates exactly one preset.
7. Update P11 results, coverage, traceability, current status and execution ledger only after exact-commit CI evidence is available.

## 4. Acceptance criteria

- [x] A valid exported preset round-trips through the parser and preserves supported composition settings and external asset references.
- [x] Source clips and per-layer clip IDs never enter an exported or imported preset.
- [x] Malformed, oversized, duplicate-key, unknown-field, unsupported-version, secret-bearing or invalid-composition files fail before persistence.
- [x] Invalid imports leave the preset table and active project/composition unchanged.
- [x] Missing external assets are reported clearly while the valid preset remains importable.
- [x] Existing profile pairing revocation and focused text Undo/Redo regressions remain unchanged and pass.
- [x] scripts/check_plan.py, the full source test suite, production build and frozen packaged proof pass on Linux and Windows for the exact implementation/test commit.

## 5. Explicit limits

This slice does not claim real Windows user-machine, Chrome login, provider, GPU, HiDPI, filesystem power-loss or full 95-group product acceptance. No Chrome profile/session data is copied or deleted. Do not merge main.

## 6. Execution notes

The connected GitHub API was used for repository reads/writes. Local source execution was unavailable in this cloud turn; acceptance was gated on the exact GitHub Actions run below.

## 7. Execution result — PASS on CI

- Plan commit: [2774ef2](https://github.com/danhgold7979-cyber/fonesi-edit/commit/2774ef2955c44eee9a9bf61fcfec731231c4a5e4).
- Implementation: [a7f2328](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a7f2328fa3448b5e9664e83dcb5d0f7793f0bdec).
- Profile-scoped revocation regression: [e3d3272](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e3d3272cf8753fe08652b8f1d54bf8f5359214cb).
- [CI 41046744447](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41046744447) SUCCESS on exact HEAD e3d3272: Linux 817 passed; Windows 816 passed + 1 intentional POSIX-only skip. Both runners passed Batch 128-source synthetic FFprobe benchmark, 10^10-capacity logical Matrix benchmark (2,000 complete outputs; max per-scene spread 5), production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost download/UI proof.
- Batch dry-run: Linux 7.751278 s, Windows 10.102146 s; failed_count=0 on both.
- Matrix logical benchmark: Linux 19.860847 s, Windows 17.556047 s; 2,000/2,000 generated, complete=true, max per-scene spread 5 on both. No real 10-billion-media or real-media corpus claim.
- Artifacts: Linux evidence 391,472 bytes and Windows evidence 323,245 bytes (expire 2026-11-02); Windows development build 197,366,359 bytes (expires 2026-11-06).
- Profile revocation regression confirms profile A's bridge and pending pairing code are removed while profile A/B folders and both bindings remain, and profile B's bridge is unaffected.

The acceptance checks above close this preset/revocation regression slice only. They do not close all P11-05 requirements, P11-08, all 95 requirement groups, or any external Windows/Chrome/live-provider/GPU/power-loss gate.
