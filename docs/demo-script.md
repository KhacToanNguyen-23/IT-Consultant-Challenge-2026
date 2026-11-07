# Kịch bản video demo MVP (mục tiêu 6:40, trần đề 7:00)

Bám Round 2: (1) demo chức năng cốt lõi, (2) các hành trình chính, (3) giá trị cho người dùng/doanh nghiệp, (4) nếu MVP khác Round 1 thì giải thích thay đổi và lý do. Chấm theo: Engineering quality, Architecture, Appropriate AI usage (có người kiểm chứng), Technical reasoning khớp Round 1.

Ba thông điệp xuyên suốt (SRS 0.2): **AI không sai im lặng · Quầy không bao giờ dừng · Từ danh sách thô đến đơn xác nhận, có thời gian đo thật.**

Lời thoại tiếng Anh (hoặc phụ đề). Không nêu con số nào chưa đo. Mọi số trong `[ ]` phải điền từ lần quay thật.

## Chuẩn bị trước khi quay (bắt buộc)

- [ ] `docker compose down -v && up --build`, chờ model nạp xong (~30 s), gọi analyze một lần cho nóng máy.
- [ ] UI ở **English**, trình duyệt zoom 125%, ẩn bookmark/tab thừa, độ phân giải 1920×1080.
- [ ] Bộ đếm giờ góc trên phải (header) **thấy rõ** và reset về 0 mỗi phiên.
- [ ] Dùng các nút mẫu có sẵn (`story/samples.ts`): full, stockout, traps, nordic, email (xem `docs/demo-cases.md`). Không gõ tay trên video.
- [ ] Đã quay thử trọn vẹn một lần, đúng giờ. Mọi mục "chưa có browser E2E" trong `flow1-traceability.md` phải được thử trước khi đưa vào.
- [ ] Không lộ `.env`, API key, mật khẩu, đường dẫn cá nhân trên màn hình.

## Dòng thời gian

| Giờ | Cảnh | Làm gì trên UI | Lời thoại chính |
|---|---|---|---|
| 0:00–0:25 | **Mở đầu: giá trị** | Thẻ chữ: "12 min → <2 min (Round 1 target)". Cắt sang màn hình chính, timer 00:00 | "A contractor hands over 20–35 lines. Today the associate re-keys them for about 12 minutes. Let's see SiteDesk do it." |
| 0:25–1:25 | **1. At the counter: danh sách thô → bảng rà soát** | Bấm mẫu **Full counter list** (18 dòng). Nhấn mạnh: xem trước đã **che email/điện thoại**, "N lines read". Bấm Analyze. Bảng hiện **ngoại lệ lên trước**: xanh tự khớp, vàng/đỏ cần xem. Dừng ở dòng `120 m timber 45x95 C24` → **25 lengths ↑** | "Phone and e-mail are masked before anything is processed. Exceptions come first. 120 m becomes 25 lengths of 4.8 m, rounded up." |
| 1:25–2:05 | **2. AI không sai im lặng** | Bấm mẫu **traps**. Dừng ở `45x95 C18`: vẫn là C18, không thành C24, có **lý do** (chip). `skruer`, `blahblah`: **không gợi ý SKU**. Nút Confirm **bị khóa**, hiện số dòng còn chặn | "It never guesses silently. C18 stays C18, unknown items get no suggestion, and Confirm is blocked until a human resolves every line." |
| 2:05–2:55 | **3. Hết hàng: cứu doanh số, người duyệt** | Bấm mẫu **stockout**. Dòng gips vådrum hết hàng → hiện **thay thế an toàn (≤2)** kèm chênh lệch giá. Bấm "customer accepts". **SKU chỉ đổi sau khi khách đồng ý.** Dòng `200 sække cement` thiếu một phần | "Instead of 'sorry, out of stock', the associate offers an equal-spec alternative with the price difference. The SKU changes only after the customer agrees." |
| 2:55–3:30 | **4. Confirm → POS, đo giờ** | Chọn khách (hoặc WALKIN) → Confirm (phím Enter). Hiện `POS_ACCEPTED` + mã tham chiếu, đơn **chỉ đọc**. **Dừng timer, để số trên màn hình** | "The order is accepted by the simulated POS with a reference. Total time: [X s], measured in this MVP." |
| 3:30–4:20 | **5. POS lỗi → quầy không dừng** | Bật công tắc **POS fail**. Chạy lại nhanh một phiên, Confirm. Hiện thông báo "POS not responding — CSV exported", bấm **Download CSV** (cùng mã tham chiếu) | "When the POS is down the order is exported as a CSV with the same reference. Nothing is lost." |
| 4:20–5:10 | **6. AI lỗi → tìm tay → vẫn Confirm** | Bật **AI fail** (tắt POS fail). Banner "AI is unavailable. Search the catalog manually". Dùng ô **tìm SKU thủ công**, chọn SKU, Confirm → `POS_ACCEPTED`. Nhắc lại C18 vẫn không thành C24 ở chế độ này | "With AI off, hard rules and manual search keep the counter running. The same safety rules apply in both modes." |
| 5:10–5:40 | **7. Luồng 2: E-mail quote** *(chỉ nếu đã chạy ổn)* | Chuyển nút E-mail quote → dán email → **Save** quote `BG-DK-xxxx` → Print. Nếu không ổn, thay bằng 1 slide "Phase 2" | "Same engine, second journey: an e-mail request becomes a saved quote the associate prepares before the customer arrives." |
| 5:40–6:20 | **8. Kiến trúc và thay đổi so với Round 1** | Hiện **System Diagram L2**, rồi bảng 4 dòng bên dưới | Xem bảng "Thay đổi so với Round 1" |
| 6:20–6:40 | **9. Bằng chứng, giới hạn, bước tiếp** | Thẻ: kết quả đánh giá ban đầu, giới hạn, bước tiếp theo | "These are initial results on [N] lines, [M] human-reviewed. Next: real store data, pilot in Norway." |

