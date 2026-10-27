# P03 — Nền ứng dụng có lưu trạng thái

Đã đọc master v1.1, P01_DESIGN, P02_RESULTS và TECHNICAL_DESIGN. Người dùng cho tiếp tục phần độc lập khi cổng bên ngoài bị chặn. Dùng CPU/Qt 6.8.3 đã chạy thật; không giả lập auth/Windows.

1. P03-01/03: tạo production domain và media refs; tái dùng các proof đã test qua adapter rõ ràng, không sao chép UI giả.
2. P03-02/07: SQLite schema có version, project/preset/snapshot/job/artifact/settings/profile/binding tables; atomic save, backup trước migration, autosave/relink.
3. P03-04/05: scheduler gọi subprocess worker độc lập, lease/heartbeat, states, cancel/pause/retry/recovery; secrets không đi vào snapshot/log.
4. P03-06: output temp/validation/no overwrite và provenance; giữ nguyên media nguồn.
5. P03-08/09: registry tool versions/leases và browser metadata, cache namespace theo account; installer/browser handoff thực hiện ở phase chuyên trách.

Bàn giao: app/CLI tạo project và chạy job render bền vững, đóng/mở phục hồi queue. Kiểm tra: real FFmpeg job, crash-worker recovery, snapshots bất biến, migration/backup và no-secret serialization. Acceptance Windows vẫn mở.
