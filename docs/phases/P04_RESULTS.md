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
