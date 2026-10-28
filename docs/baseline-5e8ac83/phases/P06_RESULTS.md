# P06 — Kết quả phụ đề

Đã có SRT/VTT/ASS bằng pysubs2, cue ID/source/lock, kiểm tra timing, xuất no-overwrite, Google/LibreTranslate adapters, cache, quota reserve và thuật ngữ bảo vệ có kiểm tra marker. 3 test chuyên biệt qua cho Unicode round-trip, lock/cache/glossary/quota và warning. Transport test được gắn nhãn; không coi là chất lượng dịch live đã đạt. UI và burn-in nối chung compositor/app tiếp theo.

Vòng tích hợp thêm draft tự lưu, tìm/thay/offset, dịch câu chọn và nạp kết quả giữ sửa tay. Song ngữ có hai layer gốc/đích riêng; batch bind theo role/ngôn ngữ, auto chỉ dịch đích. Sửa recovery tái dùng file dịch cùng nội dung, giữ file đã chỉnh tay. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).
