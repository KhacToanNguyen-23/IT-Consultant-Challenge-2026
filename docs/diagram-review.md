# Rà soát 4 diagram SiteDesk (Round 2)

Ngày: 2026-11-07. File gốc: `IT-Consultant-Challenge-2026-backend/SiteDesk_C4_L1_System_Context.pdf`, `SiteDesk_C4_L2_Container.pdf`, `SiteDesk-At-Counter.pdf`, `SiteDesk_Preorder_Advance_Quote_UC5.pdf`.
Đối chiếu với: `docker-compose.yml`, `backend/services/pos_client.py`, `.env.example`. Chưa kiểm từng mũi tên với toàn bộ code.

Đánh giá chung: nội dung đúng, khoảng 7,5/10. Chưa tối ưu vì đóng gói và vài chỗ thiếu.

## 1. Yêu cầu của đề Round 2

- **User Journey**: 1 file PDF, tối đa 2 trang, ít nhất 1 hành trình end-to-end thể hiện giá trị cốt lõi.
- **System context diagram**: 1 file PDF, tối đa 2 trang, gắn nhãn mọi thực thể ngoài và mọi tương tác, chỉ vẽ tương tác thật có trong MVP.
- Tên file ngắn, đúng nội dung. Không có mật khẩu, API key, thông tin bí mật.

## 2. Việc cần làm (theo thứ tự)

### A. Đóng gói (bắt buộc)

- [ ] Gộp thành 2 file nộp:
  - `User Journey.pdf`: trang 1 = At-Counter, trang 2 = Preorder (hoặc chỉ At-Counter nếu Luồng 2 không vào video).
  - `System Diagram.pdf`: trang 1 = C4 L1, trang 2 = C4 L2.
- [ ] Đổi khổ giấy. Hiện At-Counter là 3197×756 pt (tỉ lệ 4,2:1) và Preorder là 5242×1451 pt. Khi mở vừa màn hình, chữ chỉ còn khoảng 3–4 pt. Dựng lại về A4 ngang hoặc 16:9, chữ tối thiểu 9–10 pt. At-Counter xếp thành 2 hàng.
- [ ] Mở thử bằng điện thoại để kiểm tra độ đọc.

### B. System Diagram (L1, L2)

- [ ] **L2 thêm khối embedding cục bộ** `intfloat/multilingual-e5-small` bên trong Core API, ghi "local, no data leaves". Đây là thành phần AI chính và là bằng chứng "Appropriate AI usage" cùng "Sovereign AI" của Round 1.
- [ ] **LLM API vẽ nét đứt**, ghi "optional, disabled in demo". Lý do: `.env.example` để `LLM_API_KEY` rỗng nghĩa là LLM tắt, và pipeline khớp SKU chính không dùng LLM. Chỉ vẽ nét liền nếu video có cảnh bật LLM.
- [ ] Tách đường mũi tên đến LLM và mock-pos, hiện dùng chung một trục. Đặt nhãn sát mũi tên, không để đường cắt qua nhãn.
- [ ] Thêm chiều ngược lại cho "customer approval" giữa Customer và Counter Associate.
- [ ] Thêm chú giải ký hiệu: hộp xám = hệ thống ngoài (simulated), nét đứt = tùy chọn, hình trụ = kho dữ liệu.
- [ ] Thêm dòng nguồn: "Diagram reflects MVP build at commit `<hash>`".
- [ ] Giữ nguyên các ghi chú vàng (MVP SCOPE, DATA LIMIT, OUTCOME, CONTAINER RULE, AI & PRIVACY, FALLBACK). Đây là điểm trung thực nên giữ.

### C. User Journey: At-Counter

- [ ] Sắp xếp lại thứ tự: hiện "Convert units and check live stock" nằm trước "Review by Exception", rồi "Stock Status?" lại xuất hiện sau. Làm rõ stock được kiểm một lần ở đâu.
- [ ] Thêm bước **Confirm bị chặn khi còn dòng chưa giải quyết** (đỏ/vàng/NEEDS_CLARIFICATION). Preorder đã có, At-Counter chưa có, trong khi đây là điểm mạnh của MVP.
- [ ] Đổi ghi chú "Target: under 3 s" thành số đo thật: p50 ≈ 0,2 s cho 20 dòng (báo cáo `backend/reports/evaluation_2026-11-06.md`, embedding cục bộ, LLM không dùng trong luồng khớp).
- [ ] Ghi các đầu vào được hỗ trợ: PDF, paste text, Excel, CSV (không chỉ PDF).
- [ ] Giữ nhánh AI lỗi → rules only → tìm SKU thủ công, và nhánh POS 503/timeout → CSV.

### D. User Journey: Preorder (UC5, Luồng 2)

- [ ] Quyết định có đưa vào video hay không. Nếu không quay, ghi rõ "Phase 2 / minimal in MVP" để giám khảo không thấy journey không có trong demo.
- [ ] Giữ các nhãn: Pick Slip không phải là đặt chỗ, snapshot giá và tồn chỉ mang tính tham khảo.

## 3. Điểm đã tốt, giữ nguyên

- C4 L1/L2 và swimlane 3 vai (Customer, Counter Associate, SiteDesk).
- mock-pos ghi "simulated" ở cả hai mức.
- Fallback POS 503 → CSV + `NEEDS_MANUAL`, không ghi nhận là `POS_ACCEPTED`.
- Giới hạn PII ghi trung thực (regex chỉ che email và điện thoại).
- Mock login nằm trong SiteDesk, không vẽ thành SSO ngoài.
- AI Gateway và Connector là module trong Core API, không phải container riêng.

## 4. Bảng đối chiếu với code

| Mũi tên / hộp trong diagram | Bằng chứng trong code |
|---|---|
| Core API → mock-pos: catalog | `pos_client.py` `/catalog` |
| Core API → mock-pos: khách hàng | `pos_client.py` `/customers` |
| Core API → mock-pos: tồn kho | `pos_client.py` `/stock` |
| Core API → mock-pos: gửi đơn, `Idempotency-Key` | `pos_client.py` `/orders` |
| Core API ↔ PostgreSQL 15 + pgvector | `docker-compose.yml` service `db` |
| Embedding cục bộ | `docker-compose.yml` `EMBEDDING_PROVIDER=local`, model `multilingual-e5-small` |
| LLM tùy chọn | `.env.example` `LLM_API_KEY` rỗng = tắt |
| Hai fail toggle (AI, POS) | `AI_FAIL_MODE`, `MOCK_POS_FAIL_MODE` |
