# P11-01 / P11-04 — Make stereo SFX onset delays explicit per channel

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: fa8c7f89cecee44024bca7685020b9d7bd961c21
- Alignment: P11-01 end-to-end audio behavior; P11-04 timing and decoded-output correctness.

## Evidence reviewed

Read AGENTS.md, README.md, master P11/P12 plan, requirements/coverage/status/ledger, prior SFX timing plan, render graph builder and decoded-MP4 tests.

Windows CI has intermittently failed the strict pre-trigger silence check with peak 3830 in 0.02–0.08 s, while Linux and some Windows runs pass. The failure is isolated to custom trigger-time SFX after forcing stereo and applying `adelay=<ms>:all=1`. A peak of 3830 is consistent with one stereo channel remaining undelayed before mono downmix. The exact Windows filter behavior has not yet been proven.

A local synthetic FFmpeg 7.1.5/Linux reproduction with explicit per-channel delays (`adelay=<ms>|<ms>`) produced zero peak in both stereo channels before each onset, with audible events in the configured windows. This is local evidence only; Windows CI is required.

## Implementation

1. Keep the existing 48 kHz resample and sample-clock PTS reset before onset delay.
2. Replace the implicit all-channel option with an explicit equal delay for the two channels after the graph has forced stereo, in custom-trigger, repeated-SFX and ordinary absolute/percent/scene-anchored SFX branches. Keep music-track delay behavior unchanged.
3. Update graph assertions to require explicit left/right delay values for every event.
4. Decode rendered MP4 to stereo PCM in custom-trigger, repeated and ordinary anchored SFX tests; independently assert strict pre-onset silence and intended audible windows for both channels. Correct any test windows to use seconds/sample-frame indexing rather than interleaved scalar sample indices.
5. Preserve existing silence threshold (<20), audible threshold (>100), onset times, trim, gain, duration and output validation. Do not skip, widen windows or relax assertions.
6. Run phase checker, render module, complete suite, Batch/Matrix benchmarks, production/native-host builds and frozen packaged proof on Linux and Windows.
7. Update P11 results, coverage, current status and ledger only after exact-HEAD CI passes.

## Acceptance

- [ ] Custom trigger SFX have strict pre-onset silence in both decoded stereo channels and audible output in both channels after each onset.
- [ ] Repeated SFX have strict pre-onset silence in both decoded stereo channels and audible output in both channels after each onset.
- [ ] Graphs explicitly delay both stereo channels after sample-clock normalization for custom, repeated and ordinary anchored SFX.
- [ ] Existing music, source audio mute, trim/fade/gain and duration behavior remains unchanged.
- [ ] Full render tests and phase reference checker pass.
- [ ] Exact-HEAD Linux and Windows CI, production builds and packaged proof pass.

## Limits

The local reproduction uses FFmpeg 7.1.5/Linux; it does not prove the Windows FFmpeg behavior. Exact-HEAD Windows CI and later real-media/audio-device acceptance remain required. Do not merge to main or force-push.
