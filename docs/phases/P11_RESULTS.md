# P11 — Kết quả tích hợp local

Toàn suite cuối: **92 tests qua, không lỗi/skip**. Đã kiểm tra app save/reopen/worker/output, kéo preview bằng chuột và một drag một undo, undo riêng khi nhập chữ, sub draft/song ngữ/trim-speed/loop, preset deterministic, batch settings/random zoom/flip/rotation, audio solo/duck/normalize, ma trận W/K/reservation, rename/undo/rollback/recovery, khóa scheduler/migration/orphan và tool repair/hash/traversal.

HTTP localhost thực kiểm tra cả yt-dlp và gallery-dl; fake transport riêng kiểm tra cache/quota/glossary/translation recovery. Không dùng chúng làm bằng chứng hỗ trợ mạng xã hội hoặc chất lượng dịch live. Binary đã chạy các workflow CPU chính và giải mã frame Qt trong smoke; xem [báo cáo local](../LOCAL_VERIFICATION.md), [evidence](../evidence/desktop-verification.json), [đối chiếu triển khai](../IMPLEMENTATION_COVERAGE.md).

Những sửa đáng chú ý: sub template không giữ nhầm cue/video cũ; nhiều cue dùng chung ASS track; clip split/loop giữ phạm vi sub; W/K được kiểm tra trong transaction enqueue; retry không đổi thành công thành reserved; orphan được phục hồi sau startup; nick/profile không đổi khi refresh; FFmpeg gói không nạp libavcodec của Qt; nguồn đổi tên giữ bytes và journal.

Các mục nâng cao còn phải code/kiểm chứng vẫn ở coverage/master; Windows/live API/Chrome/nguồn/GPU có cổng riêng. 92 tests không chứng minh toàn bộ 95 nhóm đã hoàn tất.

## Bổ sung đối chiếu truy vết P11 (28/10/2026)

Đã cập nhật `scripts/check_plan.py` để phát hiện mất hoặc trùng nhóm trong 95 yêu cầu, thiếu tên/nguồn/task/tiêu chí nghiệm thu và task không có trong master. Bổ sung `tests/test_plan_contract.py` kiểm tra bản gốc và các trường hợp tài liệu bị thiếu/mapping sai. Đây là kiểm tra **tài liệu truy vết**, không đánh dấu 95 nhóm chức năng đã nghiệm thu. Bộ test P11 mới nhất cần kết quả CI riêng; khi chưa có run PASS thì chưa được ghi cả phase P11 thành công.

**Kết quả kiểm thử P11 validator trên nhánh tổng:** commit `eaed54fa54c0013959c2f552a3d9f8e9676189ff`; [CI 40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919) PASS — 143 tests Linux, 142 Windows + 1 skipped fixture POSIX, packaged proof cả hai hệ PASS. Đã phát hiện/sửa lỗi import trong test mới trước run thành công. Chỉ nghiệm thu validator tài liệu/luồng kiểm thử synthetic, không nghiệm thu toàn bộ 95 nhóm hay live platform.


## Regression tích hợp P04/P10 — 28/10/2026

[CI 40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS 195 Linux, 194 Windows + 1 skipped POSIX fixture. Source suites và frozen app proof trên cả hai hệ kiểm tra proxy/cache, rendered In–Out loop, thumbnail source FFmpeg, cache quota/protected/symlink và Qt Settings/preview integration. Không phải nghiệm thu đầy đủ 95 nhóm hoặc chứng nhận PC Windows/GPU/Chrome/live source.
