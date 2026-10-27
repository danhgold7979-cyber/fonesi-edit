# P01 — Thiết kế triển khai được chốt

## 1. Bản đồ màn hình và yêu cầu

| Màn hình | Thành phần chính | Nhóm yêu cầu | Empty/error states |
| --- | --- | --- | --- |
| Tổng quan | Việc đang chạy, metrics có timestamp, shortcut quy trình | OPS, AUTO | Chưa có job; metric không đọc được là unknown |
| Tải nội dung | URL list, platform/account, filter, cây quét, đích, enqueue | SRC, AUTH | URL sai, thiếu session, quét dở, rate limit, source không hỗ trợ |
| Phụ đề | Media, cue gốc/dịch, ngôn ngữ, provider, preview/timeline | SUB, ED | Thiếu sub, mơ hồ, thiếu provider, cue lỗi |
| Edit hàng loạt | Folder tree, preset/scope, editor, audio, output plan | BAT, AUD, ED | Không có media, thiếu tool/asset, duration bất khả thi |
| Ghép theo cảnh | Scene tree, W/K, N, audio target, bảng matrix, preview | MAT, AUD | Cảnh rỗng, thiếu tổ hợp, timeout khác vô nghiệm |
| Hàng đợi/Lịch sử | State/step/ETA, filter, retry/pause/cancel, artifacts | OPS, AUTO | Chưa có việc, crash recovery, blocked configuration |
| Cài đặt | Tool table, Chrome profiles, accounts, provider, resources/preset | TOL, AUTH, WIN | Thiếu tool/Chrome, version lỗi, expired/mismatch/bridge blocked |

Inspector có nhóm Cơ bản/Nâng cao, search/reset và đơn vị. Mọi thuộc tính của ED 3–6 nằm ở inspector của loại layer tương ứng; đầy đủ bảng phím ED 9 nằm ở Cài đặt → Phím tắt.

## 2. Wireframe editor

```text
┌ Nguồn / project   Lưu   Undo/Redo       Scope: [Clip này ▼]      Xuất thử ┐
│ Media / layers  │ Preview + vùng an toàn        │ Thuộc tính / tìm       │
│ Folder/scene    │ Logo/chữ/sub/mask có handles │ Cơ bản | Nâng cao       │
│ Khóa / ẩn      │ Kéo / resize / rotate / crop │ X Y size anchor opacity │
│ Z-order        │ Snap  Zoom  Before/After      │ Font/motion/keyframes   │
├────────────────┴──────────────────────────────┴─────────────────────────┤
│ Timeline: thước/playhead/in-out/marker/snap/zoom                         │
│ Video     [clip / clip]       Mask [interval]  Logo [interval]           │
│ Sub       [cue 1][cue 2]      Audio [waveform][music][SFX]                │
├ Jobs (thu gọn) ─ Progress/ETA/lỗi ─ CPU/RAM/GPU/đĩa ────────────────────┤
└────────────────────────────────────────────────────────────────────────┘
```

Canvas selection state: idle → selected → dragging/resizing/rotating → commit command hoặc Esc rollback. Text editing có focus riêng. Zoom chỉ đổi phép nhìn. Undo một thao tác kéo là một command.

## 3. Đường dùng thường xuyên

- Tải: dán URL → đích/preset/account đã nhớ → Quét (khi cần chọn) → Đưa vào hàng đợi. Trường hợp preset auto được bật: URL → enqueue; preflight vẫn chạy.
- Folder edit: Chọn folder → chọn preset → kiểm tra một clip/đoạn → enqueue cả lô. Không bắt mở từng video.
- Sub: chọn media+sub hoặc nhận từ downloader → ngôn ngữ → dịch nếu cần → sửa/preview → xuất. Thay font không gọi dịch lại.
- Ma trận: chọn folder cảnh → kiểm tra thứ tự → N/W/K/audio → sinh → xem/sửa/khóa hàng → xuất.
- Tool: Cài đặt → scan → chọn bản hoặc tải/cài → verify → workflow có readiness mới.
- Account: chọn platform/profile → Chrome thật → người dùng login → verify web/bridge/rights → gán nguồn; expired quay lại đúng profile rồi resume.

