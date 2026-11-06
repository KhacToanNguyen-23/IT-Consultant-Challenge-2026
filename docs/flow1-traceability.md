# Flow 1: bảng truy vết yêu cầu → bằng chứng

Cập nhật 2026-11-07 trên workspace đang chạy. Kiểm tra mới nhất: `backend/scripts/acceptance_flow1.py` đạt **33/33** trên stack Compose hiện tại; backend đạt **233 test** với DB tách riêng `sitedesk_test`; frontend `pnpm build` thành công.
Lệnh test đã chạy: `docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg2://postgres:password123@db:5432/sitedesk_test backend pytest -q`. Không chạy `down -v` để tránh xóa DB demo hiện tại.

Ký hiệu: ✔ có test và chạy thật · ◐ chỉ một phần · ✘ chưa có (ghi rõ lý do).

## Yêu cầu chức năng

| ID | Trạng thái | Test tự động | Kiểm tra chấp nhận | Ghi chú |
|---|---|---|---|---|
| FR-001 nhận file, session | ✔ | `test_input_limits` (PDF/XLSX/CSV, giới hạn), `test_errors` (PDF hỏng) | PDF hỏng 422, `.exe` 422, rỗng 422, quá lớn 413, CSV có header | Giới hạn 300 dòng, 20 trang PDF (OI-04 do nhóm chốt) |
| FR-002 che email/điện thoại | ✔ | `test_core` (PII), `test_flow1_contract::contact_details_never_reach...` | "không gộp hoặc mất dòng" | Chỉ regex; tên/địa chỉ không đảm bảo |
| FR-003 AI lỗi vẫn parse | ✔ | `test_flow1_resilience` (AI off, model chưa nạp, embedding lỗi, LLM lỗi) | `NFR-006 AI off` | |
| FR-004 sửa dòng | ◐ | `test_flow1_contract::unknown_body_fields...` (API từ chối body sai) | UI có đếm và sửa tên/qty/unit; chưa có browser E2E | UI đã có trong code; thao tác lưu sau sửa chưa được kiểm chứng trực tiếp trên trình duyệt |
| FR-005 `N x L`, unreadable | ✔ | `test_core` | — | |
| FR-006 trích thuộc tính | ✔ | `test_core`, `test_chips_golden::golden_attributes` | — | |
| FR-007 top-10 vector, alias | ✔ | `test_out_of_catalog`, `test_core` (hard rules) | "hàng ngoài catalog không gợi ý" | Alias boost: không làm (SRS cho phép cắt) |
| FR-008 hybrid, ≤3 ứng viên | ✔ | `test_core::c18_is_never_matched_as_c24` | "C18 không thành C24" | |
| FR-009 band, gap | ✔ | `test_core::band_boundaries`, `gap_rule` | "thiếu cấp độ không vào band cao" | |
| FR-010 exceptions first, chặn Confirm | ✔ (API + code UI) | `test_flow1_resilience` | Acceptance xác nhận blockers chặn Confirm và nêu số dòng | UI sắp xếp ngoại lệ trước; chưa có browser E2E |
| FR-011 từ điển đơn vị | ✔ | `test_units_srs` (31 ca theo §15.2, quy tắc `m`) | "units SRS 15.2" | Tên chuẩn `sheet`; `board` vẫn nhận |
| FR-012 quy đổi, làm tròn lên | ✔ | `test_core::conversion_exact_and_ceil`, `test_flow1_contract::pack_conversion` | "120 m / 4.8 = 25" | 60 m² / 2.88 → 21 |
| FR-013 thiếu dữ liệu thì chặn | ✔ | `test_core::conversion_never_guesses`, `test_units_srs::pallet...` | — | |
| FR-014 tồn kho, nhãn, giờ | ✔ (API + code UI) | `test_flow1_resilience::pos_down_while_analysing` | Acceptance xác nhận nhãn và timestamp cho tồn kho | UI hiện nhãn và thời điểm; chưa có browser E2E |
| FR-015 thay thế ≤2 | ✔ | `test_core::partial_stock_proposes_only_safe_alternatives`, `test_flow1_contract::substitution...` | "chỉ thay thế an toàn" | |
| FR-016 khách chấp thuận mới đổi SKU | ✔ | `test_core::final_sku_only_changes...`, `test_flow1_contract` (reject cần lý do) | "SKU không đổi trước khi khách đồng ý" | |
| FR-017 khách hàng / walk-in | ✔ (API + code UI) | `test_flow1_contract::payload_matches_the_slide_9_contract` | — | UI có chọn khách/walk-in; chưa có browser E2E |
| FR-018 idempotency, khóa chỉ đọc | ✔ | `test_flow1_resilience` (lặp, đồng thời, cùng key, khác key, thiếu key, khóa) | Acceptance: cùng key replay, khác key 409, thiếu key 422 | Confirm yêu cầu header `Idempotency-Key`, truyền key xuống connector/POS |
| FR-019 API/CSV connector | ✔ | `test_flow1_resilience` (503, timeout, cả hai lỗi), `test_flow1_contract::csv_fallback` | "POS off → NEEDS_MANUAL + CSV" | |
| FR-020 payload slide 9 | ✔ | `test_flow1_contract::payload_matches_the_slide_9_contract`, `substitution...` | "payload: original_sku, score null" | |
| FR-021 store dictionary | ✔ (API + code UI) | `test_store_dictionary` (ghi sau Confirm, không ghi thay thế, gỡ, không học lại, boost ≤0,20) | API list/delete; UI `/store-dictionary` hiển thị và yêu cầu xác nhận trước khi ngừng | UI mới được build; chưa có browser E2E |
| FR-029 events | ✔ | `test_flow1_contract::decision_events_cover_the_flow...` | — | Không PII |
| FR-030 thời gian từng bước | ✔ | — | `NFR-003 p50` | `stage_timings` được lưu mỗi lần phân tích |
| FR-031 KPI SQL | ✔ | `test_kpi` (DB rỗng không chia 0, có dữ liệu thật) | — | `backend/sql/kpi.sql`, chạy bằng `python -m scripts.kpi` |
| FR-032 mock login | ✔ (backend) | `test_auth` (băm mật khẩu, token giả mạo/hết hạn, đăng nhập/xuất, không lộ tài khoản, ép đăng nhập khi bật cờ, nhân viên đăng nhập được ghi vào đơn) | `login` trả 401/503 đúng cấu trúc | Mật khẩu chỉ lấy từ `DEMO_PASSWORD`; `AUTH_REQUIRED` mặc định tắt. UI đăng nhập thuộc UI Flow 1 |
| FR-033 hai fail toggle | ✔ | `test_flow1_resilience` | AI off / POS off / cả hai | |
| FR-034 AI Gateway | ✔ | `test_ai_gateway` | — | |
| FR-035 seed 60–80 SKU | ✔ | — | healthy + catalog | 62 SKU, 5 nhóm; validator trong `generate.py` |
| FR-036 một enum trạng thái | ◐ | Dùng enum trạng thái từ API và `StatePill` dùng chung | — | Đã rà source; chưa có browser E2E cho toàn bộ trạng thái |
| FR-037 trạng thái đơn, mã chống trùng | ✔ | `test_flow1_resilience` | "replay cùng mã tham chiếu" | |

