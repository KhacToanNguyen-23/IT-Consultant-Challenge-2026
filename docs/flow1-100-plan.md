# Plan hoàn thiện 100% Flow 1 theo SRS

Lập 2026-11-06. Căn cứ: `docs/SiteDesk_MVP_SRS.md` v2.0 (đã đối chiếu khớp với `SiteDesk_MVP_SRS_v2.pdf`), đề Round 2, và kiểm tra chạy thật hôm nay.
Mốc: **khóa code 08/11 · nộp 09/11 trước 22:00 GMT+7.** Chi tiết bám đề xem `docs/round2-plan.md`, kết quả kiểm tra xem `docs/flow1-audit-and-plan.md`.

> **Cập nhật trạng thái 2026-11-07:** các bảng công việc bên dưới là snapshot lập kế hoạch ban đầu ngày 06/11, không phải trạng thái code hiện tại. Dẫn chứng mới nằm trong [`flow1-traceability.md`](flow1-traceability.md): backend 217/217 test và live acceptance 33/33; còn nghiệm thu UI chỉ-bàn-phím/accessibility và D22 human review chưa hoàn tất.

## 0. "100%" nghĩa là gì ở đây

1. Cả **30 yêu cầu** FR (001–021, 029–037) và **7 NFR** có bằng chứng chạy được hoặc test, theo đúng tiêu chí chấp nhận trong SRS.
2. **API khớp mục 7** của SRS (endpoint, mã lỗi, hợp đồng JSON). Chỗ nào cố ý khác thì ghi thành giới hạn có chủ đích.
3. Đủ 7 loại test theo **mục 11.2** và các ô trong **checklist trước quay 11.4**.
4. Có bảng truy vết FR → test → cảnh demo để giám khảo và người pitching Vòng 3 kiểm được.

**Ngoại lệ phải nói thật:** NFR-005 (≤2% khớp sai band cao) **không thể tuyên bố đạt** trong Round 2. SRS cấm khi dưới 150 dòng (hiện 98 dòng, 0 dòng được người duyệt). "100%" cho yêu cầu này nghĩa là: có báo cáo trung thực "kết quả ban đầu trên N dòng", đã có người duyệt nhãn, và **không** claim đạt.

## 1. Bảng yêu cầu → việc cần làm

Ký hiệu: ✔ đã chạy được, ◐ một phần, ✘ chưa có. Cột "Việc" trỏ tới mã công việc ở mục 2.

