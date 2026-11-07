"""Per-request UI language for API messages and print pages (vi | en).

Language comes from header `X-Lang` or query `?lang=` (print pages open in a new tab), default `en`.
Stored data stays language-neutral (codes); text is produced at response time with t().
"""
import json
from contextvars import ContextVar

LANGS = ("en", "vi")
_lang: ContextVar[str] = ContextVar("lang", default="en")


def set_lang(value: str | None) -> None:
    v = (value or "").lower()[:2]
    _lang.set(v if v in LANGS else "en")


def lang() -> str:
    return _lang.get()


M: dict[str, dict[str, str]] = {
    # labels / disclaimers
    "stock_label": {"en": "On-hand reference stock — confirm before promising delivery",
                    "vi": "Tồn tham khảo (on-hand), cần xác nhận trước khi hứa hàng"},
    "quote_disclaimer": {"en": "Prices and stock are for reference only — not guaranteed and not reserved.",
                         "vi": "Giá và tồn kho chỉ mang tính tham khảo, chưa được bảo đảm hoặc giữ chỗ."},
    "pick_not_reserved": {"en": "Not reserved in the system", "vi": "Chưa giữ chỗ trên hệ thống"},
    # blockers
    "blk_clarify": {"en": "needs clarification / SKU choice", "vi": "cần làm rõ/chọn SKU"},
    "blk_substitute": {"en": "waiting for customer to accept or reject the substitute", "vi": "chờ khách đồng ý hoặc từ chối hàng thay thế"},
    "blk_no_qty": {"en": "missing converted quantity", "vi": "thiếu số lượng quy đổi"},
    # conversion
    "conv_missing_qty": {"en": "Quantity missing", "vi": "Thiếu số lượng"},
    "conv_missing_unit": {"en": "Unit missing/unknown — not guessed", "vi": "Thiếu/không rõ đơn vị — không tự đoán"},
    "conv_fractional": {"en": "Fractional quantity for a whole selling unit", "vi": "Số lượng lẻ cho đơn vị bán nguyên"},
    "conv_sku_no_length": {"en": "SKU has no length for conversion", "vi": "SKU thiếu chiều dài để quy đổi"},
    "conv_length_mismatch": {"en": "Customer asked for {hint} m pieces, SKU is {pack} m — clarify",
                             "vi": "Khách ghi cây {hint} m, SKU dài {pack} m — cần làm rõ"},
    "conv_unconvertible": {"en": "Cannot convert {unit} → {su}", "vi": "Không quy đổi được {unit} → {su}"},
    "conv_no_pack_size": {"en": "SKU has no pack size (m²/pk) — not guessed", "vi": "SKU thiếu pack_size (m²/pk) — không đoán"},
    "conv_unsupported": {"en": "Selling unit {su} not supported yet", "vi": "Đơn vị bán {su} chưa hỗ trợ"},
    # alternatives reasons
    "alt_same": {"en": "same {attr}", "vi": "cùng {attr}"},
    "alt_grade_up": {"en": "grade {to} ≥ {frm}", "vi": "cấp {to} ≥ {frm}"},
    "alt_treatment_superset": {"en": "treatment covers the request", "vi": "xử lý gỗ bao gồm yêu cầu"},
    "alt_none": {"en": "No safe substitute with enough stock (same function, equal or better specs).",
                 "vi": "Không có SKU thay thế an toàn đủ tồn (cùng chức năng, thông số bằng/tốt hơn)."},
    "attr_cross_section_mm": {"en": "cross-section", "vi": "tiết diện"},
    "attr_strength_grade": {"en": "strength grade", "vi": "cấp cường độ"},
    "attr_thickness_mm": {"en": "thickness", "vi": "độ dày"},
    "attr_board_type": {"en": "board type", "vi": "loại tấm"},
    "attr_bag_weight_kg": {"en": "bag weight", "vi": "trọng lượng bao"},
    "attr_product_type": {"en": "product type", "vi": "loại sản phẩm"},
    "attr_treatment": {"en": "treatment", "vi": "xử lý gỗ"},
    # errors
    "session_not_found": {"en": "Session not found", "vi": "Session không tồn tại"},
    "session_locked": {"en": "Order already confirmed — read-only", "vi": "Đơn đã Confirm — chỉ đọc"},
    "line_not_found": {"en": "Line {n} not found", "vi": "Dòng {n} không tồn tại"},
    "input_type_invalid": {"en": "Invalid input_type", "vi": "input_type không hợp lệ"},
    "file_missing": {"en": "File missing", "vi": "Thiếu file"},
    "file_too_large": {"en": "File must be 5 MB or less", "vi": "File tối đa 5 MB"},
    "scan_pdf": {"en": "Scanned (image) PDF — the MVP has no OCR. Paste or type the list instead.",
                 "vi": "PDF dạng ảnh scan — MVP không OCR. Hãy dán (paste) hoặc gõ danh sách."},
    "unsupported_file": {"en": "Only text PDF, XLSX, CSV or pasted text are supported", "vi": "Chỉ hỗ trợ PDF có text, XLSX, CSV hoặc dán text"},
    "unreadable_file": {"en": "The file is damaged or cannot be read. Paste or type the list instead.",
                        "vi": "Tệp bị hỏng hoặc không đọc được. Hãy dán hoặc nhập danh sách."},
    "too_many_rows": {"en": "{n} lines is over the limit of {max} per session. Split the list and send it in parts.",
                      "vi": "{n} dòng vượt giới hạn {max} dòng mỗi phiên. Hãy chia nhỏ danh sách."},
    "pdf_too_long": {"en": "The PDF has {pages} pages; the limit is {max}. Send fewer pages or paste the list.",
                     "vi": "PDF có {pages} trang, giới hạn là {max}. Hãy gửi ít trang hơn hoặc dán danh sách."},
    "bad_request_body": {"en": "The request body is not valid", "vi": "Nội dung yêu cầu không hợp lệ"},
    "db_unavailable": {"en": "The database is not reachable right now. Nothing was changed; retry in a moment.",
                       "vi": "Hiện chưa kết nối được cơ sở dữ liệu. Chưa có gì bị thay đổi; hãy thử lại sau ít phút."},
    "dictionary_not_found": {"en": "Dictionary entry not found", "vi": "Không tìm thấy mục từ điển"},
    "login_failed": {"en": "Wrong user name or password", "vi": "Sai tên đăng nhập hoặc mật khẩu"},
    "login_disabled": {"en": "Demo sign-in is not configured (DEMO_PASSWORD is empty). The counter works without it.",
                       "vi": "Đăng nhập demo chưa được cấu hình (DEMO_PASSWORD trống). Quầy vẫn hoạt động bình thường."},
    "unauthenticated": {"en": "Sign in first (demo session missing or expired)", "vi": "Hãy đăng nhập trước (phiên demo thiếu hoặc đã hết hạn)"},
    "internal_error": {"en": "Unexpected server error. Nothing was lost; try again or continue manually.",
                       "vi": "Lỗi máy chủ không mong đợi. Không mất dữ liệu; hãy thử lại hoặc tiếp tục thủ công."},
    "no_text": {"en": "Nothing to read", "vi": "Không có nội dung để đọc"},
    "last_line": {"en": "At least one line must remain on the order", "vi": "Đơn phải còn ít nhất một dòng"},
    "qty_positive": {"en": "Quantity must be > 0", "vi": "Số lượng phải > 0"},
    "unknown_unit": {"en": "Unit '{u}' is not in the dictionary", "vi": "Đơn vị '{u}' chưa có trong từ điển"},
    "no_lines": {"en": "No lines yet — ingest first", "vi": "Chưa có dòng nào — hãy ingest trước"},
    "sku_not_in_catalog": {"en": "SKU not in catalog", "vi": "SKU không có trong catalog"},
    "sku_kept_mismatch": {"en": "SKU_KEPT must keep the suggested SKU", "vi": "SKU_KEPT phải giữ đúng SKU gợi ý"},
    "not_safe_alternative": {"en": "This SKU is not in the safe substitute list", "vi": "SKU này không nằm trong danh sách thay thế an toàn"},
    "reason_required": {"en": "A reason for the customer's rejection is required", "vi": "Cần ghi lý do khách từ chối"},
    "decision_invalid": {"en": "Invalid decision", "vi": "decision không hợp lệ"},
    "client_not_found": {"en": "Client ID does not exist", "vi": "Client ID không tồn tại"},
    "not_analyzed_confirm": {"en": "Analyze before confirming", "vi": "Cần Analyze trước khi Confirm"},
    "idempotency_key_invalid": {"en": "Idempotency-Key must contain 1–128 characters", "vi": "Idempotency-Key phải dài từ 1 đến 128 ký tự"},
    "idempotency_key_conflict": {"en": "This order was already confirmed with a different Idempotency-Key", "vi": "Đơn đã được Confirm với Idempotency-Key khác"},
    "quote_required": {"en": "An e-mail request is confirmed through its quote: save the quote, record the customer's approval and prepare it first",
                       "vi": "Yêu cầu qua email phải Confirm qua báo giá: lưu báo giá, ghi nhận khách duyệt và Prepare trước"},
    "quote_needs_prepare": {"en": "Quote {id} is {status} — record customer confirmation and Prepare before confirming",
                            "vi": "Báo giá {id} đang {status} — cần Prepare (sau khi khách xác nhận) trước khi Confirm"},
    "quote_locks_session": {"en": "Quote {id} is saved: the order can no longer be edited. Cancel it and start a new list to change it.",
                            "vi": "Đã lưu báo giá {id}: không sửa đơn được nữa. Muốn đổi, hãy hủy báo giá và tạo danh sách mới."},
    "stock_changed_confirm": {"en": "Stock changed on line(s) {lines}. Review them, then confirm again.",
                              "vi": "Tồn kho đã đổi ở dòng {lines}. Kiểm tra lại rồi Confirm lần nữa."},
    "pos_unavailable_quote": {"en": "mock-pos is not responding — cannot save a quote without current stock",
                              "vi": "mock-pos không phản hồi — không lưu được báo giá khi chưa có tồn kho hiện tại"},
    "pos_conflict": {"en": "POS already holds a different version of this order. Check it in POS; nothing was sent.",
                     "vi": "POS đã có đơn này với nội dung khác. Hãy kiểm tra trên POS; chưa gửi thêm gì."},
    "internal_error": {"en": "Server error — the order was not saved. Try again.", "vi": "Lỗi máy chủ — đơn chưa được lưu. Hãy thử lại."},
    "unresolved_confirm": {"en": "{n} line(s) must be resolved before confirming", "vi": "Còn {n} dòng cần xử lý trước khi Confirm"},
    "csv_after_confirm": {"en": "CSV export is available only after Confirm", "vi": "Chỉ xuất CSV sau khi Confirm"},
    "quote_not_found": {"en": "Quote {id} not found", "vi": "Không tìm thấy báo giá {id}"},
    "pos_live_error": {"en": "mock-pos is not responding — cannot compare current price/stock",
                       "vi": "mock-pos không phản hồi — không so sánh được giá/tồn hiện tại"},
    "quote_session_locked": {"en": "Order already confirmed — cannot create a quote", "vi": "Đơn đã Confirm, không tạo báo giá được"},
    "quote_not_analyzed": {"en": "Analyze before saving a quote", "vi": "Cần Analyze trước khi lưu báo giá"},
    "quote_exists": {"en": "This session already has a quote", "vi": "Session này đã có báo giá"},
    "valid_from_today": {"en": "Validity must be today or later", "vi": "Hiệu lực phải từ hôm nay trở đi"},
    "quote_unresolved": {"en": "{n} line(s) need clarification before saving the quote", "vi": "Còn {n} dòng cần làm rõ trước khi lưu báo giá"},
    "invalid_transition": {"en": "Cannot move {frm} → {to}", "vi": "Không chuyển được {frm} → {to}"},
    "quote_state": {"en": "Quote is {status}", "vi": "Báo giá đang {status}"},
    "channel_invalid": {"en": "Confirmation channel: email | phone | in_store", "vi": "Kênh xác nhận: email | phone | in_store"},
    "quote_cannot_prepare": {"en": "Quote is {status} — cannot Prepare", "vi": "Báo giá đang {status} — không Prepare được"},
    "customer_not_confirmed": {"en": "Record the customer's confirmation before Prepare", "vi": "Cần ghi nhận khách đã xác nhận báo giá trước khi Prepare"},
    "pos_unavailable_recheck": {"en": "mock-pos is not responding — cannot recheck stock", "vi": "mock-pos không phản hồi — không recheck được tồn kho"},
    "pos_unreachable": {"en": "Cannot reach mock-pos", "vi": "Không gọi được mock-pos"},
    "pos_unreachable_or_sku": {"en": "Cannot reach mock-pos or wrong SKU", "vi": "Không gọi được mock-pos hoặc SKU sai"},
    # print pages
    "p_quote_title": {"en": "Quote", "vi": "Báo giá"},
    "p_pick_title": {"en": "Pick slip", "vi": "Phiếu soạn hàng"},
    "p_status": {"en": "Status", "vi": "Trạng thái"},
    "p_price_source": {"en": "Price source", "vi": "Nguồn giá"},
    "p_price_time": {"en": "Price captured (UTC)", "vi": "Giờ lấy giá (UTC)"},
    "p_valid_until": {"en": "Valid until", "vi": "Hiệu lực đến"},
    "p_tier": {"en": "Discount tier", "vi": "Bậc chiết khấu"},
    "p_currency": {"en": "Currency", "vi": "Tiền tệ"},
    "p_cancelled": {"en": "CANCELLED — this quote is no longer valid", "vi": "ĐÃ HỦY — báo giá này không còn hiệu lực"},
    "p_expired": {"en": "EXPIRED", "vi": "HẾT HẠN"},
    "p_product": {"en": "Product", "vi": "Sản phẩm"},
    "p_qty": {"en": "Qty", "vi": "SL"},
    "p_unit": {"en": "Unit", "vi": "Đơn vị"},
    "p_unit_price": {"en": "Unit price", "vi": "Đơn giá"},
    "p_line_total": {"en": "Line total", "vi": "Thành tiền"},
    "p_total": {"en": "Total (snapshot)", "vi": "Tổng (snapshot)"},
    "p_current_total": {"en": "Current total after customer changes", "vi": "Tổng hiện tại sau thay đổi của khách"},
    "p_printed": {"en": "Printed (UTC)", "vi": "Ngày in (UTC)"},
    "p_quote_status": {"en": "Quote status", "vi": "Trạng thái báo giá"},
    "p_note": {"en": "Note", "vi": "Ghi chú"},
    "p_print": {"en": "Print", "vi": "In"},
    "p_simulated": {"en": "SiteDesk MVP — POS/ERP, prices and stock are simulated data.",
                    "vi": "SiteDesk MVP — POS/ERP/giá/tồn kho là dữ liệu mô phỏng (simulated)."},
}


def t(key: str, **kw) -> str:
    entry = M.get(key)
    if entry is None:
        return key
    return entry.get(lang(), entry["en"]).format(**kw)


def code(key: str, **kw) -> str:
    """Language-neutral message stored in the DB; render later with render()."""
    return json.dumps({"k": key, **kw}, ensure_ascii=False)


def render(stored: str | None) -> str | None:
    if not stored:
        return stored
    try:
        d = json.loads(stored)
        return t(d.pop("k"), **d)
    except (ValueError, TypeError, KeyError, AttributeError):
        return stored  # legacy free text
