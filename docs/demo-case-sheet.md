# Kịch bản demo theo đề Round 2: 3 điều MVP phải có + 4 tiêu chí chấm

Địa chỉ app: http://localhost:3001 (UI English, zoom 125%). Giữa các mục bấm **New list**. Bấm thẻ mẫu ở màn nhập thì ô nhập tự điền đúng văn bản ghi dưới đây.

## Bảng tổng: mục của đề → phần demo

| # | Đề yêu cầu | Phần demo | Giờ |
|---|---|---|---|
| **M1** | MVP phải *demonstrate the core functionality* | Danh sách 18 dòng → rà soát | 1:00 |
| **M2** | MVP phải *showcase its main user journeys* | Hành trình 1 tại quầy → Confirm; Hành trình 2 email → báo giá | 1:30 |
| **M3** | MVP phải *demonstrate the value* | Biên nhận: doanh số cứu, thời gian, dòng không cần sửa | 0:25 |
| **D** | Nếu MVP đổi so với Round 1, giải thích thay đổi và lý do | Bảng thay đổi | 0:35 |
| **T1** | Tiêu chí *Engineering quality* (reliable functionality) | POS lỗi → CSV; AI lỗi → tìm tay | 1:15 |
| **T2** | Tiêu chí *Reasonable architecture* | System Diagram + `/api/health` các thành phần | 0:30 |
| **T3** | Tiêu chí *Appropriate AI usage* (có người kiểm chứng) | Dòng mơ hồ: AI không đoán, người quyết định | 0:35 |
| **T4** | Tiêu chí *Clear technical reasoning* (khớp Round 1) | 3 KPI của Round 1 đo được trên MVP | 0:25 |

Tổng khoảng 6:15 cộng mở đầu, kết khoảng 6:45.

---

## M1 · Core functionality

**Nhập** (thẻ **Full counter list**, hoặc upload `docs/demo/material-list.pdf`):
```
Hej Lars, her er listen fra Mikkel (tlf +45 31 22 44 66, mikkel@nordbyg.dk)
120 m konstruktionstræ 45x95 C24
80 m 45x70 C24
10 stk lægte 45x45 C18 3,6 m
15 stk 48x98 C24 4.8m
60 m2 rockwool 95 mm
40 m2 rockwool 145 mm
24 plader gips standard 12.5 mm
10 plader vådrum gips 12.5 mm
10 sække cement 25 kg
5 poser fliseklæb 20 kg
8 poser fugemasse 5 kg
40 stk terrassebræt 28x120 trykimp.
8 stk terrassebræt 28x145 trykimp. 4.2m
2 stk komposit terrassebræt 25x125
20 stk 45x120 C24 4.8m
6 sække kalkmørtel 20 kg
12 m2 isolasjon 195 mm
8 sekker betongblanding 25 kg
```
**Bước**
1. **Upload file** → `material-list.pdf` → **Read list**.
2. Mở **Source**: SĐT/email đã bị che.
3. **Analyze** (F9). Dừng, chưa xử lý dòng đỏ.
4. Chỉ: `120 m → 25 × piece_4.8m`; `60 m² ÷ 2.88 → 21 × pack` + "Rounded up"; "Needs a look (6)" ở đầu bảng; `14/18 lines needed no edit`.

**Phải thấy:** đọc file, che thông tin, khớp SKU, quy đổi đơn vị, làm tròn lên, kiểm tồn.
**Nói:** "A PDF list, contact details masked first. Eighteen lines read, matched, converted and stock-checked in a fraction of a second."

## M2 · Main user journeys

**Hành trình 1: tại quầy** (tiếp tục phiên của M1)
1. Dòng rockwool mở sẵn (đỏ "Only 5 left, need 21 — alternative ready") → **Customer accepts**.
2. Dòng vådrum tự mở → **Customer accepts**.
3. Dòng `45x120 C24` tự mở (đề xuất **C30**) → **Customer accepts**.
4. Chỉ nút **Customer: Walk-in** → **Confirm order to POS** (F9).

