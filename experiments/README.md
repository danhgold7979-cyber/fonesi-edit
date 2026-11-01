# P02 isolated synthetic experiments

These are newly authored experimental programs, **not the Fonesi Edit application**. Never import the old implementation or use old tests as evidence.

```bash
UV_CACHE_DIR="$PWD/.uv-cache" uv venv .venv
UV_CACHE_DIR="$PWD/.uv-cache" uv pip sync --python .venv/bin/python experiments/requirements.lock
QT_QPA_PLATFORM=offscreen .venv/bin/python experiments/run_local_probe.py --output-dir runtime/p02-640 --width 640 --height 360
```

Use a new nonexistent output directory; runner never deletes/reuses existing destination. FFmpeg/ffprobe system tools required for local experiment and their versions are recorded, not bundled. Actual licensed CJK font prerequisite required. `--width 1920 --height 1080` is the full-resolution second corpus case; raster timing excludes decode/encode and is not full playback performance.

Frozen test: run PyInstaller on `experiments/frozen_probe.py` with build/dist/spec paths under ignored runtime; execute produced binary `--report <new-report-path>` with `QT_QPA_PLATFORM=offscreen` on Linux. This checks Qt startup only, not Windows/package media acceptance.

Qt6.12 default audio device discovery crashed in this headless container because PipeWire client configuration was missing. Import/format discovery did not crash. Official Qt implementation honors QT_AUDIO_BACKEND; selecting pulseaudio for isolated Linux/headless probes avoids that path and correctly reports zero audio devices. No system services/configuration/security changed. Do not apply this Linux experiment environment override to Windows or label zero devices as physical playback proof. Probe device availability in a child process before initializing optional audio in UI.

Sources checked2026-11-01: [Qt6.12 Windows support](https://doc.qt.io/qt-6.12/windows.html), [Qt Linux audio requirements](https://doc.qt.io/qt-6/qtmultimedia-linux.html), [Qt official audio-backend selection source](https://raw.githubusercontent.com/qt/qtmultimedia/6.12/src/multimedia/platform/qplatformaudiodevices.cpp). Qt6.12 lists Windows10>=1809 and Windows11; actual target machine remains unverified. Minimal Essentials/Addons dependency split avoids unnecessary WebEngine/PDF, not Chrome substitution.
