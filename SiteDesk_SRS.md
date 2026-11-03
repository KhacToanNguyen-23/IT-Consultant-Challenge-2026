# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)
## Dự án: SiteDesk – Trợ lý Web Hỗ trợ Tiếp nhận Đơn & Bán hàng tại Quầy
**Đơn vị mục tiêu:** Company A (Chuỗi bán lẻ vật liệu xây dựng Đan Mạch – Na Uy – Thụy Điển)  
**Nền tảng vận hành:** Ứng dụng Web (Web-based Tool) chạy trực tiếp trên trình duyệt máy tính sẵn có tại quầy bán hàng.  
**Người dùng chính:** Nhân viên bán hàng tại quầy (Sales Desk / Trade Counter Associate).

---

## 1. MỤC TIÊU & PHẠM VI THỰC TẾ (Project Scope)

### 1.1. Tình huống thực tế tại cửa hàng (Pain Point)
Khách hàng (cả thợ thầu B2B lẫn người tiêu dùng B2C mua số lượng lớn để sửa nhà) thường mang theo hoặc gửi trước một danh sách vật tư dài (file PDF báo giá, file Excel, hoặc danh sách liệt kê qua email).
* **Hiện trạng thủ công (Manual):** Nhân viên phải mở hệ thống POS/ERP cũ, đọc từng dòng của khách rồi gõ tìm kiếm thủ công từng mã SKU, kiểm tra xem cửa hàng còn hàng không. Mất nhiều thời gian, dễ nhầm quy cách, và khách phải đứng chờ lâu.
* **Vận hành không đồng nhất (Inconsistent):** Khi một món hàng bị hết, nhân viên có kinh nghiệm sẽ biết tư vấn món khác thay thế; nhân viên mới thì không biết tra cứu thông số kỹ thuật tương đương ở đâu dẫn đến việc báo hết hàng và mất đơn.

### 1.2. Giải pháp SiteDesk
SiteDesk là một **Web Tool nội bộ gọn nhẹ**, hoạt động như một "màn hình phụ" hỗ trợ nhân viên tại quầy:
1. **Đọc danh sách tự động:** Nhân viên tải file (PDF/Excel) hoặc dán (Paste) nội dung danh sách của khách vào Tool.
2. **AI khớp mã SKU:** AI đọc hiểu tên vật tư (bằng tiếng địa phương) và tự động điền sẵn mã sản phẩm (SKU) tương ứng trong danh mục của công ty.
3. **Kiểm tra tồn kho & Gợi ý thay thế:** Báo ngay món nào cửa hàng đang còn, món nào hết. Nếu hết, AI gợi ý 1-2 mã tương đương kỹ thuật có sẵn trong kho để nhân viên tư vấn ngay cho khách.
4. **Nhân viên duyệt & Xuất đơn:** Nhân viên kiểm tra lại màn hình trong 30 giây, xác nhận với khách, rồi bấm nút xuất dữ liệu sang hệ thống cũ (hoặc in báo giá).

---

## 2. KIẾN TRÚC PHẦN MỀM: CORE & CONNECTOR (Pragmatic Architecture)

Kiến trúc được tối giản hóa thực tế, không dùng thuật ngữ trừu tượng quá mức:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SITEDESK CORE (BỘ MÁY DÙNG CHUNG)                    │
│  - Document Parsing Engine: Bóc tách danh sách vật tư từ file văn bản. │
│  - Semantic SKU Matcher: Thuật toán AI so khớp tên gọi ra mã SKU chuẩn. │
│  - Alternative Engine: Quy tắc gợi ý sản phẩm thay thế theo thông số. │
└────────────────────────────────────────────────────────────────────────┘
                                    │ (Giao tiếp qua REST API)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                LOCAL CONNECTOR (KẾT NỐI HỆ THỐNG CŨ)                   │
│  - Đọc danh mục sản phẩm (Catalog) và số lượng tồn kho từ ERP/POS cũ.  │
│  - Tùy biến theo từng nước: Đan Mạch (DKK), Na Uy (NOK), Thụy Điển (SEK)│
│  - Giao diện: Web Portal đơn giản, không cần cài đặt phần mềm mới.     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CÁC LUỒNG SỬ DỤNG THỰC TẾ (Core Use Cases)

### Use Case 1: Tự động hóa bóc tách danh sách vật tư (Automated List Intake)
* **Tác nhân:** Nhân viên bán hàng tại quầy.
* **Tình huống:** Khách gửi một file PDF/Excel gồm 20 loại vật tư khác nhau.
* **Các bước thực hiện:**
  1. Nhân viên kéo thả file PDF/Excel vào giao diện SiteDesk trên máy tính.
  2. Hệ thống hiển thị bảng danh sách vật tư đã được AI tự động bóc tách (Tên vật tư, số lượng, đơn vị tính).
  3. AI đối chiếu với Catalog nội bộ và tự động điền mã SKU tương ứng kèm mức độ tự tin (Confidence Score).
  4. Nếu dòng nào AI không chắc chắn (dưới 80%), dòng đó sẽ sáng màu vàng để nhân viên kiểm tra lại bằng mắt.

