# P08 — Batch và thời lượng/âm thanh

Đã đọc master P08, PR 5–6 và P07_RESULTS. Dùng cùng Composition/renderer, không viết đường render lô khác preview.

1. Quét folder đệ quy không đi symlink, bỏ cache/output và cho chọn/loại theo nhóm; không xóa nguồn.
2. Snapshot preset mỗi output, seed ổn định, tên theo source/preset, folder kênh edit; dry-run trước enqueue.
3. Duration planner giữ đủ scene/clip, bounds speed, proportional/equal/weights/manual; báo bất khả thi. Loop/freeze chỉ khi chọn.
4. Audio main/music/SFX, gain/fade/offset/loop và target-duration; giữ bản nguồn, no-overwrite/reuse qua manifest.
5. Test bounds, scene preservation, folder exclusions và job batch render thực. Codec/Windows giữ kiểm chứng riêng.
