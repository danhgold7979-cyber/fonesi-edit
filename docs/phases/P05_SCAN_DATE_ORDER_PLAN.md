# P05 — Sắp xếp kết quả scan theo ngày cũ/mới

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh tích hợp:** `develop/fonesi-full`  
**Trạng thái:** code và Qt regression đã xác nhận qua [CI 40838160968](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40838160968); P05 tổng thể vẫn mở.

## 1. Đối chiếu đặc tả và code

`PRODUCT_REQUIREMENTS.md` mục 3.2 yêu cầu "chọn thứ tự cũ trước/mới trước"; `REQUIREMENTS_TRACEABILITY.md` mục SRC-05 / P05-02 yêu cầu kiểm thử biên dữ liệu. `P05_METADATA_FILTERS_PLAN.md` đã chuẩn hóa ngày đăng; `DownloadsPage.scan_sort` hiện chỉ sắp thứ tự nguồn/tên/loại.

P05 vẫn chưa có provider-side pagination/checkpoint, metadata live tin cậy ở mọi nguồn hoặc kiểm thử tài khoản Chrome thật. Chỉ triển khai sắp xếp **cục bộ** trên các mục đã quét.

## 2. Phạm vi và rủi ro

1. Thêm "Ngày cũ trước" và "Ngày mới trước" trong `scan_sort`; không đổi mặc định "Thứ tự nguồn" để tránh thay đổi hành vi cũ.
2. Ngày đã chuẩn hóa `YYYYMMDD` phải sắp theo lịch; giá trị thiếu/sai đứng **cuối** ở cả hai chiều; các ngày bằng nhau giữ thứ tự chỉ số nguồn để ổn định.
3. Sắp xếp sau khi áp dụng tìm kiếm, loại media, trạng thái URL và bộ lọc metadata; phân trang theo thứ tự đã sắp.
4. Không thay `scan_selected` hoặc dữ liệu index gốc, account snapshot, duplicate URL checks và cap 500 mục; không gọi provider hoặc lưu URL nhạy cảm.
5. Test Qt regression cho 2 chiều, ngày trùng, ngày thiếu/sai, các trang và checkbox/download xuyên đổi sort.

## 3. Thực hiện và xác minh

- Đưa kế hoạch vào commit trước commit code, cùng nhánh tích hợp.
- Thay đổi UI sort và khóa quy tắc tie/unknown-last bằng integration test.
- Chạy `scripts/check_plan.py`, `pytest -q`, build app/native-host và frozen packaged proof Linux/Windows qua GitHub Actions.
- Chỉ cập nhật P05_RESULTS/coverage/ledger theo kết quả CI thật; không đóng full P05 hoặc các cổng live/Windows máy người dùng.

## 4. Tiêu chí nghiệm thu lát cắt

- [x] Ngày tăng/giảm đúng, ngày trùng ổn định và thiếu/sai luôn ở cuối.
- [x] Filter + sort + pagination không làm thay đổi checkbox gốc; selected download giữ account/adapter.
- [x] CI source và packaged proof Linux/Windows trên đúng code SHA đều PASS.
- [x] Cổng provider/Chrome/Windows user-device vẫn được ghi mở.
