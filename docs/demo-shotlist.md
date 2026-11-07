# Shot list video demo: từng giây (tổng 6:25, dư 35 giây so với trần 7:00)

Dùng cùng `docs/demo-script.md` (đó là bản theo case). File này là bản chia nhịp để quay: mỗi dòng là một cú máy, có **giờ**, **thao tác**, **câu nói** (tối đa khoảng 2 từ mỗi giây). Số trong `[ ]` đọc từ màn hình lúc quay thật.

## Vì sao kịp 7 phút (số đo, không phải ước đoán)

| Hạng mục | Đo được |
|---|---|
| Lời thoại cả video | 410 từ, khoảng 3 phút 10 giây nếu đọc 130 từ/phút |
| Thao tác thuần (chạy thử liền mạch, nghỉ 0,7 giây giữa các cú bấm) | Case 1: 6 s · Case 2: 3 s · Case 4: 6 s · Case 5: 16 s · Case 6: 5 s · Case 7: 8 s · Case 8: ~10 s, tổng khoảng 55 giây |
| Máy chủ trả lời | Phân tích 0,1–1,4 s; Confirm dưới 1 s |

Nghĩa là: thao tác chỉ chiếm khoảng 1 phút, lời thoại khoảng 3 phút. Phần còn lại là **thời gian để người xem đọc màn hình**, nên đừng nói liên tục, hãy dừng sau mỗi ý.

## Quy ước

- **Thẻ**: chữ 2 giây trên nền tối ở đầu mỗi case.
- **Chỉ**: đưa con trỏ vào đúng chỗ, giữ yên 2–3 giây.
- **Cắt**: dùng jump cut để bỏ chỗ chờ (nạp trang, Analyze).

---

## Case 0 · Bài toán Round 1 (0:00–0:20)

| Giờ | Thao tác | Nói |
|---|---|---|
| 0:00 | Thẻ chữ: "20–35 lines re-keyed by hand · ~12 min per list (Round 1 estimate)" | "At a building-materials counter, a contractor hands over a long material list." |
| 0:08 | Cắt vào màn hình chính, đồng hồ 00:00 | "Today every line is re-keyed by hand, about twelve minutes by our Round 1 estimate." |
| 0:16 | Giữ màn hình nhập | "This is the working MVP." |

## Case 1 · Core functionality (0:20–1:15)

| Giờ | Thao tác | Nói |
|---|---|---|
| 0:20 | Thẻ `CASE 1 · Core functionality` | — |
| 0:22 | Bấm **Upload file** → chọn `material-list.pdf` | "The list arrives as a PDF." |
| 0:28 | Bấm **Read list**. Trang session mở, khung **Source** hiện | "Phone numbers and e-mail addresses are masked first." |
| 0:34 | **Chỉ** dòng đã bị che | (im lặng 3 giây) |
| 0:37 | Bấm **Analyze** (F9) — *cắt phần chờ* | "Eighteen lines, checked in [X] milliseconds." |
| 0:43 | **Chỉ** 3 thẻ: masked · semantic match · stock checked | "Masked, matched by meaning, stock checked." |
| 0:48 | **Chỉ** thanh số đo `[X] ms` và `14/18` | "Fourteen need no edit at all." |
| 0:53 | **Chỉ** nhóm **Needs a look (6)** ở đầu bảng | "Exceptions come first." |
| 0:57 | Cuộn xuống, **chỉ** `120 m → 25 × piece_4.8m` | "One hundred twenty metres becomes twenty-five lengths." |
| 1:03 | **Chỉ** `60 m² ÷ 2.88 = 20,83 → 21` + nhãn **Rounded up** | "Sixty square metres becomes twenty-one packs, rounded up." |
| 1:10 | Cuộn lên đầu bảng, dừng | — |

## Case 2 · Main user journey #1, at the counter (1:15–2:00)

