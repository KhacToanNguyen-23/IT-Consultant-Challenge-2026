"""MVP-FR-012/015/016/020/037, NFR-002: payload (slide 9), CSV fallback, substitution record, PII. Integration (see conftest)."""
import csv
import io

from services.connector import CSV_HEADER

TOP_KEYS = {"order_session_id", "quote_id", "store_id", "client_id", "confirmed_by_associate", "processing_time_seconds", "line_items"}
LINE_KEYS = {"line_no", "raw_customer_input", "final_sku", "quantity", "selling_unit", "confidence_score", "fulfillment_action"}


def _keep_all(counter, sid):
    """Associate keeps the system's suggestion on every line, then Confirm."""
    counter.analyze(sid)
    counter.resolve_all(sid)
    r = counter.confirm(sid)
    assert r.status_code == 200, r.text
    return r.json()


def test_payload_matches_the_slide_9_contract(counter, pos):
    sid = counter.open("120 m timber 45x95 C24\n5 poser cement 25 kg")
    out = _keep_all(counter, sid)
    p = out["payload"]
    assert set(p) == TOP_KEYS and p["quote_id"] is None  # At-Counter has no quote
    assert p["confirmed_by_associate"] == "EMP-1042" and p["client_id"].endswith("-WALKIN")
    assert [set(i) for i in p["line_items"]] == [LINE_KEYS, LINE_KEYS]
    timber = p["line_items"][0]
    assert timber["quantity"] == 25 and timber["selling_unit"] == "piece_4.8m"  # 120 m / 4.8, in the SKU's selling unit
    assert timber["fulfillment_action"] == "direct_pick" and "original_sku" not in timber
    assert pos.orders[sid_ref(out)]["payload"] == p  # exactly what the POS received


def sid_ref(out):
    return out["order_session_id"]


def test_substitution_records_original_sku_and_nulls_the_score(counter):
    sid = counter.open("10 plader gips vådrum 12.5 mm")
    counter.analyze(sid)
    # the customer asked for the wet-room board that is out of stock; the associate keeps it and asks for alternatives
    assert counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"}).status_code == 200
    alts = counter.call("GET", f"/sessions/{sid}/lines/1/alternatives").json()
    assert [a["sku"] for a in alts["items"]] == ["SKU-GYP-MR-125-B"]  # same board type, enough stock, nothing else
    before = counter.view(sid)["lines"][0]
    assert before["final_sku"] == "SKU-GYP-MR-125"  # SKU does not change before the customer agrees (FR-016/039)
    assert counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-GYP-MR-125-B", "decision": "SUBSTITUTION_ACCEPTED"}).status_code == 200
    out = counter.confirm(sid).json()
    item = out["payload"]["line_items"][0]
    assert item["original_sku"] == "SKU-GYP-MR-125" and item["final_sku"] == "SKU-GYP-MR-125-B"
    assert item["fulfillment_action"] == "substituted" and item["confidence_score"] is None


def test_rejecting_a_substitution_needs_a_reason_and_keeps_the_original(counter):
    sid = counter.open("10 plader gips vådrum 12.5 mm")
    counter.analyze(sid)
    counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"})
    no_reason = counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SUBSTITUTION_REJECTED"})
    assert no_reason.status_code == 422
    ok = counter.call("PUT", f"/sessions/{sid}/lines/1/selection",
                      json={"sku": "SKU-GYP-MR-125", "decision": "SUBSTITUTION_REJECTED", "reason": "Customer will wait"})
    assert ok.status_code == 200 and counter.view(sid)["lines"][0]["final_sku"] == "SKU-GYP-MR-125"


def test_pack_conversion_rounds_up_and_keeps_the_formula(counter):
    sid = counter.open("60 m2 rockwool 95 mm")
    counter.analyze(sid)
    counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-RW-095", "decision": "SKU_EDITED"})
    conv = counter.view(sid)["lines"][0]["conversion"]
    assert conv["selling_quantity"] == 21 and conv["rounded"] is True  # 60 / 2.88 = 20.83 -> 21 (SRS FR-012)
    assert "2.88" in conv["formula"]


