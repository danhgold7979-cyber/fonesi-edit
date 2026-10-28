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