| Giờ | Thao tác | Nói |
|---|---|---|
| 1:15 | Thẻ `CASE 2 · Main user journey: at the counter` | — |
| 1:17 | Dòng rockwool đã mở. **Chỉ** chữ đỏ "Only 5 left, need 21 — alternative ready" | "Instead of 'sorry, out of stock'…" |
| 1:22 | **Chỉ** thẻ Isover Plus, chênh `+105,00 DKK` | "…the associate sees a safe, priced alternative." |
| 1:27 | Bấm **Customer accepts** | "The SKU changes only after the customer agrees." |
| 1:32 | Dòng vådrum tự mở → **chỉ** "Out of stock — safe alternative ready" → **Customer accepts** | — |
| 1:38 | Dòng `45x120 C24` tự mở → **chỉ** thẻ **C30** | "A higher grade is labelled as such." |
| 1:43 | **Customer accepts** | — |
| 1:47 | **Chỉ** nút **Customer: Walk-in**, rồi bấm **Confirm order to POS** (F9) | "One click confirms the order to the simulated POS." |
| 1:53 | Biên nhận hiện: **chỉ** `POS_ACCEPTED` và mã tham chiếu | (im lặng 3 giây) |

## Case 3 · Business value (2:00–2:25)

| Giờ | Thao tác | Nói |
|---|---|---|
| 2:00 | Thẻ `CASE 3 · Business value` (giữ nguyên biên nhận) | — |
| 2:02 | **Chỉ** "Sales rescued by substitutes: [R] DKK" | "Three lines that would have been lost sales, [R] Danish kroner at list price, were rescued." |
| 2:11 | **Chỉ** "Time from upload → Confirm: [T] s" và dòng "a target, not benchmarked" | "The whole order took [T] seconds against our twelve-minute estimate." |
| 2:18 | **Chỉ** thanh `14/18` | "Fourteen of eighteen lines needed no touch." |
| 2:22 | Giữ yên | "Measured on this simulated MVP, not on a real store." |

## Case 4 · Appropriate AI usage (2:25–3:00)

| Giờ | Thao tác | Nói |
|---|---|---|
| 2:25 | Thẻ `CASE 4 · AI with human validation` | — |
| 2:27 | **New list** → thẻ **AI must not be wrong silently** → **Read list** → **Analyze** | "Now the cases where the AI must not guess." |
| 2:35 | Dòng `45x95 timber` mở. **Chỉ** chữ đỏ "Not stated: strength grade — not guessed" và hai thẻ C24/C18. **Không bấm Choose** | "A missing strength grade is not guessed." |
| 2:42 | **Chỉ** `skruer`, `blahblah`: "Not in catalog — no suggestion" | "Items outside the catalog get no suggestion." |
| 2:47 | **Chỉ** `20 m isolering`: "Unit missing/unknown — not guessed" | — |
| 2:50 | **Chỉ** nút Confirm mờ và "4 line(s) to resolve" | "Confirm stays blocked until a human decides." |
| 2:55 | Cuộn xuống, **chỉ** `45x95 C18` vẫn là C18 | "And C18 never becomes C24." |

## Case 5 · Main user journey #2, e-mail quote (3:00–3:40)

| Giờ | Thao tác | Nói |
|---|---|---|
| 3:00 | Thẻ `CASE 5 · Main user journey: e-mail pre-order` | — |
| 3:02 | **New list** → **E-mail quote** → thẻ **Customer e-mail** → **Read list** → **Analyze** → **Customer accepts** (các dòng thay thế) | "The same engine serves a second journey." |
| 3:12 | Bấm **Save quote** (F8). Trang `BG-DK-xxxx` mở | "An e-mail request becomes a saved quote with a price and stock snapshot." |
| 3:18 | **Chỉ** "this quote does not reserve items" | — |
| 3:21 | Bấm **Record sent**, rồi chọn **E-mail**, bấm **Record approval** | "The customer approves outside the system." |
| 3:28 | Mở **Demo: simulate price/stock changes** → chọn một SKU → nhập **New stock** nhỏ → **Apply** | "Now stock changes while the quote waits." |
| 3:33 | Bấm **Re-check stock & price** → **chỉ** dòng đổi | "On arrival the associate re-checks live data and sees what changed." |
| 3:38 | Bấm **Reset** trong khung Demo để trả dữ liệu | — |

*Nếu không đủ giờ: dừng ở 3:21 và cắt phần Demo.*

## Case 6 · One core, three markets (3:40–3:55)

| Giờ | Thao tác | Nói |
|---|---|---|
| 3:40 | Thẻ `CASE 6 · One core, three markets` | — |
| 3:42 | **New list** → **One tool, three markets** → **Read list** → **Analyze** | "Norwegian, Swedish and English wording…" |
| 3:49 | **Chỉ** các dòng `Konstruksjonsvirke`, `säckar`, `decking … pcs` | "…resolve to the same catalog." |

