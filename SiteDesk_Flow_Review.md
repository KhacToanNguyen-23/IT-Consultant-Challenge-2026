# SiteDesk · Bất cập và giải pháp theo từng giai đoạn của 2 luồng

> **Nguyên tắc:** giữ nguyên 2 luồng đã nộp ở Round 1. Mỗi bất cập đi kèm giải pháp **bổ sung vào luồng**, không bỏ bước nào.
> Nguồn đối chiếu: slide Round 1 (`SiteDesk_SRS_10_Slides_EN.pptx`) và SRS.
> Đây là phân tích của team dựa trên cách vận hành quầy vật liệu xây dựng nói chung. Các giả định về ERP/POS (ví dụ API ghi khó, ERP đã có báo giá) chưa kiểm chứng với Company A.

**Cột "Phạm vi" dùng 3 mức:**
- **MVP**: làm được và nên có trong bản demo Round 2.
- **Mô phỏng**: có màn hình/dữ liệu mẫu, không nối hệ thống thật.
- **Nêu**: chỉ nói trong video và tài liệu như hướng phát triển.

---

## LUỒNG 1: AT-COUNTER (UC1 → UC4 → UC2 → UC3)

```
F1-P1 Nhận list → P2 Bóc tách → P3 Khớp SKU → P4 Quy đổi → P5 Tồn kho → P6 Rà soát → P7 Thay thế → P8 Confirm & push → P9 Sau đơn
```

### F1-P1 · Nhận danh sách và đăng nhập (FR-01)

| Bất cập | Giải pháp (giữ nguyên luồng) | Phạm vi |
|---|---|---|
| Đầu vào chỉ PDF/Excel/text. Thực tế còn ảnh chụp, giấy viết tay, chat. | Giữ 3 đầu vào theo doc. Quy trình tại quầy: nhân viên gõ/dán lại vào ô paste. Hướng phát triển: OCR ảnh. | Nêu |
| File chứa tên, SĐT, email, địa chỉ của khách. | Che PII (email, số điện thoại bằng regex; tên, địa chỉ bằng NER) **trước khi gọi AI**. Hiện bản đã che cho nhân viên xem trước. | MVP (regex) |
| SSO tự đăng xuất khi bỏ trống, mất phiên làm dở khi quầy đông. | Tự lưu bản nháp phiên làm việc. Đăng nhập lại thì mở tiếp. | Nêu |

### F1-P2 · Bóc tách dòng (Document Parsing)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| PDF bảng phức tạp hoặc scan: bóc sai, **bỏ sót dòng âm thầm**. | Hiện "Đã đọc N dòng" cùng bản xem trước đã bóc tách, cho **sửa trực tiếp ô** (tên, số lượng, đơn vị) trước khi khớp SKU. Dòng không đọc được hiện cảnh báo, không bỏ qua. | MVP |
| Số lượng và đơn vị viết lẫn ("2x 3m", "pk", "stk"). | Từ điển đơn vị theo ngôn ngữ (DA/NO/SV/EN). Không nhận ra thì gắn cờ vàng thay vì đoán. | MVP (vài đơn vị) |

### F1-P3 · Khớp SKU và độ tự tin (FR-02)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Khớp sai nhưng tự tin cao (≥90%) là lỗi nguy hiểm nhất, vì nhân viên lướt qua dòng xanh. | **Khớp lai:** ngữ nghĩa (embedding) kết hợp quy tắc cứng. Nếu kích thước, cấp độ, độ dày trích được không khớp thông số SKU thì **tự hạ confidence**. | MVP |
| Điểm confidence chưa hiệu chuẩn. | Chạy bộ test có nhãn (50–100 dòng mẫu), đo độ chính xác theo từng ngưỡng rồi mới chốt ngưỡng. Báo cáo kết quả trong video. | MVP |
| Dải 80–90% chưa có trạng thái (vàng <80%, zero-touch >90%). | Chốt **3 trạng thái:** ≥90% xanh (zero-touch); 80–<90% xanh nhạt "kiểm nhanh" (không tính zero-touch); <80% vàng (3 ứng viên + ô tìm). | MVP |
| Khó đối chiếu nhanh dòng xanh. | Mọi dòng hiện thông số chính (kích thước, chiều dài, loại) cạnh SKU. | MVP |

