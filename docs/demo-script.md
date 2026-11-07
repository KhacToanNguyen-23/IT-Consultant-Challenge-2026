# Kịch bản video demo theo case: mỗi case đáp ứng một yêu cầu của Round 2

Mục tiêu 6:45, trần của đề là 7:00. Lời thoại bằng tiếng Anh (đọc hoặc phụ đề). Mọi số trong `[ ]` điền từ **lần quay thật**.

## 1. Yêu cầu của đề Round 2 và case đáp ứng

Đề yêu cầu MVP phải: **(A)** demonstrate the core functionality · **(B)** showcase its main user journeys · **(C)** demonstrate the value it brings to users or the business · **(D)** nếu MVP đã đổi so với Round 1, giải thích thay đổi và lý do. Bốn tiêu chí chấm: **Engineering quality** (reliable functionality), **Reasonable architecture**, **Appropriate AI usage** (human validation), **Clear technical reasoning** (khớp bài toán Round 1).

| Case | Tên | Yêu cầu / tiêu chí đáp ứng | Bằng chứng giám khảo thấy | Giờ |
|---|---|---|---|---|
| 0 | Bài toán Round 1 | Technical reasoning | Nỗi đau và mục tiêu Round 1 | 0:00–0:20 |
| 1 | Danh sách thô → đơn đã rà soát | **A. Core functionality** | Che SĐT/email, ngoại lệ lên trước, quy đổi, làm tròn | 0:20–1:20 |
| 2 | Hành trình tại quầy, đầu đến cuối | **B. Main user journey #1** | Cứu hàng thiếu → khách đồng ý → Confirm → `POS_ACCEPTED` | 1:20–2:10 |
| 3 | Giá trị đo được | **C. Value** | Doanh số cứu được `[R] DKK`, `[T] s`, `14/18` không cần sửa | 2:10–2:35 |
| 4 | AI không sai im lặng | **Appropriate AI usage** | Không đoán, chữ đỏ nêu lý do, Confirm bị khóa | 2:35–3:15 |
| 5 | Hành trình email → báo giá | **B. Main user journey #2** | `BG-DK-xxxx`, snapshot, re-check | 3:15–3:50 |
| 6 | Một công cụ, ba thị trường | Technical reasoning (Round 1: Scale) | Cách viết NO/SV/EN cùng khớp catalog | 3:50–4:05 |
| 7 | POS lỗi → CSV | **Engineering quality (reliable)** | "Nothing is lost", Download CSV | 4:05–4:45 |
| 8 | AI lỗi → tìm tay → Confirm | **Engineering quality (reliable)** | Banner, tìm thủ công, vẫn tới POS | 4:45–5:30 |
| 9 | Kiến trúc và thay đổi so với Round 1 | **D. Changes** + **Reasonable architecture** | System Diagram + bảng thay đổi | 5:30–6:20 |
| 10 | Bằng chứng và giới hạn | Technical reasoning | Số đo thật, giới hạn trung thực | 6:20–6:45 |

**Cách đánh dấu case trên video:** đầu mỗi case chèn thẻ chữ 2 giây dạng `CASE 4 · Appropriate AI usage` (có thể đặt trên nền tối, chữ trắng). Giám khảo thấy ngay mình đang chấm yêu cầu nào.

Nếu trễ giờ: cắt Case 5 trước, rồi rút Case 6. **Không cắt** Case 1, 2, 3, 4, 7, 8, 9.

## 2. Chuẩn bị trước khi quay

- [ ] `docker compose down -v && docker compose up --build`, đợi `/api/health` báo `embedding.status = up`, chạy một lần phân tích để làm nóng.
- [ ] Trình duyệt 1920×1080, zoom 125%, UI **English**, ẩn bookmark và tab thừa, tắt thông báo.
- [ ] Công tắc **Demo** (góc trái dưới) tắt cả AI fail và POS fail; góc phải ghi **System ready**.
- [ ] Có sẵn `docs/demo/material-list.pdf`. Các thẻ mẫu hiện ở màn nhập.
- [ ] Quay thử trọn một lượt rồi mới quay thật. Giữa các case bấm **New list**.
- [ ] Không lộ `.env`, API key, đường dẫn cá nhân.

