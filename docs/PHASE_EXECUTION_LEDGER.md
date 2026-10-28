# Fonesi Edit — Sổ triển khai tích hợp và cổng nghiệm thu

**Ngày rà soát:** 28/10/2026  
**Nhánh mã nguồn thống nhất:** `develop/fonesi-full`  
**Pull request kiểm tra tích hợp:** [PR #5](https://github.com/danhgold7979-cyber/fonesi-edit/pull/5)  
**Nhánh phát hành gốc:** `main`, chưa merge cập nhật này.

Tài liệu này là sổ thực hiện theo phase, **không phải chứng nhận ứng dụng đã hoàn thiện**. 12 phase / 94 đầu việc / 95 nhóm yêu cầu được xác định trong `IMPLEMENTATION_PLAN.md` và `REQUIREMENTS_TRACEABILITY.md`. Một test qua không đồng nghĩa toàn nhóm chức năng đã được nghiệm thu.

## Mã nguồn và bằng chứng kiểm tra từng phần

| Phase | Phần code/đối chiếu gần nhất | Bằng chứng CI đã xác nhận | Cổng còn mở |
| --- | --- | --- | --- |
| P01 | 12 phase, 94 task, 95 nhóm truy vết đã đặc tả | P01_RESULTS; check_plan qua các run | Chỉ cập nhật khi yêu cầu thay đổi |
| P02 | Sửa gallery-dl console Unicode, packaged proof Linux/Windows | [40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095) PASS | Live source, API dịch, Chrome, GPU, trải nghiệm máy đích |
| P03 | SQLite backup integrity/no-overwrite, alias bí mật, worker và SQLite boundary lọc credential/token trước khi lưu lỗi | [40652053745](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40652053745) PASS; có test cả failed/blocked | Crash/power-loss soak, máy Windows thật |
| P04 | Snap/group/grid/undo; loop rendered In–Out theo fingerprint; thumbnail nguồn cache nền và source proxy 640/1280/1920; crop normalized model, even-pixel FFmpeg crop, CropDialog/8 handles, crop preview/Qt drag/undo test | [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS for earlier P04 slice; [40686663256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40686663256) PASS: 262 Linux/261 Windows+1 skip + frozen proof | Crop ratio/rotation metadata edge cases, VFR/HiDPI/4K/seek parity, keyboard focus hardening and Windows user acceptance |
| P05 | Gallery session lifecycle, cây chọn item từ scan, trang 200 hàng/giữ chọn, download đúng adapter và account snapshot, chặn signed/duplicate URL, idempotent enqueue, localhost scan→PNG | [40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) PASS: 162 Linux, 161 Windows + 1 skip và frozen proof | API/source pagination/checkpoint thật, album/live 10 nền tảng, Chrome/session thật, bulk-scale UI |
| P06 | Phụ đề overwrite atomic, dịch cache không đổi vì daily_limit | [40638612141](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40638612141) PASS | Chất lượng/chi phí dịch live, undo đầy đủ bảng cue, corpus lớn |
| P07 | Validation chặn NaN/infinity âm lượng và FPS/canvas sai kiểu | [40638796940](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40638796940) PASS (trước test thêm), [40639294385](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639294385) PASS tích hợp | Font fallback, style parity, GPU/4K/soak |
| P08 | Batch multi-root local/dedup/stale, filter FFprobe duration/short-edge, checkbox; audio mapping/solver; SFX mốc giây-%-cảnh **và lặp count/interval với PCM thật**, music loop crossfade Windows-safe | [40658101720](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658101720) 225/224+1; [40659216526](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40659216526) 233/232+1; [40660385646](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40660385646) **246 Linux/245 Windows+1 skip**, frozen proof hai hệ PASS | SFX arbitrary/playlist, metadata codec/FPS/bitrate, realtime meter/solo, corpus/ETA, Windows máy đích/live provider |
| P09 | Matrix history/lock/WK; regenerate riêng hàng bằng worker và stale recheck; tần suất góc; sửa góc cập nhật formula; **weights/manual per-scene + speed min/max** trong UI/render | [40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) PASS: 180 Linux /179 Windows + 1 skip, frozen proof | Cân bằng lớn, kéo reorder cảnh, exFAT/soak Windows thực |
| P10 | Resource profile/GPU unknown/secret redaction; SQLite quota proxy cache, janitor nền chỉ hash-file, active playback protected | [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS: 195 Linux/194 Windows+1 skip + frozen proof | Task Scheduler, GPU/VRAM/driver thật, quota cache khác, installer/Windows ACL/soak |
| P11 | Bổ sung validator truy vết 95 hàng/task/acceptance và unit tests | [40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919) PASS: 143 Linux, 142 Windows + 1 skip | Chưa audit tương tác đầy đủ 95 nhóm, stress/corpus/soak |
| P12 | CI retry FFmpeg Chocolatey version 7.1.1 hữu hạn, không bỏ test khi hết retry; giữ native host | [40639294385](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639294385) PASS | Máy Windows người dùng, installer/updater ký, Chrome/GPU/audio/HiDPI |

CI mới nhất cho bộ mã P11: [40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919): **143 tests PASS trên Linux; 142 PASS và 1 skip fixture POSIX có lý do trên Windows**. Cả hai hệ chạy source regressions, build app/native host và frozen app proof bằng media synthetic/localhost: render batch và ma trận, video/ảnh, burn-in sub, rename/undo và UI smoke/frame decode. Đây là bằng chứng của những luồng kiểm thử cụ thể, không phải chứng nhận đầy đủ yêu cầu.

## Các cổng bắt buộc chưa đủ bằng chứng

1. Từng nền tảng: live profile/channel pagination, album/caption, xác thực, khôi phục, các giới hạn account/region, đủ loại media; chưa có bằng chứng kiểm thử live từ các tài khoản thực.
2. Dịch: provider thật, giá/quota/thanh toán, độ chính xác Trung–Việt với thuật ngữ và câu dài, kiểm tra lỗi và timeout billable.
3. Windows 10/11 trên máy người dùng không có bộ dev: cài đặt/rollback, long path, Unicode, quyền ghi, antivirus, HiDPI, audio output và loa thật.
4. Google Chrome chính thức trên Windows, nhiều profile/nick: đăng nhập người dùng, bridge → downloader đúng phiên, mismatch/expired/OTP/QR/CAPTCHA.
5. GPU/VRAM/driver và benchmark 1080p/4K, timeline dài, hàng trăm video/ma trận lớn, crash/power-loss soak.
6. Các tùy chọn editor/batch/audio/ma trận/automation còn trong `IMPLEMENTATION_COVERAGE.md`: crop handles, proxy, timeline thumbnails/loop, font fallback/auto-fit, random constraints, SFX chính sách, row regeneration, cache/auto cleanup và các trường hợp lỗi người dùng.

## Nguyên tắc tiếp tục

- **Một tool, một nhánh tích hợp**: mỗi phase là tập commit/kiểm thử, không tách ra thành các EXE độc lập.
- Đọc lại master → cập nhật phase plan → code/test → ghi Pxx_RESULTS → chỉ PASS phần thật sự đã có evidence.
- Không force push, không ghi secrets, browser profiles hoặc media runtime lên GitHub. Main giữ nguyên cho đến khi đủ điều kiện merge.
- Mỗi lỗi kiểm thử phải phân biệt lỗi code với lỗi môi trường (ví dụ: Chocolatey 504), và được sửa hoặc ghi blocker, không vô hiệu hóa assertions.

## Bằng chứng P05-03 cập nhật

[CI run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) PASS toàn suite: Linux 162 tests; Windows 161 tests + 1 skip POSIX; packaged proof hai hệ PASS. Phân trang UI/check chọn/anti-duplicate/account-snapshot và scan/download localhost là phần đã được kiểm chứng. Chưa có chứng cứ quét nhiều trang live của provider, OTP/Chrome thực, bản cài người dùng và các trường hợp tải hỗn hợp qua tài khoản live.

## Bằng chứng P08-04 cập nhật

[CI run 40642781347](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40642781347) đạt 166 test Linux, 165 test Windows + 1 skip POSIX-only. PyInstaller native-host và frozen proof render/download/Qt trên Linux & Windows đều đạt, nhưng SFX theo cảnh, music crossfade, meter realtime và nghiệm thu Windows người dùng vẫn mở. [P08_RESULTS](phases/P08_RESULTS.md) mô tả mapping và trường hợp đã thử.

## P09 — Tạo lại hàng và thời lượng cảnh

[CI 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) xác nhận 180 test Linux, 179 test Windows + 1 skip; binary frozen app proof đạt hai hệ. MAT-05 có nút tạo lại một hàng/check khóa/WK/history toàn chuỗi, thống kê góc; MAT-06 có weights/manual scene seconds và min/max speed được đưa vào snapshot render. Chưa có chứng nhận ma trận tối ưu với tập lớn hoặc Windows máy người dùng. [P09_RESULTS](phases/P09_RESULTS.md).

## Cập nhật P04/P10 ngày 28/10/2026

CI [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) **PASS 195 test Linux, 194 Windows + 1 skip**, build/frozen proof hai hệ đạt. Loop In–Out, thumbnail/cache source proxy và giới hạn dọn cache đã có code/test; hiệu năng thật, Chrome/live providers, GPU và phát hành Windows chưa được nghiệm thu đầy đủ.

## P03 SQLite redaction và P08 SFX/Batch workflow

[CI 40655116611](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40655116611): **219 Linux passed, 218 Windows passed +1 POSIX-only skip**, packaged app/native host/frozen proof PASS hai hệ. P08 mới: SFX trigger theo scene/%/cuối video trong AudioDialog và FFmpeg render (audio PCM được kiểm), Batch tìm/lọc/đảo chọn có invalidation khi cấu hình thay đổi. P03 SQLite boundary redaction có CI [40652053745](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40652053745) PASS. Cổng crossfade/metadata filters/live/Windows người dùng vẫn PENDING; không gắn phase đã nghiệm thu toàn bộ.

## P08-01 — Multiple local source roots

[CI 40656796768](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40656796768) xác nhận **222 Linux / 221 Windows + 1 skip**, frozen binary proof hai hệ. Local BatchPage đã quét nhiều root có dedup nguồn (cha/con trùng), filter & checkbox, chặn plan/scan stale khi đổi nguồn/thiết lập. Không đồng nhất multi-root local với quét profile/channel social nhiều trang hay pass hết P08. Metadata filters, stress/soak máy đích và live providers vẫn PENDING.

## P08-01/P08-04 — Đợt nghiệm thu metadata và music crossfade (28/10/2026)

Sau kế hoạch chi tiết trước code đã thêm FFprobe worker đọc duration/dimensions, filter theo duration & cạnh ngắn, chống callback cũ, không đổi checkbox của video ẩn; kết quả [40658101720](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658101720) **225 Linux, 224 Windows +1 skip và frozen proof PASS**. Music loop crossfade đã được kiểm tra cả domain/UI/FFmpeg xuất thực; Windows phát hiện assertion FFmpeg 7.1.1 trên nhánh asplit ở [40658721822](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658721822), sửa dùng input riêng và **[40659216526](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40659216526) PASS 233 Linux/232 Windows+1 skip cùng packaged proof**. Cổng full P08 vẫn mở cho corpus lớn/metadata cao cấp/SFX repeat/real-time meters/live provider và máy Windows thực.

## P08-04 — Fixed-interval SFX repeat (28/10/2026)

Trong cùng source Fonesi Edit, track SFX có repeat_count 1–32 và repeat_interval; domain reject role/policy không đúng, compositor resolve mốc/cảnh/% và reject onset vượt video, render FFmpeg PCM thật hai lần với điểm lặng ở giữa, UI AudioDialog nhập/lưu round-trip. [CI 40660385646](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40660385646) **246 Linux /245 Windows +1 skip và frozen proof hai hệ PASS**. Trigger không đều, meter realtime, corpus lớn, loa/installer Windows thực và live provider vẫn pending.


## P04-02/P04-03 — Crop source pipeline and UI (28/10/2026)

[CI run 40686663256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40686663256) **PASS: 262 Linux tests, 261 Windows tests + 1 POSIX-only skip; packaged app/native-host proof passed on both systems**. The verified crop slice adds normalized Clip geometry with backward-compatible full-frame defaults, validation, even-pixel source crop before flip/rotation/fit, actual FFmpeg export, source-frame overlay, eight handles, Qt drag, cancel and Undo. Remaining: full aspect-ratio/edge interaction matrix, rotated metadata/VFR/HiDPI/4K and real Windows user acceptance. This does not close all P04 requirements.
