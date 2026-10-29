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

## P11-01/P11-04 — Two-clip subtitle time-map QA (29/10/2026)

A new synthetic FFmpeg integration uses two clipped sources with different speeds, 100 ms transition and two independent source/translated subtitle layers. It inspects actual ASS cue timestamps and text for both clip scopes, probes the encoded output, renders a reference frame using the shared graph and verifies source media remains unchanged. Production mapping now raises on a positive source cue that becomes 0 ms in output timing, rather than reporting successful render with lost text. ASS output is quantized to 10 ms; test enforces deterministic centisecond serialization and ≤5 ms rounding per cue edge.

[CI 40881166137](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40881166137) **SUCCESS**, exact source/test SHA `e8656dc8`: 587 Linux/586 Windows tests PASS + 1 intentional Windows skip; desktop/native host and frozen synthetic proof both OS PASS. Intermediate [CI 40880618234](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40880618234) failed one new incorrectly strict millisecond assertion in ASS on each runner; verified centisecond expectation fixed without dropping the test.

This is not confirmation of full P11 pixel/audio parity, VFR/rotation/mixed FPS, real Windows device, GPU or 95 full requirement gates.
