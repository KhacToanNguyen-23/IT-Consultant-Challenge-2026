# Kịch bản video theo câu chuyện một ngày của Mette (6:40)

Xương sống là kiến trúc của SRS và slide Round 1: **READ → MATCH → SUBSTITUTE → CONFIRM**, rồi luồng email (UC5), rồi các chế độ lỗi (NFR-06). Mỗi chương bắt đầu bằng một nỗi đau trong câu chuyện và kết thúc bằng quyết định thiết kế giải nỗi đau đó, nên người xem hiểu **vì sao** hệ thống làm như vậy.

Nhân vật là hư cấu: **Mette** (nhân viên quầy, cửa hàng DK-CPH-04, tên cửa hàng có thật trong app) và **Jens** (nhà thầu, khách quen). Giọng đọc tiếng Anh, câu ngắn, khoảng 130 từ mỗi phút. Thao tác chi tiết: `docs/demo-case-sheet.md`.

| Phần | Giờ | Thành phần SRS |
|---|---|---|
| Mở bài: một buổi sáng ở quầy | 0:00–0:55 | Vấn đề Round 1, lựa chọn |
| Chương 1 · READ | 0:55–1:40 | UC1 · FR-001, 002, 005 |
| Chương 2 · MATCH và CONVERT | 1:40–2:25 | UC4 · FR-006 đến 013 |
| Chương 3 · SUBSTITUTE | 2:25–3:10 | UC2 · FR-014 đến 016 |
| Chương 4 · CONFIRM | 3:10–3:40 | UC3 · FR-017 đến 020 |
| Chương 5 · Buổi chiều: một email | 3:40–4:30 | UC5 · FR-022 đến 028 |
| Chương 6 · Khi mọi thứ hỏng | 4:30–5:20 | NFR-06 · FR-003, 019, 033 |
| Kiến trúc và thay đổi so với Round 1 | 5:20–5:50 | NFR-07, FR-034 |
| Chốt: lợi ích, triển khai, giới hạn | 5:50–6:40 | KPI Round 1 · FR-029 đến 031 |

## Vì sao mỗi quyết định thiết kế tồn tại (sợi logic của câu chuyện)

| Nỗi đau trong chuyện | Quyết định thiết kế | SRS |
|---|---|---|
| Gõ lại từng dòng, tốn 12 phút | Đọc file, nhận email, paste | FR-001 |
| Dữ liệu khách không nên đi xa hơn cần thiết | Che email và số điện thoại trước mọi bước AI | FR-002 |
| "trykimp", "isolasjon": nhiều ngôn ngữ, tiếng lóng | Khớp theo nghĩa bằng embedding cục bộ | FR-006 đến 008 |
| C18 không phải C24, sai thì tốn kém | Luật cứng quyết định cái gì được phép; thiếu thông tin thì không đoán | FR-009, 013 |
| 120 m, nhưng hàng bán theo thanh 4,8 m | Quy đổi và làm tròn lên | FR-011, 012 |
| Hết hàng: lời tư vấn phụ thuộc người trực | Hàng thay thế cùng thông số, kèm chênh giá, khách đồng ý mới đổi | FR-015, 016, 039 |
| Một lỗi gõ thành lấy nhầm hàng và giao lại | Cổng chặn Confirm, mã chống nhập trùng, một định dạng đơn chuẩn | FR-010, 018, 020 |
| Mỗi nước một hệ thống | Connector riêng cho từng nước; lõi dùng chung | FR-019, 034 |
| Khách gửi email cho ngày mai | Báo giá không giữ chỗ, kiểm lại lúc lấy hàng | FR-022 đến 028 |
| Hệ thống có lúc hỏng | AI tắt: luật cứng; POS tắt: CSV; quầy không dừng | NFR-06 |

---

## MỞ BÀI: một buổi sáng ở quầy (0:00–0:55)

**[Thẻ tiêu đề, 5 s]** *SiteDesk · one standard order for every counter* · tên đội.

"It is half past nine on a Tuesday at store DK-CPH-04. Mette is behind the counter. A contractor, Jens, hands her a list: eighteen lines, in Danish, with a few Norwegian words and one English one."

"Mette has done this a thousand times. She retypes every line into the POS, searches for each product, converts metres into lengths and checks stock, one item at a time. About twelve minutes, by our estimate, if nothing goes wrong. And when a line is out of stock, what she says depends on how experienced she is."

"Now picture this in three countries. As the group grew, each market kept its own systems and its own way of working. Same counter, three different realities."

"A single new ERP would take years. So we asked a smaller question: what if the list simply became a clean order, in one standard format, without changing the systems behind the counter?"

"That is SiteDesk. It works in four steps: Read, Match, Substitute and Confirm. The AI does the heavy reading and matching. Mette keeps the final call." *[Hiện thẻ 4 bước, hoặc System Diagram trang 1]*

## CHƯƠNG 1 · READ (0:55–1:40) · `CASE 1 · Customer at the counter`

*[Upload `material-list.pdf` → Read list → mở Source]*

"Step one: Read. Mette drops Jens's PDF into SiteDesk. It could also be pasted text, an Excel sheet, or a CSV. Before anything else, SiteDesk masks phone numbers and e-mail addresses, because customer data should not travel further than it has to. Every line is kept. Even a line it cannot read is shown, never silently dropped."

