"""Flow 2 — Pre-order / Advance Quote (UC5, MVP-FR-022..028, 038, 040). Thin slice per SRS v2 §3.3.

SAVED → SENT → PREPARING → CONFIRMED | EXPIRED | CANCELLED. Expiry evaluated on access (no scheduler).
Prepare requires customer_confirmed_at + customer_confirmed_by. No reservation, no versioning.
"""
import html
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.common import ApiError
from api.sessions import LOCKED, do_confirm, get_session, lines_of, refresh_status
from config import PICK_SLIP_NOT_RESERVED, QUOTE_DISCLAIMER, settings
from db.database import get_db
from db.models import Customer, DiscountTier, OrderSession, Quote, QuoteLineSnapshot, SessionLine
from services import pipeline, pos_client, telemetry
from services.pipeline import now

router = APIRouter(prefix="/api/v1", tags=["Quotes (Flow 2)"])

PRICE_SOURCE = "mock-pos simulated"
OPEN_STATES = ("SAVED", "SENT", "PREPARING")
CONFIRM_CHANNELS = ("email", "phone", "in_store")


def _money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _rate(db: Session, tier: str) -> Decimal:
    t = db.get(DiscountTier, tier)
    return Decimal(str(t.discount_rate)) if t else Decimal("0")


def get_quote(db: Session, quote_id: str, for_update: bool = False) -> Quote:
    q = db.query(Quote).filter(Quote.quote_id == quote_id)
    if for_update:
        q = q.with_for_update()
    quote = q.first()
    if not quote:
        raise ApiError(404, "NOT_FOUND", f"Không tìm thấy báo giá {quote_id}")
    return quote


def touch_expiry(db: Session, quote: Quote) -> None:
    """Expiry on access (MVP-FR-027): no scheduler."""
    if quote.status in OPEN_STATES and quote.valid_until < datetime.now(timezone.utc).date():
        quote.status = "EXPIRED"
        quote.status_changed_by, quote.status_changed_at = "system", now()
        s = db.get(OrderSession, quote.session_id)
        if s:
            s.masked_source = None  # retention: purge source on expiry
        telemetry.event(db, "QUOTE_EXPIRED", quote.session_id)
        db.commit()


def _snapshots(db: Session, quote: Quote) -> list[QuoteLineSnapshot]:
    return db.query(QuoteLineSnapshot).filter(QuoteLineSnapshot.quote_id == quote.quote_id).all()


