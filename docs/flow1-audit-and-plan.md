# Flow 1: kiểm tra so với SRS và kế hoạch tối ưu điểm

Kiểm tra ngày 2026-11-06 trên `main` (87366f3) chạy Docker thật, DB sạch. Mốc SRS: **khóa code 08/11, nộp 09/11 lúc 22:00**.
Mọi con số dưới đây lấy từ lần chạy thật hôm nay, trừ chỗ ghi rõ là suy đoán.

## 1. Đã đạt (có bằng chứng chạy thật)

| Yêu cầu | Bằng chứng |
|---|---|
| FR-001 upload, 422 cho scan-only | PDF trắng hợp lệ trả 422 `SCAN_ONLY_PDF`; `.xls`/`.exe` trả 422 `UNSUPPORTED_FILE`; file >5 MB trả 413; file rỗng trả 422 |
| FR-002 mask PII | Sau bản vá b61f76d, số điện thoại có ngoặc/ext được che, ngày giữ nguyên |
| FR-005, FR-011..013 | `120 m` / 4.8 = 25; `10 x 4.8m` hiểu là 10 tấm; thiếu thông tin thì chặn, không đoán |
| FR-007..009 | Bộ test biên band, gap, must-match, c18 không bao giờ khớp c24 (đều pass) |
| FR-010 | Confirm bị chặn 409 kèm số dòng |
| FR-014..016, 039 | `MR-125` hết hàng → đề xuất `MR-125-B` → khách chấp thuận → SKU gốc giữ, SKU cuối đổi, trạng thái `CUSTOMER_ACCEPTED`. Từ chối thiếu lý do bị 422 |
| FR-018..020, 037 | Gửi confirm lần hai trả cùng mã tham chiếu, sửa sau confirm bị 409 khóa |
| FR-019 POS lỗi | Rơi sang `NEEDS_MANUAL` + CSV, CSV có chống formula injection |
| FR-029 events | Có `SESSION_CREATED`, `AI_SUGGESTED`, `PARSE_EDITED`, `SKU_KEPT/EDITED`, `SUBSTITUTION_ACCEPTED/REJECTED`, `CONFIRMED`, `POS_ACCEPTED`/`CSV_EXPORTED` |
| FR-031 | 2 truy vấn KPI trong SRS chạy được trên schema thật (chưa lưu thành file) |
| FR-033 | Hai toggle độc lập, AI lỗi chuyển sang chế độ `rules` |
| NFR-003 | 20 dòng phân tích: p50 ≈ 209 ms, tối đa 307 ms (8 lần, đã warm). Mục tiêu 3 s. Báo cáo cũ ghi p95 724 ms |
| FR-035 seed | 62 SKU, 5 nhóm |

Đính chính danh sách trước của tôi: `isolering 100 mm` không ra SKU là **đúng** (catalog không có 100 mm, luật cứng loại các độ dày khác); `processing_time_seconds = 0` không phải lỗi vì kịch bản chạy tức thì và KPI SQL tính từ timestamp; FR-016 và FR-029 đã có.

## 2. Sai hoặc thiếu so với SRS

