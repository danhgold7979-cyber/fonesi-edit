> Rebuild notice (2026-10-28): statuses below describe baseline planning/alpha history, NOT current clean-code acceptance. Current plan: [REBUILD_MASTER_PLAN.md](REBUILD_MASTER_PLAN.md); evidence: [CURRENT_STATUS.md](CURRENT_STATUS.md). Original scope is retained.

# Fonesi Edit — Thiết kế kỹ thuật để chuẩn bị code

Trạng thái: thiết kế đề xuất. Những lựa chọn có nhãn P02 cần kết quả thực nghiệm trước khi khóa. Không có thư viện hoặc nền tảng nào đã được cài/kiểm chứng bởi tài liệu này.

## 1. Kiến trúc và trách nhiệm

| Lớp/module dự kiến | Trách nhiệm | Không được làm |
| --- | --- | --- |
| `ui/` | Qt workspace, inspector, timeline, bảng nguồn/job | Chạy FFmpeg hoặc gọi mạng chặn UI |
| `domain/` | Project, media, track, cue, keyframe, preset, time map | Phụ thuộc widget hoặc provider cụ thể |
| `application/` | Use case, command/undo, phạm vi áp dụng, lập kế hoạch | Ghi đè cấu hình job đang chạy |
| `jobs/` | DAG, scheduler, lease, cancellation, retry, recovery | Tự coi tệp tồn tại là job đã xong |
| `storage/` | SQLite, migration, project format, config/cache | Lưu cookie/API key vào project |
| `connectors/` | Registry, nhận dạng URL, enumerate/download/sub/auth | Báo mọi nguồn cùng mức hỗ trợ |
| `subtitles/` | Parser/cue/style/time map/validation/export | Giả lập OCR/ASR khi không có sub |
| `translation/` | Adapter, glossary, batch/cache/quota | Gọi dịch trả phí chưa cấu hình |
| `media/` | Probe, fingerprint, proxy, waveform, thumbnail | Đọc toàn bộ thư mục lớn trên UI |
| `preview/` | Playback, composition và frame tại timestamp | Tự định nghĩa tọa độ khác exporter |
| `render/` | Compile render plan, FFmpeg, kiểm tra artifact | Nội suy keyframe khác preview |
| `assembly/` | Duration planner, cảnh/góc, solver W/K, history | Nới ràng buộc im lặng |
| `resources/` | Metrics, encoder capabilities, admission policy | Dựa vào tên GPU để khẳng định tăng tốc |
| `dependencies/` | Discovery, tool manifest, download/install/verify/version/lease/rollback | Đè bản hệ thống hoặc đổi binary đang dùng |
| `browser/` | Chrome thật, profile, account binding, session broker và preflight | Coi đăng nhập web là connector đã dùng được phiên |

Định hướng: Python + PySide6 + SQLite + FFmpeg/ffprobe; yt-dlp/gallery-dl qua adapter. Phiên bản Python/Qt/FFmpeg, engine playback và packaging được quyết định ở P02 bằng tương thích/benchmark, không dùng bản mới nhất mặc định.

## 2. Cấu trúc repository dự kiến

```text
docs/                       Đặc tả, quyết định và evidence
src/fonesi_edit/             Các module trong bảng trên
tests/                      Test logic, integration và GUI cần thiết
fixtures/                   Mẫu nhỏ được phép lưu, không có cookie/API key
scripts/                    Dev/bootstrap/package/diagnostics
packaging/                  Windows manifest và cấu hình đóng gói
pyproject.toml              Manifest khi bắt đầu P03
<dependency lock>           Chọn định dạng sau kiểm chứng toolchain
```

Đây là sơ đồ, chưa tạo các file manifest/dependency ở bước lập kế hoạch. Repository hiện có được dùng trực tiếp, không cần tạo worktree cho mỗi phase.

## 3. Dữ liệu và danh tính