### Thay đổi so với Round 1 (hiển thị chữ, ~30 s)

| Round 1 | MVP | Vì sao |
|---|---|---|
| LLM rerank cho khớp SKU | **Quy tắc cứng + embedding cục bộ** | Xác định, không đoán C18 thành C24; dữ liệu không rời máy (khớp "sovereign AI") |
| POS/ERP thật | mock-pos **simulated** | Không có hệ thống thật; vẫn kiểm được hợp đồng payload slide 9 |
| "Che PII" | Regex che email/điện thoại, **nêu rõ giới hạn** | Trung thực: tên/địa chỉ không đảm bảo |
| Mục tiêu 12 → <2 phút | **Đo thật** trong MVP | Round 1 chỉ là giả định |

## UI phải thể hiện được gì ở mỗi thao tác (checklist "wow")

- **Mỗi cảnh chỉ một ý.** Zoom/halo vào đúng chỗ đang nói; không cuộn lung tung.
- **Màu và trạng thái nhất quán** (một enum trạng thái dòng): xanh = tự khớp, vàng = xem lại, đỏ = chặn. Thanh trạng thái, thẻ chip lý do luôn đọc được ở độ phân giải video.
- **Chip lý do** cạnh dòng vàng/đỏ ("grade missing", "C18 ≠ C24"). Đây là cách biến điều *không xảy ra* (không đoán sai) thành thứ nhìn thấy.
- **Biểu tượng làm tròn ↑** và công thức ngắn (120 / 4.8 = 25) hiện ngay trên dòng.
- **Banner AI/POS lỗi** nổi bật, ô tìm thủ công và nút Download CSV **luôn dùng được**, không mất dữ liệu khi tải lại trang.
- **Timer** hiển thị cố định, dừng lại khi Confirm. Một con số đo thật quan trọng hơn mọi lời giải thích.
- **Phím tắt Enter** để Confirm (khớp slide 6 "Confirm & push order (Enter)").
- **Không có dev text, log, lỗi console** trong khung hình.

## Lỗi hay gặp, tránh

- Quay khi model chưa nạp xong → analyze chậm hoặc chạy chế độ rules mà không báo.
- Giải thích dài khi đang chờ. Cắt ghép (jump cut) chỗ chờ, giữ phần kết quả.
- Hứa số liệu chưa đo (≥30%, ≥70%). Chỉ nói "mục tiêu Round 1" hoặc số đo thật.
- Quay Luồng 2 khi chưa ổn. Cắt theo SRS 0.3.
- Đề cập deploy hoặc link ngoài làm bản chính.

## Nếu lúc quay một cảnh lỗi

Dừng, reset DB, quay lại đúng cảnh đó rồi ghép. Không sửa code sau 08/11 khóa code trừ lỗi chặn.
