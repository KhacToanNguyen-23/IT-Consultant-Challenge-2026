# Cấu trúc video demo MVP (6:40, trần của đề 7:00)

Ba phần: **Mở bài (0:00–0:50) · Demo (0:50–5:50) · Chốt (5:50–6:40)**. Lời thoại bằng tiếng Anh (hoặc phụ đề). Chi tiết từng thao tác, đầu vào, nút bấm: `docs/demo-case-sheet.md`.

## A. MỞ BÀI (0:50)

| Giờ | Màn hình | Nội dung | Lời thoại chính |
|---|---|---|---|
| 0:00–0:10 | Thẻ tiêu đề: **SiteDesk · from a customer's list to a confirmed order** · tên đội · Round 2 | Giới thiệu, có logo và tên đội | (nhạc nền nhỏ hoặc im lặng) |
| 0:10–0:30 | Thẻ vấn đề: "20–35 lines re-keyed by hand · stock-outs · advice depends on the shift" | **Vấn đề Round 1** và vì sao chọn quầy làm điểm bắt đầu | "At a building-materials counter, every customer list is re-keyed by hand. Out-of-stock lines lose sales, and the advice depends on who is on shift." |
| 0:30–0:50 | Thẻ lộ trình: ① Counter ② E-mail ③ AI down ④ POS down ⑤ Architecture | Cho người xem biết sẽ thấy gì | "In the next minutes: two journeys, two failure modes, and how it is built. POS, stock and prices are simulated." |

## B. DEMO (5:00), mỗi case đáp ứng một yêu cầu của đề

Đầu mỗi case chèn **thẻ 2 giây cùng một mẫu**: `CASE n · tên yêu cầu của đề`.

| Giờ | Case | Đáp ứng | Bằng chứng giám khảo thấy |
|---|---|---|---|
| 0:50–2:20 | **1. Happy case tại quầy** (PDF → Confirm) | Core functionality, Main journey #1, Value | Che thông tin, ngoại lệ lên trước, quy đổi, hàng thay, `POS_ACCEPTED`, doanh số cứu được và thời gian trên biên nhận |
| 2:20–2:55 | **2. AI không đoán, người quyết** | AI có người kiểm chứng | Chữ đỏ "not guessed", Confirm bị khóa, C18 vẫn là C18 |
| 2:55–3:50 | **3. Happy case email** (hộp thư giả) | Main journey #2 | Copy email, thư báo lại có đề xuất, báo giá, khách duyệt, kiểm lại, nhận hàng |
| 3:50–4:35 | **4. AI lỗi, nhập tay tại quầy** | Engineering quality (reliable) | Banner, gợi ý "rule-based", tìm thủ công, vẫn `POS_ACCEPTED` |
| 4:35–5:05 | **5. POS lỗi → CSV** | Engineering quality (reliable) | "Nothing is lost", CSV cùng mã tham chiếu |
| 5:05–5:50 | **6. Kiến trúc + thay đổi so với Round 1** | Reasonable architecture + yêu cầu giải thích thay đổi | System Diagram (2 trang) + bảng thay đổi 4 dòng |

Nếu trễ giờ: cắt Case 3 trước (SRS 0.3), rồi Case 2. **Không cắt** Case 1, 4, 5, 6.

## C. CHỐT (0:50)

| Giờ | Màn hình | Nội dung | Lời thoại chính |
|---|---|---|---|
| 5:50–6:10 | Thẻ **3 điều cần nhớ** | Tóm lược | "One: a list becomes a confirmed order in seconds, and a human makes the final call. Two: the AI is never wrong silently, and the counter never stops. Three: we say what we measured and what we did not." |
| 6:10–6:30 | Thẻ **giới hạn trung thực + bước tiếp** | Uy tín | "POS, stock and prices are simulated; only e-mail and phone are masked; evaluation is initial. Next: a store pilot with the real catalog and POS." |
| 6:30–6:40 | Thẻ kết: tên sản phẩm · tên đội · "Thank you" | Đóng video | (im lặng) |

## Nguyên tắc để video trông chuyên nghiệp

- **Một khung thẻ thống nhất** (cùng màu, phông, vị trí) cho tiêu đề, thẻ case, thẻ chốt.
- **Mỗi cảnh một ý.** Con trỏ hoặc vòng sáng chỉ vào đúng chỗ đang nói, giữ yên 2–3 giây.
- **Jump cut** cho mọi chỗ chờ (nạp trang, đợi phân tích). Không có khoảng chết.
- **Phụ đề tiếng Anh** cỡ đọc được ở 1080p, hoặc đọc lời thuyết minh rõ ràng, tốc độ khoảng 130 từ mỗi phút.
- **Không đọc số chưa đo** và không đọc những số màn hình không còn hiển thị. Chỉ đọc số trên biên nhận (doanh số cứu được, thời gian).
- **Thống nhất ngôn ngữ giao diện** là English suốt video.

## Chuẩn bị kỹ thuật trước khi quay

- [ ] `docker compose down -v && docker compose up --build`, đợi mô hình nạp xong, chạy một lần để làm nóng.
- [ ] **Tắt LLM** (xóa `LLM_API_KEY` trong `.env`) để lời "dữ liệu không rời máy" đúng. **Tắt cả hai công tắc Demo.**
- [ ] 1920×1080, zoom 125%, tắt thông báo, ẩn thanh bookmark; không lộ `.env`, key, đường dẫn cá nhân.
- [ ] Mở sẵn: `docs/demo/material-list.pdf`, `docs/demo/mailbox.html` ở tab riêng, hai file diagram.
- [ ] Quay thử trọn một lượt, đúng giờ; đo tổng thời lượng ≤ 7:00.

## Sau khi quay

- Xuất **MP4**, ≤ 7:00, đặt tên `MVP.mp4`. Xem lại trên điện thoại.
- Kiểm tra không có key hay mật khẩu trong khung hình.
- Gửi cùng `User Journey.pdf`, `System Diagram.pdf`, `AI Journal.pdf` tới `EB.VN@netcompany.com`, tiêu đề **"Round 2 – tên đội"**, trước **22:00 ngày 9/11**.