---

## 3. Chi tiết từng case

### Case 0 — Bài toán Round 1 (0:00–0:20)
- **Màn hình:** thẻ chữ "20–35 lines re-keyed by hand · ~12 min per list (Round 1 estimate)", rồi vào màn hình chính, đồng hồ 00:00.
- **Nói:** "At a building-materials counter, a contractor hands over a long list. Today the associate re-keys every line, about twelve minutes by our Round 1 estimate. This is the working MVP."
- **Slide R1:** 2, 3.

### Case 1 — Danh sách thô → đơn đã rà soát · A. Core functionality (0:20–1:20)
- **Thẻ:** `CASE 1 · Core functionality`
- **Thao tác:** **Upload file** → `material-list.pdf` → **Read list** → mở **Source** → **Analyze** (F9).
- **Giám khảo phải thấy:**
  1. Source: số điện thoại và email đã bị che; "Read N lines".
  2. 3 thẻ bằng chứng: masked · semantic match · stock checked (simulated POS).
  3. `[X] ms analysed in`, `14/18 lines needed no edit`.
  4. "Needs a look (6)" lên đầu; `120 m → 25 × piece_4.8m`; `60 m² ÷ 2.88 = 20,83 → 21` + **Rounded up**; `15 stk 48x98 C24 4.8m` đúng 15.
- **Nói:** "The list arrives as a PDF. Contact details are masked first. Eighteen lines are read and checked in [X] milliseconds, exceptions first. One hundred twenty metres becomes twenty-five lengths; sixty square metres becomes twenty-one packs, rounded up to sellable units."
- **Slide R1:** 5 (Read, Match), 6 (List intake, Unit conversion). **SRS:** FR-001–013.

### Case 2 — Hành trình tại quầy, đầu đến cuối · B. Main user journey #1 (1:20–2:10)
- **Thẻ:** `CASE 2 · Main user journey: at the counter` (tiếp tục cùng phiên của Case 1)
- **Thao tác:** dòng 5 đã mở sẵn → chỉ chữ đỏ **"Only 5 left, need 21 — alternative ready"** → **Customer accepts**. Hệ thống tự mở dòng kế: dòng vådrum 12.5 mm → **Customer accepts**; dòng `45x120 C24` (hết hàng) → thẻ đề xuất **C30** (cấp cao hơn, có chênh giá) → **Customer accepts**. Chỉ nút "Customer: Walk-in" → **Confirm order to POS** (F9). Dừng ở biên nhận 4 giây.
- **Giám khảo phải thấy:** từng dòng đỏ có hàng thay thế và giá chênh; SKU chỉ đổi sau khi khách đồng ý; biên nhận `POS_ACCEPTED` kèm mã tham chiếu.
- **Nói:** "Instead of 'sorry, out of stock', every problem line comes with a safe, priced alternative, and the SKU changes only after the customer agrees. One click confirms the order to the simulated POS."
- **Slide R1:** 6 (Stockout salvage, 1-click push). **SRS:** FR-014–016, 018–020.
- **Lưu ý:** không bấm **Customer declines…** (sẽ mở ô nhập lý do).

### Case 3 — Giá trị đo được · C. Value (2:10–2:35)
- **Thẻ:** `CASE 3 · Business value`
- **Màn hình:** giữ nguyên biên nhận của Case 2; đưa con trỏ chỉ lần lượt: **"Sales rescued by substitutes: [R] DKK"** (3 dòng khách chấp nhận thay vì "hết hàng"), **"Time from upload → Confirm: [T] s"** và dòng "Round 1 target … a target, not benchmarked", thanh số đo **"14/18 lines needed no edit"**.
- **Nói:** "The value is visible on the receipt. Three lines that would have been lost sales, [R] Danish kroner at list price, were rescued by substitutes. The whole order took [T] seconds, against our twelve-minute estimate. Fourteen of eighteen lines needed no touch. These are measurements from this simulated MVP, not claims about a real store."
- **Slide R1:** 8–9 (Go/No-go KPIs: time-to-serve, substitution acceptance, zero-touch). **Tiêu chí:** Technical reasoning (KPI Round 1 đo được trên MVP).

