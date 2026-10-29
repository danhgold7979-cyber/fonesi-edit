# P06-04 / SUB-05–06 — Non-lossy source/target subtitle split and merge

**Date:** 2026-10-29. **Repository / single branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. **Plan before changing code.**

## Review and defect

Read AGENTS.md, README.md, IMPLEMENTATION_PLAN P06-04, PRODUCT_REQUIREMENTS 4.1–4.2, EDITOR_SPEC, REQUIREMENTS_TRACEABILITY SUB-05/06, CURRENT_STATUS, IMPLEMENTATION_COVERAGE, P06_PLAN/P06_RESULTS, `SubtitlesPage.split/merge` and existing caption/Qt tests.

Today `split()` constructs two captions using `cue.text.split()` but drops `source_text`. One-word or CJK subtitle input can create a fabricated `…` cue; `merge()` joins translated text yet also drops every source caption. This silently damages a bilingual draft. A 1 ms cue cannot be split into two positive intervals.

## Planned change and tests

1. Implement pure `split_caption` and `merge_captions` helpers that preserve all characters of both original and translated text, source/target role, lock state, and full timing coverage. Prefer splitting at a whitespace boundary; if no valid boundary, use a safe internal character boundary for CJK. Reject an unsplittable one-character text/source and intervals shorter than two milliseconds rather than introducing `…` or invalid times.
2. Use the helpers in existing Qt `SubtitlesPage` operations, retaining current selection and draft persistence. Keep editor/project format and provider contracts unchanged.
3. Unit-test Chinese text without spaces, Unicode original/translation with independent word counts, lock propagation, merge source retention, one-character and 1 ms boundary, and raw-character conservation. Add a Qt test that editing one bilingual caption, splitting, then merging maintains original/translated content and lock state.
4. Run the plan validator and full Linux/Windows CI with packaged binary proof. Record only completed run evidence; do not close phase P06 based on synthetic tests alone.

## Gates

- [ ] Split never fabricates words or drops any original/translated characters.
- [ ] Merge keeps original and translated tracks plus lock/timing state.
- [ ] Invalid split is rejected before modifying the table or editor.
- [ ] Existing behavior for normal captions remains usable; source and packaged Linux/Windows tests pass.

Open: drag-undo full subtitle editor history, provider live Chinese→Vietnamese quality, practical long corpus, Chrome/auth, GPU/Windows physical installation, and external filesystem/power-loss acceptance.