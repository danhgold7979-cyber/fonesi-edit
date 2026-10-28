# P12 — Kết quả đóng gói bản phát triển

Đã tạo app production và native messaging host trên Linux bằng PyInstaller. Gói chứa module downloader/extractor/EJS/formats/Qt plugins, extension, FFmpeg/ffprobe, hướng dẫn, docs và build-info/hash. FFmpeg Linux được tách thư viện khỏi Qt; Windows builder tránh gói nhầm Chocolatey shim. Entrypoint phân biệt GUI, worker và verification.

`uv run python scripts/verify_packaged.py --folder .local/packaged-handoff` đã qua trên binary: 2 job render (batch/ma trận, song ngữ), 2 job tải video/ảnh qua localhost, đổi tên/undo và smoke UI có giải mã frame. Script kiểm tra FFmpeg/ffprobe nằm trong bundle. 36 file Python source khớp hash build-info. Xem [báo cáo local](../LOCAL_VERIFICATION.md) và [evidence](../evidence/desktop-verification.json).

CI đã được mở rộng Windows/Linux: khóa dependency, toàn suite, build app/native host, chạy proof binary và upload evidence; artifact Windows phát triển chỉ được giữ khi các bước thành công. Chưa đọc được kết quả CI sau push trong phiên này, không ghi Windows đã pass. Bản Linux không thay nghiệm thu Windows/Chrome/GPU. Không tạo public release.

P12 vẫn chưa qua cổng phát hành đầy đủ: Windows máy thật, Chrome/session handoff và installer/driver, chất lượng dịch live, tải từng nguồn, HiDPI/audio/độ bền, app updater và các tùy chọn nâng cao còn lại trong coverage. Không đánh dấu toàn phase hoàn tất.
