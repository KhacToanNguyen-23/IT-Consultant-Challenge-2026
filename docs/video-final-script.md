# Kịch bản video chốt (6:40): kể chuyện, 3 case, chốt lợi ích và hướng triển khai

Giọng đọc: tiếng Anh, câu ngắn, khoảng 130 từ mỗi phút. `[ ]` là thao tác trên màn hình. Chi tiết nút bấm và đầu vào: `docs/demo-case-sheet.md`. Chuẩn bị: reset DB, **tắt LLM**, tắt hai công tắc Demo, mở sẵn `material-list.pdf`, `mailbox.html`, hai file diagram.

| Phần | Giờ | Thời lượng |
|---|---|---|
| Mở bài: câu chuyện | 0:00–1:10 | 70 s |
| Case 1: khách mua tại quầy | 1:10–2:45 | 95 s |
| Case 2: khách gửi file hoặc email | 2:45–3:55 | 70 s |
| Case 3: khi hệ thống gặp sự cố | 3:55–5:15 | 80 s |
| Kiến trúc và thay đổi so với Round 1 | 5:15–5:50 | 35 s |
| Chốt: lợi ích và hướng triển khai | 5:50–6:40 | 50 s |

---

## MỞ BÀI: câu chuyện nỗi đau (0:00–1:10)

**[0:00] Thẻ tiêu đề:** *SiteDesk · one standard order for every counter* · tên đội · Round 2.

**[0:08] Thẻ bản đồ DK · NO · SE, mỗi nước một hệ thống riêng:**
"Company A is a Danish building-materials retailer with stores in Denmark, Norway and Sweden. As the business grew across countries, each market kept its own systems and its own way of working."

**[0:25] Thẻ quầy hàng, một danh sách dài:**
"The pain shows up in the same place in every country: the store counter. A contractor hands over a list of twenty or thirty lines. The associate retypes every line into an old POS, searches for each product, and when something is out of stock, the advice depends on who is on shift."

**[0:42] Thẻ lựa chọn:**
"We did not try to replace the ERP. That takes years. We chose one problem: turn a customer's messy list into one clean, standard order, at the counter, without touching the legacy systems."

**[0:55] Thẻ SiteDesk:**
"That is SiteDesk, a thin layer on top. It uses parsing and product matching to turn a list into reviewable order lines. AI can help with product matching, while the associate makes the final decision."

**[1:05] Thẻ lộ trình (3 case):** "Three cases: a customer at the counter, a customer who sends a file or an e-mail, and what happens when something breaks."

---

## CASE 1: khách mua tại quầy (1:10–2:45)

**Thẻ:** `CASE 1 · Customer at the counter`

- **[1:12]** [Upload `material-list.pdf` → Read list → mở Source]
  "A contractor is at the counter with a list. The associate drops it in. Phone numbers and e-mail addresses are masked before anything else."
- **[1:27]** [Analyze]
  "SiteDesk reads every line, matches each one to a product, converts units and checks stock."
- **[1:35]** [Chỉ `120 m → 25 lengths`, rồi `60 m² → 21 packs` và "Rounded up"]
  "One hundred twenty metres becomes twenty-five lengths. Sixty square metres becomes twenty-one packs, rounded up to what the store can sell."
- **[1:48]** [Chỉ nhóm "Needs a look" và chữ đỏ "Only 5 left"]
  "Exceptions come first. Three lines have a problem: not enough stock."
- **[1:55]** [Customer accepts ×3, dừng ở thẻ C30]
  "Instead of 'sorry, we do not have it', the associate offers a safe alternative with the price difference. A higher grade is labelled as such. A substitute counts only once the customer agrees."
- **[2:20]** [Confirm → biên nhận, dừng 4 giây]
  "One click sends the order to our simulated POS in a standard format. The receipt shows the order result, substitute decisions and elapsed time; these are demo records, not measured real sales."

## CASE 2: khách gửi file hoặc email (2:45–3:55)

**Thẻ:** `CASE 2 · Customer sends a file or e-mail`

- **[2:47]** [Tab hộp thư: mở email Jens → Copy email text → sang SiteDesk, E-mail quote, Ctrl+V → Analyze]
  "Not every customer comes in. Many send a file or an e-mail. Jens sends his list; the associate copies it in. Same engine, same rules. A file works the same way: PDF, Excel or CSV."
- **[3:05]** [Chỉ banner tím và 2 dòng đỏ → Copy reply to customer]
  "Two lines are short on stock, so SiteDesk drafts a reply with alternatives."
- **[3:15]** [Dán vào hộp thư → Send → khách trả lời]
  "The associate sends it from their own mailbox. SiteDesk never sends e-mail on its own. The customer agrees."
