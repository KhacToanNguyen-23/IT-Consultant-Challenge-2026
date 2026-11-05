"""Flow 2 (SRS §11.2): quote save/print/prepare/diff/confirm.

The API tests need the running stack and skip without it. Run: docker compose exec backend pytest -q
"""
import os
from datetime import date, timedelta

import httpx
import pytest

from services import connector

API = os.getenv("SITEDESK_API_URL", "http://localhost:8000/api/v1")
MOCK_POS = os.getenv("MOCK_POS_URL", "http://localhost:8001")

TIMBER, DECK = "SKU-DK-4595-480", "SKU-DECK-28120-420"
ROCKWOOL, ISOVER = "SKU-RW-095", "SKU-ISOVER-095"
IN_STOCK_LIST = "Timber 45x95 C24 - 120 m\nTerrassebræt 28x120 trykimp 10 x 4.2m"
SHORT_LIST = IN_STOCK_LIST + "\nRockwool FlexiBatts 95mm - 15 pk"


# ---------- no stack needed ----------
def test_payload_hash_ignores_elapsed_time_only():
    order = {"order_session_id": "SD-1", "processing_time_seconds": 10, "line_items": [{"final_sku": "A", "quantity": 1}]}
    assert connector.payload_hash(order) == connector.payload_hash({**order, "processing_time_seconds": 99})
    assert connector.payload_hash(order) != connector.payload_hash({**order, "line_items": [{"final_sku": "A", "quantity": 2}]})


def test_unexpected_error_stays_inside_cors():
    from fastapi.testclient import TestClient

    import main

    async def boom():
        raise RuntimeError("boom")

    main.app.add_api_route("/__test_boom", boom)
    origin = main.settings.cors_origins[0]
    r = TestClient(main.app, raise_server_exceptions=False).get("/__test_boom", headers={"Origin": origin})
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL"
    assert r.headers.get("access-control-allow-origin") == origin


# ---------- running stack ----------
@pytest.fixture
def api():
    with httpx.Client(base_url=API, timeout=60, headers={"X-Lang": "en"}) as c:
        try:
            c.get("/health")
        except httpx.HTTPError:
            pytest.skip("stack not running")
        yield c
        c.post("/admin/fail-modes", json={"pos": False, "ai": False})
        c.post("/admin/pos-reset")


def session(api, text=IN_STOCK_LIST):
    sid = api.post("/sessions", json={"input_type": "email", "market": "DK"}).json()["session_id"]
    assert api.post(f"/sessions/{sid}/ingest", json={"text": text, "language_hint": "DA"}).status_code == 200
    assert api.post(f"/sessions/{sid}/analyze", json={}).status_code == 200
    return sid


def save(api, sid, client="C-88921"):
    valid = (date.today() + timedelta(days=7)).isoformat()
    r = api.post("/quotes", json={"session_id": sid, "client_id": client, "valid_until": valid})
    assert r.status_code == 200, r.text
    return r.json()


def prepare(api, qid):
    assert api.post(f"/quotes/{qid}/customer-confirmation", json={"channel": "email"}).status_code == 200
    r = api.post(f"/quotes/{qid}/prepare")
    assert r.status_code == 200, r.text
    return r.json()


def accept_isover(api, sid, line_no=3):
    r = api.put(f"/sessions/{sid}/lines/{line_no}/selection", json={"sku": ISOVER, "decision": "SUBSTITUTION_ACCEPTED"})
    assert r.status_code == 200, r.text


def error_code(r):
    return r.json()["error"]["code"]


