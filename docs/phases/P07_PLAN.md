# P07 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-07`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P07-01 — font hệ thống/TTF/OTF riêng, tìm/yêu thích/mẫu/fallback/glyph/thiếu font; cùng font/layout preview-render.

- **Depends on:** P04-06,P02-04. Only independent work may proceed while external portions remain blocked.
- **Input:** System/private licensed TTF/OTF, requested family/style/glyph set.
- **Output/interface:** Font registry search/favorites/recents/sample/fallback; resolved hash/layout shared preview-export.
- **Errors/cancellation:** Missing glyph/font warning+explicit substitute; no silent system install; cancel scan leaves prior usable catalog.
- **Tests and acceptance:** Vietnamese/Chinese combining/punctuation/wrap cases same raster source; missing font relink persistence, font license before distribution.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-02 — chữ/viền/bóng/nền/padding/căn/giãn dòng/giãn chữ/ngắt dòng/nội dung động; nhiều logo, vị trí/lề/opacity/thời gian.

- **Depends on:** P07-01, P04-02, P06-06.model_ready (not P06-06.accepted). Only independent work may proceed while external portions remain blocked.
- **Input:** Text/bilingual/logo layer styles/content and channel metadata.
- **Output/interface:** Full text outline/shadow/background/padding/wrap/spacing and logo intervals/opacity controls+evaluator.
- **Errors/cancellation:** Overflow policy bounded or warning; dynamic metadata allowlist; wrong/missing logo blocked, canceled replacement preserves transform.
- **Tests and acceptance:** Each style option round-trip/render parity, bilingual independent blocks, alpha logo and multiple intervals; no clipped glyph success.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-03 — nhiều vùng blur/mosaic/màu, bo góc/cường độ/feather theo khả năng engine đã chứng minh; cảnh báo thuộc tính không khả dụng.

- **Depends on:** P04-02,P02-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Mask layer geometry/mode/radius/feather/intensity and z order.
- **Output/interface:** Multiple blur/mosaic/color masks, timeline intervals/fade and supported keyframe geometry.
- **Errors/cancellation:** Unsupported filter/property errors by path; invalid amount rejected; cancel edit returns old model.
- **Tests and acceptance:** Known pixel-region oracle, mask below/above text z tests, rounded/feather parity; enabled unsupported effect cannot export success.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-04 — keyframe X/Y/scale/rotation/opacity, linear/easing, copy/paste, thời gian tuyệt đối/tương đối, playhead và undo.

- **Depends on:** P04-04/05,P01-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Property keyframes and playhead/absolute-relative mode.
- **Output/interface:** Shared keyframe interpolation/edit/copy/paste/time-shift commands.
- **Errors/cancellation:** Duplicate time/unsupported path rejected; lock respected; cancel edit atomic; base edit on animated field asks scope.
- **Tests and acceptance:** Linear/ease boundaries exact, fps/zoom independence, clipboard time modes and undo; preview/output evaluated values identical.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-05 — chạy thẳng/chéo/A→B/nhiều điểm/qua góc/lặp/đi-về/nảy/zoom/xoay/fade; speed/duration/delay/hold/repeat/vùng.

- **Depends on:** P07-04,P04-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Motion preset parameters speed/duration/delay/hold/repeat/region.
- **Output/interface:** Compile straight/diagonal/A-B/multipoint/corners/loop/ping-pong/bounce/zoom/rotate/fade into canonical plan.
- **Errors/cancellation:** Inconsistent speed-duration normalized through explicit chosen driver; impossible bounds warning; cancel preview leaves model.
- **Tests and acceptance:** Boundary anchors/object sizes, repeated cycles and delay/hold; deterministic preset→evaluated positions; no FPS-dependent motion.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-06 — random có seed/khoảng/xác suất, biến thể mỗi clip, vùng tránh/cảnh báo xung đột, giữ khóa tay.

- **Depends on:** P07-04/05,P01-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Seed/ranges/probability/output IDs/avoid regions/manual locks.
- **Output/interface:** Deterministic motion/parameter variation plan with reason/conflict warnings.
- **Errors/cancellation:** Empty feasible area warns or holds chosen position; no unlimited solver; cancel generates no persisted variant.
- **Tests and acceptance:** Same full snapshot+seed reproduces; independent clip variation stable under ordering contract; locked keyframes unaffected.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-07 — fit/crop/nền/tỷ lệ/màu/flip/rotate/speed; thứ tự filter, time map sub, capability CPU/GPU.

- **Depends on:** P03-03,P07-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Clip crop/fit/background/color/flip/rotate/speed options and output ratio.
- **Output/interface:** Canonical ordered filter/time-map compiler; CPU/GPU capability policy.
- **Errors/cancellation:** Impossible crop/bad gamma/speed rejects; GPU-required unsupported blocks, Auto fallback recorded; cancel owned render.
- **Tests and acceptance:** Every ratio and color/control tested with golden fixture; rotation/SAR/VFR; sub time-map after trim/speed; decode/filter/encode capabilities separate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P07-08 — compiler từ model chung, đối chiếu frame, progress FFmpeg/cancel/validation; tối ưu một lần encode khi có thể, ghi lý do cần intermediate.

- **Depends on:** P07-01..07,P03-06,P02-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Validated complete CompositionPlan plus resolved tools/assets.
- **Output/interface:** Actual FFmpeg/canonical compositor execution, progress/cancel/output validation; intermediate rationale.
- **Errors/cancellation:** Unsupported property blocks before execution; failed decode or publication never success; cancellation handles process tree.
- **Tests and acceptance:** Lossless+lossy frame/audio parity and deliberate failure sentinels, full decode/output expected metadata, single-encode path where equivalent.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P07_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
