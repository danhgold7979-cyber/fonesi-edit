# P06-03 — Prevent glossary marker collision and translation-text corruption

Repository `danhgold7979-cyber/fonesi-edit`; integration branch `develop/fonesi-full`; 29/10/2026. Plan preceding code.

## Master alignment

Read AGENTS, README, implementation plan P06-03/P11-02, product requirements §4.1, traceability SUB-03/SUB-04/SUB-06, implementation coverage/status/ledger and P06 plan/results; inspected `subtitles.py` and translation tests. Current glossary protection injects a predictable literal `FONESIPROTECTEDTERM{n}END`, then substitutes every appearance of that token in translated output. User source text can itself contain the token, causing accidental replacement of content that was never in the glossary. A provider may also duplicate/delete tokens.

## Work slice

1. Generate a deterministic marker that does not occur in the source cue, glossary key or glossary value; preserve existing glossary behavior for natural text and cached captions. Keep the fingerprint keyed on original source/config.
2. For each protected term count its occurrences before replacement and verify the provider returned exactly the same marker count. Fail rather than silently invent/drop names. Cache writes occur only after successful validation.
3. Test literal old-marker text, provider marker duplication/deletion, overlapping terms, locked cues and cache reuse without external network or paid calls. Never record credentials or actual media.
4. Run full Linux/Windows source tests and frozen packaged proof, then update phase results/status only with evidence. Explicitly preserve live translator cost/quality, physical Windows/Chrome, user account, power-loss and SQLite #6 as open gates.

## Verified implementation (29/10/2026)

[Code 256c4a0](https://github.com/danhgold7979-cyber/fonesi-edit/commit/256c4a0d6b1816bc546d609f04afd18fd67e6caf) adds source-collision-safe markers and output marker counts; [follow-up 31c439b](https://github.com/danhgold7979-cyber/fonesi-edit/commit/31c439b44e60fe220cda8e332117b84177e4d1ab) uses a one-pass escaped glossary regex on the **original** cue so generated tokens cannot be accidentally reprocessed by overlapping glossary entries. [Tests c0840fb](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c0840fb9857a49887d827330ea5953d4e6c1b485) and [1a2347b](https://github.com/danhgold7979-cyber/fonesi-edit/commit/1a2347b4b653fcc2cb5e20340fcb3ee54fd827a8) cover literal legacy-token source text, longest-match protection, marker duplication/deletion, cache and token-prefix glossary entries.

[CI 40893822256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40893822256) **SUCCESS on final source/test SHA 1a2347b4**: 602 Linux passed, 601 Windows passed plus 1 intentional POSIX-only skip; plan validation, production desktop/native-host builds and frozen localhost/synthetic app proof PASS on both CI runners. Live translation provider quality, cost, billing, languages, and real Windows/Chrome/GPU acceptance remain open.