| ID | Ưu tiên | Hiện trạng | Còn thiếu | Việc |
|---|---|---|---|---|
| FR-001 | P0 | ◐ | PDF hỏng trả 500 (phải 422); XLSX/email chưa test; chưa có giới hạn số dòng/số trang/chọn sheet (OI-04) | B1, B2 |
| FR-002 | P0 | ✔ | Thêm test e2e: `raw_customer_input` trong payload đã mask (OI-13) | B19 |
| FR-003 | P0 | ✔ | Test tự động cho "AI lỗi → tạo dòng → chọn SKU → Confirm" | B12 |
| FR-004 | P1 | ◐ | UI "Đã đọc N dòng", sửa tên/số lượng/đơn vị, lưu bền; hợp đồng PATCH lệch SRS (không có `version`, `requires_reanalysis`) | U2, B18 |
| FR-005 | P0 | ✔ | — | — |
| FR-006 | P0 | ✔ | Thêm test golden attrs + provenance cho 5 nhóm | B6 |
| FR-007 | P0 | ◐ | Hàng ngoài catalog vẫn nhận gợi ý REVIEW (`skruer`, `blahblah`) | B4 |
| FR-008 | P0 | ✔ | Bổ sung dòng trap vào D22 | B4 |
| FR-009 | P0 | ✔ | — (đã có test biên 0.90 và gap) | — |
| FR-010 | P0 | ✔ | UI "exceptions first", blocker nêu số dòng | U2 |
| FR-011 | P0 | ◐ | Thiếu `förp`, `løpemeter`, `lpm`, `linear metre`, `sheet`, `palle`, `pall`, `pallet`; quy tắc `m` không đoán | B3 |
| FR-012 | P0 | ✔ | Test 60/2.88→21 và 120/4.8=25 (SRS nêu đích danh) | B11 |
| FR-013 | P0 | ✔ | — | — |
| FR-014 | P0 | ◐ | UI luôn hiện nhãn tồn kho và giờ cập nhật; trường hợp POS lỗi lúc phân tích (tồn không rõ) cần test | U2, B24 |
| FR-015 | P0 | ✔ | Test ≤2 thay thế, sắp theo chênh giá; cả ca "không có thay thế an toàn" | B11 |
| FR-016 | P0 | ✔ | UI chấp thuận/từ chối kèm lý do | U3 |
| FR-017 | P0 | ✔ | UI chọn khách hiện có hoặc walk-in, payload không PII | U3 |
| FR-018 | P0 | ✔ | Test Confirm đồng thời hai request chỉ tạo một đơn | B23 |
| FR-019 | P0 | ✔ | UI CSV nổi bật khi POS lỗi | U4 |
| FR-020 | P0 | ◐ | Chưa có contract test cho payload slide 9 và CSV | B11 |
| FR-021 | P2 | ✘ | Bảng `store_dictionary` chưa có code ghi/gỡ; thiếu `DELETE /store-dictionary/{id}` | B7 |
| FR-029 | P1 | ✔ | Test e2e: các event chính được ghi, không PII | B19 |
| FR-030 | P0 | ✔ | Ghi p50/p95, tách warm/cold, ghi phần cứng | B15 |
| FR-031 | P2 | ◐ | 2 truy vấn của SRS chạy được, chưa đóng gói, chưa test chia cho 0 | B9 |
| FR-032 | P2 | ✘ | Thiếu `POST /auth/login`, `/auth/logout`, trang `/login`, idle 300 giây, nhãn "Mock SSO" | B8, U5 |
| FR-033 | P0 | ✔ | UI đúng chế độ, không lộ secret | U1, B12 |
| FR-034 | P1 | ◐ | Chưa có test "provider giả, đổi env không đổi UI" | B10 |
| FR-035 | P0 | ✔ | Chạy lại validator (60–80 SKU, đủ 5 nhóm, có ca không thay thế) | B21 |
| FR-036 | P0 | ✔ | UI dùng đúng một enum trạng thái, không tạo cơ chế song song | U2 |
| FR-037 | P0 | ✔ | — | — |
| NFR-001 | P0 | ✔ | Smoke "fresh install" 15 phút | B21 |
| NFR-002 | P0 | ◐ | UI ghi rõ giới hạn che PII; không gọi mock login là SSO thật | U1, U5 |
| NFR-003 | P0 | ◐ | p50 ≈ 209 ms trên 20 dòng, nhưng cần ≥20 lần, tách cold/warm, ghi phần cứng | B15 |
| NFR-004 | P1 | ✘ | Test chỉ bằng bàn phím; accessibility không lỗi critical | U4, U6 |
| NFR-005 | P0 | ✘ (không thể claim) | Người duyệt 98 nhãn; chạy lại báo cáo; ghi "kết quả ban đầu" | B16 |
| NFR-006 | P0 | ✔ | Test fault R1–R8 | B12 |
| NFR-007 | P0 | ◐ | Test provider giả; LLM chỉ cấu hình qua env | B10 |

## 2. Danh sách công việc

**Phụ trách:** T = Toàn, C = Codex (UI), H = BA/HTTT, A = AlecVOV. Ước lượng giờ chỉ là phỏng đoán thô để xếp thứ tự.

### Backend và tài liệu (T)