- **[3:25]** [Save quote → Record approval]
  "A quote is saved with a price and stock snapshot. Nothing is reserved."
- **[3:35]** [Re-check → Resolve → Customer accepts → Confirm]
  "On pick-up day the system re-checks live stock and price and shows what changed. Only now are the substitutes accepted and the order confirmed."

## CASE 3: khi hệ thống gặp sự cố (3:55–5:15)

**Thẻ:** `CASE 3 · When things break`

- **[3:57] (a) AI không đoán** [Mẫu "AI must not be wrong silently" → Analyze; chỉ chữ đỏ, hai thẻ C24/C18, nút Confirm mờ]
  "First, honesty. This line has no strength grade. SiteDesk does not guess. It shows both options and asks the customer. Confirm stays locked until a person decides."
- **[4:20] (b) AI sập** [Demo → AI fail; gõ 2 dòng gips và cement → tìm tay → Confirm]
  "Now we switch the AI off. Hard rules and manual search keep the counter running, and suggestions are labelled rule-based."
- **[4:48] (c) POS sập** [Demo → POS fail; Confirm → Download CSV]
  "And now the POS goes down. The order is not lost. SiteDesk exports a file with the same reference and says clearly that the POS did not accept it."

## KIẾN TRÚC VÀ THAY ĐỔI SO VỚI ROUND 1 (5:15–5:50)

**[5:15]** [System Diagram trang 1 trong 8 giây, rồi trang 2]
"Under the hood: a web screen, one API with an AI gateway and a connector, PostgreSQL with vector search, and local embeddings. The optional external LLM is disabled in this demo. POS, stock and prices are simulated; we have not validated this build against live systems in all three markets."

**[5:35]** [Thẻ thay đổi: LLM re-ranking → hard rules + local embeddings]
"Compared with Round 1, we replaced LLM re-ranking with local embeddings for candidate retrieval and hard rules for required product attributes. That makes the match easier to inspect; it does not establish production accuracy."

## CHỐT: lợi ích và hướng triển khai (5:50–6:40)

**[5:50] Thẻ "Benefits":**
"What we expect to improve: time at the counter by reducing retyping, and the handling of stock-outs by showing safe alternatives for associate review. A pilot with real catalog and POS data would need to measure those outcomes."

**[6:08] Thẻ "How we would roll out":**
"We would start with a pilot in Norway, add a connector for each country, and judge it on three measures: time to serve, substitution acceptance, and how many lines need no touch."

**[6:22] Thẻ "What we have not proven":**
"The POS, stock and prices here are simulated, and our matching evaluation is an initial test. The next step is a pilot with the real catalog and POS."

**[6:32] Thẻ kết:**
"SiteDesk: one standard order format, an associate in control, and tested fallback paths for AI and POS failures. Thank you."

---

## Điểm sáng khi giám khảo Netcompany xem

1. **Chọn đúng một vấn đề, chịu cắt phạm vi** ("one problem, maximise the impact"): không thay ERP mà thêm một lớp mỏng.
2. **"One solution, different realities":** lõi dùng chung, riêng phần connector đổi theo nước.
3. **AI có chủ quyền và có người kiểm soát:** embedding chạy cục bộ, LLM tùy chọn và chỉ thấy văn bản đã che; AI đề xuất, luật chặn, người quyết định.
4. **Độ tin cậy được thấy tận mắt:** AI sập và POS sập mà quầy vẫn chạy.
5. **Trung thực:** nói rõ cái đã chứng minh và chưa chứng minh, nên đáng tin hơn.
6. **Thước đo rõ:** ba chỉ số của Round 1 làm cổng đánh giá khi triển khai.

## Lưu ý để lời kể không bị bắt bẻ

- **Câu chuyện "mua lại công ty địa phương" là giả định của đội**, đề Round 1 chỉ nói mỗi nước đã tự phát triển hệ thống riêng. Trong video mình dùng "as the business grew across countries". Nếu muốn nhắc mua lại, hãy nói rõ đó là giả định của đội và khớp với slide Round 1.
- **"Thống nhất đầu ra"** hiện thể hiện bằng **một định dạng đơn chuẩn và một connector mô phỏng**; video chỉ minh họa kiểu viết NO/SV/EN qua dữ liệu, không nói là đã chạy ở ba nước.
- Không đọc các con số màn hình không còn hiện (`14/18`, mili-giây). Chỉ đọc doanh số cứu được và thời gian trên biên nhận.
- Hướng triển khai (thí điểm Na Uy, rồi Đan Mạch, rồi Thụy Điển) lấy từ slide 10 của Round 1.
