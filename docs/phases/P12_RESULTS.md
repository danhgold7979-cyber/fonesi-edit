# P12 — Kết quả đóng gói bản phát triển

Đã tạo app production và native messaging host trên Linux bằng PyInstaller. Gói chứa module downloader/extractor/EJS/formats/Qt plugins, extension, FFmpeg/ffprobe, hướng dẫn, docs và build-info/hash. FFmpeg Linux được tách thư viện khỏi Qt; Windows builder tránh gói nhầm Chocolatey shim. Entrypoint phân biệt GUI, worker và verification.

`uv run python scripts/verify_packaged.py --folder .local/packaged-handoff` đã qua trên binary: 2 job render (batch/ma trận, song ngữ), 2 job tải video/ảnh qua localhost, đổi tên/undo và smoke UI có giải mã frame. Script kiểm tra FFmpeg/ffprobe nằm trong bundle. 36 file Python source khớp hash build-info. Xem [báo cáo local](../LOCAL_VERIFICATION.md) và [evidence](../evidence/desktop-verification.json).

CI branch P02 ngày 28/10/2026 đã PASS trên Linux và Windows trong [run 40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095): khóa dependency, check_plan, test source, build app/native host và frozen proof. Windows runner là Windows Server 2025; proof synthetic tải video/ảnh localhost và render batch/ma trận, phụ đề song ngữ, rename/undo, UI smoke/frame decode. Artifact Windows development build được lưu 7 ngày để review. Đây là CI evidence trên nhánh phase, không thay nghiệm thu trên máy Windows người dùng, Chrome/session handoff, GPU/driver hoặc nguồn live. Không tạo public release.

P12 vẫn chưa qua cổng phát hành đầy đủ: Windows máy thật, Chrome/session handoff và installer/driver, chất lượng dịch live, tải từng nguồn, HiDPI/audio/độ bền, app updater và các tùy chọn nâng cao còn lại trong coverage. Không đánh dấu toàn phase hoàn tất.

## Ổn định CI Windows — 28/10/2026

Một run Windows trước đó bị Chocolatey Community 504 Gateway Timeout khi cài FFmpeg 7.1.1, trước khi test ứng dụng. Pipeline nay retry giới hạn ba lần, giữ nguyên phiên bản và fail nếu vẫn không cài được. Run [40639294385](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639294385) đã PASS cả Linux/Windows với frozen proof; không suy ra Windows 10/11 máy người dùng đã nghiệm thu hoặc installer/app updater đã đầy đủ.
