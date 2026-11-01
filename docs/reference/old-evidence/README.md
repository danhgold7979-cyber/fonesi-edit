# P02 — Bằng chứng local

- [Ảnh giao diện desktop bổ sung](desktop-ui.png)
- [Frame FFmpeg có chữ, logo alpha, blur và phụ đề](p02-render-frame.png)
- [Binary Linux đóng gói mở media và chụp screenshot](p02-packaged-ui-linux.png)
- [Tóm tắt kết quả local và phiên bản thực tế](p02-local-summary.json)

Các hình dùng fixture synthetic, không có tài khoản/phiên/ảnh người dùng. Không phải screenshot bản Windows hoặc bằng chứng nguồn tải live đã hỗ trợ. Xem [P02_RESULTS](../phases/P02_RESULTS.md) cho lệnh, kiểm tra và giới hạn.

Làm sạch bằng chứng: `p02-ui-linux.png` trùng byte với `p02-packaged-ui-linux.png` (cùng Git blob SHA), nên chỉ giữ ảnh canonical của bản đóng gói; không coi đây là hai bằng chứng độc lập. `desktop-compositor.png` và `desktop-matrix.png` cũng là hai bản sao byte-identical không được tài liệu nào tham chiếu, nên bỏ khỏi cây hiện tại.