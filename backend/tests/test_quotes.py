"""Flow 2 (Pre-order / Advance Quote) state rules, no DB needed. SRS v2 §3.3, MVP-FR-022/027/040."""
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from api import quotes


def _quote(status, confirmed=False, valid_until=None):
    return SimpleNamespace(
        quote_id="BG-DK-0001", session_id="s1", status=status, status_changed_by=None, status_changed_at=None,
        customer_confirmed_at=datetime.now(timezone.utc) if confirmed else None,
        valid_until=valid_until or (datetime.now(timezone.utc).date() + timedelta(days=3)),
    )


@pytest.mark.parametrize("status,confirmed,expected", [
    ("SAVED", False, {"SEND", "RECORD_CUSTOMER_CONFIRMATION", "CANCEL"}),
    ("SENT", False, {"RECORD_CUSTOMER_CONFIRMATION", "CANCEL"}),
    ("SAVED", True, {"SEND", "PREPARE", "CANCEL"}),
    ("SENT", True, {"PREPARE", "CANCEL"}),
    ("PREPARING", True, {"PRINT_PICK_SLIP", "CONFIRM", "CANCEL"}),
    ("CONFIRMED", True, set()),
    ("EXPIRED", True, set()),
    ("CANCELLED", True, set()),
])
def test_allowed_actions_follow_state_machine(status, confirmed, expected):
    assert set(quotes._allowed(_quote(status, confirmed), None)) == expected


def test_prepare_never_offered_without_customer_confirmation():
    for st in ("SAVED", "SENT", "PREPARING"):
        assert "PREPARE" not in quotes._allowed(_quote(st, confirmed=False), None)


class _Db:
    def __init__(self):
        self.committed = False

    def get(self, *_):
        return SimpleNamespace(masked_source="source text")

    def add(self, *_):
        pass

    def commit(self):
        self.committed = True


@pytest.mark.parametrize("status", ["SAVED", "SENT", "PREPARING"])
def test_open_quote_past_validity_expires_on_access(status, monkeypatch):
    monkeypatch.setattr(quotes.telemetry, "event", lambda *a, **k: None)
    q, db = _quote(status, valid_until=date.today() - timedelta(days=5)), _Db()
    quotes.touch_expiry(db, q)
    assert q.status == "EXPIRED" and q.status_changed_by == "system" and db.committed


@pytest.mark.parametrize("status", ["CONFIRMED", "CANCELLED", "EXPIRED"])
def test_closed_quote_is_not_touched_by_expiry(status, monkeypatch):
    monkeypatch.setattr(quotes.telemetry, "event", lambda *a, **k: None)
    q, db = _quote(status, valid_until=date.today() - timedelta(days=5)), _Db()
    quotes.touch_expiry(db, q)
    assert q.status == status and not db.committed


def test_quote_valid_today_does_not_expire(monkeypatch):
    monkeypatch.setattr(quotes.telemetry, "event", lambda *a, **k: None)
    q, db = _quote("SAVED", valid_until=datetime.now(timezone.utc).date()), _Db()
    quotes.touch_expiry(db, q)
    assert q.status == "SAVED"