def test_quote_save_print_prepare_diff_confirm(api):
    sid = session(api)
    q = save(api, sid)
    qid = q["quote_id"]
    assert q["discount_rate"] == 0.1
    assert q["current_total"] == q["snapshot_total"]
    assert all(abs(l["snapshot"]["list_unit_price"] * 0.9 - l["snapshot"]["unit_price"]) < 0.0051 for l in q["lines"])

    assert error_code(api.post(f"/quotes/{qid}/prepare")) == "CUSTOMER_NOT_CONFIRMED"
    assert error_code(api.post(f"/quotes/{qid}/confirm")) == "QUOTE_STATE"
    assert api.post(f"/quotes/{qid}/transitions", json={"to_status": "SENT"}).status_code == 200

    list_price = next(l for l in q["lines"] if l["sku"] == TIMBER)["snapshot"]["list_unit_price"]
    api.post("/admin/pos-mutate", json={"sku": TIMBER, "unit_price": round(list_price * 1.1, 2), "on_hand": 20})
    timber = next(l for l in api.get(f"/quotes/{qid}").json()["lines"] if l["sku"] == TIMBER)
    assert set(timber["changed_fields"]) == {"price", "stock"} and timber["alternative_required"]
    assert timber["snapshot"]["list_unit_price"] == list_price

    prepared = prepare(api, qid)
    assert prepared["status"] == "PREPARING" and prepared["changes"]

    done = api.post(f"/quotes/{qid}/confirm").json()
    assert done["order_status"] == "POS_ACCEPTED" and done["locked"] and done["payload"]["quote_id"] == qid
    assert done["order_session_id"].startswith("SD-")
    replay = api.post(f"/quotes/{qid}/confirm").json()
    assert replay["replayed"] and replay["pos_order_ref"] == done["pos_order_ref"]

    s = api.get(f"/sessions/{sid}").json()
    assert s["masked_source"] is None and s["locked"]
    assert api.get(f"/quotes/{qid}").json()["status"] == "CONFIRMED"


@pytest.mark.parametrize("lang,disclaimer,not_reserved", [
    ("vi", "Giá và tồn kho chỉ mang tính tham khảo, chưa được bảo đảm hoặc giữ chỗ.", "Chưa giữ chỗ trên hệ thống"),
    ("en", "Prices and stock are for reference only", "Not reserved in the system"),
])
def test_both_printouts_carry_the_same_disclaimer(api, lang, disclaimer, not_reserved):
    qid = save(api, session(api))["quote_id"]
    quote = api.get(f"/quotes/{qid}/print", params={"kind": "quote", "lang": lang}).text
    slip = api.get(f"/quotes/{qid}/print", params={"kind": "pick-slip", "lang": lang}).text
    assert disclaimer in quote and disclaimer in slip
    assert not_reserved in slip
    assert "mock-pos simulated" in quote and "C-88921" in quote


def test_refs_stay_unique_after_demo_reset(api):
    refs = []
    for _ in range(2):
        q = save(api, session(api))
        prepare(api, q["quote_id"])
        r = api.post(f"/quotes/{q['quote_id']}/confirm")
        assert r.status_code == 200, r.text
        refs.append(r.json()["pos_order_ref"])
        api.post("/admin/pos-reset")
    assert refs[0] != refs[1]


def test_pos_replays_a_retry_with_new_elapsed_time(api):
    order = {"order_session_id": f"SD-TEST-{os.urandom(4).hex()}", "client_id": "C-88921", "store_id": "DK-CPH-04",
             "processing_time_seconds": 1, "line_items": [{"line_no": 1, "final_sku": TIMBER, "quantity": 1}]}
    key = {"Idempotency-Key": order["order_session_id"]}
    try:
        first = httpx.post(f"{MOCK_POS}/orders", json=order, headers=key)
    except httpx.HTTPError:
        pytest.skip("mock-pos not reachable from here")
    assert first.status_code == 201
    retry = httpx.post(f"{MOCK_POS}/orders", json={**order, "processing_time_seconds": 50}, headers=key)
    assert retry.status_code == 200 and retry.json()["pos_order_ref"] == first.json()["pos_order_ref"]
    changed = httpx.post(f"{MOCK_POS}/orders", json={**order, "line_items": [{"line_no": 1, "final_sku": TIMBER, "quantity": 2}]}, headers=key)
    assert changed.status_code == 409


