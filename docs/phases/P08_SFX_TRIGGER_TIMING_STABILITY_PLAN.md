# P08 — SFX trigger timing assertion stability
Date: 2026-10-30. Repository: danhgold7979-cyber/fonesi-edit. Integration branch: develop/fonesi-full.

## Evidence and finding
Windows CI run 41037155082 failed once in tests/test_render_composition.py::test_custom_sfx_trigger_times_render_non_uniform_audible_events. The first expected-silence probe peak(.02,.08) measured 3830 against a strict threshold of 20. The same test passed on the next Windows run 41037280021 with no changes to render.py or the SFX scheduling implementation.

The first SFX trigger is at 0.10 s, so the silence probe ends only 20 ms before the event. The output is MP4/AAC; one AAC-LC frame at 48 kHz is 1024 samples (about 21.3 ms). Encoder transform pre-echo/priming near a transient is a plausible explanation, but not yet proven. The other silence probes also start close to previous event end boundaries. Do not weaken the silence threshold or change production audio behavior without evidence.

## Scope
1. Move silence measurement windows at least 40–50 ms away from all trigger start/end boundaries while retaining the strict peak threshold below 20.
2. Keep the three audible-event windows and their peak threshold above 500 so timing and audibility are still verified.
3. Make the assertion report each silence-window peak and interval independently for diagnosis.
4. Do not change SFX trigger scheduling, trim/delay filters, mix graph, codec settings or production output behavior.
5. Run the targeted test repeatedly where possible, then full Linux/Windows regression, phase-reference check and packaged proof.

## Acceptance
- [ ] Silence probes are outside AAC frame-edge transient windows and remain strictly below peak 20.
- [ ] All three scheduled SFX windows remain audibly above peak 500.
- [ ] The assertion reports the interval and measured peak on failure.
- [ ] Linux and Windows full regression and frozen packaged proof pass on exact code/test SHA.

## Limits
The observed 3830 peak is a one-run CI failure followed by a passing rerun, not proof of a production audio defect. The pre-echo explanation is a hypothesis. If safer measurement windows still fail, inspect decoded samples and FFmpeg filter output before changing implementation. Do not merge main.
