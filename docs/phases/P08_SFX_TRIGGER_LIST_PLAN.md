# P08-04 / P11-04 — Danh sách trigger SFX tùy ý trên timeline xuất

**Ngày:** 30/10/2026. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`.
**Base HEAD đã rà soát:** `899509efa469e5dd8873b90d81bffe7275d4515e`. Kế hoạch được ghi trước khi sửa code.

## 1. Đối chiếu yêu cầu và hiện trạng

Đã đọc `AGENTS.md`, `README.md`, master `IMPLEMENTATION_PLAN.md` (P08/P11), `PRODUCT_REQUIREMENTS.md` §6, `IMPLEMENTATION_COVERAGE.md`, `REQUIREMENTS_TRACEABILITY.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P08_PLAN.md`, `P08_RESULTS.md` và lát cắt P08-07 existing-output preflight.

Yêu cầu sản phẩm §6 cho phép đặt **nhiều sound effect trên timeline**. Code hiện tại hỗ trợ một SFX tại một anchor, hoặc lặp đều bằng `repeat_count/repeat_interval` (tối đa 32). Chưa có danh sách thời điểm không đều. AudioDialog có 17 cột; `compile_graph` đang tạo FFmpeg input riêng cho từng lần lặp, vì nhánh `asplit` từng gây lỗi assertion trên FFmpeg 7.1.1 Windows.

## 2. Phạm vi lát cắt

Thêm trường tùy chọn `trigger_times` cho một track SFX. Đây là danh sách thời điểm (giây) tính từ **đầu timeline đầu ra sau trim/speed/transition**, không phải thời gian trong file nguồn.

- Cho phép 2–32 thời điểm, số hữu hạn, không âm, tối đa 86.400 giây, tăng nghiêm ngặt và không trùng.
- Chỉ áp dụng cho `mode=sfx`; mỗi sự kiện dùng cùng source, trim, gain, fade và policy mute/solo của track.
- Khi có `trigger_times`, yêu cầu anchor `absolute`, `offset=0`, `repeat_count=1`, `repeat_interval=0`, `loop=false`. Không trộn hai cơ chế đặt lịch; không tự fallback.
- Từng thời điểm phải nằm trước cuối timeline thực tế. Nếu bất kỳ trigger nào ở ngoài timeline, từ chối toàn bộ render trước khi xuất; không bỏ riêng trigger lỗi.
- Không có trường mới thì giữ nguyên hoàn toàn hành vi cũ của anchor đơn và repeat đều; không đổi schema version, preset cũ vẫn đọc được.

## 3. Thiết kế triển khai

1. **Domain:** validate type chặt (không nhận bool như số), length 2–32, finite/range, strict ordering/uniqueness, role SFX và tính loại trừ với anchor/repeat/loop. Bảo toàn serialization qua `Composition.to_dict/from_dict`.
2. **Renderer:** dùng một FFmpeg input độc lập cho mỗi trigger (không dùng `asplit`). Áp cùng trim/PTS/volume/resample/stereo/fade, delay theo giây của timeline xuất, pad/trim về tổng duration; mix N event bằng `amix`. Kiểm tra toàn bộ onsets trước khi dựng graph; giới hạn N ở 32.
3. **AudioDialog:** thêm cột thứ 18 “SFX mốc tùy chỉnh (s)” nhận các số giây phân tách bằng dấu phẩy hoặc chấm phẩy, dùng dấu chấm thập phân. Ô trống giữ cách đặt cũ. Hiển thị lại danh sách đã lưu; lỗi parse/domain không được thay composition đang mở.
4. **Tương thích:** track cũ không có `trigger_times` không đổi; không tác động main/music, video gốc, Batch/Matrix snapshot, SQLite schema, output naming hay no-overwrite finalizer.
5. **Tài liệu:** sau khi CI đạt, cập nhật P08_RESULTS, P08_PLAN, CURRENT_STATUS, IMPLEMENTATION_COVERAGE và PHASE_EXECUTION_LEDGER bằng SHA/run thực tế. Không đánh dấu toàn P08/P11 hoàn tất.

## 4. Kiểm thử bắt buộc

- Domain: hợp lệ; rỗng/1/>32; chuỗi/object/bool/NaN/Inf/âm/quá lớn; trùng/không tăng; track không phải SFX; loop; anchor tương đối/nonzero offset; repeat conflict.
- Serialization: round-trip không mất thứ tự, giá trị hoặc trường cũ.
- FFmpeg graph: N input độc lập, đúng từng `adelay`, đúng `amix=inputs=N`; từ chối trigger bằng/vượt cuối video và không tạo output dở.
- Media regression: render MP4 synthetic có ít nhất ba trigger không đều; giải mã PCM chứng minh âm thanh xuất hiện tại từng cửa sổ dự kiến và không xuất hiện ở khoảng im lặng xen giữa; nguồn giữ nguyên.
- Qt regression: nhập/lưu/mở lại danh sách; dấu phẩy/chấm phẩy; chuỗi sai, số không hữu hạn và track sai role phải hiện cảnh báo, giữ composition trước đó.
- Chạy `uv run python scripts/check_plan.py`, `uv run pytest -q`, build desktop/native host và `scripts/verify_packaged.py`; GitHub Actions Linux + Windows phải PASS trên đúng SHA.

## 5. Giới hạn và cổng chưa đóng

Lát cắt này chỉ đóng phần **trigger SFX không đều**. Playlist nhiều file nguồn, meter/clipping realtime, solo monitoring qua thiết bị thật, normalization loudness theo corpus, benchmark render ETA/kích thước, corpus lớn, Windows user hardware/driver/installer/ACL/AV, live providers/Chrome/GPU và SQLite issue #6 vẫn OPEN. CI synthetic/localhost không thay nghiệm thu trên máy Windows người dùng.


## 6. Triển khai và bằng chứng (30/10/2026)

- [Code/test f6d90e4](https://github.com/danhgold7979-cyber/fonesi-edit/commit/f6d90e4470cdca3e98f23e48f4f0983521540a80) bổ sung `trigger_times` cho track SFX: 2–32 timestamp, số hữu hạn, tăng nghiêm ngặt, không trùng, trong 0–86.400 giây; từ chối sai role hoặc xung đột anchor/offset/repeat/loop.
- FFmpeg dùng input độc lập mỗi trigger, không dùng `asplit`; áp trim/gain/fade/delay và mix. AudioDialog có cột 18, parse dấu phẩy/chấm phẩy, decimal dot. Project cũ và schema version không đổi.
- [CI 40988695667 attempt 2](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40988695667) **SUCCESS exact SHA f6d90e4**: Linux **656 passed**; Windows **655 passed + 1 intentional POSIX skip**; check_plan, benchmark 128 file, desktop/native-host và frozen packaged proof PASS hai OS.
- Lần đầu Windows provisioning gặp Chocolatey 503; retry job cài được FFmpeg và toàn bộ Windows checks PASS. Artifact `FonesiEdit-Windows-development` khoảng 197 MB, hết hạn 06/11/2026; không phải installer/release.

**Còn mở:** playlist nhiều file nguồn/track, meter/clipping/solo realtime, corpus lớn/ETA/output size, Windows user hardware/installer/ACL/AV/HiDPI/GPU, Chrome/live providers và SQLite issue #6. Không đóng toàn P08/P11.
