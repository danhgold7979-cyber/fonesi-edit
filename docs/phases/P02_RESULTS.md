**HỒ SƠ BASELINE TRƯỚC REBUILD:** nội dung/bằng chứng dưới đây thuộc implementation trước đợt làm lại 30/10/2026, không chứng nhận code mới. Xem [trạng thái rebuild hiện hành](../REBUILD_STATUS.md). Baseline tích hợp được giữ tại commit `edbb47189b0e864c74623d0a4db5b5f169f2103c`.

# P02 — Kết quả kiểm chứng kỹ thuật

**Cập nhật:** 28/10/2026  
**Trạng thái:** kiểm thử source và packaged synthetic proof đã PASS trên CI Linux/Windows; cổng nghiệm thu bên ngoài vẫn mở. Không đánh dấu hoàn tất toàn bộ phase P02.  
**Nhánh:** phase/p02-windows-packaged-proof  
**Commit kiểm chứng:** ff3254ea8619bff5aefd4c2dac6e36bda637ac37  
**GitHub Actions:** [Desktop verification — run 40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095)

## 1. Nguyên nhân lỗi Windows đã tìm thấy và sửa

Bản đóng gói Windows trước đó thất bại khi tải ảnh qua gallery-dl trong proof. Artifact đã ghi rõ lỗi: UnicodeEncodeError do bảng mã console Windows (cp1252), không phải lỗi render video hoặc kết nối HTTP.

Nguyên nhân: trong chế độ mặc định, gallery-dl chọn PipeOutput khi stdout không phải terminal và in đường dẫn đầu ra. Proof sử dụng thư mục có ký tự Trung Quốc (download 中文); khi đường dẫn được ghi vào stdout kế thừa của tiến trình đóng gói, console cp1252 không mã hóa được một số ký tự. gallery-dl bắt lỗi và trả status khác 0, khiến wrapper trước đó chỉ báo lỗi chung.

Thay đổi đã triển khai:

- Đặt output mode của gallery-dl thành null trong worker desktop; ứng dụng GUI không cần in đường dẫn tải xuống ra console.
- Thu thập cảnh báo/lỗi gallery-dl có giới hạn, làm sạch URL query/fragment và che các giá trị trông như token/key/password/cookie trước khi lưu chẩn đoán.
- Kiểm tra ảnh bằng QImageReader cả bước nhận dạng định dạng và bước decode thực tế; lỗi nêu định dạng/supported formats để dễ điều tra hơn.
- Bổ sung regression test mô phỏng stdout Windows cp1252 nghiêm ngặt trong test tải ảnh vào thư mục Unicode.

Không thay đổi TLS, proxy bảo mật, xác thực tài khoản hoặc kiểm tra tính hợp lệ của ảnh. Không bỏ job tải ảnh khỏi proof.

## 2. Bằng chứng CI mới nhất

| Kiểm tra | Linux runner | Windows runner |
| --- | --- | --- |
| Dependency lock và check_plan.py | PASS | PASS |
| Test source | 92 tests; 0 fail, 0 error, 0 skip | 92 tests; 0 fail, 0 error, 1 skip |
| Lý do skip | — | Fixture cài công cụ kiểu POSIX; kiểm tra installer Windows thực vẫn cần môi trường phù hợp |
| Build ứng dụng/native host | PASS | PASS |
| Frozen packaged proof | PASS | PASS |
| Job proof | 2 render + 1 tải video + 1 tải ảnh qua localhost | 2 render + 1 tải video + 1 tải ảnh qua localhost |
| Bằng chứng tích hợp | Phụ đề song ngữ, rename/undo, UI smoke/frame decode | Phụ đề song ngữ, rename/undo, UI smoke/frame decode |

Windows proof báo passed=true, frozen=true, rename_undo_verified=true và bilingual_render_verified=true; thời gian proof 8.781 giây. Linux proof báo passed=true và frozen=true; thời gian proof 5.231 giây. Các đầu vào tải/render trong proof đều là synthetic/localhost, không phải bằng chứng hỗ trợ nền tảng mạng xã hội thật.

Artifacts của lần chạy nằm trong [GitHub Actions run](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095). Artifact Windows development build là bản review nội bộ, không phải public release.

## 3. Trạng thái từng đầu việc P02

| Task | Trạng thái | Bằng chứng / điều kiện còn thiếu |
| --- | --- | --- |
| P02-01 | Một phần | Dependency lock và toolchain CI Linux/Windows đã chạy; benchmark/ma trận codec-filter-font trên máy mục tiêu chưa đủ |
| P02-02 | BLOCKED/PENDING | YouTube và Bilibili bị proxy chặn CONNECT HTTP 403 trong lần thử trước; chưa chứng minh quét nguyên kênh hoặc auth từng nền tảng |
| P02-03 | BLOCKED/PENDING | Adapter và báo thiếu cấu hình có test; chưa dịch live hoặc xác nhận chất lượng/chi phí provider |
| P02-04 | Một phần | Qt/FFmpeg và frozen proof đạt; parity/seek/độ mượt UI Windows đầy đủ vẫn cần kiểm thử tương tác |
| P02-05 | BLOCKED | CPU proof đạt; không có GPU/driver/VRAM tương ứng để xác nhận encode GPU thật |
| P02-06 | PASS trên CI | Frozen app Windows khởi chạy, render song ngữ, tải video/ảnh localhost, rename/undo và UI smoke đã đạt |
| P02-07 | BLOCKED/PENDING | Có số đo fixture CPU nhỏ; benchmark trên máy tham chiếu và ngân sách UI/proxy/seek chưa chốt |
| P02-08 | Một phần | Root cause Windows Unicode console đã được ghi nhận và sửa; quyết định live provider/auth và các cổng bên ngoài vẫn mở |
| P02-09 | Một phần | Tool discovery/version/path và proof cục bộ có; installer/update/lease/rollback trên máy Windows thực còn mở |
| P02-10 | BLOCKED/PENDING | Profile isolation có test; Chrome thật, đăng nhập người dùng và session handoff vào downloader chưa được xác nhận end-to-end |

## 4. Các cổng chưa được xác nhận

- Tải nguyên kênh, phân trang, checkpoint, ảnh/video/sub và xác thực trên từng nền tảng.
- Dịch live Trung–Việt, chi phí, quota và chất lượng provider với nội dung đại diện.
- Chrome thật trên Windows: OTP/QR/CAPTCHA do người dùng xử lý, phiên dùng được bởi connector, đổi nick/mismatch và resume.
- GPU/VRAM/driver, HiDPI, thiết bị âm thanh vật lý, installer/update/rollback trên máy người dùng và soak/crash/power-loss dài hạn.
- Toàn bộ tương tác nâng cao của 95 nhóm yêu cầu; những mục còn mở tiếp tục nằm trong IMPLEMENTATION_COVERAGE.md.

Proxy trả 403 trước khi nhận được response từ website, vì vậy không được kết luận website chặn tài khoản hoặc extractor sai. Cấu hình egress/provider chưa được xác nhận áp dụng chỉ vì có bản nháp.

## 5. Bước tiếp theo

Giữ P02-06 hoàn tất theo bằng chứng CI; không đóng toàn phase P02 khi các cổng bên ngoài còn mở. Tiếp tục hoàn thiện phần độc lập ở P03 trở đi theo master plan và phase plan riêng. Không sửa/xóa source media, không commit secrets, browser profiles, downloaded media hoặc runtime artifacts.
