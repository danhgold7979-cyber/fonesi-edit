# P02 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-02`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P02-01 — ghi toolchain/máy/OS/codec/filter/encoder/font; lấy công cụ từ nguồn tin cậy, giữ TLS/checksum/chữ ký, pin sau kiểm chứng.

- **Depends on:** P01-06/07. Only independent work may proceed while external portions remain blocked.
- **Input:** Installed runtime/tools/fonts and trusted release metadata.
- **Output/interface:** Toolchain report and fresh dependency lock candidates; record binary hash/build/filter inventory.
- **Errors/cancellation:** Missing executable/version/architecture or license blocks relevant experiment; bounded child process canceled as owned group.
- **Tests and acceptance:** Version/hash/capability probe and actual decode/render sample agree; no “exists” readiness.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-02 — thử yt-dlp/gallery-dl trên nguồn công khai và nguồn có cấu hình đăng nhập; quét nhiều trang, tải video/ảnh/sub theo bảng nền tảng.

- **Depends on:** P01-01/08,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Permitted public/live URLs and explicitly configured accounts for ten platforms.
- **Output/interface:** Connector capability-cell experiment reports: identify/enumerate/download/subtitles/pagination/sync.
- **Errors/cancellation:** 403/auth/challenge/rate-limit recorded per cell; cancellation preserves partial cursor without full-channel claim.
- **Tests and acceptance:** Actual validated output and second sync per claimed cell; fixture-only cells remain NOT_RUN live.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-03 — thử dịch Trung–Việt với thuật ngữ/tên riêng/câu dài; so chất lượng, tốc độ, chi phí, cache và quota.

- **Depends on:** P01-06,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Rights-cleared Chinese/Vietnamese cues/glossary; authorized configured provider.
- **Output/interface:** Provider comparison: cue mapping, model version, usage/cost, human adequacy, latency/cache report.
- **Errors/cancellation:** Missing credential stays blocked; capped spend; timeout-after-submit unknown billing, no automatic duplicate paid call.
- **Tests and acceptance:** Exact cue ID preservation, names/glossary review, quota/retry/cache fault cases; human quality approval before provider accepted.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-04 — so engine preview cho Qt; mẫu alpha logo, chữ Việt/Trung, blur, seek, waveform, keyframe, audio; so mốc với FFmpeg export.

- **Depends on:** P01-07,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Composition alpha/CJK/blur/motion/audio fixtures and same plan timestamp set.
- **Output/interface:** Preview candidate spike and canonical frame comparison; record layout/raster authority decision.
- **Errors/cancellation:** Unsupported font/filter returns path-specific diagnostic; seek cancels stale request, does not overwrite current frame.
- **Tests and acceptance:** Lossless geometry/text parity plus timing/seek protocol; shifted-layer sentinel must fail; source thumbnail is not composition preview.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-05 — thử CPU/encoder GPU thật, phân biệt encode GPU và filter CPU; đo RAM/VRAM và fallback.

- **Depends on:** P02-01/04. Only independent work may proceed while external portions remain blocked.
- **Input:** Actual CPU/GPU/driver, selected codecs and representative composition.
- **Output/interface:** Separate decode/filter/encode capability probes; CPU fallback policy and RAM/VRAM report.
- **Errors/cancellation:** Encoder listed but runtime fails=unavailable; GPU-required errors, Auto fallback explicit; terminate owned process on cancel.
- **Tests and acceptance:** Tiny actual CPU/GPU output validates; modes separately tested on available hardware, absent GPU BLOCKED.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-06 — bản đóng gói Windows thử: mở UI, media/font/sub, FFmpeg, Unicode, startup.

- **Depends on:** P02-01/04. Only independent work may proceed while external portions remain blocked.
- **Input:** Fresh minimal desktop and chosen package candidates on Windows runner/PC.
- **Output/interface:** Frozen experiment with no Python prerequisite; startup/media/font/project/Unicode report.
- **Errors/cancellation:** Missing DLL/tool/font or incompatible OS prevents accepted package; canceled startup/export no success claim.
- **Tests and acceptance:** Launch frozen EXE then actual import/preview/render/save/reopen; startup-only proof separately labelled; physical PC gate open if absent.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-07 — benchmark có máy/mẫu; chốt ngân sách UI/proxy/seek, sai số hình/thời gian và mức song song ban đầu trước P04/P07.

- **Depends on:** P01-06,P02-04/05/06. Only independent work may proceed while external portions remain blocked.
- **Input:** Actual measured hardware and manifest-hashed corpus.
- **Output/interface:** Benchmark report p50/p95/max, proposed budgets and concurrency recommendation.
- **Errors/cancellation:** Incomplete samples/thermal/storage variance recorded; cancel marks incomplete, not median pass.
- **Tests and acceptance:** 5 warmups+30 seeks/60s UI latency protocol, RAM/VRAM and contention; budgets accepted only on declared environment.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-08 — ghi quyết định provider dịch, preview, FFmpeg build, packaging; blocker cho Windows/nguồn chưa truy cập được.

- **Depends on:** P02-01..07/09/10. Only independent work may proceed while external portions remain blocked.
- **Input:** All experimental reports, failed candidates and blocked prerequisites.
- **Output/interface:** Versioned ADR decisions with evidence refs, compatibility/licensing and fallback boundaries.
- **Errors/cancellation:** No evidence means proposed/blocked, not selected as proven; rejected candidate reason persists.
- **Tests and acceptance:** Reviewer can trace each chosen technology to exact experiment; all unresolved source/Windows/Chrome/provider gates listed.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-09 — thử discovery/tool manifest, nguồn Windows đáng tin, đường dẫn tùy chỉnh/version/capability, tải-cài-verify và rollback khi job đang dùng bản cũ.

- **Depends on:** P01-08,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Verified publisher manifests, isolated managed root, external-tool sentinel.
- **Output/interface:** Discovery/trust/install/activate/rollback experiment including ffprobe pairing.
- **Errors/cancellation:** Invalid checksum/signature/archive path blocks activation; cancel cleans owned staging only; active lease blocks removal.
- **Tests and acceptance:** Interrupt download/install, corrupt artifact, traversal/Unicode/path/version tests leave old binary+external sentinel intact.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P02-10 — Google Chrome chính thức trên Windows, hồ sơ độc lập, nhiều nền tảng/một hồ sơ và nhiều nick cùng nền tảng khác hồ sơ; kiểm chứng session handoff vào downloader với Chrome đang mở, mã hóa hiện tại và account mismatch.

- **Depends on:** P01-08,P02-01/02. Only independent work may proceed while external portions remain blocked.
- **Input:** Official Windows Chrome, app-owned profiles A/B, permitted configured accounts.
- **Output/interface:** Session-handoff feasibility report by Chrome/connector version and expected account identity.
- **Errors/cancellation:** Locked/challenge/expired/mismatch/bridge failure separate; never delete lock/decrypt profile; cancel leaves profile.
- **Tests and acceptance:** A multiple platforms+B alternate account, open/restart/check/handoff/download and mismatch cases; website login alone not PASS.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P02_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
