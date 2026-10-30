# Tiến độ task của rebuild — không thay nghiệm thu

Checkpoint code remotea08e5d337018fe0041e6e8833f0198b8af95e80d, CI41137290389 SUCCESS; các lát cắt UI/source/tool đã thêm, chưa đóng nghiệm thu task. Các số này không chứng nhận toàn task/phase. 12 phase, 94 task master; **0/94 task được nghiệm thu toàn bộ**. Những task không liệt kê vẫn chưa có lát cắt code được đối chiếu tại đây; hoạt động sửa plan không tự chứng minh tính năng. Không có % dòng code.

Mỗi dòng dưới là IN_PROGRESS/PARTIAL, không phải DONE. Test tương ứng nằm trong tests/test_*.py; nguồn trong src/fonesi_edit; phạm vi/giới hạn chi tiết tại REBUILD_*_PLAN và REBUILD_STATUS.

| Task | Đã triển khai/kiểm chứng ở phạm vi hẹp | Còn thiếu để nghiệm thu |
|---|---|---|
| P02-01 | Khóa Python/Qt/Ruff/PyInstaller và CI tool versions | Corpus/codec/filter/font/target inventory đầy đủ |
| P02-04 | Qt khung đầu nguồn và mở UI thật | Preview layer/audio/seek và parity với export |
| P02-05 | Render CPU synthetic có decode/probe/hash | GPU/RAM/VRAM/fallback benchmark trên target |
| P02-06 | EXE Windows khởi động Editor/SRT/batch, 6 checks PASS | Installer/signing/media/font/Unicode/target-PC acceptance |
| P02-08 | Ghi candidate Qt/FFmpeg/PyInstaller và giới hạn proof | Provider/preview/full packaging decisions |
| P02-09 | Existing-tool CLI role/version/encoder check | Trusted manifests/install/repair/rollback và target package provenance |
| P03-01 | Scaffold, dependency lock, Windows/Linux CI | Config/user-data ownership và nền ứng dụng đầy đủ |
| P03-02 | Project/job schema1, reject drift, online backup validated | Các schema preset/artifact/history/cache; migrations/restore faults |
| P03-03 | ffprobe thật, rational interval/time mapping | Strong source fingerprint/VFR corpus và provenance đầy đủ |
| P03-04 | Qt worker, bounded direct child, SQLite lease primitive | Durable scheduler/descendant containment/pause/crash recovery integration |
| P03-05 | Immutable intent/seed/hash, lỗi UI được lọc | Queue UI, typed error taxonomy và worker snapshot integration |
| P03-06 | Staging/decode/probe/hash/atomic no-overwrite; scan exclude output | Artifact/job provenance transaction và toàn ma trận filesystem |
| P03-07 | Project save-as/open, exact edits, manual relink/undo, ledger backup | Autosave/cache recovery và abrupt-close fault corpus |
| P03-08 | Session-only explicit paths, busy/generation guards | Persistent registry/ownership/version leases/installer lifecycle |
| P04-01 | Native panel/theme/media/inspector/numeric controls | HiDPI/drag/drop/reset/full workspace interaction |
| P04-05 | Trim/speed controls, numeric source-frame request và mapping khi export | Timeline/playhead/split/gap/ripple/waveform/loop |
| P04-08 | Native existing-tool selector | Full settings/install/account/profile/readiness UI |
| P06-01 | UTF8 SRT parser/exporter, diagnostics | VTT/ASS/style/sidecar matching và ambiguity |
| P06-04 | SRT table edit/manual lock/undo-redo/literal find-replace/split-merge | Song ngữ/tách/gộp/dịch câu chọn và lưu lịch sử bền vững |
| P06-05 | Rational cue map/trim/speed/overlap diagnostics | Timeline/offset UI và đầy đủ source/render integration |
| P06-06 | Xuất SRT mới không overwrite | ASS/bilingual/style/burn-in pipeline |
| P08-01 | Bounded scan/no-follow và dialog chọn checkbox | Multi-folder UI/filter/search/tree/exclusion controls |
| P08-02 | Selected tuple snapshot và tên output preview/no-overwrite | Presets/clip override/source-content snapshot/versioning |
| P08-07 | Actual CPU batch/decode/probe và isolated failures | ETA/resume/durable queue/full duration-tracks corpus |
| P09-02 | Lazy combination/history scope/uniqueness | Real media hashes/reservations/durable history |
| P09-03 | Seed/W/K/candidate-time budgets/cancel, incomplete distinct | Full corpus/performance/production integration acceptance |