### F1-P4 · Quy đổi đơn vị (FR-03)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Thuộc tính catalog thiếu hoặc sai thì quy đổi sai cả đơn. | **Thiếu thuộc tính thì không quy đổi**, gắn cờ vàng và hiện lý do, không đoán. | MVP |
| Làm tròn lên không đúng cho mọi hàng (hao hụt, pallet, quy cách tối thiểu). | Quy tắc làm tròn **theo nhóm hàng** (cây gỗ, tấm thạch cao, bao xi măng...). Hiện công thức ("120 ÷ 4,8 = 25") và số khách ghi song song. Cho nhân viên nhập % hao hụt (mặc định 0). | MVP (2–3 nhóm) |
| Dòng làm tròn dễ bị bỏ qua. | Biểu tượng cảnh báo, và dòng làm tròn nằm trong nhóm "cần xem" ở bước rà soát. | MVP |

### F1-P5 · Kiểm tra tồn kho (FR-04)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Doc chỉ có Còn/Hết. Thực tế **tồn không đủ số lượng cần** (cần 25, còn 10). | Đối chiếu tồn với số lượng cần: **Đủ / Thiếu một phần (còn X) / Hết**. Thiếu một phần thì đề xuất tách dòng: lấy X và thay thế phần còn lại. | MVP |
| Tồn tổng cửa hàng là on-hand, chưa trừ hàng đã dành cho báo giá khác. | Nhãn "On-hand · cập nhật hh:mm" (NFR-06). Trừ phần **đã giữ trong SiteDesk** (xem F2-P5). | MVP |
| Tồn kho đồng bộ chậm. | Hiện timestamp, quá ngưỡng (ví dụ 15 phút) thì cảnh báo màu. | MVP |

### F1-P6 · Rà soát dòng vàng/đỏ (UC4, human-in-the-loop)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| "30 giây" cho 20–35 dòng là không thực tế (~1 giây/dòng). | **Review theo ngoại lệ:** xếp vàng, đỏ, thiếu hàng, làm tròn lên trên cùng; dòng xanh thu gọn nhưng mở được. Hiện tiến độ "còn 3 dòng cần xem". Điều chỉnh cách nói thành "30 giây cho phần ngoại lệ". | MVP |
| Nhân viên quá tin AI (automation bias). | Dòng vàng **bắt buộc chọn** mới Confirm được. Dòng giá trị lớn hoặc nhạy kích thước luôn nằm trong nhóm "cần xem". | MVP |
| Thao tác chuột chậm khi quầy đông. | Điều hướng bàn phím (↑↓ Enter), theo NFR-04. | MVP |
| Từ điển tự học bị học sai thì nhân lên toàn cửa hàng. | Lưu **theo cửa hàng**, chỉ ghi **sau Confirm**, có nút gỡ, ghi người sửa. Quản lý duyệt khi áp dụng đa cửa hàng. | MVP (lưu cơ bản), Nêu (duyệt) |

### F1-P7 · Gợi ý thay thế (UC2, Alternative Engine)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Chỉ lọc theo spec, UC2 lại nói "giá tương đương". | Hiện **chênh lệch giá** (đơn giá và tổng), sắp xếp theo gần giá gốc nhất. | MVP |
| Mã thay thế cũng có thể thiếu hàng. | Chỉ gợi ý mã **còn đủ số lượng cần**. | MVP |
| Hàng có chứng nhận (chịu lửa, cấp tải C24, yêu cầu dự án). | Gắn cờ nhóm "cần khách xác nhận"; nhân viên luôn hỏi khách trước khi đổi (đã có trong UC2). | MVP (cờ) |
| Không biết vì sao khách từ chối thì khó đạt KPI 30%. | Khi không chọn mã thay thế, ghi **lý do** (giá, thương hiệu, spec...) vào telemetry. | MVP |

### F1-P8 · Confirm và đẩy POS/ERP (UC3, FR-05)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| ERP cũ có thể không có API ghi. | Local Connector hỗ trợ **2 chế độ trên cùng một payload:** API push và file export (CSV/JSON). CSV được coi là chế độ chuẩn, không chỉ dự phòng. | MVP (xuất file + endpoint mock) |
| `client_id` bắt buộc, trong khi khách lẻ/mới không có mã. | Cho phép **mã khách vãng lai**. Có ô tra cứu `client_id` từ ERP (mock). | MVP (mock) |
| Bấm Confirm hai lần sinh đơn trùng; mất mạng giữa chừng. | Confirm **idempotent** theo `order_session_id`. Hiện trạng thái push; lỗi thì tự chuyển CSV. Sau Confirm, đơn **khóa chỉ đọc**; sửa thì tạo phiên bản mới. | MVP |
| Chỉ có tồn kho đủ, thiếu giá. | Payload có chỗ cho giá, có thể để trống ở MVP. | Nêu |

