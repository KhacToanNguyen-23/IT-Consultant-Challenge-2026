"""Analyze pipeline for one line: match → conversion → stock → alternatives → line state (SRS v2 §3.2, §5)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from config import STOCK_LABEL
from db.models import Product, SessionLine
from services import conversion, matcher, parser, pos_client
from services.matcher import MUST_MATCH, compare_must


def now() -> datetime:
    return datetime.now(timezone.utc)


def product_dict(p: Product) -> dict:
    return {
        "sku": p.sku, "name": p.name, "category": p.category, "selling_unit": p.selling_unit,
        "pack_size": float(p.pack_size) if p.pack_size is not None else None,
        "unit_price": float(p.unit_price), "currency": p.currency,
        "technical_specs": p.technical_specs or {}, "aliases": p.aliases or {},
    }


def load_products(db: Session) -> dict[str, dict]:
    return {p.sku: product_dict(p) for p in db.query(Product).filter(Product.active.is_(True)).all()}


def load_stock(skus: list[str], store_id: str) -> Optional[dict[str, dict]]:
    """None when POS is unavailable (stock shown as UNKNOWN, never guessed)."""
    try:
        out: dict[str, dict] = {}
        skus = list(skus)
        for i in range(0, len(skus), 50):
            out.update(pos_client.stock(skus[i:i + 50], store_id))
        return out
    except pos_client.PosUnavailable:
        return None


def line_attrs(line: SessionLine) -> dict:
    length_hint = (line.attributes or {}).get("length_hint")
    attrs = parser.extract_attributes(line.parsed_name or "", None)
    if length_hint:
        attrs["length_hint"] = length_hint
    return attrs


def match_lines(db: Session, lines: list[SessionLine], products: dict[str, dict]) -> dict:
    """Batch: embed all readable lines once, vector top-k per line, then hard rules per line."""
    from services import retrieval

    readable = [l for l in lines if l.parse_status != "UNREADABLE" and l.parsed_name]
    attrs = {l.line_id: line_attrs(l) for l in readable}
    sem, timings = retrieval.semantic_candidates(db, [l.parsed_name for l in readable],
                                                 [attrs[l.line_id].get("category") for l in readable])
    sem_by_line = {l.line_id: s for l, s in zip(readable, sem)}
    for l in lines:
        match_line(l, products, sem_by_line.get(l.line_id))
    return timings


def match_line(line: SessionLine, products: dict[str, dict], semantic: Optional[dict] = None) -> None:
    """(Re)compute candidates for the line from its current parsed fields."""
    line.line_status = "NEEDS_CLARIFICATION"
    if line.parse_status == "UNREADABLE" or not line.parsed_name:
        line.candidates, line.original_sku, line.final_sku = [], None, None
        line.match_score, line.score_band, line.attributes = None, None, {}
        line.reasons = ["Dòng không đọc được — cần nhập tay"]
        return
    attrs = line_attrs(line)
    line.attributes = attrs
    cands = matcher.match(line.parsed_name, {k: v for k, v in attrs.items() if k != "length_hint"},
                          list(products.values()), semantic)
    line.candidates = cands
    if cands:
        top = cands[0]
        line.original_sku = top["sku"]
        line.final_sku = top["sku"]
        line.match_score = top["score"]
        line.score_band = top["band"]
    else:
        line.original_sku = line.final_sku = None
        line.match_score, line.score_band = None, "LOW"
    line.resolved = False
    line.customer_accepted_substitution_at = None
    line.substitution_rejection_reason = None


def alternatives_for(line: SessionLine, original: dict, products: dict[str, dict], stock: dict[str, dict]) -> list[dict]:
    must = MUST_MATCH.get(original["category"], [])
    ospecs = original["technical_specs"]
    out = []
    for p in products.values():
        if p["sku"] == original["sku"] or p["category"] != original["category"]:
            continue
        specs, reasons, ok = p["technical_specs"], [], True
        for a in must:
            if a not in ospecs or a not in specs:  # not comparable → fail closed
                ok = False
                break
            if not compare_must(a, ospecs[a], specs[a], for_alternative=True):
                ok = False
                break
            if a == "strength_grade" and specs[a] != ospecs[a]:
                reasons.append(f"grade {specs[a]} ≥ {ospecs[a]}")
            elif a == "treatment" and set(specs[a]) != set(ospecs[a]):
                reasons.append("treatment superset")
            else:
                reasons.append(f"same {a.replace('_mm', '').replace('_', ' ')}")
        if not ok:
            continue
        conv = conversion.convert(_f(line.requested_qty), line.requested_unit, p, (line.attributes or {}).get("length_hint"))
        need = conv["selling_qty"]
        on_hand = (stock.get(p["sku"]) or {}).get("on_hand", 0)
        if need is None or on_hand < need:
            continue
        unit_delta = round(p["unit_price"] - original["unit_price"], 2)
        orig_conv = conversion.convert(_f(line.requested_qty), line.requested_unit, original, (line.attributes or {}).get("length_hint"))
        orig_total = (orig_conv["selling_qty"] or 0) * original["unit_price"]
        out.append({
            "sku": p["sku"], "name": p["name"], "on_hand": on_hand, "needed_quantity": need,
            "selling_unit": p["selling_unit"], "formula": conv["formula"],
            "unit_price": p["unit_price"], "currency": p["currency"], "unit_price_delta": unit_delta,
            "total_price_delta": round(need * p["unit_price"] - orig_total, 2),
            "different_grade": ospecs.get("strength_grade") not in (None, specs.get("strength_grade")),
            "reasons": reasons,
        })
    out.sort(key=lambda a: (abs(a["total_price_delta"]), a["sku"]))
    return out[:2]


def _f(x) -> Optional[float]:
    return float(x) if x is not None else None


def fulfil_line(line: SessionLine, products: dict[str, dict], stock: Optional[dict[str, dict]]) -> None:
    """Conversion + stock + alternatives + single line-state machine (FR-010/012-016/036/039)."""
    line.selling_qty = line.selling_unit = line.conversion_formula = line.conversion_block_reason = None
    line.rounded = False
    line.stock_status = line.on_hand = line.stock_updated_at = None
    line.fulfillment_action = None
    line.alternatives = []
    sku = line.original_sku
    if not sku or sku not in products:
        line.line_status = "NEEDS_CLARIFICATION"
        return
    original = products[sku]
    length_hint = (line.attributes or {}).get("length_hint")
    missing = bool(line.candidates and line.candidates[0]["sku"] == sku and line.candidates[0]["reasons"].get("missing"))
    low = line.score_band == "LOW"
    unresolved_match = (missing or low) and not line.resolved

    conv = conversion.convert(_f(line.requested_qty), line.requested_unit, original, length_hint)
    line.conversion_block_reason = conv["blocked_reason"]

    if unresolved_match or conv["blocked_reason"]:
        line.line_status = "NEEDS_CLARIFICATION"
        line.final_sku = sku
        if conv["selling_qty"] is None:
            return
    line.selling_qty, line.selling_unit = conv["selling_qty"], conv["selling_unit"]
    line.conversion_formula, line.rounded = conv["formula"], conv["rounded"]

    # stock of the requested (original) SKU
    if stock is None:
        line.stock_status = "UNKNOWN"
    else:
        s = stock.get(sku)
        if s:
            line.on_hand, line.stock_updated_at = s["on_hand"], s["updated_at"]
            need = conv["selling_qty"]
            line.stock_status = "IN_STOCK" if s["on_hand"] >= need else ("PARTIAL" if s["on_hand"] > 0 else "OUT_OF_STOCK")
        else:
            line.stock_status = "UNKNOWN"

    if line.line_status == "NEEDS_CLARIFICATION" and (unresolved_match or conv["blocked_reason"]):
        return

    line.line_status = "UNIT_CONVERTED"
    line.final_sku = sku
    line.fulfillment_action = "direct_pick"
    if line.stock_status in ("PARTIAL", "OUT_OF_STOCK") and stock is not None:
        line.alternatives = alternatives_for(line, original, products, stock)
        if line.substitution_rejection_reason:
            line.fulfillment_action = "backorder"
        elif line.alternatives:
            line.line_status = "SUBSTITUTE_PROPOSED"
            line.fulfillment_action = None
        else:
            line.fulfillment_action = "backorder"


def apply_accepted_substitution(line: SessionLine, alt: dict) -> None:
    line.final_sku = alt["sku"]
    line.selling_qty = alt["needed_quantity"]
    line.selling_unit = alt["selling_unit"]
    line.conversion_formula = alt["formula"]
    line.line_status = "CUSTOMER_ACCEPTED"
    line.fulfillment_action = "substituted"


def evaluate(line: SessionLine, products: dict[str, dict], stock: Optional[dict[str, dict]]) -> None:
    """Fulfil + re-apply a previously accepted substitution if still valid."""
    accepted_sku = line.final_sku if line.customer_accepted_substitution_at else None
    fulfil_line(line, products, stock)
    if accepted_sku:
        alt = next((a for a in line.alternatives if a["sku"] == accepted_sku), None)
        if alt:
            apply_accepted_substitution(line, alt)
        else:  # substitute no longer valid (stock changed) → ask again
            line.customer_accepted_substitution_at = None


BLOCKER_TEXT = {
    "NEEDS_CLARIFICATION": "cần làm rõ/chọn SKU",
    "SUBSTITUTE_PROPOSED": "chờ khách đồng ý hoặc từ chối hàng thay thế",
}


def blockers(lines: list[SessionLine]) -> list[dict]:
    out = []
    for l in lines:
        if l.line_status in BLOCKER_TEXT:
            out.append({"line_no": l.line_no, "reason": BLOCKER_TEXT[l.line_status]})
        elif not l.selling_qty:
            out.append({"line_no": l.line_no, "reason": "thiếu số lượng quy đổi"})
    return out


def serialize_line(l: SessionLine, products: dict[str, dict]) -> dict:
    p = products.get(l.final_sku or "") or {}
    op = products.get(l.original_sku or "") or {}
    chips = []
    attrs = {k: v for k, v in (l.attributes or {}).items() if k not in ("category", "length_hint")}
    specs = p.get("technical_specs") or {}
    must = MUST_MATCH.get(p.get("category", ""), [])
    for a in (must + [k for k in specs if k not in must])[:4]:
        if a not in specs:
            continue
        val = specs[a]
        unit = {"thickness_mm": " mm", "length_m": " m", "bag_weight_kg": " kg"}.get(a, "")
        val = {"moisture": "vådrum", "fire": "brand", "impact": "robust", "pressure_treated": "trykimp."}.get(val, val) \
            if isinstance(val, str) else ([{"pressure_treated": "trykimp.", "ntr_ab": "NTR/AB"}.get(v, v) for v in val] if isinstance(val, list) else val)
        label = ", ".join(val) if isinstance(val, list) else (("vådrum" if val else "standard") if a == "moisture_resistant" else f"{val:g}{unit}" if isinstance(val, (int, float)) and not isinstance(val, bool) else f"{val}{unit}")
        if a not in attrs:
            tone = "slate"
        elif compare_must(a, attrs[a], val, for_alternative=l.line_status == "CUSTOMER_ACCEPTED"):
            tone = "emerald"
        else:
            tone = "red"
        chips.append({"attr": a, "value": label, "tone": tone})
    return {
        "line_id": str(l.line_id), "line_no": l.line_no,
        "source": {"text": l.raw_customer_input, "start": l.source_start, "end": l.source_end},
        "parsed": {"name": l.parsed_name, "quantity": _f(l.requested_qty), "unit": l.requested_unit,
                   "unit_raw": l.unit_raw, "status": l.parse_status, "warnings": l.parse_warnings or []},
        "match": {"sku": l.original_sku, "name": op.get("name"), "match_score": _f(l.match_score), "band": l.score_band,
                  "reasons": (l.candidates[0]["reasons"] if l.candidates and l.candidates[0]["sku"] == l.original_sku else {}),
                  "candidates": l.candidates or []},
        "final_sku": l.final_sku, "final_name": p.get("name"),
        "unit_price": p.get("unit_price"), "currency": p.get("currency"),
        "chips": chips,
        "conversion": {"requested": l.unit_raw if "n_x_l_review" in (l.parse_warnings or []) else f"{_fmt(l.requested_qty)} {l.unit_raw or l.requested_unit or ''}".strip(),
                       "selling_quantity": _f(l.selling_qty), "selling_unit": l.selling_unit,
                       "formula": l.conversion_formula, "rounded": l.rounded, "blocked_reason": l.conversion_block_reason},
        "line_status": l.line_status,
        "stock": {"status": l.stock_status, "on_hand": _f(l.on_hand),
                  "updated_at": l.stock_updated_at.isoformat() if hasattr(l.stock_updated_at, "isoformat") else l.stock_updated_at,
                  "label": STOCK_LABEL},
        "alternatives": l.alternatives or [],
        "fulfillment_action": l.fulfillment_action,
        "resolved": l.resolved, "associate_edited": l.associate_edited,
        "substitution": {"accepted_at": l.customer_accepted_substitution_at.isoformat() if l.customer_accepted_substitution_at else None,
                         "rejection_reason": l.substitution_rejection_reason},
        "requires_review": l.line_status in BLOCKER_TEXT or l.score_band != "HIGH" or l.stock_status in ("PARTIAL", "OUT_OF_STOCK"),
    }


def _fmt(x) -> str:
    if x is None:
        return "?"
    f = float(x)
    return str(int(f)) if f == int(f) else str(f)
