"""Flow 1 (At-Counter) session API — SRS v2 §7.1. Also the review/confirm surface reused by Flow 2."""
import random
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.common import ApiError
from config import runtime, settings
from db.database import get_db
from db.models import Customer, OrderSession, Quote, SessionLine
from services import connector, parser, pii, pipeline, telemetry
from services.pipeline import now

router = APIRouter(prefix="/api/v1", tags=["Sessions (Flow 1)"])

LOCKED = ("CONFIRMED", "SENT_OR_EXPORTED", "POS_ACCEPTED", "NEEDS_MANUAL")
MAX_UPLOAD = 5 * 1024 * 1024


# ---------- helpers ----------
def get_session(db: Session, session_id: str, for_update: bool = False) -> OrderSession:
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise ApiError(404, "NOT_FOUND", "Session không tồn tại")
    q = db.query(OrderSession).filter(OrderSession.session_id == sid)
    if for_update:
        q = q.with_for_update()
    s = q.first()
    if not s:
        raise ApiError(404, "NOT_FOUND", "Session không tồn tại")
    return s


def ensure_editable(s: OrderSession) -> None:
    if s.status in LOCKED:
        raise ApiError(409, "SESSION_LOCKED", "Đơn đã Confirm — chỉ đọc")


def lines_of(db: Session, s: OrderSession) -> list[SessionLine]:
    return db.query(SessionLine).filter(SessionLine.session_id == s.session_id).order_by(SessionLine.line_no).all()


def get_line(db: Session, s: OrderSession, line_no: int) -> SessionLine:
    l = db.query(SessionLine).filter(SessionLine.session_id == s.session_id, SessionLine.line_no == line_no).first()
    if not l:
        raise ApiError(404, "NOT_FOUND", f"Dòng {line_no} không tồn tại")
    return l


def refresh_status(s: OrderSession, lines: list[SessionLine]) -> None:
    if s.status in LOCKED or s.status in ("DRAFT", "PARSED"):
        return
    s.status = "REVIEW_REQUIRED" if pipeline.blockers(lines) else "READY_TO_CONFIRM"


def session_view(db: Session, s: OrderSession, products: Optional[dict] = None) -> dict:
    products = products if products is not None else pipeline.load_products(db)
    lines = lines_of(db, s)
    quote = db.query(Quote).filter(Quote.session_id == s.session_id).first()
    analyzed = s.status not in ("DRAFT", "PARSED")
    return {
        "session_id": str(s.session_id), "order_session_id": s.order_session_id, "status": s.status,
        "input_type": s.input_type, "market": s.market, "store_id": s.store_id, "user_id": s.user_id,
        "client_id": s.client_id, "masked_source": s.masked_source, "read_line_count": len(lines),
        "ai_degraded": s.ai_fail_mode, "analyzed": analyzed, "locked": s.status in LOCKED,
        "stage_timings_ms": s.stage_timings or {},
        "lines": [pipeline.serialize_line(l, products) for l in lines],
        "blockers": pipeline.blockers(lines) if analyzed else [],
        "quote": {"quote_id": quote.quote_id, "status": quote.status} if quote else None,
        "confirmation": {
            "order_status": s.status if s.status in LOCKED else None,
            "fulfillment_reference": s.fulfillment_reference, "pos_order_ref": s.pos_order_ref,
            "csv_download_url": f"/api/v1/sessions/{s.session_id}/export.csv" if s.status == "NEEDS_MANUAL" else None,
            "confirmed_at": s.confirmed_at.isoformat() if s.confirmed_at else None,
            "processing_time_seconds": int((s.confirmed_at - s.processing_started_at).total_seconds())
            if s.confirmed_at and s.processing_started_at else None,
        },
    }


# ---------- endpoints ----------
class CreateSession(BaseModel):
    input_type: str = "paste_text"  # paste_text | email | file
    market: str = "DK"


@router.post("/sessions")
def create_session(body: CreateSession, db: Session = Depends(get_db)):
    if body.input_type not in ("paste_text", "email", "file"):
        raise ApiError(422, "VALIDATION", "input_type không hợp lệ")
    for _ in range(5):
        osid = f"SD-{now().year}-{body.market}-{random.randint(10000, 99999)}"
        if not db.query(OrderSession).filter(OrderSession.order_session_id == osid).first():
            break
    s = OrderSession(order_session_id=osid, store_id=settings.default_store, user_id=settings.default_user,
                     status="DRAFT", input_type=body.input_type, market=body.market)
    db.add(s)
    db.flush()
    telemetry.event(db, "SESSION_CREATED", s.session_id, actor_id=s.user_id, input_type=body.input_type)
    db.commit()
    return {"session_id": str(s.session_id), "order_session_id": s.order_session_id, "status": s.status, "store_id": s.store_id}


