# First Settings navigation metadata chain — source CLEAR

2026-11-01 16:25 UTC. Verified inventoryeb76595c…, shell66c4a3bc…, inventorytesta3bf76a6…, firstopentestd74623d4… exact hashes. No native executable/baseline rerun.

One-shot attempt marked before dispatch; triggered only actual Settings navigation, not constructor. Existing preference worker loads missing defaults without files; foreign/corrupt errors suppress automatic fallback. Captured generation/revision + worker identity and wait(0) govern completion. Manual Scan/Load/Save/cancel increment generation before early busy refusal, preventing stale auto continuation; close sets stopping and cancels. Unknown-save state prevents auto chain.

Loaded fields intentionally update edit revision; queued scanner uses post-apply revision AND exact current fields, then rechecks generation/busy/stopping/uncertainty immediately before dispatch. User edits during load do not overwrite fields or launch old scan. Leaving Settings may allow background completion by explicit design; repeated navigation never rearms canceled/failed/completed attempt. Metadata-only scanner remains bounded/readonly/UNCHECKED; no pair trust/activation or executable invocation.

Independent3selected tests PASS/2deselected exit0: corrupt preferences no fallback, edited input while load suppresses auto scan, queued callback canceled before launch. Other tests/source inspected without full rerun; old constructor/no-navigation-scan test deliberately replaced with real MainWindow first-navigation one-shot and missing-tools-still-open assertion. Existing TOL-01.03 safety is preserved, not redefined into readiness.

No source blocker found. Workflow not yet supplied/reviewed for this checkpoint. Actual target CI/any broader SB-L032 criterion closure remains separate; no new ledger increment from local proof. Minor test-description precision: queued-scan test currently exercises cancel-generation supersession, not a second explicit Load/Save or close despite its broad name; source paths use same generation/stopping guards, but do not label that one test as individually proving all those stimuli.

Workflow addendum16:25: verified `3e68aad8cb84bfea9649db9a82fd56361b539fb830c60822afe26427865cb053` exact scoped delta. CLEAR for `[tool-first-open]` alone: four-target unchanged matrix/eight relevant UI files, LinuxQt retained; unchanged storage backend suite/aggregate/plan/schema/frozen/native FFmpeg excluded. Defaults/pinned actions/permissions unchanged. No further tests rerun for workflow check.