### Case 4 — AI không sai im lặng · Appropriate AI usage (2:35–3:15)
- **Thẻ:** `CASE 4 · AI with human validation`
- **Thao tác:** **New list** → thẻ **"AI must not be wrong silently"** → Read → Analyze. Dòng 2 (`45x95 timber`) mở sẵn với hai thẻ C24/C18. **Không bấm Choose.**
- **Giám khảo phải thấy, theo thứ tự:** "Not stated: strength grade — not guessed" (đỏ); `skruer`, `blahblah`: "Not in catalog — no suggestion"; `20 m isolering`: "Unit missing/unknown — not guessed"; **Confirm** mờ với "4 line(s) to resolve"; dòng `45x95 C18` ở dưới **vẫn là C18**.
- **Nói:** "The AI is never allowed to be wrong silently. A missing grade is not guessed, unknown items get no suggestion, C18 stays C18, and Confirm stays blocked until a human decides."
- **Slide R1:** 5 (Humans retain the final call), 7 (guardrails). **SRS:** FR-007–010, 013.

### Case 5 — Hành trình email → báo giá · B. Main user journey #2 (3:15–3:50)
- **Thẻ:** `CASE 5 · Main user journey: e-mail pre-order`
- **Thao tác:** **New list** → **E-mail quote** → thẻ **Customer e-mail** → Read → Analyze → **Customer accepts** các dòng thay thế → **Save quote** (F8). Trang `BG-DK-xxxx`: chỉ vào "this quote does not reserve items", snapshot giá. **(chưa chạy thử đến cuối)** bấm **Print quote**, **Record approval**, **Demo: simulate price/stock changes**, **Re-check**.
- **Nói:** "The same engine serves a second journey. An e-mail request becomes a saved quote with a price and stock snapshot. On arrival the associate re-checks live data and sees what changed."
- **Nếu bước cuối lỗi:** dừng ở Save quote và nói một câu về re-check; hoặc thay bằng slide "Phase 2".
- **Slide R1:** 6 (07:00 Pre-pick). **SRS:** FR-022–028.

### Case 6 — Một công cụ, ba thị trường (3:50–4:05)
- **Thẻ:** `CASE 6 · One core, three markets`
- **Thao tác:** **New list** → **"One tool, three markets"** → Read → Analyze.
- **Giám khảo phải thấy:** dòng kiểu NO (`Konstruksjonsvirke … meter`), SV (`säckar`, `terrassebrädor … st`), EN (`pressure treated decking … pcs`) cùng khớp catalog.
- **Nói:** "Norwegian, Swedish and English wording resolve to the same catalog. The core is shared; local differences live in the connector and dictionary."
- **Slide R1:** 2, 7, 10.

### Case 7 — POS lỗi → CSV · Engineering quality (4:05–4:45)
- **Thẻ:** `CASE 7 · Reliable functionality: POS down`
- **Thao tác:** **New list** → **"Out-of-stock rescue"** → Read → Analyze → **Customer accepts** dòng 1 → **Demo → POS fail** (bật *sau* Analyze) → **Confirm** → chỉ "POS not responding — CSV exported, manual entry needed", nút vàng **Download CSV**, mã `CSV-SD-…`, "Nothing is lost" → bấm Download CSV → **tắt POS fail**.
- **Nói:** "If the POS is down, the order is not lost. SiteDesk exports a CSV with the same reference, and the status says clearly the POS did not accept it."
- **Slide R1:** 7 (Zero Downtime Fallback). **SRS:** FR-019, 033.

### Case 8 — AI lỗi → tìm tay → Confirm · Engineering quality (4:45–5:30)
- **Thẻ:** `CASE 8 · Reliable functionality: AI down`
- **Thao tác:** **New list** → **Demo → AI fail** (bật *trước* Analyze) → gõ hai dòng `12 skivor gips 12.5 mm` và `5 poser cement 25 kg` → Read → Analyze. Chỉ banner **"AI is unavailable. Search the catalog manually to continue."** và thẻ "Rules · manual SKU search". Ô tìm đã điền `gips 12.5 mm`; sửa thành `gips standard 12.5` → Search → bấm **Gipsplade standard 12.5mm … SKU-GYP-STD-125** → **Confirm** → `POS_ACCEPTED` → **tắt AI fail**.
- **Nói:** "With the AI switched off, hard rules and manual search keep the counter running, and the same safety rules apply. The order still reaches the POS."
- **Slide R1:** 7. **SRS:** FR-003, 033.

