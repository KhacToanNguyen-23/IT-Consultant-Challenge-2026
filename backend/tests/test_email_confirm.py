"""An e-mail request can only be confirmed through its quote, after the customer's approval. Integration (see conftest)."""
from datetime import date, timedelta

TEXT = "120 m timber 45x95 C24\n5 poser cement 25 kg"


def test_email_session_without_a_quote_cannot_be_confirmed(counter):
    sid = counter.open(TEXT, input_type="email")
    counter.analyze(sid)
    counter.resolve_all(sid)
    r = counter.confirm(sid)
    assert r.status_code == 409 and r.json()["error"]["code"] == "QUOTE_REQUIRED"


def test_counter_session_is_still_confirmed_directly(counter):
    sid = counter.open(TEXT)  # paste_text: the associate is serving the customer at the counter
    counter.analyze(sid)
    counter.resolve_all(sid)
    assert counter.confirm(sid).status_code == 200


def test_quote_without_customer_approval_cannot_be_prepared_or_confirmed(counter):
    sid = counter.open(TEXT, input_type="email")
    counter.analyze(sid)
    counter.resolve_all(sid)
    valid = (date.today() + timedelta(days=7)).isoformat()
    q = counter.call("POST", "/quotes", json={"session_id": sid, "client_id": "C-88921", "valid_until": valid})
    assert q.status_code == 200, q.text
    qid = q.json()["quote_id"]
    assert counter.call("POST", f"/quotes/{qid}/transitions", json={"to_status": "SENT"}).status_code == 200  # "sent" is not approval
    assert counter.call("POST", f"/quotes/{qid}/prepare").json()["error"]["code"] == "CUSTOMER_NOT_CONFIRMED"
    r = counter.confirm(sid)
    assert r.status_code == 409 and r.json()["error"]["code"] == "QUOTE_STATE"
