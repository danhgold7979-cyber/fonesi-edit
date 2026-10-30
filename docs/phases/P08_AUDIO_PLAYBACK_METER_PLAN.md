# P08-03 / P11-04 — Real-time playback peak/RMS meter and sample clipping indication

**Date:** 30/10/2026. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`.
**Reviewed HEAD:** `00bdd95c5d9c2758169775d1828dd5da5804ee87`. This plan is committed before source changes.

## 1. Master-plan and requirement alignment

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P08-03, P11-01/P11-04/P11-05), `docs/PRODUCT_REQUIREMENTS.md` §6, `docs/REQUIREMENTS_TRACEABILITY.md` AUD-01/AUD-02, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P08 plan/results and P11 results, plus `src/fonesi_edit/ui/editor.py`, `render.py`, `domain.py`, `ui/dialogs.py` and the existing Qt/FFmpeg audio tests.

Current code already applies a final `alimiter=limit=0.95`, optional EBU-style `loudnorm=I=-16:TP=-1.5:LRA=11`, and optional ducking in the export graph. The editor uses `QMediaPlayer` + `QAudioOutput` for source/proxy playback and rendered-composition preview, but has no visible level meter or sample-clipping indicator. The existing waveform is a static timeline asset and is not a playback level meter. The existing solo/mute track settings remain in the render graph.

## 2. Scope of this slice

Add a **playback-stream meter** in the Editor's playback controls:

- Use Qt Multimedia `QAudioBufferOutput` (already covered by the locked PySide6/Qt 6.8.3 dependency) connected to the existing `QMediaPlayer`. The Qt API is available from Qt 6.8 and emits decoded `QAudioBuffer` objects; Qt documents the buffer-output feature as FFmpeg-backend-only. See [PySide6 QAudioBufferOutput 6.8](https://doc.qt.io/qtforpython-6.8/PySide6/QtMultimedia/QAudioBufferOutput.html).
- For each non-empty decoded buffer, calculate peak dBFS, RMS dBFS and the count of samples at/near full scale. Support `UInt8`, `Int16`, `Int32` and `Float`; reject unknown/invalid formats safely. Samples are interleaved across channels.
- Display peak and RMS bars/labels and a clear sample-clip indicator. Identify the reading as decoded playback-stream level (pre-device/room acoustics), not a calibrated hardware meter.
- The meter follows whichever source the existing player is playing: original/proxy playback or a rendered composition preview. A rendered preview therefore measures its composed output; raw-source playback measures the source stream. Do not imply the raw-source meter represents the composition mix.
- Reset readings on source replacement and when starting a new playback session; handle empty end-of-stream buffers and unsupported backend gracefully.
- Metering is observational only: it must not modify composition JSON, project schema, source media, playback samples, render graph, gain, limiter or loudness-normalization settings.

## 3. Implementation design

1. Add a small UI-independent `audio_meter.py` helper that converts supported PCM sample formats into normalized values and returns immutable metrics: peak, RMS, peak dBFS, RMS dBFS, and clipped-sample count. Validate buffer alignment, finite float samples and gain; ignore no malformed bytes silently.
2. Attach `QAudioBufferOutput` to the editor's existing `QMediaPlayer` when the API is present. Consume buffers in the editor's Qt object context and pass raw bytes/format into the helper. If the FFmpeg backend/API is unavailable, keep playback functional and show an explicit unavailable state rather than claiming zero audio.
3. Add compact peak/RMS bars and sample-clipping count to the playback control row. Use a bounded dBFS display range (−60 to 0 dBFS); values above 0 remain visible in the numeric label and increment the clip counter rather than being silently clamped as safe.
4. Clear the meter on `sourceChanged`, new play from stopped state and empty/invalid buffer boundaries; keep pause/resume state predictable. Do not reset on every buffer or timeline seek.
5. Keep current `alimiter` and `loudnorm` graph exactly unchanged. A later slice may add an explicit offline output analysis/report; this slice only meters the player stream.
6. Update P08 results/plan, AUD coverage, current status, user guide and execution ledger only after code/test/CI evidence is known.

## 4. Required tests

- Pure PCM unit tests for silence, signed 16-bit positive/negative peaks, 32-bit integers, float, unsigned 8-bit midpoint, little-endian host representation, clipping threshold, RMS, output gain/mute, empty input, partial sample, unknown format, NaN/Inf and extreme float values.
- Qt regression constructs real `QAudioFormat`/`QAudioBuffer` fixtures and emits `QAudioBufferOutput.audioBufferReceived`; assert peak/RMS UI values, clipping counter, empty-buffer behavior, reset on source change and no change to composition payload.
- Ensure `QAudioBufferOutput` is attached to the same player used by the editor and rendered preview; missing API/backend must not stop source playback.
- Existing FFmpeg output tests continue to verify limiter/loudnorm and audio track preservation; no render graph assertion is weakened.
- Run `uv run python scripts/check_plan.py`, targeted audio/Qt tests, full `uv run pytest -q`, desktop/native-host build, frozen package verification, and GitHub Actions Linux + Windows on the exact source/test SHA.

## 5. Acceptance boundaries and blockers

This slice provides a **decoded digital playback-stream** peak/RMS meter and sample-peak warning only. It does not prove true-peak/inter-sample clipping, loudness compliance, hardware output level, speaker/driver calibration, per-track pre-mix levels, physical Windows audio quality or real-device playback. The Qt buffer API is documented as FFmpeg-backend-only; unsupported backends must report unavailable without affecting playback.

Still OPEN after this slice: multi-file playlist workflows, track-specific pre-mix meters, true-peak/loudness analysis, Windows hardware/driver/installer/ACL/AV/HiDPI/GPU acceptance, large-corpus render ETA/output-size forecasting, Chrome/live providers, long soak and SQLite issue #6. Do not mark P08 or P11 complete.