| # | Vấn đề | Bằng chứng | Mức |
|---|---|---|---|
| A | **PDF hỏng gây 500** thay vì 422 | `PdfReadError: startxref not found` thành `Internal Server Error`; SRS 11.2 có test "unsupported upload" | P0 |
| B | **Từ điển đơn vị thiếu so với §15.2** | Không nhận ra: `förp`, `løpemeter`, `lpm`, `linear metre`, `sheet`, `palle`, `pall`, `pallet`. Bị gắn `missing_unit` (an toàn, nhưng SRS ghi KEEP và yêu cầu §15 fixtures map) | P0 |
| C | **Quy tắc `m`** | SRS: "`m` không đủ context thì không đoán; flag review". Hiện `50 m timber` tự thành `linear_metre`, không cờ | P1 |
| D | **Tên đơn vị lệch SRS** | SRS dùng `sheet`, code dùng `board` | P1 (xác nhận với AlecVOV vì dùng chung) |
| E | **Hàng ngoài catalog vẫn nhận gợi ý** | `10 stk skruer 5x50` gợi ý gỗ 35x70; `blahblah` gợi ý sàn gỗ; cả hai band REVIEW 0.89. Báo cáo đánh giá ghi trap lines = 0, nên bộ trap chưa bao phủ hai dạng này | P0 (ảnh hưởng điểm trung thực của matcher) |
| F | **`Moisture board 12.5mm` khớp sai** sang bảng chống cháy | Là lỗi E046 đã nằm trong báo cáo đánh giá; tiếng Việt/Đan Mạch (`vådrum`, `våtrom`) khớp đúng | P1 |
| G | **D22 chưa được người duyệt** | Báo cáo ghi `labels human-reviewed 0/98`; SRS: chỉ trích dẫn số sau khi đồng đội duyệt từng dòng | P0 (việc của người, không phải code) |
| H | **Bộ test thiếu loại** | Có 51 unit test. Thiếu: contract (Core↔mock-pos, payload slide 9), integration (pgvector, idempotency), E2E, fault (DB lỗi), security (secret scan, upload) | P1 |
| I | Truy vấn KPI chưa là file chạy được | Query chạy được nhưng chưa có `backend/sql/kpi.sql`, chưa test chia cho 0 | P2 |
| J | Cold vs warm chưa tách trong báo cáo hiệu năng | SRS 11.2 yêu cầu tách riêng. Model tải ~32 giây lúc khởi động | P2 |
| K | `README` ghi `password123` | Chỉ là mật khẩu demo local; SRS yêu cầu không để secret trong deliverable | P2 (ghi chú "demo only") |

Không làm (SRS cho phép cắt): FR-021 store dictionary, FR-032 đăng nhập chi tiết, dashboard KPI, highlight nguồn.

## 3. Kế hoạch ưu tiên

Việc dưới đây thuộc phần Flow 1 của Toàn. Backend (A–F) không đụng frontend nên chạy song song với Codex.

**Hôm nay (06/11)**
1. A: PDF hỏng trả 422. Nửa giờ.
2. B + D: bổ sung đơn vị còn thiếu, kèm test theo bảng §15.2. Cần hỏi AlecVOV về `sheet` và `board` vì hai flow dùng chung `parser`.
3. E: ngưỡng chặn gợi ý khi không có category và không trùng từ nào (đưa về band NONE). Thêm 5–10 dòng trap mới vào bộ đánh giá nhưng **không** chỉnh ngưỡng sau khi xem kết quả (SRS 11.1).
4. G: nhờ đồng đội duyệt 98 nhãn. Việc này chạy lâu nhất, nên giao sớm.

**Ngày mai (07/11)**
5. F: sửa `Moisture board` rồi chạy lại báo cáo D22, ghi rõ "kết quả ban đầu trên N dòng, chưa đạt 150 nên không tuyên bố NFR-005".
6. C: quy tắc `m` theo SRS (cân nhắc rủi ro so với lợi ích vì có thể làm demo đông dòng hơn).
7. H: chuyển các kịch bản kiểm tra tay hôm nay thành test E2E, thêm contract slide-9 và test upload.
8. UI Flow 1 (Codex): xong PR 2 (màn rà soát) và PR 3 (thay thế, khách). Kiểm tra nhãn tồn kho, chip tối đa 4/nhóm theo §15.3, chặn Confirm khi còn vàng.
9. Kịch bản demo cố định + tag `demo-ok-1`.

**08/11 (khóa code, chỉ sửa lỗi)**
10. I, J nếu còn thời gian. Chạy smoke 15 phút trên Compose mới (`down -v` rồi `up`). Dựng kịch bản video theo SRS 11.3.

**Kịch bản demo nên chuẩn bị** (đều đã chạy được hôm nay): `120 m timber` (quy đổi 25 tấm), `10 plader gips vådrum 12.5 mm` (hết hàng → thay thế MR-125-B → khách đồng ý), `200 sække cement` (thiếu hàng một phần), dòng thiếu cấp độ bền (bị chặn Confirm), AI lỗi, POS lỗi (CSV).

## 4. Rủi ro lớn nhất
Thời gian: chỉ còn ~2 ngày tới khóa code. Việc thiết kế lại UI Flow 1 và việc người duyệt nhãn D22 là hai đường dài nhất. Nên chốt phạm vi UI ở mức demo-được (PR 1–3) trước khi làm PR 4 và chi tiết phụ.
