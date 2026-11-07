# Kịch bản video demo MVP — chi tiết (mục tiêu 6:45, trần đề 7:00)

Bám Round 2: (1) demo chức năng cốt lõi, (2) các hành trình chính, (3) giá trị cho người dùng và doanh nghiệp, (4) nếu MVP khác Round 1 thì giải thích thay đổi và lý do. Tiêu chí chấm: Engineering quality, Reasonable architecture, Appropriate AI usage (có người kiểm chứng), Clear technical reasoning khớp Round 1.

**Ba thông điệp xuyên suốt (SRS 0.2):**
1. *AI không được sai một cách im lặng.*
2. *Quầy không bao giờ dừng.*
3. *Từ danh sách thô đến đơn xác nhận, có thời gian đo thật.*

Lời thoại bằng tiếng Anh (đọc hoặc làm phụ đề). Mọi số trong `[ ]` phải điền từ **lần quay thật**, không dùng số chưa đo. Các ca và đầu vào xem `docs/demo-cases.md`.

---

## A. Chuẩn bị trước khi quay (bắt buộc)

- [ ] `docker compose down -v && docker compose up --build`, đợi `/api/health` báo `embedding.status = up`, chạy một lần phân tích để làm nóng.
- [ ] Trình duyệt 1920×1080, zoom 125%, UI **English**, ẩn bookmark và tab thừa, tắt thông báo hệ thống.
- [ ] Đồng hồ góc trên phải thấy rõ. Công tắc **Demo** (góc trái dưới) đang tắt cả hai.
- [ ] File sẵn để mở: `docs/demo/material-list.pdf`. Các nút mẫu có sẵn trên màn nhập.
- [ ] Quay thử trọn vẹn một lượt, đúng giờ, rồi mới quay thật.
- [ ] Không để lộ `.env`, API key, đường dẫn cá nhân trong khung hình.
- [ ] Phím tắt hữu ích: **F9** Analyze/Confirm, **F6** Next issue, **F7** Customer.

## B. Dòng thời gian

| Giờ | Cảnh | Ghi chú |
|---|---|---|
| 0:00–0:25 | Mở đầu: nỗi đau và kết quả | Thẻ chữ rồi vào màn hình |
| 0:25–1:00 | 1. Nhận file thật và che thông tin | Upload PDF |
| 1:00–1:40 | 2. Phân tích: ngoại lệ lên trước, quy đổi, làm tròn | "Full counter list" |
| 1:40–2:30 | 3. Cứu 3 dòng thiếu hàng, người quyết định, Confirm | Dừng đồng hồ |
| 2:30–3:10 | 4. AI không sai im lặng | Mẫu traps |
| 3:10–3:30 | 5. Một công cụ, ba thị trường | Mẫu nordic |
| 3:30–4:10 | 6. POS lỗi → CSV | Công tắc POS |
| 4:10–4:55 | 7. AI lỗi → tìm tay → Confirm | Công tắc AI |
| 4:55–5:30 | 8. Luồng 2: email → báo giá | Chỉ nếu đã chạy ổn |
| 5:30–6:15 | 9. Kiến trúc và thay đổi so với Round 1 | System Diagram + bảng |
| 6:15–6:45 | 10. Bằng chứng, giới hạn, bước tiếp | Thẻ chữ + lời kết |

Nếu trễ: cắt cảnh 8 trước, rồi rút cảnh 5 (SRS 0.3). **Không cắt** cảnh 2, 3, 4, 6, 7.

---

## C. Chi tiết từng cảnh

### Mở đầu (0:00–0:25)
- **Màn hình:** thẻ chữ lớn: "20–35 lines re-keyed by hand · ~12 min per list (Round 1 estimate)". 0:10 cắt sang màn hình chính, đồng hồ 00:00.
- **Lời thoại:** "At a building-materials counter, a contractor hands over a long material list. Today the associate re-keys every line into the POS, about twelve minutes by our Round 1 estimate. Here is SiteDesk, the working MVP."
- **Slide Round 1:** 2, 3. **Tiêu chí R2:** nối bài toán Round 1.