@pytest.mark.parametrize("stage", ["saved", "preparing"])
def test_order_cannot_drift_from_the_quote(api, stage):
    sid = session(api)
    q = save(api, sid)
    if stage == "preparing":
        prepare(api, q["quote_id"])
    blocked = [
        api.patch(f"/sessions/{sid}/lines/2", json={"requested_qty": 99}),
        api.put(f"/sessions/{sid}/lines/1/selection", json={"sku": "SKU-DK-4595-C18-480", "decision": "SKU_EDITED"}),
        api.put(f"/sessions/{sid}/client", json={"client_id": "C-77310"}),
        api.post(f"/sessions/{sid}/analyze", json={}),
        api.post(f"/sessions/{sid}/ingest", json={"text": "Timber 45x95 C24 - 1 m"}),
    ]
    assert [r.status_code for r in blocked] == [409] * 5
    assert {error_code(r) for r in blocked} == {"QUOTE_LOCKED"}
    assert [l["conversion"]["selling_quantity"] for l in api.get(f"/sessions/{sid}").json()["lines"]] == [l["quantity"] for l in q["lines"]]


def test_session_route_keeps_the_quote_client(api):
    sid = session(api)
    q = save(api, sid, "C-88921")
    prepare(api, q["quote_id"])
    r = api.post(f"/sessions/{sid}/confirm", json={"client_id": "C-65002"})
    assert r.status_code == 200 and r.json()["payload"]["client_id"] == "C-88921"


def test_stock_drop_after_prepare_stops_confirm_once(api):
    q = save(api, session(api))
    qid = q["quote_id"]
    prepare(api, qid)
    api.post("/admin/pos-mutate", json={"sku": TIMBER, "on_hand": 0})
    stopped = api.post(f"/quotes/{qid}/confirm")
    assert stopped.status_code == 409 and error_code(stopped) == "STOCK_CHANGED"
    assert stopped.json()["error"]["details"]["line_nos"] == [1]
    assert api.get(f"/quotes/{qid}").json()["status"] == "PREPARING"
    done = api.post(f"/quotes/{qid}/confirm").json()
    assert next(i for i in done["payload"]["line_items"] if i["final_sku"] == TIMBER)["fulfillment_action"] == "backorder"


def test_quote_needs_real_stock(api):
    api.post("/admin/fail-modes", json={"pos": True})
    sid = session(api)
    valid = (date.today() + timedelta(days=7)).isoformat()
    r = api.post("/quotes", json={"session_id": sid, "client_id": "C-88921", "valid_until": valid})
    assert r.status_code == 503 and error_code(r) == "POS_UNAVAILABLE"
    api.post("/admin/fail-modes", json={"pos": False})
    assert all(l["snapshot"]["on_hand"] > 0 for l in save(api, sid)["lines"])


def test_substitute_before_save_snapshots_its_own_stock(api):
    sid = session(api, SHORT_LIST)
    accept_isover(api, sid)
    q = save(api, sid)
    line = next(l for l in q["lines"] if l["sku"] == ISOVER)
    assert line["snapshot"]["on_hand"] == 42 and line["current"] is None
    reopened = next(l for l in api.get(f"/quotes/{q['quote_id']}").json()["lines"] if l["sku"] == ISOVER)
    assert reopened["changed_fields"] == []


def test_substitute_after_save_keeps_snapshot_and_shows_current_total(api):
    sid = session(api, SHORT_LIST)
    q = save(api, sid)
    accept_isover(api, sid)
    v = api.get(f"/quotes/{q['quote_id']}").json()
    assert v["snapshot_total"] == q["snapshot_total"]
    line = next(l for l in v["lines"] if l["sku"] == ROCKWOOL)
    assert line["current"]["sku"] == ISOVER and line["current"]["unit_price"] == 112.95
    assert line["alternative_required"] is False
    assert v["current_total_delta"] == pytest.approx(round(15 * (112.95 - 108.45), 2))
    assert v["current_total"] == pytest.approx(v["snapshot_total"] + v["current_total_delta"])
    printed = api.get(f"/quotes/{q['quote_id']}/print", params={"kind": "quote", "lang": "en"}).text
    assert f"{v['snapshot_total']:.2f}" in printed and f"{v['current_total']:.2f}" in printed


def test_accepted_substitute_survives_the_original_restocking(api):
    sid = session(api, SHORT_LIST)
    accept_isover(api, sid)
    q = save(api, sid)
    api.post("/admin/pos-mutate", json={"sku": ROCKWOOL, "on_hand": 500})
    prepare(api, q["quote_id"])
    done = api.post(f"/quotes/{q['quote_id']}/confirm").json()
    assert ISOVER in [i["final_sku"] for i in done["payload"]["line_items"]]