### Use Case 2: Xử lý hết hàng & Gợi ý sản phẩm thay thế (Stockout & Substitution)
* **Tác nhân:** Nhân viên bán hàng tại quầy & Khách hàng.
* **Tình huống:** Trong 20 món khách đặt, có 2 món kho của cửa hàng báo số lượng tồn bằng 0.
* **Các bước thực hiện:**
  1. Trên bảng kết quả, 2 món hết hàng hiển thị cảnh báo màu đỏ: *"Hết hàng tại cửa hàng"*.
  2. Ngay bên cạnh, AI hiển thị nút **[Xem gợi ý thay thế]**.
  3. Nhân viên bấm vào, màn hình hiện ra 1-2 sản phẩm có cùng tiêu chuẩn kỹ thuật (kích thước, công năng) nhưng khác thương hiệu/quy cách đang có sẵn trong kho.
  4. Nhân viên hỏi ý kiến khách: *"Mã X đang hết, bên em có mã Y tính năng tương đương giá tương đương, anh lấy mã này nhé?"*.
  5. Khách đồng ý $\to$ Nhân viên bấm chọn mã thay thế.

### Use Case 3: Xác nhận và Xuất đơn hàng (Review & Push to POS)
* **Tác nhân:** Nhân viên bán hàng tại quầy.
* **Tình huống:** Hoàn tất việc rà soát danh sách sản phẩm.
* **Các bước thực hiện:**
  1. Nhân viên rà soát lần cuối toàn bộ bảng danh sách (Human-in-the-loop).
  2. Nhân viên bấm nút **"Xác nhận đơn hàng" (Confirm Order)**.
  3. Hệ thống trả về file định dạng chuẩn (CSV/JSON) hoặc tự động đẩy đơn qua API vào hệ thống POS/ERP cũ của cửa hàng để tiến hành thanh toán hoặc xuất phiếu xuất kho.

---

## 4. YÊU CẦU CHỨC NĂNG (Functional Requirements - FR)

* **FR-01 (Xử lý tài liệu):** Cho phép tải lên file định dạng PDF, Excel (.xlsx/.csv) hoặc dán trực tiếp đoạn văn bản thô vào ô nhập liệu.
* **FR-02 (So khớp SKU):** Sử dụng thuật toán tìm kiếm ngữ nghĩa (Vector Search / Embeddings) để map tên gọi tự do của khách với mã SKU chính thức trong catalog.
* **FR-03 (Kiểm tra tồn kho đơn giản):** Hiển thị trạng thái tồn kho ở mức cơ bản: **Còn hàng (In Stock)** hoặc **Hết hàng (Out of Stock)** dựa trên số lượng tồn tổng của cửa hàng (không cần dữ liệu vị trí ngăn kệ).
* **FR-04 (Gợi ý thay thế):** Khi một SKU hết hàng, hiển thị danh sách tối đa 2 SKU thay thế tương đương dựa trên các thuộc tính kỹ thuật chung.
* **FR-05 (Xuất dữ liệu):** Xuất danh sách đơn hàng hoàn chỉnh ra định dạng chuẩn để đồng bộ vào hệ thống bán hàng hiện có.

---

## 5. YÊU CẦU PHI CHỨC NĂNG (Non-Functional Requirements - NFR)

* **NFR-01 (Chi phí bảo trì & Vận hành siêu rẻ):**
  * Không yêu cầu mua thêm bất kỳ phần cứng nào (tận dụng 100% máy tính quầy hiện có).
  * Chạy trên nền tảng Web nhẹ (React/Next.js cho Frontend, Python FastAPI cho Backend).
* **NFR-02 (Bảo mật & Chủ quyền dữ liệu - Sovereign AI):**
  * Không lưu trữ thông tin cá nhân của khách hàng (PII) trên máy chủ AI.
  * AI chỉ đọc hiểu văn bản danh mục vật tư kỹ thuật công khai.
* **NFR-03 (Tốc độ):** Thời gian phân tích và khớp một danh sách 20 mặt hàng không quá **3 giây**.
* **NFR-04 (Dễ sử dụng):** Giao diện trực quan dạng bảng tính (Spreadsheet-like UI), nhân viên chỉ mất 5 phút hướng dẫn là dùng được ngay.

---

## 6. PHẠM VI CODE DEMO CHO ROUND 2 (MVP Scope - Khả thi 100%)

Trong 2-3 tuần của Round 2, team chỉ cần code đúng **1 trang Web duy nhất** với các chức năng:
1. **Nửa trên màn hình:** Ô kéo thả file PDF đơn hàng mẫu (danh sách 5-10 loại vật liệu xây dựng).
2. **Nửa dưới màn hình:** Bảng kết quả sau khi bấm "Phân tích":
   * Cột 1: Tên gốc khách ghi.
   * Cột 2: Mã SKU + Tên sản phẩm chính thức mà AI đã tìm thấy.
   * Cột 3: Trạng thái tồn kho (Xanh: Còn hàng | Đỏ: Hết hàng).
   * Cột 4: Nút bấm hiển thị mã thay thế nếu bị Đỏ.
   * Góc dưới: Nút "Tạo đơn hàng".

---

## 7. PHÂN CHIA NHIỆM VỤ TRONG NHÓM

* **Kỹ sư phần mềm (SE - Lead Dev):** 
  * Dựng giao diện Web (React/Tailwind) trực quan, gọn nhẹ.
  * Viết Backend API tiếp nhận file và kết nối luồng dữ liệu giữa AI và giao diện.
* **Kỹ sư Trí tuệ nhân tạo (AI):** 
  * Viết script dùng OCR/LLM để bóc tách văn bản từ file PDF.
  * Cài đặt cơ sở dữ liệu vector nhẹ (FAISS / ChromaDB) nạp sẵn 100-200 mã vật liệu mẫu để làm tính năng so khớp SKU và tìm hàng thay thế.
* **Hệ thống thông tin (HTTT / Business Analyst):** 
  * Chuẩn bị tập dữ liệu mẫu (1 file PDF đơn hàng mẫu thực tế + 1 file Excel danh mục 100 sản phẩm vật liệu).
  * Viết phần thuyết minh Business Impact, tính ROI và hoàn thiện 10 slide cho Round 1.