| Đối tượng | Trường/hành vi thiết yếu |
| --- | --- |
| Project | UUID, schema version, settings, media refs, timeline, presets, created/updated |
| Source | Connector, account scope ref, stable platform ID, display name, canonical URL, scan cursor |
| SourceItem | Source/post/media IDs, loại, ngày, quyền truy cập, chất lượng/sub có sẵn |
| MediaAsset | UUID, path ref, fingerprint/hash, probe, rotation/time base, source relation |
| TimelineClip | Asset ID, source in/out, output offset, speed/time map, audio mapping |
| Layer | ID/type/z-order, interval, anchor/transform/style, keyframes, lock/visibility |
| SubtitleCue | ID, source text, translated text, language, interval, style ref, manual lock |
| PresetVersion | ID/version, groups, normalized values, schema, parent/version provenance |
| Job/Step | ID/type/state, dependency, snapshot, attempts, lease, progress, error/result |
| Artifact | Path, job/snapshot/inputs, validation, duration/tracks, tool versions, status |
| MatrixRow | Scene IDs/asset IDs, seed/rules, reservation, artifact link, history scope |
| CacheEntry | Namespace/key/version, size, checksum khi cần, last use, references |
| ToolInstallation | ID/name/version/path/origin/architecture, manifest, hash/signature, capability check, active leases |
| BrowserProfile | ID/name, Chrome installation ref, user-data-dir, ownership, running/locked state |
| PlatformAccountBinding | ID/platform/profile ref, account identity khi xác minh được, default scope, auth/bridge status, checked time |

- Stable ID nền tảng không dựa tên kênh hoặc URL hiển thị. ID media cục bộ không đổi chỉ vì đổi tên/di chuyển khi relink nhận diện được.
- Cache nhanh dùng metadata/fingerprint; chống trùng mạnh hoặc quyết định tệp giống hệt cần hash nội dung. Không coi size+mtime là bằng chứng tuyệt đối.
- SQLite giữ index/hàng đợi/lịch sử; project trao đổi có schema riêng và tham chiếu media, không nhúng toàn bộ video.
- Dùng transaction cho job/artifact/history; một writer hoặc hàng đợi ghi có kiểm soát. Không chia sẻ connection tùy tiện giữa worker process.
- Migration có version, backup, kiểm tra tương thích và khôi phục; không sửa project bản gốc nếu mở phiên bản không hỗ trợ.

## 4. Hợp đồng giữa các module

### Connector

- `identify(url)` → loại URL, canonical source/item ID, platform.
- `capabilities(context)` → khả năng cụ thể theo loại nội dung và auth, không chỉ boolean website.
- `enumerate(source, filters, cursor, cancel)` → trang item, cursor mới, complete/partial/unknown, cảnh báo.
- `list_subtitles(item)` → language/origin/format/URL hoặc handle; không giả định mọi item có sub.
- `download(item, quality, target, cancel)` → kết quả/tệp tạm và metadata; validation do media/artifact layer tiếp tục.
- `auth_status(account_binding_ref)` → đúng danh tính/trạng thái web/khả năng connector dùng phiên/quyền nguồn; không trả bí mật cho UI/log. Không nhận global cookie jar dùng lẫn các tài khoản.

### Translation provider

- Capabilities về ngôn ngữ, batch limit, tính năng style/context/usage.
- Request gồm cue ID, ngữ cảnh, ngôn ngữ, glossary/version, khóa manual và request ID.
- Response ánh xạ cue ID → text, usage, lỗi từng phần, provider/model version.
- Kiểm tra đủ ID/không cue lạ/không rỗng bất thường. Dịch không tự đổi timestamp.
- Cache key từ nội dung/ngữ cảnh, ngôn ngữ, glossary, provider/model/config. Giá trị bí mật không tham gia bản export/cache key công khai.
- Timeout sau khi gửi request có thể là trạng thái không rõ đã tính phí. Không hứa exactly-once với provider không có idempotency; ghi nhận và áp chính sách retry/hạn mức rõ ràng.

