# P02 scoped local results — whole phase OPEN

New experiment code: `e0cfb14acbf390261120306aa68622085159f640`. Reports under `docs/evidence/p02`, records have empty runtime criterion_ids deliberately. No product feature accepted.

| Experiment | Actual result | Limit |
|---|---|---|
| Python3.12.14 + Qt6.12.0 minimal Essentials/Addons | Fresh universal hash-pinned install; Qt offscreen widgets/fonts work | Windows10/11 not run; no claim upstream support equals target test |
| Qt raster640×360/60frames→H264/AAC→full decode | PASS; frame30 lossless exact, lossy RGB MAE1.188/255,p99=6/255; shifted3px negative rejected | Synthetic typography/shapes only, not full evaluator/effects |
| Same candidate1920×1080 | PASS; lossless exact, lossy MAE1.079/255,p99=4/255 | Raster-only p95≈12.71ms excludes source decode/PNG IO/encode; not UI/seek/full playback benchmark |
| Explicit source audio streams1/2 | FFT peaks440/880Hz, second starts250ms; PASS | FFmpeg tool experiment, not application time-map implementation |
| Linux frozen minimal Qt binary | PASS launched actual onedir bundle; visible widget/font enumeration | Startup-only; no Windows/installer/media-binary acceptance |
| Default Qt audio device enumeration | FAIL processSIGSEGV; missing PipeWire config in headless container | Isolated import/format query succeeds; actual speaker test blocked |
| Official QT_AUDIO_BACKEND=pulseaudio for isolated Linux probe | No crash;0input/0output devices reported accurately | No physical audio PASS; no system/service/security modification |

Developer artifacts `P02-01.dev_toolchain_ready` and `P02-04.canonical_preview_candidate` LOCAL_VERIFIED, sufficient for independent P03 domain/storage/schema work per dependency graph. No whole P02 task ACCEPTED: font/effect parity set, continuous playback, reference performance, Windows/GPU/tool distribution/live sources/provider/Chrome still open. GPU device absent in this container (`/dev/dri` absent, nvidia-smi absent); do not infer unsupported user hardware.

Decisions: retain Qt shared raster/layout candidate for text/overlay preview/export to avoid separate shaping engines; validate actual complete compositor before full P04/P07. FFmpeg7.1.5 system binary is developer tool only, build flags/hash recorded; no selected redistributable Windows binary yet. Device health probing must be isolated so backend failure cannot kill project UI. Authenticated sessions/provider spend not exercised without required configuration/authority.

Size measurement for exact new minimal-dependency bundle:184,832KiB allocated (`du -sk`);188,649,851bytes regular file contents excluding symlinks;280,358,723bytes when each symlink target is counted again. These are different metrics, not Windows installer size. Earlier scratch-meta-package bundle size is not current evidence.