**Phải thấy:** `POS_ACCEPTED` + mã tham chiếu. SKU chỉ đổi sau khi khách đồng ý.

**Hành trình 2: email → báo giá** (dùng hộp thư giả để cảnh này khác hẳn luồng tại quầy)

**Chuẩn bị:** mở 2 tab cạnh nhau.
- **Tab A (hộp thư giả):** `file:///D:/Project/Personal/IT-Consultant-Challenge-2026/docs/demo/mailbox.html`. Đạo cụ demo, ghi rõ "simulated", không gửi gì thật.
- **Tab B:** SiteDesk, chế độ **E-mail quote**.

**Các bước**
1. Tab A: mở email của Jens "Materialer til fredag" → bấm **Copy email text**.
2. Tab B: bấm **E-mail quote**, nhấp vào ô nhập, **Ctrl+V** → **Read list** → **Analyze**. **Không** bấm Record customer agreement (khách chưa trả lời).
3. Chỉ banner tím "E-mail request: save the quote first…", hai dòng đỏ thiếu hàng kèm đề xuất (rockwool, vådrum).
4. Bấm **Copy reply to customer** (trong banner tím). Thư soạn sẵn liệt kê hàng có sẵn, hàng thiếu kèm đề xuất thay và chênh giá.
5. Tab A: **Reply** → **Ctrl+V** → **Send**. Sau 1,5 giây khách trả lời "Det er fint. Vi tager alternativerne…".
6. Tab B: **Save quote** (F8) → **Record sent** (báo giá đã gửi) → **Record approval** (kênh E-mail, khách đã đồng ý) .
7. *(tùy chọn)* mở **Demo: simulate price/stock changes** → chọn SKU → **New stock** nhỏ → **Apply**.
8. **Re-check stock & price** → bấm **Resolve 2 short line(s)** → khách đến lấy hàng: **Customer accepts** từng dòng → **Confirm order to POS** → **Reset** trong khung Demo.

**Phải thấy:** một chuỗi thật: email khách → SiteDesk đọc, che, kiểm tồn → thư báo lại có đề xuất → khách trả lời → báo giá → kiểm lại khi nhận hàng → đơn. SiteDesk **không gửi email**: nhân viên gửi từ hộp thư của họ.
**Đừng đọc số thời gian của luồng này** (đồng hồ gồm cả khoảng chờ).
**Nói:** "Journey one: counter, end to end. Journey two: a customer e-mail arrives. SiteDesk reads it, finds two short lines and drafts a reply with alternatives. The associate sends it, the customer agrees, and the substitutes are only accepted when the customer arrives, after a live re-check."

## M3 · Value

**Không nhập.** Quay lại biên nhận của Hành trình 1. Chỉ lần lượt:
1. **Sales rescued by substitutes: 6.379,10 DKK** (3 dòng khách chấp nhận thay vì "hết hàng").
2. **Time from upload → Confirm: `[T] s`** và dòng "Round 1 target … a target, not benchmarked".
3. Thanh `14/18 lines needed no edit`.

**Nói:** "Three lines that would have been lost sales, [R] kroner at list price, were rescued. The order took [T] seconds against our twelve-minute estimate. Measured on this simulated MVP, not a real store."

## D · Thay đổi so với Round 1

**Không nhập.** Hiện bảng:

| Round 1 | MVP | Vì sao |
|---|---|---|
| Rerank bằng LLM | Quy tắc cứng + embedding cục bộ; LLM chỉ tùy chọn | Xác định, không đoán C18 thành C24; dữ liệu không rời máy mặc định |
| POS/ERP thật | mock-pos **simulated** | Không có hệ thống thật; vẫn kiểm được payload slide 9 |
| "Che PII" | Regex che email/điện thoại, nêu rõ giới hạn | Trung thực, không hứa quá mức |
| Mục tiêu 12 → <2 phút | Đo thật trên MVP | Round 1 chỉ là giả định |

## T1 · Engineering quality (reliable functionality)

