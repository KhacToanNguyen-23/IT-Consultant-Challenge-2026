# Các ca demo (đã chạy thật trên stack Compose, DK catalog, tồn kho mô phỏng)

Mọi đầu vào dưới đây nằm sẵn trong UI (nút mẫu ở màn nhập) hoặc trong `docs/demo/`. Số liệu "kết quả" lấy từ lần chạy ngày 2026-11-07; con số thời gian có thể thay đổi, chỉ đọc số đo từ lần quay thật.

Ghi chú: UI để tiếng English. Tồn kho, giá, khách hàng đều **simulated** (mock-pos).

## Bảng ca demo

| # | Ca (nút mẫu) | Chứng minh điều gì | Slide Round 1 | SRS / FR |
|---|---|---|---|---|
| 1 | **Full counter list** (18 dòng) | Từ danh sách thô đến đơn xác nhận: che email/điện thoại, quy đổi, làm tròn lên, 3 dòng thiếu hàng được cứu, Confirm | Slide 5, 6 (09:30 List intake, 11:00 Unit conversion) | FR-001/002, 011–016, 018–020 |
| 2 | **Out-of-stock rescue** | Hết hàng → thay thế an toàn kèm chênh lệch giá; SKU chỉ đổi sau khi khách đồng ý | Slide 6 (09:31 Stockout salvage) | FR-014–016 |
| 3 | **AI must not be wrong silently** | C18 vẫn là C18, thiếu cấp độ/đơn vị thì không đoán, ngoài catalog không gợi ý, Confirm bị khóa | Slide 5 ("Humans retain the final call"), slide 7 guardrails | FR-007–010, 013 |
| 4 | **One tool, three markets** | Văn bản kiểu NO, SV, EN cùng khớp về một SKU | Slide 2, 7, 10 (ba thị trường, một lõi) | FR-006, 011 (từ điển đơn vị DA/NO/SV/EN) |
| 5 | **Customer e-mail** (chọn "E-mail quote") | Luồng 2: lưu báo giá `BG-DK-xxxx`, snapshot giá/tồn, ghi nhận duyệt ngoài hệ thống, recheck, in | Slide 6 (07:00 Pre-pick) | FR-022–028 (UC5) |
| 6 | **Upload PDF** (`docs/demo/material-list.pdf`) | Nhận file PDF thật, vẫn che thông tin liên hệ | Slide 5 (Read: PDF/Excel/text) | FR-001 |
| 7 | **POS lỗi** (công tắc Demo → POS fail) | POS lỗi → CSV cùng mã tham chiếu, không mất đơn | Slide 7 ("Zero Downtime Fallback") | FR-019, 033 |
| 8 | **AI lỗi** (công tắc Demo → AI fail) | AI tắt vẫn xong đơn bằng quy tắc + tìm tay; C18 vẫn không thành C24 | Slide 7 | FR-003, 033 |

## Chi tiết từng ca: đầu vào, kết quả mong đợi, điểm chỉ trên màn hình

### 1. Full counter list
- **Vào:** nút "Full counter list" → Read list → Analyze.
- **Kết quả đã đo:** 18 dòng đọc được (dòng chào có SĐT/email bị che, không thành dòng hàng); phân tích khoảng 140–160 ms (có thể ~1,4 s khi LLM tham gia); 14/18 dòng không cần sửa; 5 lần quy đổi đơn vị; 3 dòng cần xử lý (rockwool 60 m² thiếu một phần, vådrum 12.5 hết hàng, 45x120 C24 hết hàng).
- **Chỉ vào:** `120 m → 25 × piece_4.8m`; `60 m² ÷ 2.88 = 20,83 → 21` (Rounded up); `15 stk 48x98 C24 4.8m` đúng 15 (lỗi cũ biến thành 1 đã được sửa); `45x120 C24` hết hàng → đề xuất **C30** (cấp cao hơn, chênh giá).
- **Thao tác:** bấm "Customer accepts" 3 lần → Confirm → `POS_ACCEPTED`, thời gian upload→Confirm ~4 s.
- **Lời thoại:** "Eighteen lines, read and checked in a fraction of a second. Three lines need a human decision, and each one comes with a safe, priced alternative."