### Preview/render

- Đầu vào chung là `CompositionPlan`: output spec, ordered tracks/layers, time maps, font/style assets, keyframes, audio plan, seed và version.
- Cùng phép đánh giá transform tại timestamp, thứ tự layer, đơn vị và font layout. Compiler riêng phải qua phép so frame/time map.
- `compile(plan, capabilities)` → render steps, tài nguyên dự kiến, warnings hoặc unsupported reasons.
- Preview chất lượng thấp dùng proxy theo cùng plan; khung kiểm tra chất lượng cao lấy từ đường render chuẩn.
- Nếu engine không biểu diễn đúng một thuộc tính, đánh dấu giới hạn, bổ sung đường render preview hoặc chặn tính năng đó; không giả preview khớp.

## 5. Quy ước thời gian, hình học và font

- Cue và clip dùng khoảng nửa mở [start, end). Lưu timestamp nguyên với time base được định nghĩa, tính speed/FPS bằng rational để tránh tích lũy float; làm tròn khi đổi sang frame/sample theo cùng quy tắc.
- Với đoạn nguồn [a,b), speed r>0 và offset d, ánh xạ điểm t trong nguồn là `d + (t-a)/r`. Cue được giao với đoạn nguồn trước khi ánh xạ.
- Ghép/lặp/crossfade là time map nhiều đoạn; sub/audio đi theo cùng map. Không chỉ nhân toàn bộ SRT một hệ số khi clip có nhiều biến đổi.
- VFR, rotation metadata, sample aspect ratio và audio offset phải probe/chuẩn hóa theo chiến lược P02, không giả mọi đầu vào CFR vuông pixel.
- Hình học đánh giá trên canvas đầu ra sau khi xử lý hướng hiển thị. Vị trí/size tương đối + anchor có quy đổi pixel; preview zoom là phép nhìn, không sửa giá trị project.
- Tốc độ chuyển động % canvas/giây hoặc duration liên kết, độc lập FPS. Random có seed và thứ tự nguồn ổn định.
- Chốt thứ tự biến đổi crop/fit/rotate/flip/scale/overlay/mask/sub bằng CompositionPlan; không dùng thứ tự khác giữa batch và preview.
- Font có asset/family/style/version ref, fallback và cảnh báo glyph. Cùng shaping/wrapping/line metrics hoặc có phép đối chiếu trước khi công bố hỗ trợ.

## 6. Preset, sửa tay và undo

Thứ tự giá trị: mặc định app → preset version → ghi đè theo clip → giá trị/keyframe được khóa. Auto chỉ cập nhật trường chưa ghi đè/chưa khóa, trừ thao tác reset rõ ràng.

- Command ghi giá trị trước/sau, đối tượng và scope. Một drag tạo một command, nhiều thay đổi nhóm là transaction undo.
- Sửa inspector/canvas/timeline cùng cập nhật domain model. Autosave lưu model sau command ổn định, không trạng thái kéo dở.
- Khi enqueue: serialize snapshot canonical, seed, nguồn và tool requirements. Preset đổi sau đó không ảnh hưởng job cũ.
- Apply hàng loạt có xem trước đối tượng/thuộc tính bị tác động; nhập preset kiểm tra version và tài nguyên còn thiếu.

## 7. Job, retry và artifact

Trạng thái job chung: pending → running → validating → succeeded hoặc succeeded_with_warnings. Nhánh lỗi: retry_wait / blocked_configuration / failed / canceled. Công đoạn riêng ghi scanning/downloading/translating/rendering để UI hiển thị.

