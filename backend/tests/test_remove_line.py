"""The associate can drop a line that is not an order line; it is logged and never possible after Confirm. Integration (see conftest)."""


def test_removing_an_unreadable_line_unblocks_confirm(counter):
    sid = counter.open("Materialeliste - Nordbyg ApS\n120 m timber 45x95 C24")
    view = counter.analyze(sid)
    assert any(b["line_no"] == 1 for b in view["blockers"])  # the title is not a product: blocked, no suggestion
    r = counter.call("DELETE", f"/sessions/{sid}/lines/1")
    assert r.status_code == 200, r.text
    after = r.json()
    assert [l["line_no"] for l in after["lines"]] == [2]
    assert after["blockers"] == [] and after["status"] == "READY_TO_CONFIRM"
    assert counter.confirm(sid).status_code == 200


def test_the_last_line_cannot_be_removed(counter):
    sid = counter.open("120 m timber 45x95 C24")
    counter.analyze(sid)
    r = counter.call("DELETE", f"/sessions/{sid}/lines/1")
    assert r.status_code == 409 and r.json()["error"]["code"] == "LAST_LINE"


def test_a_confirmed_order_is_read_only_for_removal(counter):
    sid = counter.open("120 m timber 45x95 C24\n5 poser cement 25 kg")
    counter.analyze(sid)
    counter.resolve_all(sid)
    assert counter.confirm(sid).status_code == 200
    r = counter.call("DELETE", f"/sessions/{sid}/lines/1")
    assert r.status_code == 409 and r.json()["error"]["code"] == "SESSION_LOCKED"


def test_removal_is_recorded_as_a_decision_event(counter):
    from db.database import SessionLocal
    from db.models import DecisionEvent

    sid = counter.open("Materialeliste - Nordbyg ApS\n120 m timber 45x95 C24")
    counter.analyze(sid)
    assert counter.call("DELETE", f"/sessions/{sid}/lines/1").status_code == 200
    with SessionLocal() as db:
        removed = [e for e in db.query(DecisionEvent).filter(DecisionEvent.event_type == "LINE_REMOVED").all() if str(e.session_id) == sid]
    assert len(removed) == 1 and removed[0].metadata_["line_no"] == 1
