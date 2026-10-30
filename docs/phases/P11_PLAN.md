# P11 — Tích hợp và hoàn thiện

Đã đọc master P11, tất cả phase plans/results local và 95 nhóm yêu cầu. Chỉ đạo tiếp tục không biến kiểm tra bên ngoài thành pass.

1. Chạy toàn bộ suite: Store/worker, editor, downloads/session, captions/translation, motion/render, batch/matrix/automation/tools.
2. Tạo app production thật đủ khu vực, save/autosave/preset, nguồn/job UI, sub editor, dry-run batch, matrix model virtualized, Settings tools/browser/provider/resources.
3. Integration UI→snapshot→worker→FFmpeg→artifact, mở lại project/queue; kiểm tra scope, shortcut không ăn IME, lỗi source/quota/no overwrite.
4. Rà bug time map, input hashing, cancel, app close, CLI/tool override và browser secret boundary; fix và chạy lại check bị ảnh hưởng.
5. Báo riêng implemented/local-tested/live-blocked/pending; không đánh dấu full Windows/platform/AI đã có. Lưu hiện vật/run summary và cập nhật traceability thực tế.

## Vòng rà soát tích hợp tiếp theo

Đối chiếu lại master P03–P12 trước sửa: ưu tiên đường dùng xuyên tab và kiểm chứng binary.

- P06-05/P07-08/P08-02/P09-06: sub là layer kéo được; bind lại đúng sidecar từng video trong batch/ma trận, map trim/speed/loop, chuỗi dịch cập nhật đúng tham chiếu; lưu bản nháp bảng sub.
- P03-04/P03-05/P09-03: khóa scheduler, migration có backup, kiểm tra W/K lần cuối trong transaction đặt chỗ, tên đầu ra theo thứ tự hàng và snapshot tool.
- P04-03/P04-05/P07-01: đa chọn/nhóm, căn chỉnh, clip inspector, ripple/in-out và audio timeline; giữ undo nguyên tử và font riêng trong canvas.
- P03-08/P10-04: repair cài bản mới cạnh bản hỏng, không thay tệp đang được job sử dụng; kiểm tra nguồn dịch không chứa bí mật trong URL.
- P12-01/P12-03: chạy batch + matrix thật qua worker binary; CI build production trên Linux/Windows và giữ evidence cụ thể. Cập nhật README/hướng dẫn/trạng thái theo kết quả thực.

Vòng công cụ phụ: import/export preset schema có kiểm tra, thu hồi pairing extension theo profile không xóa Chrome, giữ undo riêng của ô nhập khi phím tắt ứng dụng có focus. Đối chiếu OPS-07/AUTH-11/ED-19 trước đóng gói lại.


## Vòng P11 — Khóa tính toàn vẹn master và traceability (28/10/2026)

**Nhánh:** `develop/fonesi-full`. Đã đọc lại IMPLEMENTATION_PLAN, REQUIREMENTS_TRACEABILITY, IMPLEMENTATION_COVERAGE, CURRENT_STATUS và checklist các phase. Tổng thể có 12 phase, 94 task và 95 nhóm yêu cầu gốc.

**Lý do cần bổ sung:** `scripts/check_plan.py` hiện kiểm tra phase/order, duplicate ID và liên kết. Tuy nhiên, mất một yêu cầu khỏi traceability hoặc một hàng thiếu mapping/acceptance vẫn có thể không bị phát hiện nếu ID còn lại không trùng.

**Lát cắt P11-05/P11-07:**

1. Yêu cầu tất cả 95 nhóm có ID duy nhất và mapping ít nhất một task `Pxx-yy` có trong master.
2. Kiểm tra từng hàng có đầy đủ tên yêu cầu, nguồn, task và bằng chứng nghiệm thu; không chấp nhận ô rỗng hoặc placeholder.
3. Không ép `[x]` trên master; validator chỉ kiểm tra cấu trúc/yêu cầu, không tuyên bố 95 nhóm đã chạy pass.
4. Test kiểm tra đúng bộ tài liệu gốc và trường hợp thiếu một hàng/mapping/acceptance bằng fixture tạm.
5. Chạy source + packaged proof Linux/Windows; ghi P11_RESULTS kết quả thật và blocker ngoài fixture.

**Cổng mở:** nghiệm thu 95 nhóm theo UI/chức năng thực, Windows user/GPU/HiDPI/audio, Chrome login, live provider/nguồn, crash soak và benchmark corpus lớn vẫn chưa được xác nhận. Script validation không thay thế chúng.
