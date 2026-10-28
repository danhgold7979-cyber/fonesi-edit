# P04 — Kết quả lớp editor

Đã code canvas layer text/image/mask với kéo/resize/rotate, khóa/thứ tự, căn snap và zoom không đổi model; inspector style/motion/keyframes; undo snapshot; timeline move/trim/split/playhead/zoom và Qt playback. Hai test editor đã qua: sửa Unicode/undo/redo/nhân bản/xóa/round-trip và split giữ ánh xạ source time. Lưu project/preset nối với Store ở app shell, render tham chiếu nối compositor P07.

Đây là phần triển khai local, chưa nghiệm thu mọi thao tác trên Windows hoặc đủ mọi tổ hợp font/parity. Phần còn lại được kiểm tra tích hợp P07/P11, không ghi hoàn tất các mục chưa có evidence.

Vòng tích hợp thêm multi-select/nhóm/căn/phân bố/copy style, double-click chữ, clip trim/speed/flip/rotation/gain, In-Out/ripple, waveform nền/audio timeline, step frame, remap và undo theo focus. Mouse drag đã được thử bằng QtTest; proxy/crop tay nắm/loop đoạn và đầy đủ shortcut còn ở coverage. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).