### 2. Out-of-stock rescue
- **Kết quả:** gips vådrum hết hàng → `MR-125-B` (+40 DKK); xi măng 200 bao chỉ có 80 (Partial) và không có hàng thay thế an toàn.
- **Lưu ý:** dòng Partial không có thay thế **không chặn Confirm**. Nếu quay dòng này, hãy nói rõ trong lời thoại để người xem biết.
- **Lời thoại:** "Instead of 'sorry, out of stock', the associate offers an equal-spec alternative. The SKU changes only after the customer agrees."

### 3. AI must not be wrong silently
- **Kết quả:** `45x95 C18 - 30 stk` giữ C18; `45x95 timber` hiện cả C24 và C18, ghi "not guessed"; `skruer`, `blahblah` không SKU; `20 m isolering` ghi "Unit missing/unknown — not guessed"; Confirm bị khóa với số dòng còn lại.
- **Lời thoại:** "It never guesses silently. Confirm stays blocked until a human resolves every line."

### 4. One tool, three markets
- **Đầu vào:** `Konstruksjonsvirke 45x95 C24 - 90 meter` (NO), `5 säckar cement 25 kg` (SV), `tryckimpregnerade terrassebrädor 28x120 20 st` (SV), `pressure treated decking 28x145 - 12 pcs` (EN), `8 sekker betongblanding 25 kg` (NO).
- **Kết quả:** cả 5 dòng khớp SKU trong catalog DK; 2 dòng timber/cement ở băng cao, các dòng decking ở băng "quick check" (cần xem), 90 m → 19 thanh.
- **Lời thoại:** "The core is shared. Language and local wording are handled by the matcher, not by a different tool per country."

### 5. Customer e-mail (Luồng 2)
- **Vào:** chọn "E-mail quote" → nút "Customer e-mail" → Read list → Analyze → chấp nhận thay thế → **Save quote**.
- **Kết quả:** `BG-DK-xxxx` trạng thái Saved, snapshot giá/tồn tại thời điểm lưu, ghi chú "does not reserve items", các nút Record approval/sent, Re-check, Print quote, "Demo: simulate price/stock changes".
- **Lưu ý:** nếu email có câu văn xuôi hoặc tiêu đề, nó thành một dòng không đọc được và chặn Confirm. Bấm **Remove line (not an order line)** trong khung bên phải (bấm hai lần để xác nhận) để bỏ dòng đó; việc bỏ dòng được ghi lại (`LINE_REMOVED`) và không làm được sau Confirm hay khi đã lưu báo giá.

### 6. Upload PDF
- `docs/demo/material-list.pdf` (cùng nội dung ca 1, có dòng chào kèm SĐT/email). Cũng có `docs/demo/material-list.txt`.

### 7. POS lỗi / 8. AI lỗi
- Bật công tắc "Demo" ở góc trái dưới **trước khi phân tích** (AI) hoặc **trước khi Confirm** (POS). Nếu bật POS fail trước khi phân tích thì tồn kho hiện "Stock unknown" (hợp lý nhưng làm rối cảnh).
- Nhớ tắt công tắc sau mỗi ca.
- Kết quả: `NEEDS_MANUAL` + nút **Download CSV** nổi bật (mã `CSV-SD-…`); hoặc banner "AI is unavailable" + ô tìm SKU thủ công, vẫn tới `POS_ACCEPTED`.

## Reset trước khi quay
`docker compose down -v && docker compose up --build` (xóa dữ liệu demo, nạp lại mô hình ~1–2 phút). Đợi `/api/health` báo `embedding.status = up`, chạy một lần phân tích để làm nóng, rồi quay.

## Giới hạn đã biết (nên nói thật trong video)
- Dòng văn xuôi hoặc tiêu đề thành dòng không đọc được và chặn Confirm cho đến khi nhân viên bỏ dòng đó (đã có nút Remove line; không bỏ được dòng cuối cùng).
- Dòng Partial không có hàng thay thế không chặn Confirm.
- Cột "Current line" trong màn báo giá còn hiện giá trị nội bộ thô (`direct_pick`, `substituted`).
- Số đo thời gian trên màn hình chỉ có ý nghĩa cho một đơn trong môi trường mô phỏng.