### Case 9 — Kiến trúc và thay đổi so với Round 1 · D. Changes + Reasonable architecture (5:30–6:20)
- **Thẻ:** `CASE 9 · Architecture and what changed since Round 1`
- **Màn hình:** System Diagram trang Container 15 giây (UI → Core API (AI gateway + connector) → PostgreSQL/pgvector; mock-pos simulated; embedding cục bộ; LLM tùy chọn), rồi bảng:

| Round 1 | MVP | Vì sao |
|---|---|---|
| Rerank bằng LLM | **Quy tắc cứng + embedding cục bộ**; LLM chỉ tùy chọn cho dòng mơ hồ | Xác định, không đoán C18 thành C24; dữ liệu không rời máy mặc định |
| POS/ERP thật | mock-pos **simulated** | Không có hệ thống thật; vẫn kiểm được payload slide 9 |
| "Che PII" | Regex che email/điện thoại, **nêu rõ giới hạn** | Trung thực, không hứa quá mức |
| Mục tiêu 12 → <2 phút | **Đo thật** trên MVP | Round 1 chỉ là giả định |

- **Nói:** "The architecture is a Next.js UI, a FastAPI core with an AI gateway and a connector module, PostgreSQL with pgvector, and a simulated POS. Compared with Round 1 we replaced LLM reranking with hard rules plus local embeddings, because matching must be deterministic and safe. The LLM is optional, and when it is on, only masked text is sent."
- **Lưu ý:** System Diagram cần sửa trước khi quay (vẽ LLM nét liền nếu key đang bật, thêm khối embedding cục bộ, khổ A4).

### Case 10 — Bằng chứng và giới hạn (6:20–6:45)
- **Thẻ:** `CASE 10 · Evidence and honest limits`
- **Màn hình:** thẻ chữ ba cột:
  - *Evidence:* `[241] automated tests · 33/33 live acceptance checks · matching evaluated on 98 labelled lines (initial results)`.
  - *Honest limits:* POS, stock, prices and customers are simulated · only e-mail/phone are masked · evaluation labels [reviewed by a teammate: N/98] (chỉ ghi nếu đúng).
  - *Next:* pilot in Norway · real catalog and POS connector · measure time-to-serve in a store.
- **Nói:** "These are initial results. We do not claim production accuracy: the evaluation covers [98] lines on simulated data. The next step is a store pilot with the real catalog and POS. SiteDesk turns a customer's list into a confirmed order in seconds, a human always makes the final call, and the counter never stops."

---

## 4. Lỗi hay gặp khi quay

| Triệu chứng | Nguyên nhân | Xử lý |
|---|---|---|
| Analyze chậm 10 giây trở lên | Model chưa nạp | Chờ health báo `embedding: up`, chạy một lần nóng máy |
| "Stock unknown" khắp nơi | Bật POS fail trước Analyze | Tắt công tắc, làm lại |
| Confirm mờ | Còn dòng cần xử lý | Xem "N line(s) to resolve", bấm **Next issue** (F6) |
| Dòng không phải hàng (tiêu đề, lời chào) chặn Confirm | Parser coi là dòng hàng | Mở dòng đó → **Remove line** (bấm hai lần) |
| Con số thời gian khác mỗi lần | LLM có thể tham gia (có key) | Đọc số trên màn hình lần quay thật |

## 5. Mẹo quay

- Mỗi case một ý. Dùng **jump cut** cho chỗ chờ (nạp trang, đợi Analyze).
- Phụ đề tiếng Anh, cỡ đủ đọc ở 1080p. Không hứa số chưa đo (≥30%, ≥70%, <2 phút).
- Một cảnh lỗi: dừng, reset DB hoặc dùng đơn mới, quay lại đúng case rồi ghép. Không sửa code sau khi khóa 08/11 trừ lỗi chặn.
- Xuất MP4 xong: xem lại trên điện thoại; chắc chắn **không lộ key hay mật khẩu**.
