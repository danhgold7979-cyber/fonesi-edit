# P04 — Kết quả lớp editor

Đã code canvas layer text/image/mask với kéo/resize/rotate, khóa/thứ tự, căn snap và zoom không đổi model; inspector style/motion/keyframes; undo snapshot; timeline move/trim/split/playhead/zoom và Qt playback. Hai test editor đã qua: sửa Unicode/undo/redo/nhân bản/xóa/round-trip và split giữ ánh xạ source time. Lưu project/preset nối với Store ở app shell, render tham chiếu nối compositor P07.

Đây là phần triển khai local, chưa nghiệm thu mọi thao tác trên Windows hoặc đủ mọi tổ hợp font/parity. Phần còn lại được kiểm tra tích hợp P07/P11, không ghi hoàn tất các mục chưa có evidence.

Vòng tích hợp thêm multi-select/nhóm/căn/phân bố/copy style, double-click chữ, clip trim/speed/flip/rotation/gain, In-Out/ripple, waveform nền/audio timeline, step frame, remap và undo theo focus. Mouse drag đã được thử bằng QtTest; proxy/crop tay nắm/loop đoạn và đầy đủ shortcut còn ở coverage. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).


## P04 — Loop In–Out, thumbnail strip, source proxy (28/10/2026)

Đã triển khai và kiểm thử các đường chạy:

- **Loop In–Out:** bật từ menu Editor sau khi đặt I/O; chỉ seek trong bản playback **đã render qua compositor cho composition hiện tại**. Fingerprint thay đổi khi sửa project làm preview cũ không được tự coi còn đúng. Không lặp theo thời gian file gốc có trim/speed sai.
- **Thumbnail strip:** bật/tắt bằng action có undo/save project; tạo 3 PNG từ thời gian nguồn của clip với FFmpeg, cache theo file/stat/trim/speed, publish atomic, validate Qt, cancel/timeout; xử lý nền cho các clip nhìn thấy và hiển thị trên timeline cùng waveform. Thumbnail nguồn không phải khung đã composited.
- **Proxy nguồn:** Off / Nhanh (cạnh dài 640) / Cân bằng (1280) / Cao (1920), không upscale nguồn nhỏ. FFmpeg tạo H.264/AAC trong cache per-user bằng tệp tạm; FFprobe kiểm tra duration/video và atomic publish, giữ media nguồn không đổi. Qt chọn clip đầu an toàn, chỉ phát proxy của file nguồn, bản render final vẫn đọc nguồn.

**CI xác nhận:** [run 40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637), Linux **195 passed**, Windows **194 passed + 1 skipped** (POSIX fixture); cả hai build app/native host và frozen proof localhost/render/Qt đạt.

**Cổng còn mở:** crop handles/chín anchor đầy đủ, HiDPI/4K/VFR/seek/audio-sync/timeline dài trên Windows người dùng, parity mọi hiệu ứng, shortcut focus/IME. Đây là lát cắt đạt CI offline, **không phải P04 nghiệm thu toàn bộ**.


## P04-02/P04-03 — Crop model, FFmpeg pipeline and interactive source crop (28/10/2026)

- [x] Clip stores normalized crop coordinates; old project payloads default to full-frame crop.
- [x] Domain validation rejects non-finite, non-positive and out-of-frame crop rectangles.
- [x] FFmpeg converts normalized source coordinates into even-pixel crop geometry before flip/rotation/fit; real export retains requested output dimensions.
- [x] CropDialog shows a real source frame, darkens only the area outside the crop, draws a thirds grid and eight handles, supports dragging the crop, reset/center, ratio-lock control, and Cancel/Accept flow back to ClipDialog.
- [x] Crop values commit through the existing editor snapshot, so Undo restores the prior crop.
- [x] CI [run 40686663256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40686663256) PASS: **262 tests Linux; 261 Windows + 1 POSIX-only skip**. Both runners passed production desktop/native-host build and frozen packaged proof. Added tests cover legacy project compatibility, invalid crop bounds, odd-dimension even-pixel geometry, FFmpeg filter order and real render, crop preview pixels, Qt drag, cancel and Undo.
- [ ] Still open: full handle/ratio-lock edge-case matrix, rotated-metadata/VFR/HiDPI/4K and long-timeline testing on real Windows user machines. This is evidence for the crop slice only, not completion of all P04 tasks.

## P04-02/P04-03 — Peer-object snapping and visible alignment guides (28/10/2026)

- Added normalized-coordinate snapping to peer left/centre/right and top/centre/bottom guides, with bounded tolerance and deterministic tie-breaking.
- Drag integration excludes self, selected/group companions, hidden layers and locked layers. Group members keep one common translation delta.
- Active snap guides are dashed viewport-only overlays. They clear on rebuild/release and when Alt disables snapping; they are not inserted into the scene, project model or FFmpeg output.
- CI [run 40714649301](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40714649301) **PASS**: 326 Linux tests; 325 Windows tests + 1 intentional POSIX-fixture skip. Production app/native host and frozen proof passed on both runners.
- This verifies the offline code slice; peer-guide behavior on real Windows/HiDPI displays and the rest of P04 remain separate acceptance gates.

## P04-02/P04-03 — Crop ratio-lock geometry and bounds (28/10/2026)

- Extracted crop dragging into a pure normalized-geometry helper used by the existing CropDialog.
- With ratio lock enabled, all eight edge/corner handles preserve the crop's normalized width/height ratio. Corner handles keep the opposite corner fixed; side handles keep the opposite edge fixed and resize around the orthogonal centre.
- Added boundary clamping and tests for creating/moving/resizing, ratio preservation, free-ratio regression and out-of-frame prevention.
- CI [run 40716484637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40716484637) **PASS**: 339 Linux tests; 338 Windows tests + 1 intentional POSIX-fixture skip. Production app/native host and frozen proof passed on both runners.
- Follow-up anchor-invariant tests passed in [run 40717364128](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40717364128): **347 Linux tests; 346 Windows tests + 1 intentional skip**, with packaged proof on both systems.
- Still open: rotated metadata, VFR, mixed FPS, HiDPI/4K, long timelines, crop/preview/export parity across all transforms, and real Windows user-machine acceptance. These results do not mark all of P04 complete.