def quote_view(db: Session, quote: Quote, with_live: bool = True) -> dict:
    s = db.get(OrderSession, quote.session_id)
    lines = {l.line_id: l for l in lines_of(db, s)}
    snaps = sorted(_snapshots(db, quote), key=lambda x: lines[x.line_id].line_no if x.line_id in lines else 0)
    products = pipeline.load_products(db)
    rate = _rate(db, quote.applied_discount_tier)
    live_prices = live_stock = None
    live_error = None
    if with_live and quote.status in OPEN_STATES:
        skus = list({sn.sku for sn in snaps} | {l.final_sku for l in lines.values() if l.final_sku})
        try:
            live_prices = pos_client.prices(skus)
            live_stock = pos_client.stock(skus, s.store_id)
        except pos_client.PosUnavailable:
            live_error = "mock-pos không phản hồi — không so sánh được giá/tồn hiện tại"
    checked_at = now().isoformat() if live_prices is not None else None
    out_lines, total = [], Decimal("0")
    for sn in snaps:
        l = lines.get(sn.line_id)
        qty = Decimal(str(sn.quantity or 0))
        line_total = _money(Decimal(str(sn.unit_price)) * qty)
        total += line_total
        item = {
            "line_no": l.line_no if l else None, "raw_customer_input": l.raw_customer_input if l else None,
            "sku": sn.sku, "name": products.get(sn.sku, {}).get("name"), "category": products.get(sn.sku, {}).get("category"),
            "quantity": float(qty), "selling_unit": l.selling_unit if l else None,
            "snapshot": {"unit_price": float(sn.unit_price), "list_unit_price": float(sn.list_unit_price or 0),
                         "on_hand": float(sn.on_hand), "line_total": float(line_total)},
            "live": None, "changed_fields": [], "alternative_required": False,
            "current_line": {"final_sku": l.final_sku, "line_status": l.line_status, "stock_status": l.stock_status,
                             "fulfillment_action": l.fulfillment_action} if l else None,
        }
        if live_prices is not None and sn.sku in live_prices:
            live_net = _money(Decimal(str(live_prices[sn.sku])) * (1 - rate))
            st = (live_stock or {}).get(sn.sku, {})
            item["live"] = {"unit_price": float(live_net), "on_hand": st.get("on_hand"), "checked_at": checked_at,
                            "stock_updated_at": st.get("updated_at")}
            if live_net != _money(sn.unit_price):
                item["changed_fields"].append("price")
            if st.get("on_hand") is not None and Decimal(str(st["on_hand"])) != Decimal(str(sn.on_hand)):
                item["changed_fields"].append("stock")
            item["alternative_required"] = st.get("on_hand") is not None and Decimal(str(st["on_hand"])) < qty
        out_lines.append(item)
    cust = db.get(Customer, quote.client_id)
    return {
        "quote_id": quote.quote_id, "status": quote.status, "session_id": str(quote.session_id),
        "order_session_id": s.order_session_id, "client_id": quote.client_id,
        "customer_type": cust.customer_type if cust else None,
        "valid_until": quote.valid_until.isoformat(), "price_source": quote.price_source,
        "price_captured_at": quote.price_captured_at.isoformat(), "applied_discount_tier": quote.applied_discount_tier,
        "discount_rate": float(rate), "currency": next(iter(products.values()), {}).get("currency", "DKK"),
        "customer_confirmed_at": quote.customer_confirmed_at.isoformat() if quote.customer_confirmed_at else None,
        "customer_confirmed_by": quote.customer_confirmed_by,
        "created_at": quote.created_at.isoformat() if quote.created_at else None, "created_by": quote.created_by,
        "status_changed_at": quote.status_changed_at.isoformat() if quote.status_changed_at else None,
        "status_changed_by": quote.status_changed_by,
        "disclaimer": QUOTE_DISCLAIMER, "snapshot_total": float(total), "lines": out_lines,
        "live_checked_at": checked_at, "live_error": live_error,
        "session_status": s.status, "session_locked": s.status in LOCKED,
        "order": {"fulfillment_reference": s.fulfillment_reference, "pos_order_ref": s.pos_order_ref,
                  "csv_download_url": f"/api/v1/sessions/{s.session_id}/export.csv" if s.status == "NEEDS_MANUAL" else None},
        "allowed_actions": _allowed(quote, s),
    }


def _allowed(quote: Quote, s: OrderSession) -> list[str]:
    a = []
    if quote.status == "SAVED":
        a.append("SEND")
    if quote.status in ("SAVED", "SENT") and not quote.customer_confirmed_at:
        a.append("RECORD_CUSTOMER_CONFIRMATION")
    if quote.status in ("SAVED", "SENT") and quote.customer_confirmed_at:
        a.append("PREPARE")
    if quote.status == "PREPARING":
        a += ["PRINT_PICK_SLIP", "CONFIRM"]
    if quote.status in OPEN_STATES:
        a.append("CANCEL")
    return a


# ---------- endpoints ----------
class QuoteCreate(BaseModel):
    session_id: str
    client_id: str
    valid_until: date