## Yêu cầu phi chức năng

| ID | Trạng thái | Bằng chứng |
|---|---|---|
| NFR-001 chạy bằng Docker | ✔ | `docker compose up`; acceptance "stack healthy" |
| NFR-002 che PII, không claim quá mức | ✔ (scope MVP) | Test provider spy + UI copy nêu rõ regex chỉ che email/phone; không gọi mock login là SSO thật. Tên/địa chỉ chưa được đảm bảo che |
| NFR-003 ≤3 s cho 20 dòng | ✔ | `backend/reports/evaluation_2026-11-06.md`: 20 lần warm, p50 179.9 ms, p95 221.9 ms, max 253.1 ms; local WSL2, 16 CPU |
| NFR-004 chỉ bằng bàn phím | ✘ chưa nghiệm thu | Chưa có scripted browser test không dùng chuột hoặc accessibility scan; hiện có native controls/hotkeys nhưng đó chưa phải bằng chứng đạt. Checklist: `docs/flow1-keyboard-acceptance.md`. Browser UI check bị chặn vì automation host không xác định được URL hiện tại |
| NFR-005 ≤2% khớp sai band cao | ✘ không thể claim | 98 dòng (<150) và **0/98 nhãn được người duyệt**. 0/63 sai ở band cao, cận trên 95% = 5,75%. Chỉ được ghi "kết quả ban đầu" |
| NFR-006 AI/POS lỗi vẫn chạy | ✔ | 15 test fault + 3 kiểm tra chấp nhận |
| NFR-007 mô-đun nhà cung cấp | ✔ | `test_ai_gateway` (đổi adapter qua env không đổi API, không lộ secret) |

## Giới hạn đã biết (ghi vào video và "Known limitations")

- Không có Alembic: bảng tạo bằng `create_all`; đổi schema phải `docker compose down -v`.
- `connector_attempts.idempotency_key` không có ràng buộc UNIQUE như DDL SRS; row lock theo phiên ngăn Confirm trùng cho cùng order session, nhưng DB không cưỡng chế uniqueness liên phiên.
- Sơn, phụ kiện (vít, đinh) ngoài phạm vi; riêng "maling hvid" vẫn nhận một gợi ý điểm thấp do trùng chữ "hvid", không bao giờ tự chọn.
- Các nhãn D22 do AI soạn và chưa được người duyệt. Dòng E046 (`Moisture board`) từng sai và đã được sửa bằng cách thêm các cụm tiếng Anh lấy từ alias của catalog, nên con số 98/98 của embedding không còn độc lập với bộ đánh giá.
- Đăng nhập là giả lập (hai nhân viên demo, mật khẩu qua biến môi trường), không phải SSO; "ai chịu trách nhiệm" được ghi qua `actor_id` và `confirmed_by_associate` của nhân viên đã đăng nhập, nhưng không phải danh tính thật.
- Store dictionary chỉ cộng điểm cho ứng viên đã được truy xuất (top-10 vector); không tự thêm SKU vào danh sách ứng viên.

## Trạng thái chưa thể gọi 100%

- NFR-004 vẫn chưa được nghiệm thu bằng kịch bản UI chỉ dùng bàn phím và accessibility scan.
- NFR-005 chưa thể claim: evaluation có 98 dòng và 0 nhãn được người duyệt; SRS yêu cầu tối thiểu 150 dòng để claim mục tiêu ≤2%.
- UI Flow 1 và trang store dictionary đã có trong code, nhưng chưa chạy browser E2E. 233 test hiện là backend tests; acceptance 33/33 kiểm tra API trên stack live.