## CHƯƠNG 2 · MATCH và CONVERT (1:40–2:25)

*[Analyze → chỉ `120 m → 25 lengths`, `60 m² → 21 packs` và "Rounded up"]*

"Step two: Match. Jens wrote 'trykimp', 'konstruktionstræ', 'isolasjon'. SiteDesk matches by meaning, with a local model, so nothing leaves the machine. But meaning alone is not enough. A C18 beam is not a C24 beam, so hard rules decide what is allowed, and if a detail is missing, it does not guess."

"Then it converts. A hundred twenty metres of timber becomes twenty-five lengths of four point eight. Sixty square metres of insulation becomes twenty-one packs, rounded up to what the store can really sell."

## CHƯƠNG 3 · SUBSTITUTE (2:25–3:10)

*[Chỉ nhóm "Needs a look", chữ đỏ "Only 5 left" → Customer accepts ×3, dừng ở thẻ C30]*

"Step three: Substitute. Three lines are a problem: the store does not have enough. This is the moment that used to depend on who was on shift. Now SiteDesk offers a safe alternative with the same specification, and the price difference. A higher grade is labelled as such. Mette asks Jens. He agrees, and only then does the product change."

## CHƯƠNG 4 · CONFIRM (3:10–3:40)

*[Confirm → biên nhận, dừng 4 giây]*

"Step four: Confirm. Every line is resolved, so Confirm unlocks. One click sends the order to the POS in one standard format, with a reference that prevents double entry. This receipt is the point: the sales that would have been lost, and the time it took."

## CHƯƠNG 5 · Buổi chiều: một email (3:40–4:30) · `CASE 2 · Customer sends a file or e-mail`

*[Tab hộp thư: Copy email → SiteDesk E-mail quote, Ctrl+V → Analyze → Copy reply → Send → Save quote → Record approval → Re-check → Confirm]*

"That afternoon, an e-mail arrives for tomorrow morning's pick-up. The customer is not here, so nothing can be confirmed today. Mette copies the text in. Same engine, same rules. Two lines are short, so SiteDesk drafts a reply with alternatives, and Mette sends it from her own mailbox. SiteDesk never sends e-mail by itself."

"Jens agrees. She saves a quote: price and stock as of now, clearly not reserved. Next morning the yard needs to know what changed overnight. One click re-checks live stock and price. Only now are the substitutes accepted and the order confirmed."

## CHƯƠNG 6 · Khi mọi thứ hỏng (4:30–5:20) · `CASE 3 · When things break`

*[(a) mẫu "AI must not be wrong silently" → chữ đỏ, hai thẻ, Confirm mờ; (b) Demo → AI fail, gõ 2 dòng, tìm tay, Confirm; (c) Demo → POS fail, Confirm, Download CSV]*

"A good tool earns trust when things go wrong. First, an unclear line. 'Forty-five by ninety-five timber' has no strength grade. SiteDesk shows both options and asks. Confirm stays locked until a person decides."

"Second, the AI service goes down. The counter does not stop. Hard rules and manual search take over, and the suggestions say so."

"Third, the POS goes down. The order is not lost. SiteDesk exports a file with the same reference, and tells Mette clearly that the POS has not accepted it."

## KIẾN TRÚC VÀ THAY ĐỔI SO VỚI ROUND 1 (5:20–5:50)

*[System Diagram trang 2, rồi thẻ thay đổi]*

"How it is built: a web screen, one API that holds the matcher, the AI gateway and the connector, a database with vector search, and a local embedding model. The connector is the only part that changes per country."

"Compared with Round 1, we replaced AI re-ranking with hard rules plus local embeddings, because a wrong match costs more than a missing suggestion."

## CHỐT (5:50–6:40)

*[Ba thẻ: Benefits → Rollout → What we have not proven → kết]*

"What this gives the group: Mette's twelve minutes go to advising, not retyping. Stock-outs turn into sales. And every market speaks one standard order, so improvements can travel."

"We would start with a pilot in Norway, add one connector per country, and judge it on three measures from Round 1: time to serve, substitution acceptance, and how many lines need no touch."

"We have not proven those numbers yet. The POS, stock and prices here are simulated, and our matching test is an initial one. The next step is the real catalog and a real counter."

"SiteDesk: one standard order, a human in control, and a counter that never stops."

---

## Kiểm tra lời kể với MVP thật

- "Eighteen lines": danh sách mẫu có 18 dòng hàng (dòng chào bị che và không tính).
- "Excel, CSV, pasted text": SRS FR-001 nhận PDF, XLSX, CSV, văn bản và email.
- "Reference that prevents double entry": đúng nhãn trên biên nhận.
- "Never sends e-mail by itself": đúng, chỉ soạn thư để nhân viên tự gửi.
- "Twelve minutes": là **ước tính Round 1**, nên luôn kèm "by our estimate".
- Mette và Jens là hư cấu; tên cửa hàng DK-CPH-04 là tên có thật trong app.
- Câu chuyện "hệ thống mỗi nước một kiểu" bám đề Round 1. Không nói đã có ba connector: MVP chỉ có một connector mô phỏng.
- Không đọc `14/18` hay số mili-giây; chỉ đọc doanh số cứu được và thời gian trên biên nhận.