- Pause hàng đợi chỉ dừng nhận việc mới; hủy process hiện tại theo token riêng và dọn tệp tạm do tác vụ sở hữu.
- Job ID + step + snapshot hash là khóa chống tạo việc trùng. Kết quả bên ngoài chưa chắc chắn được đối chiếu trước khi retry.
- Lease/heartbeat phân biệt worker còn sống với job mồ côi. Mở lại đánh giá output và step, không nhận mọi running cũ là thành công/thất bại ngay.
- Retry phân loại mạng/rate limit/tạm thời so với auth/quota/input/config; giới hạn/backoff/jitter; không loop vô hạn.
- FFmpeg chạy bằng danh sách argument, không chèn tên file/tiêu đề thành shell code; thu stdout/stderr có giới hạn và giữ exit code.
- Output cùng filesystem với tệp đích khi cần rename atomic; kiểm tra decode/probe/duration/tracks theo chính sách rồi mới finalize và commit history. Dọn tệp tạm không xóa nguồn.
- Không hứa tiếp tục render từ đúng frame sau crash; công đoạn đó có thể chạy lại. Checkpoint các công đoạn đã xong.

## 8. Ma trận và duration planner

- Solver hoạt động trên scene ID/asset ID/content hash khi cần, không dùng tên C/G làm danh tính.
- Không trùng tổ hợp, W, K và cân bằng là các điều kiện riêng; định nghĩa phạm vi lịch sử/cửa sổ được lưu trong snapshot.
- Reservation tránh hai job đồng thời nhận cùng tổ hợp. Failed/canceled có trạng thái riêng; commit thành công chỉ sau artifact hợp lệ.
- Row sửa tay/khóa ô phải validate lại toàn bộ chuỗi chịu ảnh hưởng W/K, không chỉ hàng vừa sửa.
- Sinh lazy số lượng yêu cầu, có budget thời gian/cancel. Không tìm ra trước timeout khác chứng minh vô nghiệm.
- Duration planner dùng min/max đoạn, speed, thứ tự/đủ cảnh, overlap và audio target; trả plan khả thi hoặc lý do mâu thuẫn, không ngầm nới điều kiện.
- Tái tạo cùng seed đòi hỏi cùng tập đầu vào, thứ tự, preset, phiên bản thuật toán và history snapshot; seed đơn lẻ chưa đủ.

## 9. Tài nguyên, lịch và cache

- Admission control trước khi chạy job, token riêng cho mạng/render/GPU/dịch và ngân sách RAM/VRAM/đĩa. Chỉ số thiếu đọc được phải hiện unknown.
- Thông tin encoder liệt kê trong FFmpeg chưa chứng minh driver/phần cứng dùng được; thử encode nhỏ thật.
- Ngưỡng giảm/tăng tải khác nhau và có khoảng ổn định để tránh dao động, không kill render khỏe chỉ vì spike ngắn.
- Watcher loại output/cache, debounce, kiểm tra tệp ổn định và probe; chống sự kiện trùng/symlink hoặc vòng thư mục khi quét.
- Lịch lưu mốc chạy, lần cuối, chính sách bỏ lỡ khi máy ngủ và chống overlap. Mặc định chỉ chạy trong app đang mở; chạy khi app đóng cần app nền/Windows Task Scheduler được bật rõ, không mặc định đã có service.
- Cache có version/fingerprint/refcount hoặc lease đang dùng; LRU/tuổi/dung lượng, không xóa nguồn/output/user assets.

## 10. Dữ liệu riêng, cấu hình và cập nhật