@router.post("/quotes")
def create_quote(body: QuoteCreate, db: Session = Depends(get_db)):
    s = get_session(db, body.session_id, for_update=True)
    if s.status in LOCKED:
        raise ApiError(409, "SESSION_LOCKED", "Đơn đã Confirm, không tạo báo giá được")
    if s.status in ("DRAFT", "PARSED"):
        raise ApiError(400, "NOT_ANALYZED", "Cần Analyze trước khi lưu báo giá")
    if db.query(Quote).filter(Quote.session_id == s.session_id).first():
        raise ApiError(409, "QUOTE_EXISTS", "Session này đã có báo giá")
    if body.valid_until < datetime.now(timezone.utc).date():
        raise ApiError(422, "VALIDATION", "Hiệu lực phải từ hôm nay trở đi")
    cust = db.get(Customer, body.client_id)
    if not cust:
        raise ApiError(422, "INVALID_CLIENT", "Client ID không tồn tại")
    lines = lines_of(db, s)
    unresolved = [l.line_no for l in lines if l.line_status == "NEEDS_CLARIFICATION"]
    if unresolved:
        raise ApiError(409, "UNRESOLVED_LINES", f"Còn {len(unresolved)} dòng cần làm rõ trước khi lưu báo giá", {"line_nos": unresolved})
    seq = (db.query(func.count(Quote.quote_id)).scalar() or 0) + 457
    while db.get(Quote, f"BG-{s.market}-{seq:04d}"):
        seq += 1
    captured = now()
    rate = _rate(db, cust.discount_tier)
    products = pipeline.load_products(db)
    quote = Quote(quote_id=f"BG-{s.market}-{seq:04d}", session_id=s.session_id, client_id=cust.client_id, status="SAVED",
                  valid_until=body.valid_until, applied_discount_tier=cust.discount_tier, price_source=PRICE_SOURCE,
                  price_captured_at=captured, created_by=s.user_id, status_changed_by=s.user_id, status_changed_at=captured)
    db.add(quote)
    db.flush()
    for l in lines:
        if not l.final_sku or not l.selling_qty:
            continue
        lp = Decimal(str(products[l.final_sku]["unit_price"]))
        db.add(QuoteLineSnapshot(quote_id=quote.quote_id, line_id=l.line_id, sku=l.final_sku, quantity=l.selling_qty,
                                 list_unit_price=lp, unit_price=_money(lp * (1 - rate)),
                                 on_hand=l.on_hand if l.on_hand is not None else 0, captured_at=captured))
    s.client_id = cust.client_id
    telemetry.event(db, "QUOTE_SAVED", s.session_id, actor_id=s.user_id)
    db.commit()
    return quote_view(db, quote, with_live=False)


@router.get("/quotes")
def list_quotes(q: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Quote)
    if q:
        query = query.filter(Quote.quote_id == q.strip().upper())  # exact lookup, no fuzzy search
    for quote in query.all():
        touch_expiry(db, quote)
    query = db.query(Quote)
    if q:
        query = query.filter(Quote.quote_id == q.strip().upper())
    if status:
        query = query.filter(Quote.status == status)
    items = []
    for quote in query.order_by(Quote.created_at.desc()).limit(100).all():
        n = db.query(func.count()).select_from(QuoteLineSnapshot).filter(QuoteLineSnapshot.quote_id == quote.quote_id).scalar()
        items.append({"quote_id": quote.quote_id, "status": quote.status, "client_id": quote.client_id,
                      "valid_until": quote.valid_until.isoformat(), "line_count": n,
                      "created_at": quote.created_at.isoformat() if quote.created_at else None,
                      "customer_confirmed": bool(quote.customer_confirmed_at)})
    return {"items": items}


@router.get("/quotes/{quote_id}")
def read_quote(quote_id: str, db: Session = Depends(get_db)):
    quote = get_quote(db, quote_id)
    touch_expiry(db, quote)
    return quote_view(db, quote)


class Transition(BaseModel):
    to_status: str


@router.post("/quotes/{quote_id}/transitions")
def transition(quote_id: str, body: Transition, db: Session = Depends(get_db)):
    quote = get_quote(db, quote_id, for_update=True)
    touch_expiry(db, quote)
    frm, to = quote.status, body.to_status
    allowed = {("SAVED", "SENT"), ("SAVED", "CANCELLED"), ("SENT", "CANCELLED"), ("PREPARING", "CANCELLED")}
    if (frm, to) not in allowed:
        raise ApiError(409, "INVALID_TRANSITION", f"Không chuyển được {frm} → {to}")
    quote.status = to
    quote.status_changed_by, quote.status_changed_at = settings.default_user, now()
    telemetry.event(db, f"QUOTE_{to}", quote.session_id, actor_id=settings.default_user)
    db.commit()
    return {"quote_id": quote.quote_id, "from_status": frm, "to_status": to, "actor_id": quote.status_changed_by,
            "occurred_at": quote.status_changed_at.isoformat()}


class CustomerConfirmation(BaseModel):
    channel: str  # email | phone | in_store — no PII stored


