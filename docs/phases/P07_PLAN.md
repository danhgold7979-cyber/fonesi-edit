# P07 — Kế hoạch chi tiết: xác thực đầu vào render và ổn định compositor

**Ngày kiểm tra:** 28/10/2026. **Nhánh duy nhất:** `develop/fonesi-full`. **Trạng thái:** lập kế hoạch trước khi sửa.

## 1. Đối chiếu master plan

Đã kiểm tra `docs/IMPLEMENTATION_PLAN.md` P07-01…P07-08, `docs/EDITOR_SPEC.md` (font/logo/layer/motion/render), `docs/TECHNICAL_DESIGN.md`, P07_RESULTS, coverage và source `domain.py`, `motion.py`, `render.py`, `tests/test_render_composition.py`.

Hiện có CPU compositor/FFmpeg thực, song ngữ, keyframes, alpha/masks, motion, audio, output validation và kiểm chứng Linux/Windows với media synthetic. Chưa thể công bố đầy đủ parity trên mọi style/fonts/OS/GPU.

## 2. Lát cắt mã hóa/kiểm thử

- **P07-07/P07-08:** kiểm tra đầu vào `Clip.volume` đang dùng phép so sánh khoảng mà không kiểm tra `NaN`. Với NaN, hai phép so sánh đều false và một giá trị âm lượng không hợp lệ có thể đi vào graph FFmpeg. Bổ sung `math.isfinite(volume)`.
- Ràng buộc kích thước output và FPS thực sự là số nguyên theo schema đã công bố; không để `True` hoặc float lọt qua validate để báo lỗi muộn trong FFmpeg.
- Tạo regression tests cho numeric edge cases, nhất là NaN, Infinity, FPS/canvas sai type; đảm bảo giá trị hợp lệ và các sample render hiện có không hồi quy.
- Không thay đổi công thức random motion, filter/encoder, output manifest hoặc đồ thị công việc khi chưa có test parity.

## 3. Nghiệm thu lát cắt

- [ ] Numeric validation từ chối NaN/Infinity và giá trị không hợp lệ trước khi gọi FFmpeg.
- [ ] Dữ liệu project hợp lệ round-trip giữ nguyên; không thay schema.
- [ ] Full source suite và packaged proof Windows/Linux PASS; cập nhật P07_RESULTS và trạng thái.
- [ ] Không gắn GPU/driver thực, font CJK thực/HiDPI, parity mọi tổ hợp keyframe, corpus dài là PASS vì CI synthetic.

## 4. Cổng còn mở

Font favorites/fallback per glyph, auto-fit text/nội dung động, copy motion, vùng tránh, random kiểu khóa nâng cao, crop có tay nắm, preview/export parity đầy đủ, 60fps/4K/long-form benchmark và GPU Windows thực cần tiếp tục theo traceability/coverage. Không chuyển bất kỳ yêu cầu đã thống nhất nào sang nhóm “sau” chỉ vì chưa code.
