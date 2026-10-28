# P05 — Kết quả adapter và session

Đã code nhận diện nền tảng/URL, yt-dlp và gallery-dl scan/download trong worker, template folder, no-overwrite, lọc/ngôn ngữ sub, cookie jar theo binding và profile store. Có extension MV3 với thao tác gửi phiên rõ ràng, native messaging pairing mã hết hạn, Windows DPAPI và account mismatch cho danh tính xác định được; không đọc Chrome cookie DB.

Kiểm tra local gồm URL chống nhầm host, Windows filename, profile/binding isolation, pairing single-use và không có plaintext fallback. Download HTTP media từ server fixture nội bộ được test riêng, không thay kiểm chứng YouTube/Facebook/kênh nhiều trang. Live network/auth/Chrome thật vẫn mở.
