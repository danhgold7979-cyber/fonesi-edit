**HỒ SƠ BASELINE TRƯỚC REBUILD:** nội dung/bằng chứng dưới đây thuộc implementation trước đợt làm lại 30/10/2026, không chứng nhận code mới. Xem [trạng thái rebuild hiện hành](../REBUILD_STATUS.md). Baseline tích hợp được giữ tại commit `edbb47189b0e864c74623d0a4db5b5f169f2103c`.

# P01 — Kết quả

Trạng thái: hoàn tất cổng thiết kế. Không phải nghiệm thu ứng dụng.

| Task | Hiện vật và kết luận |
| --- | --- |
| P01-01 | 95 nhóm yêu cầu ở REQUIREMENTS_TRACEABILITY, phạm vi hiện tại/sau ở PRODUCT_REQUIREMENTS |
| P01-02 | P01_DESIGN mục 1–2: bảy khu vực, wireframe, state và inspector |
| P01-03 | P01_DESIGN mục 3: sáu đường dùng thường xuyên, preset giảm thao tác |
| P01-04 | P01_DESIGN mục 4–5: preset/overrides/locks/snapshot, scope luôn hiển thị |
| P01-05 | P01_DESIGN mục 4: W/K, duration, missing sub, output collision |
| P01-06 | SOURCE_CORPUS: synthetic/live, prerequisites và phương pháp đo |
| P01-07 | P01_DESIGN mục 5 + TECHNICAL_DESIGN: contracts, modules, decision register |
| P01-08 | SETTINGS_AND_BROWSER_SPEC + P01_DESIGN: scan/install/login/verify/readiness |

Kiểm tra: `python scripts/check_plan.py`; kết quả của lần đóng phase phải PASS trước commit. P01 chỉ chốt thiết kế; không đánh dấu tool/connector/Windows/GPU/dịch đã hoạt động.

Cổng tiếp theo: P02 có Linux CPU/FFmpeg hiện có; Windows/Google Chrome thật, GPU, tài khoản nguồn và provider dịch chưa được cung cấp trong máy. Tiếp tục thử nghiệm độc lập, không bỏ hoặc đóng giả các cổng này.