### Cảnh 1 — Nhận file thật và che thông tin (0:25–1:00)
- **Thao tác:** bấm **Upload file** → chọn `material-list.pdf` → **Read list**. Trang session hiện, bấm **Source**.
- **Chỉ vào:** dòng chào có số điện thoại và email đã bị thay bằng dấu che; số dòng đã đọc.
- **Lời thoại:** "The list arrives as a PDF. Before anything else, phone numbers and e-mail addresses are masked. We state the limit honestly: names and addresses in free text are not guaranteed to be removed."
- **Slide R1:** 5 (Read), 7 (Privacy by design). **SRS:** FR-001, 002.

### Cảnh 2 — Phân tích (1:00–1:40)
- **Thao tác:** bấm **Analyze** (F9). Đừng cuộn vội; để màn hình hiện đủ.
- **Chỉ vào, theo thứ tự:**
  1. Ba thẻ bằng chứng: "E-mail/phone masked", "Semantic match · rules checked", "Stock checked … · simulated POS".
  2. Thanh số đo: `[X] ms analysed in`, `[N]/18 lines needed no edit`, đồng hồ.
  3. **"Needs a look (6)" lên đầu**, ngoại lệ trước.
  4. Dòng `120 m konstruktionstræ → 25 × piece_4.8m`.
  5. Dòng `60 m² ÷ 2.88 = 20,83 → 21` có nhãn **Rounded up**.
  6. Dòng `15 stk 48x98 C24 4.8m` đúng 15 thanh.
- **Lời thoại:** "Eighteen lines are read and checked in [X] milliseconds. The associate sees exceptions first. One hundred twenty metres becomes twenty-five lengths of 4.8 metres. Sixty square metres becomes twenty-one packs, rounded up to sellable units. [N] of eighteen lines need no edit at all."
- **Slide R1:** 6 (09:30 List intake, 11:00 Unit conversion). **SRS:** FR-006–013.

### Cảnh 3 — Cứu thiếu hàng, người quyết định, Confirm (1:40–2:30)
- **Thao tác:** dòng 5 đã chọn sẵn → chỉ dòng chữ đỏ **"Only 5 left, need 21 — alternative ready"** → bấm **Customer accepts**. Sau mỗi lần chấp nhận, hệ thống tự mở dòng cần xử lý kế tiếp: dòng 8 (vådrum) → **Customer accepts**; dòng 15 (`45x120 C24` hết hàng) → thẻ đề xuất là **C30**, cấp cao hơn, có chênh giá → **Customer accepts**.
- Chỉ vào nút "Customer: Walk-in" (khách mặc định, đổi bằng F7 nếu cần) → **Confirm order to POS** (F9). **Dừng đồng hồ**, để số trên màn hình.
- **Chỉ vào:** biên nhận "Sent to POS", mã tham chiếu, `[T] s` upload → Confirm, dòng "Round 1 target … (a target, not benchmarked)".
- **Lời thoại:** "Instead of 'sorry, out of stock', each problem line comes with a safe alternative and the price difference. The SKU changes only after the customer agrees, and the higher grade, C30 for C24, is labelled as such. One click confirms the order to the simulated POS. Total time, upload to confirmation: [T] seconds."
- **Slide R1:** 6 (09:31 Stockout salvage, Anytime 1-click push), 8 (Substitution acceptance KPI). **SRS:** FR-014–016, 018–020.

### Cảnh 4 — AI không sai im lặng (2:30–3:10)
- **Thao tác:** **New list** → mẫu **"AI must not be wrong silently"** → Read → Analyze. Dòng 2 (`45x95 timber`) chọn sẵn, bên phải hiện "Ask the customer: which one?" với hai thẻ C24 và C18.
- **Chỉ vào:**
  1. Chữ đỏ "Not stated: strength grade — not guessed", nhãn "Closest candidate, not confirmed".
  2. `skruer`, `blahblah`: "Not in catalog — no suggestion".
  3. `20 m isolering`: "Unit missing/unknown — not guessed".
  4. Nút **Confirm** bị khóa, "4 line(s) to resolve".
  5. Dòng `45x95 C18 – 30 stk` ở dưới **vẫn là C18**, không thành C24.
