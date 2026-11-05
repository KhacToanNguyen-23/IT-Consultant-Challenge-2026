# Flow 1: đối chiếu code `main` với SRS

Kiểm tra nhanh bằng đọc route/grep ngày 2026-11-05, chưa chạy end-to-end trên Docker. "Có" nghĩa là có code, chưa chứng minh đúng. Cần xác minh bằng test hoặc chạy thật.

| Yêu cầu | Trạng thái | Ghi chú |
|---|---|---|
| FR-001/002 nhận file, mask PII | Có | `POST /sessions/{id}/ingest`; PII đã vá (b61f76d). Cần test file scan-only trả 422 |
| FR-003 AI lỗi vẫn chạy bằng rules | Có | `/admin/fail-modes`; cần chạy thật |
| FR-004 sửa dòng | Có | `PATCH .../lines/{no}` |
| FR-005 unreadable, `N x L` | Có | `ParsedRow.length_m`, status UNREADABLE |
| FR-006..009 match, band, must-match | Có | `matcher.py` theo SRS; cần kiểm tra biên 0.90 |
| FR-010 Confirm bị chặn khi còn NEEDS_CLARIFICATION | Cần xác minh | `POST /sessions/{id}/confirm` |
| FR-011..013 đơn vị, conversion, block | Có | `conversion.py`; cần chạy 120/4.8=25 và 60/2.88→21 |
| FR-014..016 tồn kho, thay thế, khách chấp thuận | Có | `/alternatives`, `.../selection` ghi `customer_accepted_substitution_at` |
| FR-017 client / WALKIN | Có | `PUT .../client`, `GET /customers` |
| FR-018..020, 037 idempotency, connector, CSV | Có | `connector.py` dùng `connector_attempts`; `GET .../export.csv` |
| FR-021 store dictionary | **Thiếu** | Chỉ có model, chưa có code ghi/gỡ mapping sau Confirm |
| FR-029 decision events | Một phần | `telemetry.py` có; cần kiểm tra các sự kiện chính được ghi |
| FR-030 thời gian từng bước | Có | `stage_timings`, `ai_invocations`; cần log p95 cho NFR-003 |
| FR-031 SQL cho 3 KPI | **Thiếu** | Không thấy truy vấn KPI |
| FR-032 mock login | **Thiếu** | Có `demo_users` trong schema, chưa có endpoint đăng nhập |
| FR-033 hai fail toggle | Có | `/admin/fail-modes` |
| FR-035 seed 60–80 SKU | Có | `mock-pos/seeds/catalog.json` 62 mục. `services/seed.py` còn ghi TODO, cần xem lại |
| NFR-005 đánh giá 80–100 nhãn | Một phần | `seeds/evaluation.jsonl`, `scripts/evaluate.py`; chưa chắc đủ 80–100 dòng có người duyệt |
| UI Flow 1 | Do Toàn làm lại | Hiện dùng UI POS của AlecVOV |

Test hiện có: 51 (unit, không cần DB). Chưa có test cho API `sessions` trên DB thật.

## Đề xuất thứ tự cho Toàn

1. Chạy Docker, thử luồng upload → analyze → review → confirm → CSV, ghi lại chỗ lỗi.
2. Test hợp đồng: 120/4.8=25, 60/2.88→21, biên band 0.90, confirm bị chặn, replay idempotency, POS 503 → CSV.
3. FR-021 store dictionary, FR-031 KPI SQL.
4. UI Flow 1, rồi FR-032 login nếu còn thời gian.
