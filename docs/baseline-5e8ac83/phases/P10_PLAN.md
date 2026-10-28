# P10 — Tự động hóa và tài nguyên

Đã đọc master P10, PR 8–9, các phase local và Store/job contracts.

1. Admission theo RAM/đĩa/CPU với quiet/balanced/max và giới hạn từng loại job; không kill việc khỏe để tăng benchmark.
2. Workflow download→sub/translate→render dùng deterministic IDs/dependency, khôi phục không enqueue trùng.
3. Folder watcher ổn định hai lần kiểm tra, không theo output/symlink; schedule persisted/skip missed/không overlap.
4. Tool manager quét/path/manifest/hash/staging/install/rollback; không đè external tool hay binary phiên bản đang dùng; Chrome installer cần chữ ký hợp lệ và bước OS rõ.
5. CPU/GPU metrics phân biệt unknown; progress/elapsed/ETA và logs có lọc bí mật; nền automation không chạy trên UI thread.
6. Test idempotence/watcher/resource admission/manifest traversal/hash/rollback và workflow real media. Live network/installer/Chrome Windows chỉ được pass sau chạy thật.