| Mã | Việc | Giờ | Nghiệm thu |
|---|---|---|---|
| B1 | PDF hỏng/lạ → 422, thêm handler lỗi chung trả `{error:{code,message,request_id}}`, không bao giờ 500 trần | 1,5 | Test upload PDF hỏng, tệp lạ; log không còn traceback do đầu vào xấu |
| B2 | Giới hạn: số dòng, số trang PDF, chọn sheet XLSX (chốt OI-04, ghi vào tài liệu); test XLSX/CSV/email | 2 | Test từng định dạng + vượt giới hạn trả 413/422 |
| B3 | Từ điển đơn vị đủ §15.2; quy tắc `m`; thống nhất `sheet`/`board`; `pallet` ánh xạ được, quy đổi bị chặn có lý do nếu thiếu dữ liệu | 2 | Bảng test §15.2 pass; fixture `m` gắn cờ review |
| B4 | Hàng ngoài catalog không được gợi ý (sàn điểm/điều kiện từ vựng → band NONE); thêm dòng trap vào D22 **không chỉnh ngưỡng sau khi xem kết quả** | 3 | `skruer`, `blahblah` → NONE; trap lines = 0 trong báo cáo |
| B5 | `Moisture board 12.5mm` khớp đúng `MR-125`/`MR-125-B` | 1 | E046 pass |
| B6 | Test golden attrs 5 nhóm; kiểm tra thứ tự chip theo §15.3, tối đa 4 chip | 2 | Test từng nhóm |
| B7 | **FR-021:** ghi `store_dictionary` sau Confirm (theo cửa hàng, boost ≤0,20, unique), `DELETE /store-dictionary/{id}` đặt inactive, dùng boost lúc khớp | 3 | Trước Confirm không ghi; sau Confirm có; gỡ thì inactive |
| B8 | **FR-032:** `/auth/login`, `/auth/logout`, 2 tài khoản demo (hash, không ghi mật khẩu vào repo), cookie, `idle_timeout_seconds=300`; cờ `AUTH_REQUIRED` mặc định tắt để không phá Flow 2 | 3 | Đăng nhập/đăng xuất được; 401 khi bật cờ; có test |
| B9 | **FR-031:** `backend/sql/kpi.sql` (3 truy vấn của SRS) + test chia cho 0 | 1 | Chạy trên seed, không lỗi chia 0 |
| B10 | **FR-034/NFR-007:** test provider embedding/LLM giả; đổi env không đổi UI; đổi embedding → reindex | 2 | Test pass |
| B11 | Contract test: payload slide 9, CSV (BOM, dấu `;`, chống formula injection), Core↔mock-pos; 120/4.8=25, 60/2.88→21; thay thế ≤2 | 3 | Bộ test pass |
| B12 | Test fault R1–R8 (model chưa nạp, embedding lỗi, LLM timeout/JSON hỏng, POS chậm/503, DB lỗi, đổi toggle giữa phiên) | 4 | Bộ test pass; không 500 |
| B15 | Báo cáo hiệu năng: ≥20 lần, p50/p95, tách warm/cold, ghi phần cứng, ghi embedding provider | 1 | Có `backend/reports/` mới |
| B16 | D22: người duyệt 98 nhãn (**H**), chạy lại báo cáo, ghi "kết quả ban đầu trên N dòng", không claim NFR-005 | 3 (người) | Cờ `reviewed` đủ; câu chữ trung thực |
| B18 | Chốt hợp đồng: ingest/PATCH trả toàn bộ session view (SRS mẫu trả `rows`/`version`). Ghi là mở rộng có chủ đích hoặc bổ sung trường | 1 | Tài liệu cập nhật |
| B19 | Test e2e: PII không rời Core, `raw_customer_input` đã mask, event chính được ghi không PII, nguồn bị xóa sau Confirm | 2 | Test pass |
| B21 | `conftest.py` (bỏ gõ `DATABASE_URL` tay), ESLint cấu hình, sửa README (cổng 3001, số test, bỏ nhánh cũ), chặn trường lạ trong body, quét secret, smoke 15 phút trên Compose mới | 3 | Lệnh trong SRS 12.3 chạy hết; log sạch |
| B23 | Test Confirm đồng thời | 1 | Chỉ một đơn |
| B24 | POS lỗi lúc phân tích → tồn "không rõ" có nhãn; Confirm vẫn được | 1 | Test pass |
| B25 | Kịch bản chấp nhận tự động `scripts/acceptance_flow1.py` (gộp các phép thử tay hôm nay), chạy được trên stack thật, dùng cho tag `demo-ok-N` | 2 | Chạy xanh |
| B26 | Bảng truy vết `docs/flow1-traceability.md`: FR → test → cảnh demo; mục "Known limitations" theo §14 | 2 | Đủ 37 dòng |

### UI Flow 1 (C, theo 4 PR đã chốt)

