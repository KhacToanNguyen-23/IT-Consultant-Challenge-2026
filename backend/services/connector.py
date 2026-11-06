"""Local Connector: slide-9 payload → mock-pos, CSV fallback (MVP-FR-018/019/020/037, SRS §7.2/7.4)."""
import csv
import hashlib
import io
import json
from typing import Optional

from sqlalchemy.orm import Session

from api.common import ApiError
from config import settings
from db.models import ConnectorAttempt, OrderSession, SessionLine
from i18n import t
from services import pos_client

CSV_HEADER = ["order_session_id", "quote_id", "store_id", "client_id", "confirmed_by_associate", "processing_time_seconds",
              "line_no", "raw_customer_input", "original_sku", "final_sku", "quantity", "selling_unit",
              "confidence_score", "fulfillment_action"]


def build_payload(s: OrderSession, lines: list[SessionLine], quote_id: Optional[str]) -> dict:
    proc = None
    if s.processing_started_at and s.confirmed_at:
        proc = int((s.confirmed_at - s.processing_started_at).total_seconds())
    items = []
    for l in sorted(lines, key=lambda x: x.line_no):
        item = {"line_no": l.line_no, "raw_customer_input": l.raw_customer_input, "final_sku": l.final_sku,
                "quantity": float(l.selling_qty), "selling_unit": l.selling_unit,
                "confidence_score": float(l.match_score) if l.match_score is not None else None,
                "fulfillment_action": l.fulfillment_action or "direct_pick"}
        if l.final_sku != l.original_sku and l.fulfillment_action == "substituted":
            item["original_sku"] = l.original_sku
            item["confidence_score"] = None
        items.append(item)
    return {"order_session_id": s.order_session_id, "quote_id": quote_id, "store_id": s.store_id,
            "client_id": s.client_id, "confirmed_by_associate": s.user_id, "processing_time_seconds": proc,
            "line_items": items}


def _sanitize(v) -> str:
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


def to_csv(payload: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerow(CSV_HEADER)
    head = [payload["order_session_id"], payload.get("quote_id"), payload["store_id"], payload["client_id"],
            payload["confirmed_by_associate"], payload.get("processing_time_seconds")]
    for li in payload["line_items"]:
        w.writerow([_sanitize(x) for x in head + [li["line_no"], li["raw_customer_input"], li.get("original_sku"),
                    li["final_sku"], li["quantity"], li["selling_unit"], li.get("confidence_score"), li["fulfillment_action"]]])
    return "﻿" + buf.getvalue()


def payload_hash(payload: dict) -> str:
    """Order content only: elapsed time changes on every attempt and must not break an idempotent replay."""
    content = {k: v for k, v in payload.items() if k != "processing_time_seconds"}
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def push(db: Session, s: OrderSession, payload: dict, idempotency_key: Optional[str] = None) -> dict:
    """POST to mock-pos with one idempotency key; retry once; else CSV + NEEDS_MANUAL."""
    key = (idempotency_key or s.order_session_id).strip()
    if not key or len(key) > 128:
        raise ValueError("Idempotency-Key must contain 1-128 characters")
    h = payload_hash(payload)
    status, body = 0, None
    if settings.connector_mode == "api":
        for _ in range(2):
            status, body = pos_client.post_order(payload, key)
            db.add(ConnectorAttempt(session_id=s.session_id, mode="api", idempotency_key=key, request_hash=h,
                                    http_status=status or None, result_ref=(body or {}).get("pos_order_ref")))
            if status in (200, 201) or status in (409, 422):
                break
    if status in (200, 201) and body:
        s.status = "POS_ACCEPTED"
        s.push_status = "POS_ACCEPTED"
        s.pos_order_ref = body["pos_order_ref"]
        s.fulfillment_reference = body["pos_order_ref"]
        return {"order_status": "POS_ACCEPTED", "delivery_status": "SENT_OR_EXPORTED", "pos_order_ref": s.pos_order_ref}
    if status == 409:  # POS already holds this order with other content: a CSV would enter it twice
        raise ApiError(409, "POS_CONFLICT", t("pos_conflict"))
    s.status = "NEEDS_MANUAL"
    s.push_status = "SENT_OR_EXPORTED"
    s.fulfillment_reference = f"CSV-{s.order_session_id}"
    s.csv_object_key = f"SiteDesk_{s.order_session_id}_{s.confirmed_at.strftime('%Y%m%dT%H%M%SZ')}.csv"
    db.add(ConnectorAttempt(session_id=s.session_id, mode="csv", idempotency_key=key, request_hash=h,
                            http_status=status or None, result_ref=s.fulfillment_reference))
    return {"order_status": "NEEDS_MANUAL", "delivery_status": "SENT_OR_EXPORTED", "pos_order_ref": None,
            "pos_error": (body or {}).get("error", {}).get("code") if body else "POS_UNREACHABLE"}