@router.post("/quotes/{quote_id}/customer-confirmation")
def customer_confirmation(quote_id: str, body: CustomerConfirmation, db: Session = Depends(get_db)):
    quote = get_quote(db, quote_id, for_update=True)
    touch_expiry(db, quote)
    if quote.status not in ("SAVED", "SENT"):
        raise ApiError(409, "INVALID_STATE", f"Báo giá đang {quote.status}")
    if body.channel not in CONFIRM_CHANNELS:
        raise ApiError(422, "VALIDATION", "Kênh xác nhận: email | phone | in_store")
    quote.customer_confirmed_at = now()
    quote.customer_confirmed_by = f"{quote.client_id} via {body.channel} (recorded by {settings.default_user})"[:64]
    telemetry.event(db, "QUOTE_CUSTOMER_CONFIRMED", quote.session_id, actor_id=settings.default_user, channel=body.channel)
    db.commit()
    return quote_view(db, quote)


@router.post("/quotes/{quote_id}/prepare")
def prepare(quote_id: str, db: Session = Depends(get_db)):
    """Recheck live price/stock, re-run alternatives on the session lines, move to PREPARING."""
    quote = get_quote(db, quote_id, for_update=True)
    touch_expiry(db, quote)
    if quote.status not in ("SAVED", "SENT"):
        raise ApiError(409, "INVALID_STATE", f"Báo giá đang {quote.status} — không Prepare được")
    if not (quote.customer_confirmed_at and quote.customer_confirmed_by):
        raise ApiError(409, "CUSTOMER_NOT_CONFIRMED", "Cần ghi nhận khách đã xác nhận báo giá trước khi Prepare")
    s = get_session(db, str(quote.session_id), for_update=True)
    products = pipeline.load_products(db)
    stock = pipeline.load_stock(list(products), s.store_id)
    if stock is None:
        raise ApiError(503, "POS_UNAVAILABLE", "mock-pos không phản hồi — không recheck được tồn kho")
    lines = lines_of(db, s)
    snap_by_line = {sn.line_id: sn for sn in _snapshots(db, quote)}
    for l in lines:
        sn = snap_by_line.get(l.line_id)
        if sn and l.final_sku != sn.sku and not l.customer_accepted_substitution_at:
            l.final_sku = sn.sku
        pipeline.evaluate(l, products, stock)
        if l.alternatives:
            telemetry.event(db, "AI_SUGGESTED", s.session_id, l.line_id, s.user_id,
                            suggested_sku=l.alternatives[0]["sku"], suggestion_type="alternative")
    refresh_status(s, lines)
    quote.status = "PREPARING"
    quote.status_changed_by, quote.status_changed_at = settings.default_user, now()
    telemetry.event(db, "QUOTE_PREPARED", s.session_id, actor_id=settings.default_user)
    db.commit()
    view = quote_view(db, quote)
    view["changes"] = [{"line_no": l["line_no"], "changed_fields": l["changed_fields"],
                        "price": {"before": l["snapshot"]["unit_price"], "after": (l["live"] or {}).get("unit_price")},
                        "stock": {"before": l["snapshot"]["on_hand"], "after": (l["live"] or {}).get("on_hand")},
                        "alternative_required": l["alternative_required"]}
                       for l in view["lines"] if l["changed_fields"] or l["alternative_required"]]
    view["print_url"] = f"/api/v1/quotes/{quote.quote_id}/print?kind=pick-slip"
    return view


@router.post("/quotes/{quote_id}/confirm")
def confirm_quote(quote_id: str, db: Session = Depends(get_db)):
    quote = get_quote(db, quote_id)
    s = get_session(db, str(quote.session_id), for_update=True)
    return do_confirm(db, s, quote.client_id)


# ---------- print (browser) ----------
PRINT_CSS = """
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:#0f172a;margin:32px;max-width:900px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 6px;text-transform:uppercase;letter-spacing:.04em;color:#334155}
.meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 24px;font-size:13px;margin:12px 0}
.meta b{color:#475569;font-weight:600}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left}th{background:#f1f5f9}
td.n{text-align:right;font-variant-numeric:tabular-nums}.warn{border:2px solid #b45309;background:#fffbeb;padding:10px 12px;margin:16px 0;font-weight:600}
.sim{font-size:11px;color:#64748b;margin-top:24px}button{margin-bottom:16px;padding:6px 14px}
@media print{button{display:none}body{margin:0}}
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


@router.get("/quotes/{quote_id}/print", response_class=HTMLResponse)
def print_quote(quote_id: str, kind: str = Query("quote", pattern="^(quote|pick-slip)$"), db: Session = Depends(get_db)):
    quote = get_quote(db, quote_id)
    touch_expiry(db, quote)
    v = quote_view(db, quote, with_live=False)
    cur = v["currency"]
    if kind == "quote":
        rows = "".join(
            f"<tr><td>{_e(l['sku'])}</td><td>{_e(l['name'])}</td><td class=n>{l['quantity']:g}</td><td>{_e(l['selling_unit'])}</td>"
            f"<td class=n>{l['snapshot']['unit_price']:.2f}</td><td class=n>{l['snapshot']['line_total']:.2f}</td></tr>"
            for l in v["lines"])
        body = f"""
