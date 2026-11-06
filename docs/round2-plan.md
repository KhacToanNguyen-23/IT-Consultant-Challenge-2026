# Kế hoạch Round 2: bám đề, tối đa điểm

Lập ngày 2026-11-06. Nguồn: `IT Consultant Challenge 2026 - Round 2.pdf` (16 trang, đã đọc trực tiếp), `docs/SiteDesk_MVP_SRS.md`, và kiểm tra chạy thật hôm nay (xem `docs/flow1-audit-and-plan.md`).
Mốc: **khóa code 08/11 · nộp 09/11 trước 22:00 GMT+7 · nộp muộn không được nhận.**

## 1. Đề Round 2 thật sự yêu cầu gì

**4 sản phẩm phải nộp** (checklist trang 12 của đề):
1. **MVP Demo Video**: MP4, tối đa 7 phút, có lời hoặc chữ giải thích, nên có tiếng Anh. Nếu MVP khác Round 1 thì phải giải thích thay đổi và lý do.
2. **User Journey**: PDF tối đa 2 trang, ít nhất một hành trình end-to-end thể hiện giá trị cốt lõi.
3. **System context diagram**: PDF tối đa 2 trang, gắn nhãn mọi thực thể bên ngoài và mọi tương tác, chỉ vẽ tương tác thật có trong MVP.
4. **AI Journal**: điền mẫu rồi **lưu PDF** (trong repo mới có `.docx`).

Quy định chung: file tên ngắn, đúng nội dung; ban giám khảo mở được; **không mật khẩu, API key, thông tin bí mật**.

**4 tiêu chí chấm** (trang 15):

| Tiêu chí | Đề viết | Ý nghĩa cho dự án |
|---|---|---|
| Engineering quality | Well-implemented, reliable functionality | Chạy ổn, không vấp khi demo, test và log sạch |
| Reasonable architecture | Logical organisation of system components | Tách lớp rõ, diagram khớp code |
| Appropriate AI usage | Effective AI use with human validation | AI có kiểm soát: luật cứng, người duyệt nhãn, ghi nhận lần bác bỏ |
| Clear technical reasoning | Aligned with the Round 1 problem | Mỗi quyết định kỹ thuật gắn với bài toán Round 1 |

## 2. Trọng tâm: "AI sập thì quầy vẫn chạy" (reliable functionality)

**Đã kiểm chứng hôm nay (API, Docker thật):**

| Tình huống | Kết quả |
|---|---|
| AI lỗi → chọn SKU thủ công → Confirm | Đạt. `ai_degraded=true`, ra dòng bằng chế độ `rules`, Confirm trả `POS_ACCEPTED` |
| POS lỗi → Confirm | Đạt. `NEEDS_MANUAL` + mã `CSV-...` + tải CSV |
| AI và POS cùng lỗi | Đạt. Vẫn Confirm được, ra CSV |
| Tìm SKU thủ công khi AI lỗi | Đạt. `/catalog/search` vẫn trả kết quả |
| Luật cứng khi AI lỗi (C18 không thành C24) | Đạt. Cùng bộ luật ở cả hai chế độ |
| Gửi confirm hai lần / sửa sau confirm | Đạt. Cùng mã tham chiếu, khóa 409 |

**Chưa có bằng chứng, cần làm (đây là phần "đánh mạnh"):**

| # | Tình huống lỗi | Việc cần làm | Cách chứng minh |
|---|---|---|---|
| R1 | Phân tích đúng lúc model chưa nạp xong (~32 s sau khởi động) | Test: khởi động backend, gọi analyze ngay | Test tự động: trả 200, `mode=rules`, không 500 |
| R2 | Embedding ném lỗi giữa chừng | Test giả lập lỗi (monkeypatch) | Rơi về `rules_after_error`, dòng vẫn ra |
| R3 | LLM hết giờ / trả JSON hỏng | Đã có unit test; thêm một test tích hợp với LLM giả | Dòng vẫn ra bằng quy tắc, không gọi lại vô hạn |
| R4 | POS chậm hoặc trả 503 giữa chừng | Mặc định đợi 2 giây rồi thử lại một lần; kiểm tra thêm POS chậm hơn timeout | CSV, đơn không bị tạo hai lần |
| R5 | DB không sẵn sàng khi Confirm | Trả lỗi có cấu trúc, không 500 trần | Test lỗi chuẩn `{error:{code,message}}` |
| R6 | PDF hỏng/lạ | Hiện 500 → sửa thành 422 | Test upload |
| R7 | UI khi AI lỗi | Banner rõ, ô tìm SKU thủ công luôn dùng được, nút tải CSV nổi bật, không mất dữ liệu khi tải lại | Quay thử đúng cảnh video 3:30–4:10 |
| R8 | Bật tắt toggle giữa phiên | Ghi lại trạng thái đúng ở phiên đang mở | Test E2E |

