# Flow 1: bảng truy vết yêu cầu → bằng chứng

Cập nhật 2026-11-06 trên nhánh `fix/flow1-backend`. "Acceptance" là `backend/scripts/acceptance_flow1.py` (28 kiểm tra trên stack thật, 28/28 đạt).
Test chạy bằng `docker compose exec backend pytest` (unit không cần DB; integration cần `TEST_DATABASE_URL`, xem `backend/tests/conftest.py`): 171 test pass.

Ký hiệu: ✔ có test và chạy thật · ◐ chỉ một phần · ✘ chưa có (ghi rõ lý do).

## Yêu cầu chức năng

| ID | Trạng thái | Test tự động | Kiểm tra chấp nhận | Ghi chú |
|---|---|---|---|---|
| FR-001 nhận file, session | ✔ | `test_input_limits` (PDF/XLSX/CSV, giới hạn), `test_errors` (PDF hỏng) | PDF hỏng 422, `.exe` 422, rỗng 422, quá lớn 413, CSV có header | Giới hạn 300 dòng, 20 trang PDF (OI-04 do nhóm chốt) |
| FR-002 che email/điện thoại | ✔ | `test_core` (PII), `test_flow1_contract::contact_details_never_reach...` | "không gộp hoặc mất dòng" | Chỉ regex; tên/địa chỉ không đảm bảo |
| FR-003 AI lỗi vẫn parse | ✔ | `test_flow1_resilience` (AI off, model chưa nạp, embedding lỗi, LLM lỗi) | `NFR-006 AI off` | |
| FR-004 sửa dòng | ◐ | `test_flow1_contract::unknown_body_fields...` (không sửa nhầm) | — | Phần UI "Đã đọc N dòng" thuộc UI Flow 1 (Codex), chưa kiểm chứng |
| FR-005 `N x L`, unreadable | ✔ | `test_core` | — | |
| FR-006 trích thuộc tính | ✔ | `test_core`, `test_chips_golden::golden_attributes` | — | |
| FR-007 top-10 vector, alias | ✔ | `test_out_of_catalog`, `test_core` (hard rules) | "hàng ngoài catalog không gợi ý" | Alias boost: không làm (SRS cho phép cắt) |
| FR-008 hybrid, ≤3 ứng viên | ✔ | `test_core::c18_is_never_matched_as_c24` | "C18 không thành C24" | |
| FR-009 band, gap | ✔ | `test_core::band_boundaries`, `gap_rule` | "thiếu cấp độ không vào band cao" | |
| FR-010 exceptions first, chặn Confirm | ✔ (API) | `test_flow1_resilience` | "blockers chặn Confirm, nêu số dòng" | UI sắp xếp: Codex PR 2 |
| FR-011 từ điển đơn vị | ✔ | `test_units_srs` (31 ca theo §15.2, quy tắc `m`) | "units SRS 15.2" | Tên chuẩn `sheet`; `board` vẫn nhận |
| FR-012 quy đổi, làm tròn lên | ✔ | `test_core::conversion_exact_and_ceil`, `test_flow1_contract::pack_conversion` | "120 m / 4.8 = 25" | 60 m² / 2.88 → 21 |
| FR-013 thiếu dữ liệu thì chặn | ✔ | `test_core::conversion_never_guesses`, `test_units_srs::pallet...` | — | |
| FR-014 tồn kho, nhãn, giờ | ✔ (API) | `test_flow1_resilience::pos_down_while_analysing` | "mọi số tồn có nhãn và giờ" | UI luôn hiện nhãn: Codex PR 2 |
| FR-015 thay thế ≤2 | ✔ | `test_core::partial_stock_proposes_only_safe_alternatives`, `test_flow1_contract::substitution...` | "chỉ thay thế an toàn" | |
| FR-016 khách chấp thuận mới đổi SKU | ✔ | `test_core::final_sku_only_changes...`, `test_flow1_contract` (reject cần lý do) | "SKU không đổi trước khi khách đồng ý" | |
| FR-017 khách hàng / walk-in | ✔ | `test_flow1_contract::payload_matches_slide_9` | — | Chọn khách trên UI: Codex PR 3 |
| FR-018 idempotency, khóa chỉ đọc | ✔ | `test_flow1_resilience` (hai lần Confirm, đồng thời, khóa) | "Confirm lặp, khóa chỉ đọc" | |
| FR-019 API/CSV connector | ✔ | `test_flow1_resilience` (503, timeout, cả hai lỗi), `test_flow1_contract::csv_fallback` | "POS off → NEEDS_MANUAL + CSV" | |
| FR-020 payload slide 9 | ✔ | `test_flow1_contract::payload_matches_the_slide_9_contract`, `substitution...` | "payload: original_sku, score null" | |
| FR-021 store dictionary | ✘ | — | — | Có bảng, chưa có code ghi/gỡ. Bậc 3, SRS cho phép cắt |
| FR-029 events | ✔ | `test_flow1_contract::decision_events_cover_the_flow...` | — | Không PII |
| FR-030 thời gian từng bước | ✔ | — | `NFR-003 p50` | `stage_timings` được lưu mỗi lần phân tích |
| FR-031 KPI SQL | ◐ | — | — | Truy vấn của SRS chạy được trên schema thật, chưa đóng gói thành `kpi.sql` |
| FR-032 mock login | ✘ | — | — | Chỉ có nhân viên cố định `EMP-1042`. Bậc 3, SRS cho phép cắt |
| FR-033 hai fail toggle | ✔ | `test_flow1_resilience` | AI off / POS off / cả hai | |
| FR-034 AI Gateway | ✔ | `test_ai_gateway` | — | |
| FR-035 seed 60–80 SKU | ✔ | — | healthy + catalog | 62 SKU, 5 nhóm; validator trong `generate.py` |
| FR-036 một enum trạng thái | ◐ | — | — | Backend dùng một enum; UI mới (Codex) chưa kiểm chứng |
| FR-037 trạng thái đơn, mã chống trùng | ✔ | `test_flow1_resilience` | "replay cùng mã tham chiếu" | |

