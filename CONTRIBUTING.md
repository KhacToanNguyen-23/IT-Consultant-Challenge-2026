# Quy ước làm việc chung

Nền chung: `main`, schema theo `docs/SiteDesk_MVP_SRS.md` mục 6.1. Mọi người kéo từ `main`, không làm tiếp trên nhánh cũ.

## Phân vùng

| Phạm vi | Người phụ trách | Ghi chú |
|---|---|---|
| Flow 1 (At-Counter): `services/parser.py`, `matcher.py`, `conversion.py`, `pii.py`, `retrieval.py`, `api/sessions.py`, UI Flow 1 | Khắc Toàn | P0 trong SRS |
| Flow 2 (Pre-order): `api/quotes.py`, quote/print/pick slip, `components/pos`, trang `quotes/` | AlecVOV | P1/THIN, cắt trước nếu trễ |
| Dùng chung: `db/models.py`, `services/pipeline.py`, `services/connector.py`, `mock-pos/`, `docker-compose.yml`, `.env.example` | Cả hai | Báo nhau trước khi sửa |

## Schema (điểm dễ xung đột nhất)

- `db/models.py` phải khớp DDL trong SRS 6.1. Không tạo bảng song song với bảng đã có (session, quote, idempotency, POS).
- Muốn thêm hoặc đổi cột: mở PR riêng chỉ chứa thay đổi schema, người còn lại duyệt trước khi merge.
- Hợp đồng giữa hai flow: đầu ra của pipeline (`order_sessions`, `session_lines`) là thứ Flow 2 đọc để lưu quote (SRS MVP-FR-022). Đổi nó phải báo người kia.
- Sau khi đổi schema: `docker compose down -v` rồi `up --build` (chưa dùng migration).

## Quy trình

1. `git fetch` rồi tạo nhánh từ `main`: `feat/<flow>-<việc>`.
2. Commit nhỏ. PR vào `main`, không commit thẳng.
3. Trước khi mở PR: `cd backend && DATABASE_URL=postgresql+psycopg2://u:p@localhost:5432/x python -m pytest -q` phải xanh.
4. Không commit `.env`, API key, `node_modules`, `.venv`.
5. Ưu tiên theo SRS: Flow 1 chạy từ upload tới bảng kết quả và Confirm trước, Flow 2 chỉ cần demo save/reopen/print.
