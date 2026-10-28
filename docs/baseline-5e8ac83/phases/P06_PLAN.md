# P06 — Phụ đề và dịch

Đã đối chiếu master P06 và PR 4/ED 3. Dùng pysubs2 cho SRT/VTT/ASS thay vì tự viết parser không đủ; giữ mapping thời gian và báo rõ formatting không hỗ trợ.

1. Caption có ID, source/target, interval, style và lock; nhập/xuất Unicode, cue lỗi/chồng/tràn, editor song song.
2. Dịch qua adapter Google đã có và LibreTranslate server người dùng cấu hình, không tạo output giả khi thiếu key/provider.
3. Cache theo nội dung/ngôn ngữ/provider/glossary; không dịch lại câu khóa; quota ký tự được reserve trước request để timeout không tự gây phí lặp.
4. Xuất sub và gắn vào composition, time map sau trim/speed; ASS render chung ở P07.
5. Test parser VTT/ASS, round-trip/timing/lock/cache/quota bằng transport test gắn nhãn; live quality/billing chưa đạt nếu chưa có cấu hình.

Vòng hoàn thiện SUB-09: bật song ngữ tạo hai subtitle layer gốc/đích độc lập, mỗi layer có font/vị trí/motion riêng. Batch bind lại từng role bằng ngôn ngữ ưu tiên, ID layer xác định để lập cùng kế hoạch không tạo tên output mới. Chuỗi auto chỉ dịch role đích và giữ nguyên track gốc. Test attach/song ngữ/render/time map và idempotence preset.