## 3. Việc cần làm theo từng tiêu chí

### Engineering quality (reliable functionality)
- A. PDF hỏng gây 500 → 422 (R6).
- B. Bổ sung đơn vị theo SRS 15.2: `förp`, `løpemeter`, `lpm`, `linear metre`, `sheet`, `palle`, `pall`, `pallet`. Hỏi AlecVOV về `sheet` và `board` (dùng chung `parser`).
- E. Hàng ngoài catalog (`skruer`, `blahblah`) không được nhận gợi ý REVIEW: thêm sàn điểm/điều kiện từ vựng, đưa về band NONE. Bổ sung dòng trap vào bộ đánh giá **mà không chỉnh ngưỡng sau khi xem kết quả**.
- F. `Moisture board 12.5mm` khớp sai sang bảng chống cháy (lỗi E046 đã ghi trong báo cáo).
- C. Quy tắc `m` theo SRS (không đủ ngữ cảnh thì không đoán, gắn cờ review). Cần cân nhắc vì có thể làm nhiều dòng demo bị vàng.
- Bộ test theo SRS 11.2: contract (payload slide 9, Core↔mock-pos), E2E (bộ kịch bản hôm nay), fault (R1–R5), security (upload, secret scan). Hiện chỉ có 51 unit test.
- `pytest` chạy được một lệnh, không phải gõ `DATABASE_URL` thủ công (thêm `conftest.py` đặt mặc định).
- `npm run lint` hiện **không chạy được** (chưa có cấu hình ESLint) trong khi SRS 12.3 liệt kê lệnh này. Thêm cấu hình ESLint tối thiểu cho Next.js.
- API bỏ qua trường lạ mà không báo (gửi `quantity` thay `requested_qty` vẫn trả 200 và không đổi gì). Chặn trường thừa trong các body của `sessions`.
- README sai: ghi cổng 3000 (thực tế 3001), ghi 35 test (nay 51), còn nhắc tên nhánh cũ. Sửa cho đúng bản `main`.
- Truy vấn KPI (SRS mục 10) lưu thành `backend/sql/kpi.sql` và test không chia cho 0.
- Chạy sạch từ đầu: `docker compose down -v && up --build` rồi smoke 15 phút, log không có lỗi.

### Reasonable architecture
- Diagram **chỉ vẽ cái có thật** và khớp code. Thực thể trong hệ thống: Web UI (Next.js), Core API (parser/matcher/conversion/alternatives), AI Gateway, embedding cục bộ, PostgreSQL + pgvector, Connector. Thực thể ngoài, **ghi "simulated"**: mock-pos, đăng nhập giả, nhà cung cấp LLM (tùy chọn, hiện tắt), nhân viên quầy, khách.
- Lập bảng đối chiếu: mỗi hộp và mũi tên → file hoặc endpoint trong code (SRS 16 yêu cầu). Đối chiếu trước 07/11.
- Quyết định cần chốt: SRS ghi dùng Alembic nhưng code dùng `create_all`. Đề xuất **không thêm Alembic** (rủi ro cho DB dùng chung với Flow 2, ít giá trị với giám khảo), ghi rõ trong "Known limitations".

### Appropriate AI usage (human validation)
- **D22:** đang `human-reviewed 0/98`. Người (không phải AI) duyệt từng dòng, rồi chạy lại báo cáo. Ghi "kết quả ban đầu trên N dòng", **không tuyên bố NFR-005 đạt** vì dưới 150 dòng.
- Giữ thông điệp "AI không sai im lặng": C18 không bao giờ thành C24, thiếu thuộc tính thì không vào band cao, hàng ngoài catalog thì không gợi ý.
- AI Journal: ghi các lần **bác bỏ hoặc sửa** output AI, có chứng cứ thật. Ví dụ có thể dùng (cần bạn xác nhận đúng sự thật trước khi ghi): bản vá PII sau khi test bắt được số điện thoại có ngoặc bị lộ và ngày bị che nhầm; quyết định không đưa matcher của nhánh cũ vào vì chọn C24 cho yêu cầu C18; nhãn D22 do AI soạn và phải người duyệt. Lưu PDF.