- **Lời thoại:** "This is the point of the design: the AI is never allowed to be wrong silently. A missing strength grade is not guessed. Items outside the catalog get no suggestion. C18 stays C18. Confirm remains blocked until a human decides."
- **Slide R1:** 5 (Humans retain the final call), 7 (guardrails). **SRS:** FR-007–010. **Tiêu chí R2:** Appropriate AI usage.

### Cảnh 5 — Một công cụ, ba thị trường (3:10–3:30)
- **Thao tác:** **New list** → mẫu **"One tool, three markets"** → Read → Analyze.
- **Chỉ vào:** các dòng viết kiểu NO (`Konstruksjonsvirke … meter`), SV (`säckar`, `terrassebrädor … st`), EN (`pressure treated decking … pcs`) cùng khớp về SKU trong catalog.
- **Lời thoại:** "Norwegian, Swedish and English wording all resolve to the same catalog. The core is shared, and local differences live in the connector and the dictionary, not in a different tool per country."
- **Slide R1:** 2, 7, 10 (Built once globally, connected locally).

### Cảnh 6 — POS lỗi → CSV (3:30–4:10)
- **Thao tác:** quay lại **Full counter list** (hoặc mẫu stockout, nhanh hơn) → Analyze → xử lý các dòng → bật công tắc **Demo → POS fail** → **Confirm**.
- **Chỉ vào:** trạng thái "Fallback active", dòng "POS not responding — CSV exported, manual entry needed", nút vàng **Download CSV**, mã `CSV-SD-…`, câu "Nothing is lost".
- **Lời thoại:** "If the POS is down, the order is not lost. SiteDesk exports a CSV with the same reference so the associate can finish in the legacy system. The status says clearly that the POS did not accept it."
- **Chú ý:** bật POS fail **sau khi phân tích**, trước Confirm (nếu bật trước, tồn kho hiện "Stock unknown"). Tắt công tắc sau cảnh này.
- **Slide R1:** 7 (Zero Downtime Fallback). **SRS:** FR-019, 033.

### Cảnh 7 — AI lỗi → tìm tay → Confirm (4:10–4:55)
- **Thao tác:** bật **Demo → AI fail** → mẫu stockout hoặc Full → Read → Analyze.
- **Chỉ vào:** banner vàng "AI is unavailable. Search the catalog manually to continue", thẻ "Rules · manual SKU search", **ô tìm SKU thủ công** đã mở sẵn. Gõ `gips` → Search → chọn một SKU. Xử lý hết, **Confirm** → `POS_ACCEPTED`.
- **Lời thoại:** "Now the AI is switched off. Hard rules and manual catalog search keep the counter running, and the same safety rules apply: C18 never becomes C24. The order still reaches the POS."
- **Slide R1:** 7. **SRS:** FR-003, 033. **Tiêu chí R2:** reliable functionality. Tắt công tắc sau cảnh này.

### Cảnh 8 — Luồng 2: email → báo giá (4:55–5:30) *(chỉ nếu chạy ổn)*
- **Thao tác:** nút **E-mail quote** → mẫu **Customer e-mail** → Read → Analyze → chấp nhận thay thế → **Save quote**. Trang `BG-DK-xxxx`: chỉ vào "Reference price and stock; this quote does not reserve items", **Record approval**, **Re-check**, **Print quote**, và nút **Demo: simulate price/stock changes** rồi Re-check cho thấy khác biệt.
- **Lời thoại:** "The same engine serves the second journey. An e-mail request becomes a saved quote with a price and stock snapshot. The customer approves outside the system, and on arrival the associate re-checks live data and sees what changed."
- **Nếu không ổn:** thay bằng một slide "Phase 2: pre-order quote" và nói một câu.
- **Slide R1:** 6 (07:00 Pre-pick). **SRS:** FR-022–028.

