# Typed media observations — corrected source CLEAR for scoped CI

2026-11-01. Verified source f2cab723…, CLI ffbed3f…, tests81489274…, workflow2e9b1b31… supplied pins. No aggregate or actual FFmpeg rerun.

1. Input resource cap: len(metadata_json.encode()) encodes/allocates entire arbitrarily large caller input before enforcing16MiB. Independently confirmed oversized string encode trap reached. Check character cap first, then encoded byte cap; preserve fixed failure behavior.
2. Rotation provenance: valid displaymatrix with missing/invalid rotation produces rotation=None but basis DISPLAY_MATRIX_SUMMARY and no ORIENTATION_NOT_OBSERVED. Independently reproduced. Keep raw matrix; only claim summary basis when parsed summary exists, otherwise explicit unknown/diagnostic. No render authority issue because render_ready is alwaysFalse, but typed provenance must be truthful.

Otherwise exact stream-global indices/source order, signed tick-first timing, separate container duration, rational-vs-rounded-decimal conflict handling, bounded SAR parsing and all-track preservation are sound in observation scope. Raw matrix facts are not coerced into executable orientation. Input private tags/paths are not echoed; explicit caller-authorized probe uses existing owned runner, no discovery/download/fallback. Observation never becomes CompositionPlan or frame map.

Independent selected tests: signed exact timing/SAR/multistream; attached picture/reflection facts; rational summary provenance; fresh headless CLI — **4 PASS /12 deselected, exit0**. No Windows FFmpeg or complete frame-map evidence inferred. Linux actual-media receipt intentionally pins prior normalization source; current rational-summary change does not affect that measured tick/decimal fixture. Reconstructed old source supports diff attribution, not independent rerun.

Workflow [media-observation] ALONE preserves four targets, uses new observation + headless CLI tests, excludes unnecessary Qt/aggregate/plan/schema/frozen; source safety fixes still required before publication. Default importer/asset editing/render readiness/frame-PTS scans remain open. No criterion acceptance.

## Targeted final recheck, 14:01 UTC
Verified final observations.py `ef07a3c8aafbe7c148f088d40a9fbbec70b391cac549a333ee743478ae720455` and tests `8d7cc3ac116579361dded3c9b2fd3224ea6fc7c45f0fd277ae08b374cc93ccf5`. Character count precedes UTF8 allocation, invalid Unicode converted to controlled ProbeError; summary basis only set for parsed rotation. Missing/invalid rotation summary explicitly UNKNOWN with diagnostic; valid raw matrix still remains an observed orientation fact, correctly not discarded. Both findings closed.

Independent new causal cases only: oversized-before-encode plus two unknown rotation variants, **3 PASS /16 deselected, exit0**. Prior four and actual FFmpeg not repeated. Source+already reviewed workflow CLEAR for scoped CI; no readiness/frame-map/native-codec/criterion closure inferred. Prior measured receipt remains pinned to original1b8b0f7 source; corrected paths do not change its valid small no-matrix tick/decimal fixture.