## Case 7 · Reliable functionality: POS down (3:55–4:30)

| Giờ | Thao tác | Nói |
|---|---|---|
| 3:55 | Thẻ `CASE 7 · Reliable functionality: POS down` | — |
| 3:57 | **New list** → **Out-of-stock rescue** → **Read list** → **Analyze** → **Customer accepts** | "Now the POS goes down." |
| 4:07 | Mở **Demo** → bật **POS fail** (góc phải đổi "Fallback active") | — |
| 4:12 | Bấm **Confirm order to POS** | "The order is not lost." |
| 4:16 | **Chỉ** "POS not responding — CSV exported, manual entry needed" và mã `CSV-SD-…` | "A CSV is exported with the same reference…" |
| 4:22 | Bấm **Download CSV** | "…and the status says the POS did not accept it." |
| 4:27 | Mở **Demo** → tắt **POS fail** | — |

## Case 8 · Reliable functionality: AI down (4:30–5:10)

| Giờ | Thao tác | Nói |
|---|---|---|
| 4:30 | Thẻ `CASE 8 · Reliable functionality: AI down` | — |
| 4:32 | **New list** → **Demo → AI fail** *(trước khi phân tích)* | "Now the AI is switched off." |
| 4:38 | Gõ `12 skivor gips 12.5 mm` và `5 poser cement 25 kg` → **Read list** → **Analyze** | — |
| 4:47 | **Chỉ** banner "AI is unavailable. Search the catalog manually" và thẻ "Rules · manual SKU search" | "Hard rules and manual search keep the counter running." |
| 4:53 | Sửa ô tìm thành `gips standard 12.5` → **Search** → bấm **Gipsplade standard 12.5mm … SKU-GYP-STD-125** | — |
| 5:01 | Bấm **Confirm order to POS** → `POS_ACCEPTED` | "The order still reaches the POS." |
| 5:06 | Mở **Demo** → tắt **AI fail** | — |

## Case 9 · Architecture and what changed (5:10–5:55)

| Giờ | Thao tác | Nói |
|---|---|---|
| 5:10 | Thẻ `CASE 9 · Architecture and what changed since Round 1`, hiện **System Diagram** trang Container | "A Next.js UI, a FastAPI core with an AI gateway and a connector, PostgreSQL with pgvector, and a simulated POS." |
| 5:25 | Hiện bảng 4 dòng (Round 1 → MVP → vì sao), đọc từng dòng | "We replaced LLM reranking with hard rules plus local embeddings, because matching must be deterministic and safe." |
| 5:45 | **Chỉ** dòng "LLM optional" | "The LLM is optional, and only masked text is ever sent." |

## Case 10 · Evidence and honest limits (5:55–6:25)

| Giờ | Thao tác | Nói |
|---|---|---|
| 5:55 | Thẻ `CASE 10 · Evidence and honest limits`, hiện thẻ ba cột | "These are initial results." |
| 6:02 | **Chỉ** cột Evidence (`[241]` tests, `33/33` acceptance checks, `98` labelled lines) | "Automated tests and a live acceptance run pass." |
| 6:09 | **Chỉ** cột Limits | "The POS, stock and prices are simulated, and only e-mail and phone are masked." |
| 6:16 | **Chỉ** cột Next | "Next: a store pilot with the real catalog and POS." |
| 6:21 | Quay lại màn hình chính | "The AI helps, a human decides, and the counter never stops." |

---

## Sau khi quay Case 5: dọn dữ liệu

Lệnh **Apply** trong khung Demo làm đổi tồn kho hoặc giá của một SKU trong mock-pos, và thay đổi đó **giữ nguyên cho các case sau**, làm số liệu của các case khác lệch đi. Luôn bấm **Reset** ngay sau khi xong, hoặc chạy `docker compose restart mock-pos` để trả về dữ liệu gốc.

## Kiểm tra trước khi nộp

- [ ] Tổng thời lượng ≤ 7:00. Nếu vượt: cắt phần Demo của Case 5, rút Case 6.
- [ ] Mọi `[ ]` đã thay bằng số đọc từ màn hình.
- [ ] Không lộ key, mật khẩu, đường dẫn cá nhân.
- [ ] Cả hai công tắc Demo đã tắt khi kết thúc.
