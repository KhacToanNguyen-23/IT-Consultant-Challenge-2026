# Các case demo cho video: nhập gì, bấm nút nào, thấy gì, nói gì

Mỗi case đáp ứng một yêu cầu của Round 2. Địa chỉ: http://localhost:3001 (UI English, zoom 125%). Giữa các case bấm **New list**.
**Mẹo:** bấm thẻ mẫu ở màn nhập thì ô nhập tự điền đúng văn bản ghi dưới đây, khỏi phải gõ.
Yêu cầu của đề: **A** core functionality · **B** main user journeys · **C** value · **D** changes since Round 1. Tiêu chí: Engineering quality, Architecture, AI có người kiểm chứng, Technical reasoning.

| Case | Tên | Đáp ứng | Thời lượng |
|---|---|---|---|
| 1 | Happy case: danh sách đầy đủ → đơn xác nhận | A, B (hành trình 1), C | 1:55 |
| 2 | Hết hàng → hàng thay thế | B, C | 0:35 |
| 3 | Dòng mơ hồ: AI không đoán | AI có người kiểm chứng | 0:35 |
| 4 | POS lỗi → CSV | Engineering quality | 0:35 |
| 5 | AI lỗi → tìm tay | Engineering quality | 0:40 |
| 6 | Email → báo giá | B (hành trình 2) | 0:40 |
| 7 | Ba thị trường | Technical reasoning | 0:15 |
| 8 | Kiến trúc + thay đổi so với Round 1 | D, Architecture | 0:45 |

---

## Case 1 · Happy case (A, B, C)

**Nhập** (thẻ mẫu **Full counter list**, hoặc upload `docs/demo/material-list.pdf`):
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
**Bấm theo thứ tự**
1. **Upload file** → chọn `material-list.pdf` (hoặc dán văn bản vào ô) → **Read list**.
2. Mở khung **Source** để cho thấy SĐT/email đã bị che.
3. **Analyze** (F9).
4. Chỉ: `120 m → 25 × piece_4.8m`; `60 m² → 21 × pack` + "Rounded up"; nhóm **Needs a look (6)**; thanh `14/18 lines needed no edit`.
5. Dòng rockwool (đỏ "Only 5 left, need 21") → **Customer accepts**. Dòng vådrum → **Customer accepts**. Dòng `45x120 C24` (hết hàng, đề xuất **C30**) → **Customer accepts**.
6. **Confirm order to POS** (F9).

**Kết quả phải thấy:** 18 dòng; `14/18` không cần sửa; 3 dòng đỏ có hàng thay; `POS_ACCEPTED` + mã tham chiếu; **Sales rescued by substitutes: 6.379,10 DKK**; `[T] s` upload → Confirm.
**Nói:** "A PDF list, contact details masked, eighteen lines checked in a fraction of a second. Three out-of-stock lines each get a safe, priced alternative the customer accepts. One click sends the order to the POS in [T] seconds, with [R] kroner of sales rescued."

## Case 2 · Hết hàng → hàng thay thế (B, C)

**Nhập** (thẻ **Out-of-stock rescue**):
```
10 plader gips vådrum 12.5 mm
40 pakker isolering 95 mm
200 sække cement 25 kg
120 m timber 45x95 C24
```
**Bấm:** Read list → Analyze → dòng 1 (vådrum) đã mở → **Customer accepts** → **Confirm order to POS**.
**Phải thấy:** chữ đỏ "Out of stock — safe alternative ready", thẻ `Vådrumsplade Brand B` chênh `+40 DKK`; sau accept SKU gạch ngang SKU cũ, hiện SKU mới; `POS_ACCEPTED`.
**Lưu ý:** dòng xi măng "Only 80 left, need 200 — check before promising" **không chặn Confirm** (không có hàng thay an toàn). Nói thẳng nếu để ý.
**Nói:** "Instead of 'sorry, out of stock', the associate offers an equal-spec alternative with the price difference, and the SKU changes only after the customer agrees."

## Case 3 · Dòng mơ hồ: AI không đoán (AI có người kiểm chứng)

**Nhập** (thẻ **AI must not be wrong silently**):
```
45x95 C18 - 30 stk
45x95 timber
10 stk skruer 5x50
20 m isolering 95 mm
blahblah ukendt ting
5 poser cement 25 kg
```
**Bấm:** Read list → Analyze. Dòng `45x95 timber` đã mở bên phải ("Ask the customer: which one?", hai thẻ C24/C18). **Không bấm Choose.**
**Phải thấy (chữ đỏ):** "Not stated: strength grade — not guessed"; `skruer`, `blahblah`: "Not in catalog — no suggestion"; `20 m isolering`: "Unit missing/unknown — not guessed"; nút **Confirm** mờ, "4 line(s) to resolve"; dòng `45x95 C18` ở dưới vẫn là C18.
**Nói:** "The AI is never allowed to be wrong silently. A missing grade is not guessed, unknown items get no suggestion, C18 stays C18, and Confirm stays blocked until a human decides."

