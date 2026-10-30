# Hợp đồng foundation rebuild — P03-01/02/03/05

Được phép triển khai logic độc lập; chưa nghiệm thu P02 Windows/Qt/Chrome/GPU.

## Time map

Thời gian lưu bằng phân số nguyên (numerator/denominator), không float. Clip có source interval nửa mở [in,out), speed > 0, output_start >= 0. Cue giao với source interval trước khi map; cue ngoài clip trả None, cue bị cắt vẫn giữ nguyên text/id. Không âm thầm thay speed/interval lỗi. JSON từ bên ngoài chỉ cho numerator/denominator integer (không bool), denominator > 0.

## Project

Schema version 1, UUID project/media/cue, mỗi media có đường dẫn tham chiếu (không có bytes), URI mạng không được coi là file local. Snapshot canonical JSON UTF-8, sort keys, no NaN, version riêng và hash SHA256. Không chấp nhận arbitrary configuration blob vào project: field allowlist, reject unknown fields. Secret refs là phần cấu hình runtime riêng, chưa lưu credential trong model. Thay đổi preset không được đổi chuỗi snapshot đã xếp hàng.

## Jobs và lưu trữ

SQLite user data tách source; schema version 1. pending -> running -> validating -> succeeded/succeeded_with_warnings. running -> failed/canceled/blocked_configuration; validating -> failed/canceled; pending -> canceled/blocked_configuration. Retry tạo attempt mới trên cùng snapshot, chỉ failed/blocked_configuration/canceled về pending theo lệnh rõ. succeeded không retry ngầm. Claim dưới BEGIN IMMEDIATE, so state và generation, lease token unique; mọi mutation worker cần token đúng, stale token bị từ chối. Crash expired lease thành interrupted (chờ reconcile), không tự chạy lại side effect.

Snapshot/hash/correlation ID ghi trước khi worker chạy. Output success phải có validated artifact trong transaction; artifact validation không chỉ là tồn tại file. SQL tham số hóa. Backup SQLite online vào tệp mới, integrity_check trước khi dùng; schema mới hơn runtime phải từ chối mở ghi. Không gán PASS power-loss/disk-full nếu chưa có fault injection.

## Test đầu tiên

- Rational boundaries, trim/speed map, invalid and bool fields, cue partial overlap.
- Serialization roundtrip/version/unknown fields and deterministic digest.
- Snapshot immutability, duplicate job idempotence, conflicting payload rejection.
- Concurrent claim exactly one, stale lease/no blind recovery, success without validation rejected.
- Không mạng, không ADB, không cookie hoặc account thật trong test.