**a) POS lỗi.** Nhập thẻ **Out-of-stock rescue**:
```
10 plader gips vådrum 12.5 mm
40 pakker isolering 95 mm
200 sække cement 25 kg
120 m timber 45x95 C24
```
**Bước:** Read list → Analyze → **Customer accepts** → mở **Demo**, bật **POS fail** → **Confirm order to POS** → **Download CSV** → tắt **POS fail**.
**Phải thấy:** "POS not responding — CSV exported, manual entry needed", mã `CSV-SD-…`, "Nothing is lost".

**b) AI lỗi.** Mở **Demo**, bật **AI fail** *trước khi phân tích*; gõ:
```
12 skivor gips 12.5 mm
5 poser cement 25 kg
```
**Bước:** Read list → Analyze → ô tìm đã điền `gips 12.5 mm`, sửa thành `gips standard 12.5` → **Search** → bấm **Gipsplade standard 12.5mm … SKU-GYP-STD-125** → **Confirm order to POS** → tắt **AI fail**.
**Phải thấy:** banner "AI is unavailable. Search the catalog manually"; các gợi ý mang nhãn **"Rule-based guess (AI off), verify"** và không có điểm khớp (đó là luật dự phòng, không phải AI); `POS_ACCEPTED`.
**Nói:** "When the POS is down the order is exported, not lost. When the AI is down, rules and manual search keep the counter running."

## T2 · Reasonable architecture

**Không nhập.**
1. Hiện **System Diagram** (Container): UI → Core API (AI gateway + connector) → PostgreSQL/pgvector; mock-pos; embedding cục bộ.
2. Mở tab mới: `http://localhost:8000/api/health`. Chỉ các thành phần: `database`, `embedding`, `llm`, `mock_pos`.
3. Bật **Demo → POS fail**, tải lại tab health: `mock_pos` đổi thành `fail_mode`; tắt lại.

**Nói:** "A UI, a core API with an AI gateway and a connector, a vector database, a local embedding model and a simulated POS. Each component is separate and observable, and failing one does not stop the others."

## T3 · Appropriate AI usage (có người kiểm chứng)

**Nhập** (thẻ **AI must not be wrong silently**):
```
45x95 C18 - 30 stk
45x95 timber
10 stk skruer 5x50
20 m isolering 95 mm
blahblah ukendt ting
5 poser cement 25 kg
```
**Bước:** Read list → Analyze. Dòng `45x95 timber` đã mở với hai thẻ C24/C18; **không bấm Choose**.
**Phải thấy (chữ đỏ):** "Not stated: strength grade — not guessed"; `skruer`, `blahblah`: "Not in catalog — no suggestion"; `20 m isolering`: "Unit missing/unknown — not guessed"; Confirm mờ, "4 line(s) to resolve"; `45x95 C18` vẫn là C18.
**Nói:** "The AI suggests, hard rules gate, and a human decides. It never guesses a missing grade, and Confirm stays blocked until a person resolves every line."

## T4 · Clear technical reasoning (khớp Round 1)

**Quan trọng:** số KPI hiện tại **lẫn các phiên chạy thử tự động**. Trước khi quay: `docker compose down -v && docker compose up --build`, rồi chỉ chạy các case thật của video, **sau đó** mới chạy lệnh dưới.

**Bước:** mở terminal, chạy `docker compose exec backend python -m scripts.kpi`. Chỉ 3 dòng: `time_to_serve`, `substitution_acceptance`, `zero_touch`.
**Nói:** "Round 1 set three go/no-go gates: time to serve, substitution acceptance and zero-touch matching. The MVP measures all three. These figures come only from this demo's sessions on simulated data, so they show the instrumentation works, not store performance."

---

**Thứ tự quay khuyến nghị:** M1 → M2 (hành trình 1) → M3 → T3 → M2 (hành trình 2) → T1a → T1b → T2 → T4 → D. Các case bật công tắc đặt cuối để khỏi quên tắt. Chia nhịp từng giây xem `docs/demo-shotlist.md`.