## Yêu cầu phi chức năng

| ID | Trạng thái | Bằng chứng |
|---|---|---|
| NFR-001 chạy bằng Docker | ✔ | `docker compose up`; acceptance "stack healthy" |
| NFR-002 che PII, không claim quá mức | ◐ | Test PII đạt; UI ghi chú giới hạn (PR 1 Codex). Mock login: không có (nhân viên cố định, không gọi là SSO) |
| NFR-003 ≤3 s cho 20 dòng | ✔ | `evaluation_2026-11-05.md`: p50 201 ms, p95 298 ms, max 305 ms (20 lần, embedding thật, CPU, WSL2) |
| NFR-004 chỉ bằng bàn phím | ✘ | Thuộc UI Flow 1 (Codex PR 4); chưa kiểm chứng |
| NFR-005 ≤2% khớp sai band cao | ✘ không thể claim | 98 dòng (<150) và **0/98 nhãn được người duyệt**. 0/63 sai ở band cao, cận trên 95% = 5,75%. Chỉ được ghi "kết quả ban đầu" |
| NFR-006 AI/POS lỗi vẫn chạy | ✔ | 15 test fault + 3 kiểm tra chấp nhận |
| NFR-007 mô-đun nhà cung cấp | ✔ | `test_ai_gateway` (đổi adapter qua env không đổi API, không lộ secret) |

## Giới hạn đã biết (ghi vào video và "Known limitations")

- Không có Alembic: bảng tạo bằng `create_all`; đổi schema phải `docker compose down -v`.
- `connector_attempts.idempotency_key` không có ràng buộc UNIQUE như DDL SRS, vì logic thử lại POS ghi hai lần cùng khóa.
- Sơn, phụ kiện (vít, đinh) ngoài phạm vi; riêng "maling hvid" vẫn nhận một gợi ý điểm thấp do trùng chữ "hvid", không bao giờ tự chọn.
- Các nhãn D22 do AI soạn và chưa được người duyệt. Dòng E046 (`Moisture board`) từng sai và đã được sửa bằng cách thêm các cụm tiếng Anh lấy từ alias của catalog, nên con số 98/98 của embedding không còn độc lập với bộ đánh giá.
- Đăng nhập: một nhân viên cố định; "ai chịu trách nhiệm" được ghi qua `actor_id` và `confirmed_by_associate`, không phải danh tính thật.