| Mã | PR | Nội dung | Phủ yêu cầu |
|---|---|---|---|
| U1 | PR1 ✔ | Nhập đơn `/counter`, ghi chú giới hạn PII, banner AI/POS | FR-001, 002, 033, NFR-002 |
| U2 | PR2 | Bảng rà soát: dòng ngoại lệ trước nhưng không ẩn dòng ổn, "Đã đọc N dòng", sửa dòng, nhãn tồn kho + giờ cập nhật, chip ≤4, đúng enum trạng thái, blocker nêu số dòng | FR-004, 010, 014, 036 |
| U3 | PR3 | Thay thế (đồng ý/từ chối + lý do), chọn khách hiện có hoặc walk-in | FR-015, 016, 017 |
| U4 | PR4 | Confirm, kết quả `POS_ACCEPTED`/`NEEDS_MANUAL`, tải CSV nổi bật, phím tắt, ô tìm SKU thủ công luôn dùng được khi AI lỗi | FR-019, NFR-004, 006 |
| U5 | PR5 (nếu làm B8) | Trang `/login` nhãn "Mock SSO", idle notice, đăng xuất | FR-032, NFR-002 |
| U6 | PR4 | Kiểm tra chỉ bằng bàn phím + accessibility không lỗi critical | NFR-004 |

### Người (H, A)
- **H:** duyệt nhãn D22 (B16); AI Journal ra PDF với chứng cứ bác bỏ/sửa output AI; User Journey, System Diagram theo bản build; duyệt câu chữ cảnh báo giá/tồn (OI-20).
- **A:** trả lời `sheet`/`board`; giữ Flow 2 chạy khi tôi đụng `parser`/`models`; xác nhận cờ `AUTH_REQUIRED` không ảnh hưởng.

## 3. Thứ tự và lịch

Tổng ước lượng backend khoảng **40 giờ** cộng UI. Một người không làm hết trong 2 ngày, nên chia làm 3 bậc, làm theo thứ tự:

| Bậc | Gồm | Vì sao |
|---|---|---|
| **1 (bắt buộc, P0)** | B1–B6, B11, B12, B15, B16, B19, B21, B23–B25; U1–U4, U6 | Là FR/NFR P0 và là phần giám khảo thấy trực tiếp |
| **2 (nên có, P1)** | B10, B18, B26 | Bằng chứng kiến trúc và truy vết |
| **3 (P2, SRS cho phép cắt)** | B7 (FR-021), B8 + U5 (FR-032), B9 (FR-031) | Làm sau cùng; nếu trễ thì ghi vào "Known limitations" |

| Ngày | Việc |
|---|---|
| **06/11** | Bậc 1: B1, B2, B3, B4, B5, B21; Codex làm U2 |
| **07/11** | Bậc 1 còn lại: B6, B11, B12, B19, B23, B24; Codex làm U3; Bậc 2: B10, B18; B16 (người duyệt) hoàn tất |
| **08/11 khóa code** | B15, B25, B26; Codex làm U4 + U6; Bậc 3 chỉ làm nếu đã xong hết; chạy smoke 15 phút, tag `demo-ok-N`; chỉ sửa lỗi |
| **09/11** | Dự phòng; không code mới |

Việc nào không kịp bậc 3 thì ghi trung thực vào "Known limitations" và nói trong video, đúng thứ tự cắt của SRS (dòng 42–47).

## 4. Điều kiện hoàn thành (Definition of Done)

- [ ] `pytest` xanh bằng một lệnh; có đủ unit, contract, integration, fault, security, E2E, performance.
- [ ] `scripts/acceptance_flow1.py` chạy xanh trên Compose mới (`down -v` rồi `up --build`), log không lỗi.
- [ ] Mọi dòng trong bảng truy vết có test hoặc cảnh demo.
- [ ] Hai fail toggle đạt và reset được; chế độ AI lỗi, POS lỗi, cả hai đều hoàn tất Confirm.
- [ ] D22 có người duyệt, báo cáo ghi n, phần cứng, cấu hình, không claim NFR-005.
- [ ] Không secret trong repo, tài liệu, ảnh, video.
- [ ] README đúng với bản chạy thật.

## 5. Rủi ro và điều phải quyết

- **Thời gian:** bậc 3 gần như chắc chắn không đủ nếu chỉ một người làm. Có thể giao B-series độc lập cho Codex chạy song song trên worktree riêng, nhưng cần duyệt từng PR.
- **Vùng dùng chung:** `parser.py`, `models.py` và cờ `AUTH_REQUIRED` ảnh hưởng Flow 2; cần AlecVOV biết trước.
- **Điểm cần bạn chốt:** (1) `sheet` hay `board`; (2) quy tắc `m`; (3) Alembic (đề xuất bỏ); (4) có làm FR-032 và FR-021 hay ghi vào giới hạn.
