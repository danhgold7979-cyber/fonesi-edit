# Fonesi Edit — Trạng thái triển khai

Bản phát triển, chưa tuyên bố nghiệm thu toàn bộ 95 nhóm yêu cầu. Theo chỉ đạo người dùng, tiếp tục phần độc lập qua mọi phase; không dừng vì mạng/tài khoản/Windows/GPU và không gắn các mục đó là pass.

| Phase | Code/kiểm chứng hiện có | Cổng còn riêng |
| --- | --- | --- |
| P01 | Thiết kế, luồng, contracts, traceability | Cập nhật theo thay đổi đã được chấp thuận |
| P02 | Source tests và frozen packaged proof Linux/Windows CI đạt; đã sửa lỗi gallery-dl Unicode console | Live nguồn/dịch, Chrome/session handoff, GPU/VRAM, installer/rollback và nghiệm thu trên máy Windows người dùng |
| P03 | Domain/SQLite/snapshots/worker; backup có integrity/no-overwrite, credential alias checks và error redaction; CI Linux/Windows pass | Soak/crash/power-loss, filesystem không hỗ trợ hard link, installer và nghiệm thu máy Windows người dùng |
| P04 | Canvas/inspector/timeline/undo, rendered In–Out loop, thumbnail source strip async, validated source proxy 3 mức; CI Linux/Windows frozen PASS | Crop/9 anchor, VFR/HiDPI/4K/seek/timeline dài, đầy đủ shortcut và máy Windows user |
| P05 | yt-dlp/gallery-dl, profile/binding và bridge; thêm scan→cây checkbox theo trang, lựa chọn/tải item đúng engine/account, URL signed/duplicate bảo vệ; CI/packaged Linux/Windows PASS | Provider pagination/checkpoint và live 10 nền tảng, tài khoản Chrome/identity thực, batch lớn và filter/sort nâng cao |
| P06 | SRT/VTT/ASS, sửa/lock/cache/quota/provider adapters | Chất lượng/chi phí dịch live và kiểm tra ngôn ngữ provider |
| P07 | Compositor, motion/keyframes, font, mask, alpha, audio, reference | Từng tổ hợp style/OS/GPU, performance target |
| P08 | Folder dry-run, output kênh, duration solver/loop/freeze và audio shared/by_name/ordered/random theo seed, UI chọn audio folder; source/packaged CI Linux/Windows PASS | SFX theo cảnh/phần trăm, music crossfade/solo/meter realtime, corpus lớn, Windows user audio |
| P09 | Lazy matrix, W/K/history/lock, **regenerate một hàng** không đổi hàng khác, thống kê usage, formula sync; **weights/manual seconds** và speed bounds từ UI đến render; CI/frozen Linux/Windows PASS | Stress solver ma trận lớn, reorder cảnh/locks nâng cao và Windows/exFAT thực |
| P10 | Workflow/watch/schedule và resources; Settings quota proxy cache/janitor nền an toàn, bảo vệ file QMediaPlayer đang phát; CI/frozen PASS | Task Scheduler, GPU/VRAM/driver thật, cache khác/installer và Windows/ACL/soak |
| P11 | Test local và app integration đang mở rộng | Regression cuối và đối chiếu đầy đủ tùy chọn |
| P12 | Script/build app + native host; frozen proof Linux/Windows CI đã đạt | Cài đặt/rollback, máy Windows người dùng, Chrome/GPU/HiDPI/audio và nghiệm thu release còn mở |

Chạy `uv run fonesi-edit`. Bản CLI/prototype cũ vẫn giữ để hồi quy. Runtime, browser profiles, video và API keys không được commit.

Baseline local trước lát cắt hardening: 92 tests qua. CI mới nhất: Linux 108 pass; Windows 107 pass + 1 skip có chủ đích. Cả hai runner build app/native host và chạy frozen proof thành công; binary chạy render batch/ma trận song ngữ, tải video/ảnh localhost, rename/undo, UI smoke và giải mã frame Qt. 36 file source khớp hash của bundle. Xem [báo cáo](LOCAL_VERIFICATION.md), [evidence JSON](evidence/desktop-verification.json) và [phần đã có/còn mở theo 95 nhóm](IMPLEMENTATION_COVERAGE.md).

