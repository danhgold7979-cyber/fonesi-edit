# P06-03 — Prevent glossary marker collision and translation-text corruption

Repository `danhgold7979-cyber/fonesi-edit`; integration branch `develop/fonesi-full`; 29/10/2026. Plan preceding code.

## Master alignment

Read AGENTS, README, implementation plan P06-03/P11-02, product requirements §4.1, traceability SUB-03/SUB-04/SUB-06, implementation coverage/status/ledger and P06 plan/results; inspected `subtitles.py` and translation tests. Current glossary protection injects a predictable literal `FONESIPROTECTEDTERM{n}END`, then substitutes every appearance of that token in translated output. User source text can itself contain the token, causing accidental replacement of content that was never in the glossary. A provider may also duplicate/delete tokens.

## Work slice

1. Generate a deterministic marker that does not occur in the source cue, glossary key or glossary value; preserve existing glossary behavior for natural text and cached captions. Keep the fingerprint keyed on original source/config.
2. For each protected term count its occurrences before replacement and verify the provider returned exactly the same marker count. Fail rather than silently invent/drop names. Cache writes occur only after successful validation.
3. Test literal old-marker text, provider marker duplication/deletion, overlapping terms, locked cues and cache reuse without external network or paid calls. Never record credentials or actual media.
4. Run full Linux/Windows source tests and frozen packaged proof, then update phase results/status only with evidence. Explicitly preserve live translator cost/quality, physical Windows/Chrome, user account, power-loss and SQLite #6 as open gates.