Thao tác đếm trên đường dùng thường xuyên, không bao gồm lần đầu chọn ổ đĩa/đăng nhập. Không bỏ bước kiểm tra an toàn chỉ để giảm số click.

## 4. Quy tắc đã khóa

- Giá trị: defaults → preset version → clip overrides. Lock là metadata giữ nguyên giá trị/keyframe đã chọn; auto chỉ cập nhật field chưa override/lock.
- Enqueue tạo snapshot bất biến. Muốn áp preset mới cho pending jobs là thao tác riêng; running jobs không đổi.
- W: không dùng lại cùng asset tại cùng scene trong W hàng liền trước. K: ít nhất K vị trí scene khác so với hàng trước hoặc mọi hàng trong W, theo cấu hình được ghi rõ.
- Unique-combination default bật; cân bằng là mục tiêu ưu tiên sau ràng buộc cứng. Lịch sử mặc định trong project, phân biệt reserved/succeeded/failed.
- Giữ đủ/thứ tự cảnh là ưu tiên cứng. Duration solver trả plan hợp lệ hoặc lý do; không tự bỏ cảnh/tăng speed vượt min-max.
- Edit mỗi clip một output không tự chuyển sang mode ghép nhiều clip. Thiếu sub mặc định tiếp tục có warning.
- Tên output: source ID + preset/snapshot suffix khi xung đột; không đè file có sẵn. Chỉ skip nếu artifact và config thật sự khớp.
- Mọi platform có UI auth nhưng readiness riêng theo connector. Account selected expired thì blocked, không silent public fallback.

## 5. Hợp đồng dữ liệu bản 1

Các hợp đồng này độc lập Qt; schema phải có version khi P03 triển khai. Không chứa secret/session value.

| Hợp đồng | Field bắt buộc | Validation |
| --- | --- | --- |
| Project | schema_version, UUID, media_refs, composition, preset_refs, created/updated | ID duy nhất, reference tồn tại hoặc missing có trạng thái |
| MediaRef | UUID, relative/absolute path ref, fingerprint, probe ref, source ref nếu có | Không nhận path là danh tính; relink phải xác minh |
| Composition | canvas width/height/FPS, ordered tracks, clips/layers, audio plan | Kích thước/rate dương; time map nhất quán |
| Clip | asset_id, source_in/out, output_offset, speed rational | 0 ≤ in < out, speed > 0; khoảng nửa mở |
| Layer | ID/type/order, interval, anchor/transform/style, keyframes, locks | Interval hợp lệ, font/asset refs; tọa độ tương đối và quy đổi pixel |
| Cue | ID/start/end/text/lang/style_ref/manual_lock | start < end, ID ổn định; cue dài/chồng là warning phân loại |
| Preset | schema_version, ID/version, groups, normalized values | Field lạ/không hỗ trợ báo rõ; không lẫn credential |
| Job | ID/type/state/step/dependency/snapshot/attempt/lease | Transition hợp lệ; finished cần artifact validation |
| Artifact | ID/path/job/input+config hashes/tool versions/validation | Thành công chỉ sau verify/atomic finalize |
| AccountBinding | platform/profile_id/identity_ref/web+bridge state/checked_at | Không lưu cookie; mismatch khác expired |
| ToolInstallation | name/version/path/origin/capabilities/lease | Path/version thật, không đè bản ngoài |

Time map cơ bản: output = offset + (source - in)/speed; ghép/lặp/crossfade tạo nhiều đoạn. Mọi layer và cue dùng cùng model đánh giá ở timestamp. Font/shaping, engine và dung sai được thử/chốt ở P02.

## 6. Tiêu chí kiểm tra thiết kế

- 95 nhóm yêu cầu vẫn có hàng traceability với phase/task hợp lệ.
- Từng màn hình có empty/loading/error/blocked, một hướng khắc phục và đường quay lại công việc.
- Tool/Chrome/session/source readiness là các cột riêng; không dùng cookie file tồn tại làm bằng chứng auth.
- Không có yêu cầu hiện tại nào bị lùi sang phần AI tích hợp sau.