def test_csv_fallback_format_is_safe_and_matches_the_contract(counter, pos):
    pos.mode = "503"
    sid = counter.open("=cmd timber 45x95 C24 - 120 m\n5 poser cement 25 kg")
    _keep_all(counter, sid)
    text = counter.call("GET", f"/sessions/{sid}/export.csv").text
    assert text.startswith("\ufeff")
    rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff")), delimiter=";"))
    assert rows[0] == CSV_HEADER and len(rows) == 3
    raw = rows[1][CSV_HEADER.index("raw_customer_input")]
    assert raw.startswith("'=")  # formula injection neutralised (a spreadsheet would otherwise execute it)
    assert rows[1][CSV_HEADER.index("original_sku")] == "" and rows[1][CSV_HEADER.index("quantity")] == "25.0"


def test_contact_details_never_reach_the_pos_the_csv_or_the_stored_session(counter, pos):
    sid = counter.open("120 m timber 45x95 C24 ring +45 22 33 44 55 eller kunde@firma.dk")
    v = counter.analyze(sid)
    blob = str(v)
    assert "22 33 44 55" not in blob and "kunde@firma.dk" not in blob
    out = counter.resolve_all(sid) and counter.confirm(sid).json()
    raw = out["payload"]["line_items"][0]["raw_customer_input"]
    assert "[PHONE]" in raw and "[EMAIL]" in raw and "kunde@firma.dk" not in raw and "22 33 44 55" not in raw
    assert "kunde@firma.dk" not in str(pos.orders)
    assert counter.view(sid)["masked_source"] is None  # source purged after Confirm (retention)


def test_decision_events_cover_the_flow_without_personal_data(counter, app_env):
    from db.database import SessionLocal
    from db.models import DecisionEvent

    sid = counter.open("120 m timber 45x95 C24 ring +45 22 33 44 55\n10 plader gips vådrum 12.5 mm")
    counter.analyze(sid)
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"})
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125-B", "decision": "SUBSTITUTION_ACCEPTED"})
    counter.resolve_all(sid)
    counter.confirm(sid)
    with SessionLocal() as db:
        events = db.query(DecisionEvent).all()
        kinds = {e.event_type for e in events}
        assert {"SESSION_CREATED", "AI_SUGGESTED", "SUBSTITUTION_ACCEPTED", "CONFIRMED", "POS_ACCEPTED"} <= kinds
        assert "22 33 44 55" not in str([(e.event_type, e.metadata_) for e in events])


# ------------------------------------------------------------------ typos in request bodies are errors, not silent no-ops
def test_unknown_body_fields_are_rejected_with_the_field_name(counter):
    sid = counter.open("120 m timber 45x95 C24")
    counter.analyze(sid)
    for method, path, body in [
        ("PATCH", f"/sessions/{sid}/lines/1", {"quantity": 5}),                      # should be requested_qty
        ("PUT", f"/sessions/{sid}/lines/1/selection", {"sku": "SKU-DK-4595-480", "decision": "SKU_KEPT", "why": "x"}),
        ("POST", f"/sessions/{sid}/confirm", {"client": "C-88921"}),
        ("POST", f"/sessions/{sid}/analyze", {"lang": "DA"}),
        ("POST", "/sessions", {"input_type": "paste_text", "markett": "DK"}),
        ("POST", f"/sessions/{sid}/ingest", {"text": "x", "txt": "y"}),
    ]:
        r = counter.call(method, path, json=body)
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION", (method, path, r.text)
        assert r.json()["error"]["details"]["fields"], (method, path)
    assert counter.view(sid)["lines"][0]["parsed"]["quantity"] == 120  # nothing was changed by the rejected calls