### F1-P9 · Sau đơn: log, dữ liệu, KPI (FR-07, NFR-02)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| "Xóa file gốc sau Confirm" mâu thuẫn với "ghi log nguyên văn" (EU AI Act) và báo giá lưu nhiều ngày. | Tách **2 lớp dữ liệu:** (1) file gốc và văn bản thô → xóa sau Confirm hoặc khi báo giá hết hạn; (2) log quyết định (SKU, confidence, hành động, thời gian) → giữ, **chỉ chứa văn bản đã che PII**. | MVP |
| "Zero PII" quá mạnh vì `client_id` gắn được về một khách. | Diễn đạt lại: "**Không gửi PII cho AI**; hệ thống lưu mã khách đã giả danh (pseudonymised)". | MVP (câu chữ) |
| KPI 12 phút → dưới 2 phút chưa có baseline. | Telemetry đo thời gian upload → Confirm; baseline đo thủ công ở cửa hàng pilot. Trong MVP gọi là "kết quả demo", không phải số liệu đã chứng minh. | MVP |

---

## LUỒNG 2: PRE-ORDER / ADVANCE QUOTE (UC5)

```
F2-P1 Nhận email → P2 Xử lý → P3 Lưu báo giá → P4 Gửi khách → P5 Chuẩn bị hàng → P6 Mở lại lúc nhận → P7 Confirm & push
```

### F2-P1 · Nhận email trước (07:00)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Email có chữ ký, chuỗi trích dẫn, tên khách lẫn vào danh sách. | Bước làm sạch: tách phần thân danh sách, bỏ chữ ký và phần trích dẫn, che PII. Hiện phần bị loại để nhân viên kiểm. | MVP |
| Nhân viên phải dán tay 35 dòng. | Giữ dán tay ở MVP (đúng UC5). Hướng phát triển: đọc hộp thư dùng chung. | Nêu |

### F2-P2 · Bóc tách, khớp mã, kiểm tra tồn kho

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Lặp lại logic Luồng 1. | **Dùng chung toàn bộ F1-P2 → P7**, không làm lõi thứ hai. Chỉ khác ở bước kết thúc. | MVP |
| Lúc 14:00 muốn biết dòng nào là tồn kho tại thời điểm lưu. | Lưu **ảnh chụp** tồn kho và giá tại lúc lưu (snapshot) và "ngày cần hàng". | MVP |

### F2-P3 · Lưu báo giá (FR-06)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Hai nguồn sự thật nếu ERP cũng có báo giá. | Quote ID sinh trong SiteDesk (`BG-DK-0457`). Có trường **`erp_quote_ref` tùy chọn** để đối chiếu với số báo giá ERP. Báo giá SiteDesk là bản làm việc; đơn thật chỉ tồn tại khi đẩy ERP ở F2-P7. | MVP |
| Không có vòng đời, ca khác nhận không biết đang ở bước nào. | Trạng thái: **Draft → Sent → Confirmed → Prepared → Collected / Expired**. Ghi người tạo, ghi chú bàn giao, version mỗi lần sửa. | MVP |
| Khách lẻ không có `client_id`. | Gắn mã vãng lai hoặc tên liên hệ do nhân viên nhập (không đưa vào AI). | MVP |
| Hạn hiệu lực. | Mặc định ví dụ 7 ngày (cấu hình được). Hết hạn tự chuyển Expired. | MVP |

### F2-P4 · Xuất PDF gửi khách

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Khách hiểu báo giá là đã giữ hàng. | PDF ghi rõ: "Tồn kho và giá có hiệu lực đến `<ngày>`; hàng chỉ được giữ sau khi xác nhận". | MVP |
| PDF dính thông tin cá nhân. | Tên khách do nhân viên điền ở bước xuất, không đi qua AI. | MVP |

### F2-P5 · Chuẩn bị hàng và phiếu soạn

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| **Soạn hàng không giữ chỗ**: hàng đã bốc ra khỏi kệ nhưng hệ thống vẫn thấy còn, có thể bán cho người khác. | **Sổ giữ chỗ trong SiteDesk (reserved ledger):** bấm [Chuẩn bị hàng] thì số lượng được giữ, trừ vào tồn hiển thị cho mọi phiên SiteDesk khác; hết hạn thì tự nhả. Giới hạn cần nêu rõ: không chặn được bán trực tiếp qua POS. Bước sau: ghi giữ chỗ vào ERP. | MVP (sổ trong DB) |
| Nhóm phiếu theo danh mục, không có vị trí kệ. | Giữ nhóm theo danh mục (đúng doc), sắp xếp theo mã. In kèm Quote ID, giờ hẹn, ghi chú "đã giữ trong SiteDesk". Vị trí kệ là hướng phát triển khi có dữ liệu. | MVP |
| Nhân viên kho (actor phụ) không có cách phản hồi. | Màn hình tối giản: tick từng dòng "đã soạn", ghi dòng thiếu; trạng thái → Prepared, báo lại nhân viên quầy. | MVP nếu kịp, ngược lại Nêu |