<h1>Báo giá / Quote {_e(v['quote_id'])}</h1>
<div class=meta><div><b>Client ID:</b> {_e(v['client_id'])}</div><div><b>Trạng thái:</b> {_e(v['status'])}</div>
<div><b>Nguồn giá:</b> {_e(v['price_source'])}</div><div><b>Giờ lấy giá (UTC):</b> {_e(v['price_captured_at'][:16].replace('T', ' '))}</div>
<div><b>Hiệu lực đến:</b> {_e(v['valid_until'])}</div><div><b>Bậc chiết khấu:</b> {_e(v['applied_discount_tier'])} ({v['discount_rate'] * 100:g}%)</div>
<div><b>Tiền tệ:</b> {_e(cur)}</div><div><b>Order session:</b> {_e(v['order_session_id'])}</div></div>
{"<div class=warn>ĐÃ HỦY — báo giá này không còn hiệu lực</div>" if v['status'] == 'CANCELLED' else ""}
{"<div class=warn>HẾT HẠN</div>" if v['status'] == 'EXPIRED' else ""}
<table><thead><tr><th>SKU</th><th>Sản phẩm</th><th>SL</th><th>Đơn vị</th><th>Đơn giá ({_e(cur)})</th><th>Thành tiền</th></tr></thead>
<tbody>{rows}</tbody><tfoot><tr><th colspan=5>Tổng (snapshot)</th><th class=n>{v['snapshot_total']:.2f}</th></tr></tfoot></table>
<div class=warn>{_e(QUOTE_DISCLAIMER)}</div>"""
        title = f"Quote {v['quote_id']}"
    else:
        s = db.get(OrderSession, quote.session_id)
        products = pipeline.load_products(db)
        groups: dict[str, list[SessionLine]] = {}
        for l in lines_of(db, s):
            if l.final_sku and l.selling_qty:
                groups.setdefault(products.get(l.final_sku, {}).get("category", "other"), []).append(l)
        sections = ""
        for cat in sorted(groups):
            rows = "".join(
                f"<tr><td>{l.line_no}</td><td>{_e(l.final_sku)}</td><td>{_e(products[l.final_sku]['name'])}</td>"
                f"<td class=n>{float(l.selling_qty):g}</td><td>{_e(l.selling_unit)}</td><td>{_e(l.fulfillment_action or '')}</td></tr>"
                for l in groups[cat])
            sections += f"<h2>{_e(cat)}</h2><table><thead><tr><th>#</th><th>SKU</th><th>Sản phẩm</th><th>SL</th><th>Đơn vị</th><th>Ghi chú</th></tr></thead><tbody>{rows}</tbody></table>"
        body = f"""
<h1>Phiếu soạn hàng / Pick slip — {_e(v['quote_id'])}</h1>
<div class=meta><div><b>Ngày in (UTC):</b> {now().strftime('%Y-%m-%d %H:%M')}</div><div><b>Client ID:</b> {_e(v['client_id'])}</div>
<div><b>Trạng thái báo giá:</b> {_e(v['status'])}</div><div><b>Order session:</b> {_e(v['order_session_id'])}</div></div>
<div class=warn>{_e(PICK_SLIP_NOT_RESERVED)}. {_e(QUOTE_DISCLAIMER)}</div>{sections}"""
        title = f"Pick slip {v['quote_id']}"
    return f"""<!doctype html><html lang=vi><head><meta charset=utf-8><title>{_e(title)}</title><style>{PRINT_CSS}</style></head>
<body><button onclick="window.print()">In / Print</button>{body}
<p class=sim>SiteDesk MVP — POS/ERP/giá/tồn kho là dữ liệu mô phỏng (simulated).</p></body></html>"""