### Clear technical reasoning (khớp Round 1)
- Mỗi quyết định gắn với bài toán Round 1: ba KPI (Time-to-Serve, Substitution Acceptance, Zero-touch), payload slide 9, hai fail mode, "simulated" ghi rõ.
- Video phải **mở bằng phần thay đổi so với Round 1** và kết bằng giới hạn và bước tiếp theo.

## 4. Kịch bản video (≤7 phút) với đầu vào đã chạy được hôm nay

| Giờ | Cảnh | Đầu vào đã kiểm chứng |
|---|---|---|
| 0:00–0:35 | Bài toán, kiến trúc, nhãn "simulated", thay đổi so với Round 1 | Diagram |
| 0:35–2:45 | At-Counter: bản xem trước đã che PII, vàng/đỏ/thiếu hàng/làm tròn, chip, thay thế | `120 m timber 45x95 C24` (25 tấm); `45x95 C18` (không thành C24); `10 plader gips vådrum 12.5 mm` (hết hàng → `MR-125-B` → khách đồng ý); `200 sække cement` (thiếu một phần) |
| 2:45–3:30 | Confirm → mock POS; POS lỗi → CSV | Bật toggle POS |
| 3:30–4:10 | **AI lỗi → tìm tay → Confirm** | Bật toggle AI; chọn SKU thủ công; `POS_ACCEPTED` |
| 4:10–5:35 | Luồng 2 (AlecVOV): dán, lưu, in, đổi giá/tồn, mở lại thấy khác biệt | Của AlecVOV |
| 5:35–6:15 | Thay đổi: luật cứng, cách xử lý PII, pgvector + embedding cục bộ | |
| 6:15–6:50 | Telemetry, báo cáo D22 trung thực, giới hạn | p50 phân tích ≈ 209 ms trên 20 dòng, đo thật |
| 6:50–7:00 | Tổng kết giá trị | |

## 5. Lịch và phân việc

| Ngày | Toàn (Flow 1 backend + tests) | Codex (UI Flow 1) | AlecVOV (Flow 2) | BA/HTTT |
|---|---|---|---|---|
| **06/11 hôm nay** | A, B, E, F; ESLint; `conftest`; chặn trường lạ; test R1, R2, R6; sửa README | PR 2 (màn rà soát) | Đồng bộ `main`, hỏi về `sheet`/`board` | Duyệt nhãn D22; điền AI Journal; bắt đầu diagram |
| **07/11** | C; test R3–R5, R8; test contract + E2E; báo cáo D22 | PR 3 (thay thế, khách) + banner AI lỗi/ô tìm tay | Hoàn thiện Luồng 2 mỏng | Đối chiếu diagram với build; chốt User Journey |
| **08/11 khóa code** | Chỉ sửa lỗi; smoke 15 phút trên Compose mới; tag `demo-ok-N` | Chỉ sửa lỗi | Chỉ sửa lỗi | **Quay video**, AI Journal ra PDF |
| **09/11** | Dự phòng | | | Kiểm tra checklist 4 file, **gửi email trước 22:00** (nên gửi sớm vài tiếng) |

## 6. Điều cắt nếu trễ (theo SRS dòng 42–47)
Luồng 2 trước (chỉ mô tả bằng slide), rồi đăng nhập giả, telemetry chi tiết, store dictionary. **Không cắt:** Luồng 1, hai fail mode, bộ test khớp SKU.

## 7. Điểm cần bạn quyết
1. `sheet` (SRS) hay `board` (code): đổi code theo SRS hay giữ và ghi chú.
2. Quy tắc `m` (mục C): theo SRS (an toàn nhưng thêm dòng vàng) hay giữ như hiện tại.
3. Alembic: bỏ (đề xuất) hay làm.
4. Bắt đầu ngay A, B, E, F trên nhánh `fix/flow1-backend` tách khỏi nhánh UI của Codex.