### Cảnh 9 — Kiến trúc và thay đổi so với Round 1 (5:30–6:15)
- **Màn hình:** System Diagram trang 2 (Container) trong 15 giây, rồi bảng sau (hiện chữ, đọc nhanh):

| Round 1 | MVP | Vì sao |
|---|---|---|
| Rerank bằng LLM | **Quy tắc cứng + embedding cục bộ**; LLM chỉ tùy chọn cho dòng mơ hồ | Xác định, không đoán C18 thành C24; dữ liệu không rời máy mặc định |
| POS/ERP thật | mock-pos **simulated** | Không có hệ thống thật; vẫn kiểm được payload slide 9 |
| "Che PII" | Regex che email/điện thoại, **nêu rõ giới hạn** | Trung thực, không hứa quá mức |
| Mục tiêu 12 → <2 phút | **Đo thật** trên MVP | Round 1 chỉ là giả định |

- **Lời thoại:** "The architecture is a Next.js UI, a FastAPI core with an AI gateway and a connector module, PostgreSQL with pgvector, and a simulated POS. Compared with Round 1 we dropped LLM reranking in favour of hard rules plus local embeddings, because matching must be deterministic and safe. The LLM is optional, and when it is on, only masked text is sent."
- **Tiêu chí R2:** Reasonable architecture, Clear technical reasoning.

### Cảnh 10 — Bằng chứng, giới hạn, bước tiếp (6:15–6:45)
- **Màn hình:** thẻ chữ ba cột:
  - *Evidence:* `[233+] automated tests · 33/33 live acceptance checks · matching evaluation on 98 labelled lines (initial results)`.
  - *Honest limits:* POS, stock, prices and customers are simulated · only e-mail/phone are masked · evaluation labels [reviewed by a teammate: N/98] (chỉ ghi nếu đúng).
  - *Next:* pilot in Norway · real catalog and POS connector · measure time-to-serve in a store.
- **Lời thoại:** "These are initial results. We do not claim production accuracy: the evaluation covers [98] lines and the data is simulated. The next step is a store pilot with the real catalog and POS, measuring time-to-serve and substitution acceptance. SiteDesk turns a customer's list into a confirmed order in seconds, with a human always making the final call, and the counter never stops."
- **Tiêu chí R2:** trung thực về giới hạn.

---

## D. Bảng đối chiếu nhanh: cảnh nào chứng minh tiêu chí nào

| Tiêu chí Round 2 | Cảnh |
|---|---|
| Engineering quality (chạy ổn, tin cậy) | 2, 3, 6, 7, 10 |
| Reasonable architecture | 9 |
| Appropriate AI usage (có người kiểm chứng) | 3, 4, 7, 10 |
| Clear technical reasoning (khớp Round 1) | Mở đầu, 3, 9, 10 |
| "Giải thích thay đổi so với Round 1" (bắt buộc) | 9 |

## E. Mẹo quay

- Mỗi cảnh một ý. Zoom hoặc bấm đúng chỗ đang nói. Dùng **jump cut** cho chỗ chờ (nạp trang, đợi Analyze).
- Chữ phụ đề tiếng Anh, cỡ đủ đọc ở 1080p.
- Không hứa số chưa đo (≥30%, ≥70%, <2 phút). Chỉ nói "Round 1 target" hoặc số đo thật.
- Một cảnh lỗi: dừng, reset DB (hoặc dùng đơn mới), quay lại đúng cảnh rồi ghép. Không sửa code sau khi khóa 08/11, trừ lỗi chặn.
- Sau khi xuất MP4: xem lại bằng điện thoại để chắc chữ đọc được, dung lượng hợp lý, **không lộ key hay mật khẩu**.