## Case 4 · POS lỗi → CSV (Engineering quality)

**Nhập:** như Case 2 (thẻ **Out-of-stock rescue**).
**Bấm:** Read list → Analyze → **Customer accepts** → **Demo → POS fail** (bật *sau* Analyze; góc phải ghi "Fallback active") → **Confirm order to POS** → **Download CSV** → **Demo → tắt POS fail**.
**Phải thấy:** "POS not responding — CSV exported, manual entry needed"; trạng thái "Manual entry needed"; mã `CSV-SD-…`; "Nothing is lost".
**Nói:** "If the POS is down, the order is not lost. A CSV with the same reference lets the associate finish in the legacy system, and the status says the POS did not accept it."

## Case 5 · AI lỗi → tìm tay (Engineering quality)

**Nhập (gõ tay):**
```
12 skivor gips 12.5 mm
5 poser cement 25 kg
```
**Bấm:** **Demo → AI fail** (bật *trước* Analyze) → gõ hai dòng trên → Read list → Analyze → ô tìm bên phải đã điền `gips 12.5 mm`, sửa thành `gips standard 12.5` → **Search** → bấm **Gipsplade standard 12.5mm … SKU-GYP-STD-125** → **Confirm order to POS** → **Demo → tắt AI fail**.
**Phải thấy:** banner "AI is unavailable. Search the catalog manually to continue", thẻ "Rules · manual SKU search", `POS_ACCEPTED`.
**Nói:** "With the AI switched off, hard rules and manual search keep the counter running, and the same safety rules apply."

## Case 6 · Email → báo giá (B, hành trình 2)

**Nhập** (nút **E-mail quote**, thẻ **Customer e-mail**):
```
Hej,

120 m konstruktionstræ 45x95 C24
60 m2 rockwool 95 mm
10 plader vådrum gips 12.5 mm
6 sække cement 25 kg
20 stk terrassebræt 28x120 trykimp. 4.2m

Mvh
Jens Hansen, Nordbyg ApS
Tlf +45 22 33 44 55 · jens@nordbyg.dk
```
**Bấm:** Read list → Analyze → **Customer accepts** (các dòng thay) → **Save quote** (F8) → **Record sent** → **Record approval** → mở **Demo: simulate price/stock changes**, chọn SKU, nhập **New stock** nhỏ → **Apply** → **Re-check stock & price** → **Reset**.
**Phải thấy:** `BG-DK-xxxx`, "this quote does not reserve items", trạng thái chuyển Preparing, dòng đổi tồn sau re-check; sau cùng **Pick slip** và **Confirm order to POS**.
**Nói:** "The same engine serves a second journey. An e-mail request becomes a saved quote; after the customer approves, the associate re-checks live data and sees what changed."

## Case 7 · Ba thị trường (Technical reasoning)

**Nhập** (thẻ **One tool, three markets**):
```
Konstruksjonsvirke 45x95 C24 - 90 meter
5 säckar cement 25 kg
tryckimpregnerade terrassebrädor 28x120 20 st
pressure treated decking 28x145 - 12 pcs
8 sekker betongblanding 25 kg
```
**Bấm:** Read list → Analyze. **Phải thấy:** cả 5 dòng khớp catalog; `90 meter → 19 × piece_4.8m`.
**Nói:** "Norwegian, Swedish and English wording resolve to the same catalog. The core is shared; local differences live in the connector and dictionary."

## Case 8 · Kiến trúc + thay đổi so với Round 1 (D, Architecture)

**Không nhập.** Hiện **System Diagram** (trang Container), rồi bảng:

| Round 1 | MVP | Vì sao |
|---|---|---|
| Rerank bằng LLM | Quy tắc cứng + embedding cục bộ; LLM chỉ tùy chọn | Xác định, không đoán C18 thành C24; dữ liệu không rời máy mặc định |
| POS/ERP thật | mock-pos **simulated** | Không có hệ thống thật; vẫn kiểm được payload slide 9 |
| "Che PII" | Regex che email/điện thoại, nêu rõ giới hạn | Trung thực, không hứa quá mức |
| Mục tiêu 12 → <2 phút | Đo thật trên MVP | Round 1 chỉ là giả định |

**Nói:** "A Next.js UI, a FastAPI core with an AI gateway and a connector, PostgreSQL with pgvector, and a simulated POS. Compared with Round 1 we replaced LLM reranking with hard rules and local embeddings, because matching must be deterministic and safe."

---

**Thứ tự quay khuyến nghị:** 1 → 2 → 3 → 6 → 7 → 4 → 5 → 8. Case 4 và 5 đặt gần cuối vì cần bật công tắc rồi tắt lại. Tổng khoảng 6:25; chia nhịp từng giây xem `docs/demo-shotlist.md`.