### F2-P6 · Mở lại báo giá lúc khách đến (14:00)

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Kiểm tra lúc khách đứng trước quầy thì muộn, trái mục tiêu "không phải chờ". | Ngoài kiểm tra khi mở lại (đúng doc), thêm **kiểm tra theo lịch**: danh sách báo giá trong ngày có badge "có thay đổi" khi tồn kho/giá lệch snapshot. | MVP (kiểm khi mở + badge) |
| Dòng đổi khó thấy. | Tô sáng dòng đổi, hiện "trước → sau" (tồn, giá). Dòng mới hết hàng tự gọi lại Alternative Engine. | MVP |
| Chưa có nguồn giá để kiểm tra giá. | Ở MVP so sánh tồn kho thật; giá lấy từ catalog mẫu. Nguồn giá thật (PIM/ERP, giá theo khách) là bước sau. | Mô phỏng (giá), Nêu |

### F2-P7 · Xác nhận và đẩy ERP

| Bất cập | Giải pháp | Phạm vi |
|---|---|---|
| Khách lấy một phần hoặc không đến. | Cho tách đơn khi lấy một phần. Không đến thì **Expired** và nhả giữ chỗ. | MVP |
| Giống F1-P8 (idempotent, CSV chuẩn). | Dùng lại nguyên Local Connector của Luồng 1. Payload thêm `quote_id`. | MVP |

---

## MÂU THUẪN CHUNG CẦN CHỐT

| Vấn đề | Đề xuất |
|---|---|
| Nhà cung cấp LLM: slide cam kết EU/EEA, code hiện dùng OpenAI. | Chọn một nhà cung cấp EU qua AI Gateway cho MVP, hoặc nói rõ OpenAI là tạm thời cho demo kèm lộ trình đổi. |
| Vector index đặt ở đâu. | Chọn pgvector trong PostgreSQL (ít container hơn) hoặc FAISS/Chroma riêng. |
| Thêm thị trường chỉ cần Connector mới, Core không đổi. | Thêm câu: mỗi ngôn ngữ cần đánh giá lại độ chính xác và từ điển trước khi mở thị trường. |
| Con số 12 phút, 30%, 70%. | Trình bày là mục tiêu và giả định (A1–A7), không phải kết quả đã chứng minh. |

---

## CHECKLIST CHO MVP ROUND 2

**Nên có trong demo (Luồng 1):**
- [ ] Bản xem trước bóc tách, có "đã đọc N dòng"
- [ ] Khớp lai + 3 trạng thái confidence
- [ ] Quy đổi đơn vị (gỗ, thạch cao) có công thức và cảnh báo làm tròn
- [ ] Trạng thái Đủ / Thiếu một phần / Hết
- [ ] Review theo ngoại lệ, điều hướng bàn phím
- [ ] Thay thế có chênh lệch giá và cờ nhóm cần xác nhận
- [ ] Confirm idempotent, xuất CSV/JSON (mock POS)
- [ ] Log đã che PII

**Nên có nếu kịp (Luồng 2):**
- [ ] Lưu báo giá với trạng thái và snapshot
- [ ] Sổ giữ chỗ trong SiteDesk
- [ ] Mở lại báo giá, tô sáng dòng đổi

**Chỉ nêu trong video ("Known limitations & next steps"):** OCR ảnh, đọc email tự động, SSO và tự lưu nháp, ghi giữ chỗ vào ERP, nguồn giá theo khách, vị trí kệ.

---

## ĐIỂM CẦN CHỐT TRƯỚC KHI VẼ SYSTEM DIAGRAM

1. LLM dùng nhà cung cấp nào (OpenAI hay EU)?
2. Vector index: pgvector hay FAISS/Chroma?
3. POS mock ở mức nào: chỉ xuất file hay có endpoint mock?
4. Có làm sổ giữ chỗ trong SiteDesk không? (nếu có, thêm bảng `reservations` vào Container diagram)
