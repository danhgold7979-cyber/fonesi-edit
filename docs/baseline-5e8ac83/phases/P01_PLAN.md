# P01 — Kế hoạch chi tiết trước triển khai

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` v1.1, toàn bộ PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC và bảng truy vết. Đây là phase thiết kế; chưa xây scheduler/editor hoàn chỉnh trước cổng P02.

## Phạm vi và thứ tự

1. P01-01: dùng 95 mã yêu cầu hiện có làm baseline; ghi phạm vi hiện tại/tích hợp sau, quy tắc mặc định và xử lý lỗi.
2. P01-02/P01-03: thiết kế bảy màn hình, luồng thường dùng và trạng thái rỗng/loading/lỗi; wireframe editor có đối tượng kéo thả và phạm vi áp dụng luôn thấy.
3. P01-04/P01-05: chốt preset/override/lock, W/K/history, duration planner, missing sub/output collision.
4. P01-06: lập corpus tổng hợp có nhãn, nguồn công khai cần thử, phép đo và prerequisites chưa có.
5. P01-07: hợp đồng project/preset/job và quy tắc dữ liệu chung, đối chiếu TECHNICAL_DESIGN.
6. P01-08: luồng scan/install tool và browser/account binding có readiness ba trục.

## Bàn giao và kiểm tra

- `P01_DESIGN.md`: màn hình, wireframe, field/state, luồng, rules và data contracts.
- `SOURCE_CORPUS.md`: đầu vào, cách tạo/đối chiếu, phân biệt synthetic/live, Windows/credential prerequisites.
- `P01_RESULTS.md`: từng task với hiện vật và kết luận thiết kế.
- Kiểm tra toàn bộ link, ID đầu việc, 95 yêu cầu có vị trí/phase/tiêu chí; không đánh dấu khả năng nguồn đã hoạt động.

## Cổng hoàn tất

Tất cả task thiết kế có hiện vật, các màn hình không có quy tắc mâu thuẫn. Chưa cần API key hoặc Windows để hoàn tất thiết kế; những thứ đó là cổng thực nghiệm P02, được ghi nguyên trạng.