CI P02: [run 40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095). CI hardening P03: [run 40635978628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40635978628). Cả hai dùng synthetic/localhost evidence, không phải nghiệm thu máy Windows người dùng. Mạng xã hội nguyên kênh, API dịch thật, Chrome session handoff, GPU/VRAM/driver, HiDPI/audio và installer/rollback máy thật vẫn cần kiểm chứng riêng. Những tùy chọn nâng cao chưa hoàn tất tiếp tục được ghi trong coverage, không tự đổi thành đã đạt hoặc loại khỏi phạm vi. Giọng AI/ASR/OCR/tracking thuộc giai đoạn sau.

## Cập nhật code và CI trên nhánh tổng 28/10/2026

Đã tiếp tục bổ sung code/kiểm thử theo phase P04–P10 và sửa CI P12 trên duy nhất nhánh `develop/fonesi-full`. [Sổ thực hiện](PHASE_EXECUTION_LEDGER.md) dẫn từng run và cổng còn mở. CI của bản tích hợp trước bộ test P11 mới nhất: [run 40639294385](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639294385) đạt 140 tests Linux, 139 tests Windows + 1 skip fixture POSIX, cùng packaged proof cả hai nền tảng. P11 đang bổ sung kiểm tra 95 nhóm yêu cầu. Kết quả synthetic/localhost và runner Windows Server không thay nghiệm thu dùng thật hoặc xác nhận toàn bộ tính năng.

**Bổ sung P11:** [CI 40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919) PASS (143 Linux, 142 Windows + 1 skip POSIX-fixture) cùng packaged proof binary hai hệ cho nhánh tổng. Bài kiểm tra 95 nhóm chỉ xác nhận mã truy vết/task/acceptance không rỗng, **không xác nhận 95 chức năng đã đủ hoặc sử dụng live đã hoạt động**.

## Cập nhật P05: quét chọn từng item (28/10/2026)

[CI run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) **PASS 162 test Linux, 161 test Windows + 1 skip**, build/frozen packaged proof trên cả hai hệ. Đã có cây chọn item, phân trang UI 200 hàng, lựa chọn qua nhiều trang, bảo vệ URL tải và account snapshot, chống job trùng, test scan→tải file PNG trên localhost. Phân trang UI không đồng nghĩa quét đủ nhiều trang nguồn; chưa xác nhận 10 nền tảng/live Chrome hoặc nghiệm thu installer trên Windows máy người dùng. Xem [P05_RESULTS](phases/P05_RESULTS.md) và [coverage](IMPLEMENTATION_COVERAGE.md).

## Cập nhật P08: âm thanh theo video (28/10/2026)

[CI 40642781347](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40642781347) PASS: **166 test Linux, 165 test Windows + 1 skip**, binary packaged proof hai hệ PASS. Thêm policy một audio chung/trùng tên/theo danh sách/ngẫu nhiên seed có dry-run mapping và audio track thật được FFprobe kiểm trước; không thay preset, không ghi đè nguồn. SFX/music crossfade/meters và thử nghiệm Windows trên máy người dùng vẫn mở. Xem [P08_RESULTS](phases/P08_RESULTS.md).

## P09 — Kết quả nâng cấp ma trận (28/10/2026)

[CI 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) PASS **180 Linux / 179 Windows + 1 skip**, packaged proof hai hệ đạt. Đã code tạo lại riêng hàng không vi phạm W/K/history/lock, thống kê tần suất góc, ô nhập thời lượng cảnh theo weights hoặc số giây nhập tay, speed bounds trong Matrix UI, truyền chính xác đến solver và render. Chưa khép cổng Windows/exFAT thực tế, reorder cảnh UI và solver quy mô lớn. Chi tiết [P09_RESULTS](phases/P09_RESULTS.md).

## Cập nhật P04/P10 ngày 28/10/2026

CI [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) **PASS 195 test Linux, 194 Windows + 1 skip**, build/frozen proof hai hệ đạt. Loop In–Out, thumbnail/cache source proxy và giới hạn dọn cache đã có code/test; hiệu năng thật, Chrome/live providers, GPU và phát hành Windows chưa được nghiệm thu đầy đủ.