## P04-07 — Save As project and shortcut-table parity (28/10/2026)

- Added a visible **Lưu thành** toolbar action and Ctrl+Shift+S. Save As normalizes the `.fonesi` extension, creates an independent project ID and Store record, and writes a standalone project file.
- Cancel leaves the active project unchanged. Selecting the current project path uses normal Save rather than creating a duplicate ID. Save As does not rewrite the source project file or its named database snapshot.
- CI [run 40719769956](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40719769956) **PASS**: 350 Linux tests; 349 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both systems.

## P04-07 — Focus-aware layer clipboard shortcuts (28/10/2026)

- Added Ctrl+A/C/V/X actions for layer selection and an in-app layer clipboard. Paste regenerates layer IDs and group IDs, preserves clip references/style/keyframes, applies a bounded offset and records one undo step. Cut removes only unlocked selected layers; source media files are never deleted or changed.
- When a text editor has focus, the same actions route to the native widget's select-all/copy/paste/cut methods rather than operating on layers. The layer list retains list selection semantics and supports layer clipboard actions.
- CI [run 40721462280](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40721462280) **PASS**: 362 Linux tests; 361 Windows tests + 1 intentional POSIX-fixture skip. Production app/native host and frozen proof passed on both systems.
- Remaining: real OS IME/keyboard testing, advanced multi-step shortcut customization, dense peer-guide priorities, and the remaining P04/P12 acceptance gates. These slices do not mark the whole phase complete.

## P04-02 — Escape cancels active canvas drags (28/10/2026)

- Escape now restores the exact pre-gesture composition snapshot while a canvas drag is active, clears peer snap guides and avoids creating an Undo entry for the cancelled gesture.
- A subsequent mouse release cannot commit the cancelled drag. The rendered preview fingerprint is retained because the composition has returned to its original state.
- CI [run 40723004092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40723004092) **PASS**: 363 Linux tests; 362 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both systems.
- This verifies the synthetic Qt drag regression; physical keyboard/focus and real Windows/HiDPI acceptance remain open.

## P04-02 — Crop ratio lock: handle/boundary regression expansion (28/10/2026)

- Extracted normalized crop-drag geometry into a deterministic helper and exercised all eight edge/corner handles, new-crop creation, movement clamping, invalid geometry and free-ratio behavior.
- Ratio lock preserves normalized width/height for a fixed source; edge handles keep the opposite edge fixed and resize the orthogonal axis symmetrically. Boundary clamps keep the crop inside the frame.
- CI [run 40724751585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40724751585) **PASS**: 386 Linux tests; 385 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: physical Windows/HiDPI/4K acceptance, rotated metadata, VFR/mixed FPS, and complete preview/export parity. This test slice does not mark all of P04 complete.

## P04-02 — Configurable canvas grid spacing (28/10/2026)

- Added persisted 5%, 10%, and 20% grid spacing presets in the existing editor menu. The canvas overlay and grid snapping share the same spacing; unknown stored values safely fall back to 5%.
- Grid visibility and spacing use the existing project adjustment/undo path. Grid lines remain editor-only and do not become project layers or enter the FFmpeg render graph.
- CI [run 40726135615](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40726135615) **PASS**: 398 Linux tests; 397 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: custom arbitrary numeric spacing beyond presets, guide priority in dense overlaps, HiDPI and real Windows acceptance. This increment does not mark all of P04 complete.

## P04-02 — Custom numeric grid spacing (28/10/2026)

- Added a custom percentage option (1–50%) alongside 5%, 10%, and 20% presets. The custom value persists in the existing project adjustment, supports Undo/Redo, and appears in the menu when active.
- Grid drawing now uses the same normalized step as snapping, including non-divisor values such as 7%; unsupported or invalid values safely fall back to 5%.
- CI [run 40728076508](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40728076508) **PASS**: 403 Linux tests; 402 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: dense-overlap guide priority, physical Windows/HiDPI/4K acceptance, and the remaining P04/P12 gates. This increment does not mark all of P04 complete.

## P04-02 — Inspector search and reversible reset (28/10/2026)

- Added case-insensitive property search across field labels/keys without rebuilding controls or mutating project data; clearing search restores all property rows.
- Added a single-undo reset for transform, style, motion and keyframes. It preserves layer ID, name/content, source path, group and clip scope; locked layers are not reset.
- CI [run 40729358428](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40729358428) **PASS**: 406 Linux tests; 405 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: persistent workspace layout, dense-overlap guide priority, real Windows/HiDPI acceptance and remaining P04/P12 gates.

## P04-02 — Persistent workspace layout and dense-guide priority (28/10/2026)

- Added versioned UI-layout persistence in the existing SQLite settings store: main-window geometry/state, navigation tab, editor splitter sizes and inspector tab. Invalid/stale layout payloads are ignored safely; layout settings do not contain project/media content.
- Dense peer snapping now uses stable semantic tie-breaking for equal-distance candidates: edge-to-edge, then centre-to-centre, then mixed edge/centre. Distance remains primary, and peer order does not affect the result.
- CI [run 40731502132](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40731502132) **PASS**: 411 Linux tests; 410 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: physical Windows multi-monitor/HiDPI/4K acceptance, remaining shortcut/remap/IME cases and full P04/P12 acceptance. This increment does not mark all of P04 complete.

