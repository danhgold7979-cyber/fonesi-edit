# P11-01 / P11-04 — Stabilize SFX trigger timing across Windows FFmpeg

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 1a4d486d7c27603429e6223ceb90233c17d8cc6e
- Alignment: P11-01 end-to-end audio behavior; P11-04 frame/audio/timing correctness; P11-08 Windows regression quality.

## 1. Evidence reviewed

Read AGENTS.md, README.md, the master P11/P12 plan, current status, coverage, requirements traceability, execution ledger, P11 results, the P11-08 tool lifecycle plans, `render.py`, `Composition.validate`, `create_fixture`, the SFX render tests and the exact Windows CI job log.

[CI 41076305870](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41076305870) failed on Windows at `test_custom_sfx_trigger_times_render_non_uniform_audible_events`: the decoded MP4 contained peak 3830 in the pre-trigger interval 0.02–0.08 s, where the contract expects digital silence (<20). Linux passed. This is an actual failed regression and must not be converted to a skip or relaxed threshold.

The current SFX branch normalizes timestamps using `asetpts=PTS-STARTPTS`, resamples to 48 kHz, then delays and pads. The failing test uses AAC audio embedded in the same MP4 as the video and reopens that file for each trigger. AAC priming/packet timestamps differ by platform/build, so the SFX filter should be normalized to a deterministic sample clock before delay.

A local synthetic reproduction on FFmpeg 7.1.5/Linux confirms the expected timing for the current filter graph, but does not explain or clear the Windows failure. Windows must be rerun after the source change.

## 2. Scope

- Normalize each isolated SFX segment onto a zero-based 48 kHz sample clock before applying its onset delay.
- Apply the same timing normalization to custom trigger-time SFX and repeated SFX so the two modes share deterministic timing semantics.
- Keep original audio mute behavior, trim boundaries, volume, fade, delay values, total output duration and final mix unchanged.
- Preserve strict pre-trigger silence and audible-window assertions; no widened windows, lower thresholds, skips or disabled checks.
- Add graph-level regression assertions for sample-clock normalization and retain the real MP4 decode assertions.

## 3. Implementation

1. Update both SFX filter chains to resample to 48 kHz and then reset audio PTS from the actual sample count (`asetpts=N/SR/TB`) before channel formatting/delay. Do not reset timestamps from demuxer packet PTS.
2. Keep `adelay` after the sample-clock reset; preserve the exact requested millisecond onset.
3. Add explicit tests that both custom-trigger and repeated-SFX graph branches use the sample-clock reset after resampling and before delay.
4. Run the two SFX audible-timing tests locally on the available FFmpeg build, plus the complete render test module and plan checker.
5. Run exact-HEAD CI on Linux and Windows. Inspect Windows job log and decoded timing assertions. If Windows still fails, investigate the exact generated graph/build and do not weaken the assertions.
6. After exact-HEAD CI passes, update P11 results, current status, coverage and execution ledger with the new evidence. Do not mark P11 complete.

## 4. Acceptance criteria

- [ ] Custom trigger events remain silent before each configured onset and audible in their intended windows.
- [ ] Repeated SFX remain silent before each configured onset and audible in their intended windows.
- [ ] Both SFX graph branches normalize decoded audio to a sample-derived PTS clock after 48 kHz resampling and before delay.
- [ ] Output duration, existing mute/trim/volume/fade behavior and unrelated audio tracks remain unchanged.
- [ ] Full render tests and phase reference checker pass.
- [ ] Exact-HEAD Linux and Windows CI, production builds and packaged proof pass.

## 5. Limits

Local FFmpeg 7.1.5/Linux is not Windows acceptance. CI synthetic fixtures do not prove arbitrary AAC encoders, all third-party MP4/M4A containers, physical Windows user machines, GPU/audio devices or large real-media performance. Do not merge to main or force-push.