- API key/cookie chỉ tham chiếu tên binding hoặc kho credential hệ điều hành khi phù hợp; không lưu trong preset/CSV/log/project.
- Lần dùng dịch từ xa nêu nội dung phụ đề sẽ gửi tới provider; tôn trọng cấu hình/hạn mức người dùng, không tự chọn dịch vụ trả phí khác.
- Tool/download adapter cập nhật có manifest/version, nguồn xác minh, kiểm tra tương thích và rollback; không tự chạy script từ URL người dùng nhập.
- User data/cache/log tách install directory; bản portable hoặc installer được quyết định P02; chạy cá nhân không bắt buộc quyền admin.
- Chrome tự lưu session/cookie trong kho của hồ sơ độc lập. App/project/log chỉ giữ tham chiếu profile/account, không sao chép cookie database hoặc tắt bảo vệ mã hóa để chia sẻ phiên.
- Tool resolver chọn bản theo chính sách rõ; job giữ đúng installation version/path và lease. Cập nhật app-managed qua staging/verify/self-test/activate, không thay file đang được job dùng hoặc đè tool ngoài.
- Profile manager dùng Google Chrome chính thức, user-data-dir riêng mặc định. Browser lock và auth state tách biệt; không ép mở/xóa lock của profile đang dùng.
- Session broker chọn đường handoff được kiểm chứng theo Chrome/OS/connector. Account mismatch chặn đúng job; refresh cùng danh tính có thể resume. Cache/private result được tách theo account scope.
- Hợp đồng và UI chi tiết: [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md).

## 11. Sổ quyết định trước khi khóa công nghệ

| ID | Quyết định | Hạn chốt | Evidence cần | Trạng thái |
| --- | --- | --- | --- | --- |
| D01 | Python/Qt và dependency versions | P02 | Tương thích Windows, media, packaging | Chưa kiểm chứng |
| D02 | Engine playback/composition | P02 | Seek, proxy, chữ/blur/keyframe, parity, đóng gói | Chưa kiểm chứng |
| D03 | FFmpeg build/filter/encoders | P02 | Font/sub/filter, encode CPU/GPU thật | Chưa kiểm chứng |
| D04 | Bộ dịch chính và dự phòng | P02 | Chất lượng Trung–Việt, quota/giá/cấu hình | Chưa kiểm chứng |
| D05 | Connector và mức hỗ trợ từng nguồn | P02→P05 | Bảng nguồn với ngày/phiên bản/evidence | Chưa kiểm chứng |
| D06 | Định dạng project/DB/time map | P01→P03 | Save/open/migration, cue sau speed/trim | Thiết kế đề xuất |
| D07 | Máy tham chiếu và ngân sách UI/parity | P02 | Benchmark có cấu hình, corpus và phép đo | Chưa có số đo |
| D08 | Packaging/paths/updates Windows | P02→P12 | Smoke đóng gói sớm, bản cuối trên máy thật | Chưa kiểm chứng |
| D09 | Tool discovery, installer và trusted manifests | P02→P03 | Thiếu tool, đường dẫn ngoài, verify, update bận, rollback | Chưa kiểm chứng |
| D10 | Chrome thật, profile isolation và session handoff | P02→P05 | Nhiều nền tảng/hồ sơ, mã hóa/lock, đúng nick, download dùng phiên | Chưa kiểm chứng |

## 12. Chiến lược kiểm chứng khi code

- Logic: time map, preset precedence, duration constraints, W/K/history/seed; tránh test chỉ lặp lại implementation.
- Pipeline: input thật → FFmpeg/translator/connector → artifact có validation. Test offline không thay phép thử live connector.
- GUI: drag/resize/keyframe/undo, focus tiếng Việt/Trung, snap/zoom, scope, crash recovery và proxy.
- Golden/reference samples: frame tại mốc, text layout, audio timing và media duration; dung sai/máy/corpus được khóa ở P02.
- Resilience: tệp hỏng, disk full, worker crash, mạng/auth/quota và request provider kết quả chưa rõ.
- Windows: packaged app không dev tools, Unicode, đường dẫn dài, CPU-only/GPU có thể dùng, HiDPI và driver.
- Dependency/browser: scan/version/capability, tải-cài lỗi/rollback/tool lease; Chrome thật nhiều hồ sơ, binding đúng nick, session hết hạn/khóa/handoff không được.

Không có test ứng dụng nào đã chạy trong giai đoạn chỉ chuẩn bị tài liệu. Khi triển khai, kết quả pass/fail/skip/blocked được lưu riêng với tool version và đầu vào.
