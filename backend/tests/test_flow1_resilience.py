"""NFR-006 / MVP-FR-003, 018, 019, 033: "the counter never stops". Integration tests on a real Postgres (see conftest).

Each test is a failure the SRS names in §11.2 (fault suite): AI off, model not loaded, embedding error mid-request,
LLM timeout / bad JSON, POS 503, POS timeout, POS down while analysing, DB down, duplicate and concurrent Confirm.
"""
import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from ai import embedding, llm
from config import runtime

ORDER = "120 m timber 45x95 C24\n5 poser cement 25 kg\n10 x 4.8m timber 45x95 C24"


def test_tests_never_touch_the_demo_database():
    assert os.environ["DATABASE_URL"].rsplit("/", 1)[-1].endswith("_test")


# ------------------------------------------------------------------ AI failures: staff keep working
def test_ai_switched_off_still_reaches_confirm_with_manual_choices(counter, pos):
    runtime["ai_fail_mode"] = True
    sid = counter.open(ORDER + "\n45x95 timber")
    v = counter.analyze(sid)
    assert v["ai_degraded"] is True
    assert {c["mode"] for l in v["lines"] if (l.get("match") or {}).get("candidates") for c in l["match"]["candidates"]} == {"rules"}
    counter.resolve_all(sid)
    r = counter.confirm(sid)
    assert r.status_code == 200 and r.json()["order_status"] == "POS_ACCEPTED"


def test_manual_sku_search_works_while_ai_is_off(counter):
    runtime["ai_fail_mode"] = True
    r = counter.call("GET", "/catalog/search", params={"q": "timber 45x95 C24"})
    assert r.status_code == 200 and any(i["sku"] == "SKU-DK-4595-480" for i in r.json()["items"])


def test_model_not_loaded_yet_falls_back_to_rules_instead_of_failing(counter):
    embedding.set_provider_for_tests(None)  # e.g. the first ~30 s after startup
    sid = counter.open(ORDER)
    v = counter.analyze(sid)
    assert v["ai_degraded"] is True and v["lines"][0]["final_sku"] == "SKU-DK-4595-480"
    counter.resolve_all(sid)
    assert counter.confirm(sid).json()["order_status"] == "POS_ACCEPTED"


def test_embedding_error_in_the_middle_of_a_request_is_survived(counter):
    class Broken(embedding.FakeEmbedding):
        def embed(self, texts):
            raise RuntimeError("model crashed")

    embedding.set_provider_for_tests(Broken())
    sid = counter.open(ORDER)
    v = counter.analyze(sid)  # must not be a 500
    assert v["ai_degraded"] is True and len(v["lines"]) == 3
    counter.resolve_all(sid)
    assert counter.confirm(sid).json()["order_status"] == "POS_ACCEPTED"


@pytest.mark.parametrize("replies", [["not json", "still not json"], [TimeoutError("llm timeout")]])
def test_llm_timeout_or_bad_json_never_blocks_analysis(counter, replies):
    fake = llm.FakeLLM(list(replies))
    llm.set_provider_for_tests(fake)
    sid = counter.open("Bathroom wallboard 12.5mm 10 stk\n" + ORDER)  # first line is ambiguous → the LLM is asked
    v = counter.analyze(sid)
    assert len(v["lines"]) == 4 and fake.calls and len(fake.calls) <= 2  # one repair retry at most, then rules only
    assert v["lines"][0]["line_status"] == "NEEDS_CLARIFICATION"  # unclear stays unclear: AI failure never guesses


# ------------------------------------------------------------------ POS failures
def test_pos_503_exports_csv_and_keeps_the_order(counter, pos):
    pos.mode = "503"
    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)
    r = counter.confirm(sid).json()
    assert r["order_status"] == "NEEDS_MANUAL" and r["fulfillment_reference"].startswith("CSV-")
    assert pos.post_calls == 2  # one retry, then the CSV fallback (OI-07)
    csv = counter.call("GET", f"/sessions/{sid}/export.csv")
    assert csv.status_code == 200 and csv.text.startswith("﻿order_session_id;")
    again = counter.confirm(sid).json()
    assert again["replayed"] is True and again["fulfillment_reference"] == r["fulfillment_reference"]


def test_pos_timeout_is_treated_like_a_failure_not_a_crash(counter, pos):
    pos.mode = "down"
    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)
    assert counter.confirm(sid).json()["order_status"] == "NEEDS_MANUAL"


def test_pos_down_while_analysing_shows_stock_unknown_and_still_confirms(counter, pos):
    pos.mode = "down"
    sid = counter.open(ORDER)
    v = counter.analyze(sid)
    assert {l["stock"]["status"] for l in v["lines"]} == {"UNKNOWN"}  # never guessed
    assert all(l["stock"].get("label") for l in v["lines"])
    counter.resolve_all(sid)
    assert counter.confirm(sid).json()["order_status"] == "NEEDS_MANUAL"  # POS is down at confirm too → CSV


def test_ai_and_pos_down_together_the_counter_still_finishes(counter, pos):
    runtime["ai_fail_mode"] = True
    pos.mode = "503"
    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)
    r = counter.confirm(sid).json()
    assert r["order_status"] == "NEEDS_MANUAL" and r["fulfillment_reference"].startswith("CSV-")


# ------------------------------------------------------------------ duplicate / concurrent Confirm
def test_confirm_twice_creates_exactly_one_pos_order(counter, pos):
    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)
    first = counter.confirm(sid).json()
    second = counter.confirm(sid).json()
    assert first["replayed"] is False and second["replayed"] is True
    assert first["pos_order_ref"] == second["pos_order_ref"] and len(pos.orders) == 1


def test_two_simultaneous_confirms_create_exactly_one_order(counter, client, pos):
    import main

    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)

    def go(_):
        c = TestClient(main.app, raise_server_exceptions=False)
        return c.post(f"/api/v1/sessions/{sid}/confirm", json={})

    with ThreadPoolExecutor(2) as ex:
        results = list(ex.map(go, range(2)))
    assert [r.status_code for r in results] == [200, 200]
    assert len({r.json()["fulfillment_reference"] for r in results}) == 1 and len(pos.orders) == 1


def test_a_confirmed_order_is_read_only(counter):
    sid = counter.open(ORDER)
    counter.analyze(sid)
    counter.resolve_all(sid)
    counter.confirm(sid)
    r = counter.call("PATCH", f"/sessions/{sid}/lines/1", json={"requested_qty": 999})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SESSION_LOCKED"


# ------------------------------------------------------------------ database down
def test_database_down_is_a_503_with_the_standard_envelope(client):
    import main
    from db.database import get_db

    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused password=hunter2"))
        yield  # pragma: no cover

    main.app.dependency_overrides[get_db] = broken_db
    try:
        r = client.post("/api/v1/sessions", json={"input_type": "paste_text", "market": "DK"})
    finally:
        main.app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 503 and r.json()["error"]["code"] == "DB_UNAVAILABLE"
    assert "hunter2" not in r.text and r.json()["error"]["request_id"].startswith("req_")