@router.get("/sessions/{session_id}")
def read_session(session_id: str, db: Session = Depends(get_db)):
    return session_view(db, get_session(db, session_id))


@router.post("/sessions/{session_id}/ingest")
async def ingest(session_id: str, request: Request, db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    ensure_editable(s)
    ctype = request.headers.get("content-type", "")
    language_hint = None
    if ctype.startswith("multipart/form-data"):
        form = await request.form()
        f = form.get("file")
        if f is None or not hasattr(f, "read"):
            raise ApiError(422, "VALIDATION", "Thiếu file")
        content = await f.read()
        if len(content) > MAX_UPLOAD:
            raise ApiError(413, "TOO_LARGE", "File tối đa 5 MB")
        language_hint = form.get("language_hint")
        name = (f.filename or "").lower()
        if content[:4] == b"%PDF":
            text = parser.pdf_text(content)
            if len(text.strip()) < 5:
                raise ApiError(422, "SCAN_ONLY_PDF", "PDF dạng ảnh scan — MVP không OCR. Hãy dán (paste) hoặc gõ danh sách.")
        elif name.endswith(".xlsx") and content[:2] == b"PK":
            text = parser.rows_from_table(content, name)
        elif name.endswith(".csv") or name.endswith(".txt"):
            text = parser.rows_from_table(content, name) if name.endswith(".csv") else content.decode("utf-8-sig", "replace")
        else:
            raise ApiError(422, "UNSUPPORTED_FILE", "Chỉ hỗ trợ PDF có text, XLSX, CSV hoặc dán text")
    else:
        body = await request.json()
        text = (body or {}).get("text") or ""
        language_hint = (body or {}).get("language_hint")
    if not text.strip():
        raise ApiError(422, "NO_TEXT", "Không có nội dung để đọc")

    masked = pii.mask(text)
    rows = parser.split_text(masked)
    db.query(SessionLine).filter(SessionLine.session_id == s.session_id).delete()
    for r in rows:
        db.add(SessionLine(session_id=s.session_id, line_no=r.line_no, source_start=r.source_start, source_end=r.source_end,
                           raw_customer_input=r.source_text, parsed_name=r.item_text, requested_qty=r.quantity,
                           requested_unit=r.unit, unit_raw=r.unit_raw, parse_status=r.status, parse_warnings=r.warnings,
                           attributes={"length_hint": r.length_m} if r.length_m else {}))
    s.masked_source = masked
    s.language_hint = language_hint
    s.status = "PARSED"
    s.processing_started_at = now()
    s.last_activity_at = now()
    db.commit()
    return session_view(db, s)


class LinePatch(BaseModel):
    item_text: Optional[str] = None
    requested_qty: Optional[float] = None
    requested_unit: Optional[str] = None


@router.patch("/sessions/{session_id}/lines/{line_no}")
def patch_line(session_id: str, line_no: int, body: LinePatch, db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    ensure_editable(s)
    l = get_line(db, s, line_no)
    changed = []
    if body.item_text is not None and body.item_text.strip() != (l.parsed_name or ""):
        l.parsed_name = pii.mask(body.item_text.strip())
        l.parse_status = "OK" if l.parsed_name else "UNREADABLE"
        changed.append("item_text")
    if body.requested_qty is not None and body.requested_qty != (float(l.requested_qty) if l.requested_qty is not None else None):
        if body.requested_qty <= 0:
            raise ApiError(422, "VALIDATION", "Số lượng phải > 0")
        l.requested_qty = body.requested_qty
        changed.append("requested_qty")
    if body.requested_unit is not None:
        unit = body.requested_unit if body.requested_unit in set(parser.UNIT_MAP.values()) else parser.normalize_unit(body.requested_unit)
        if unit is None:
            raise ApiError(422, "UNKNOWN_UNIT", f"Đơn vị '{body.requested_unit}' chưa có trong từ điển")
        if unit != l.requested_unit:
            l.requested_unit, l.unit_raw = unit, body.requested_unit
            changed.append("requested_unit")
    if changed:
        l.associate_edited = True
        l.parse_warnings = [w for w in (l.parse_warnings or []) if w not in ("missing_quantity", "missing_unit", "unknown_unit")]
        telemetry.event(db, "PARSE_EDITED", s.session_id, l.line_id, s.user_id, fields=changed)
        if s.status not in ("DRAFT", "PARSED"):
            products = pipeline.load_products(db)
            if "item_text" in changed:
                pipeline.match_line(l, products)
            pipeline.evaluate(l, products, pipeline.load_stock(list(products), s.store_id))
            refresh_status(s, lines_of(db, s))
    s.last_activity_at = now()
    db.commit()
    return session_view(db, s)


class AnalyzeBody(BaseModel):
    language_hint: Optional[str] = None


@router.post("/sessions/{session_id}/analyze")
def analyze(session_id: str, body: AnalyzeBody = AnalyzeBody(), db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    ensure_editable(s)
    lines = lines_of(db, s)
    if not lines:
        raise ApiError(400, "NO_LINES", "Chưa có dòng nào — hãy ingest trước")
    t0 = time.perf_counter()
    timings = {}
    s.ai_fail_mode = runtime["ai_fail_mode"]
    products = pipeline.load_products(db)
    t = time.perf_counter()
    for l in lines:
        pipeline.match_line(l, products)
    timings["match_ms"] = round((time.perf_counter() - t) * 1000, 1)
    t = time.perf_counter()
    stock = pipeline.load_stock(list(products), s.store_id)
    timings["stock_ms"] = round((time.perf_counter() - t) * 1000, 1)
    t = time.perf_counter()
    for l in lines:
        pipeline.evaluate(l, products, stock)
    timings["rules_convert_alternatives_ms"] = round((time.perf_counter() - t) * 1000, 1)
    timings["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    s.stage_timings = {**timings, "lines": len(lines), "pos_available": stock is not None}
    s.status = "ANALYZED"
    refresh_status(s, lines)
    s.processing_finished_at = now()
    s.last_activity_at = now()
    for l in lines:
        if l.original_sku:
            telemetry.event(db, "AI_SUGGESTED", s.session_id, l.line_id, s.user_id, suggested_sku=l.original_sku,
                            match_score=l.match_score, suggestion_type="match", band=l.score_band)
        if l.alternatives:
            telemetry.event(db, "AI_SUGGESTED", s.session_id, l.line_id, s.user_id,
                            suggested_sku=l.alternatives[0]["sku"], suggestion_type="alternative")
    db.commit()
    return session_view(db, s, products)


class Selection(BaseModel):
    sku: str
    decision: str  # SKU_KEPT | SKU_EDITED | SUBSTITUTION_ACCEPTED | SUBSTITUTION_REJECTED
    reason: Optional[str] = None


@router.put("/sessions/{session_id}/lines/{line_no}/selection")
def select(session_id: str, line_no: int, body: Selection, db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    ensure_editable(s)
    l = get_line(db, s, line_no)
    products = pipeline.load_products(db)
    if body.sku not in products:
        raise ApiError(404, "NOT_FOUND", "SKU không có trong catalog")
    stock = pipeline.load_stock(list(products), s.store_id)
    prev = l.final_sku
    if body.decision == "SKU_KEPT":
        if body.sku != l.original_sku:
            raise ApiError(422, "VALIDATION", "SKU_KEPT phải giữ đúng SKU gợi ý")
        l.resolved = True
    elif body.decision == "SKU_EDITED":
        l.original_sku = l.final_sku = body.sku
        l.resolved = True
        l.associate_edited = True
        l.customer_accepted_substitution_at = None
        l.substitution_rejection_reason = None
    elif body.decision == "SUBSTITUTION_ACCEPTED":
        if not any(a["sku"] == body.sku for a in (l.alternatives or [])):
            raise ApiError(409, "INVALID_STATE", "SKU này không nằm trong danh sách thay thế an toàn")
        l.final_sku = body.sku
        l.customer_accepted_substitution_at = now()
        l.substitution_rejection_reason = None
    elif body.decision == "SUBSTITUTION_REJECTED":
        if not (body.reason or "").strip():
            raise ApiError(422, "REASON_REQUIRED", "Cần ghi lý do khách từ chối")
        l.final_sku = l.original_sku
        l.customer_accepted_substitution_at = None
        l.substitution_rejection_reason = body.reason.strip()[:200]
    else:
        raise ApiError(422, "VALIDATION", "decision không hợp lệ")
    pipeline.evaluate(l, products, stock)
    telemetry.event(db, body.decision, s.session_id, l.line_id, s.user_id, suggested_sku=prev, selected_sku=l.final_sku,
                    match_score=l.match_score, reason_code=(body.reason or None) and "customer_reason")
    refresh_status(s, lines_of(db, s))
    s.last_activity_at = now()
    db.commit()
    return session_view(db, s, products)


@router.get("/sessions/{session_id}/lines/{line_no}/alternatives")
def alternatives(session_id: str, line_no: int, db: Session = Depends(get_db)):
    s = get_session(db, session_id)
    l = get_line(db, s, line_no)
    return {"line_no": l.line_no, "needed_quantity": float(l.selling_qty) if l.selling_qty else None,
            "items": l.alternatives or [],
            "message": None if l.alternatives else "Không có SKU thay thế an toàn đủ tồn (cùng chức năng, thông số bằng/tốt hơn)."}


class ClientBody(BaseModel):
    client_id: str


@router.put("/sessions/{session_id}/client")
def set_client(session_id: str, body: ClientBody, db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    ensure_editable(s)
    if not db.get(Customer, body.client_id):
        raise ApiError(422, "INVALID_CLIENT", "Client ID không tồn tại")
    s.client_id = body.client_id
    db.commit()
    return {"client_id": s.client_id}


class ConfirmBody(BaseModel):
    client_id: Optional[str] = None


def do_confirm(db: Session, s: OrderSession, client_id: Optional[str]) -> dict:
    if s.status in LOCKED:  # idempotent replay → same reference, no second order
        return {**session_view(db, s)["confirmation"], "replayed": True}
    if s.status in ("DRAFT", "PARSED"):
        raise ApiError(400, "NOT_ANALYZED", "Cần Analyze trước khi Confirm")
    quote = db.query(Quote).filter(Quote.session_id == s.session_id).with_for_update().first()
    if quote:
        from api.quotes import touch_expiry
        touch_expiry(db, quote)
        if quote.status != "PREPARING":
            raise ApiError(409, "QUOTE_STATE", f"Báo giá {quote.quote_id} đang {quote.status} — cần Prepare (sau khi khách xác nhận) trước khi Confirm")
    lines = lines_of(db, s)
    b = pipeline.blockers(lines)
    if b:
        raise ApiError(409, "UNRESOLVED_LINES", f"Còn {len(b)} dòng cần xử lý trước khi Confirm", {"line_nos": [x["line_no"] for x in b], "blockers": b})
    cid = client_id or s.client_id or f"{s.store_id}-WALKIN"
    if not db.get(Customer, cid):
        raise ApiError(422, "INVALID_CLIENT", "Client ID không tồn tại")
    s.client_id = cid
    s.confirmed_at = now()
    s.status = "CONFIRMED"
    payload = connector.build_payload(s, lines, quote.quote_id if quote else None)
    telemetry.event(db, "CONFIRMED", s.session_id, actor_id=s.user_id, lines=len(lines))
    result = connector.push(db, s, payload)
    telemetry.event(db, "POS_ACCEPTED" if result["order_status"] == "POS_ACCEPTED" else "CSV_EXPORTED", s.session_id, actor_id=s.user_id)
    for l in lines:
        l.resolved = True
    if quote:
        quote.status = "CONFIRMED"
        quote.status_changed_by, quote.status_changed_at = s.user_id, now()
        telemetry.event(db, "QUOTE_CONFIRMED", s.session_id, actor_id=s.user_id)
    s.masked_source = None  # retention: purge source after Confirm
    db.commit()
    return {**session_view(db, s)["confirmation"], "payload": payload, "replayed": False}


@router.post("/sessions/{session_id}/confirm")
def confirm(session_id: str, body: ConfirmBody = ConfirmBody(), idempotency_key: Optional[str] = Header(None),
            db: Session = Depends(get_db)):
    s = get_session(db, session_id, for_update=True)
    return do_confirm(db, s, body.client_id)


@router.get("/sessions/{session_id}/export.csv")
def export_csv(session_id: str, db: Session = Depends(get_db)):
    s = get_session(db, session_id)
    if s.status not in LOCKED:
        raise ApiError(409, "NOT_CONFIRMED", "Chỉ xuất CSV sau khi Confirm")
    quote = db.query(Quote).filter(Quote.session_id == s.session_id).first()
    payload = connector.build_payload(s, lines_of(db, s), quote.quote_id if quote else None)
    fname = s.csv_object_key or f"SiteDesk_{s.order_session_id}.csv"
    return Response(connector.to_csv(payload), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})
