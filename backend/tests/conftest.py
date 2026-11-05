"""Shared test setup.

* Unit tests need no database: DATABASE_URL gets a harmless default so `pytest` works with one command.
* Integration tests (tests/test_flow1_*.py) use a SEPARATE database `sitedesk_test` on the same Postgres, a fake
  mock-pos and the deterministic fake embedding. They never touch the demo database and skip themselves when
  Postgres (with pgvector) or the seed files are not reachable.

Override with TEST_DATABASE_URL, e.g. from the backend container:
  TEST_DATABASE_URL=postgresql+psycopg2://postgres:password123@db:5432/sitedesk_test pytest
"""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:password123@localhost:5432/sitedesk_test")
# Always point the app at the TEST database (never at whatever DATABASE_URL the shell or container carries).
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ.pop("LLM_API_KEY", None)

# repository checkout, or /seeds when running inside the backend container (compose mounts ./mock-pos/seeds there)
SEEDS = next((p for p in (Path(__file__).resolve().parents[2] / "mock-pos" / "seeds", Path("/seeds")) if (p / "catalog.json").exists()),
             Path(__file__).resolve().parents[2] / "mock-pos" / "seeds")


# ---------------------------------------------------------------- database
@pytest.fixture(scope="session")
def database():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    url = make_url(TEST_DB_URL)
    try:
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as c:
            if not c.execute(text("SELECT 1 FROM pg_database WHERE datname=:n"), {"n": url.database}).scalar():
                c.execute(text(f'CREATE DATABASE "{url.database}"'))
        admin.dispose()
        from db.database import Base, engine, init_db

        init_db()
        Base.metadata.drop_all(bind=engine)
        init_db()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"integration tests need Postgres with pgvector at {url.render_as_string(hide_password=True)}: {e}")
    return True


# ---------------------------------------------------------------- fake mock-pos
class FakePos:
    """In-memory stand-in for mock-pos with switchable failure modes: ok | 503 | down (timeout/transport)."""

    def __init__(self):
        catalog = json.loads((SEEDS / "catalog.json").read_text(encoding="utf-8"))
        extra = json.loads((SEEDS / "stock_customers.json").read_text(encoding="utf-8"))
        self.items = {i["sku"]: copy.deepcopy(i) for i in catalog["items"]}
        self.version = catalog["catalog_version"]
        self.stock_data = dict(extra["stock"])
        self.customers_data = extra
        self.mode = "ok"
        self.orders: dict[str, dict] = {}
        self.post_calls = 0
        self.seq = 122

    def _check(self):
        from services.pos_client import PosUnavailable

        if self.mode != "ok":
            raise PosUnavailable(self.mode)

    def catalog(self):
        self._check()
        return list(self.items.values()), self.version

    def customers(self):
        self._check()
        return {"items": [{**c, "type": c["type"]} for c in self.customers_data["customers"]],
                "discount_tiers": self.customers_data["discount_tiers"]}

    def stock(self, skus, store_id):
        self._check()
        return {s: {"sku": s, "on_hand": self.stock_data[s], "updated_at": "2026-11-06T08:00:00Z"} for s in skus if s in self.stock_data}

    def prices(self, skus):
        self._check()
        return {s: self.items[s]["unit_price"] for s in skus if s in self.items}

    def post_order(self, payload, key):
        self.post_calls += 1
        if self.mode == "503":
            return 503, {"error": {"code": "POS_SIMULATED_FAILURE"}}
        if self.mode == "down":
            return 0, None
        h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if key in self.orders:  # idempotent replay
            return (200, self.orders[key]["response"]) if self.orders[key]["hash"] == h else (409, None)
        self.seq += 1
        resp = {"pos_order_ref": f"POS-DK-{self.seq:06d}", "status": "accepted"}
        self.orders[key] = {"hash": h, "response": resp, "payload": payload}
        return 201, resp

    def health(self):
        return {"status": "ok" if self.mode == "ok" else "down", "fail_mode": self.mode != "ok"}

    def admin(self, path, body):
        if path == "fail-mode":
            self.mode = "503" if body.get("enabled") else "ok"
        return {}


@pytest.fixture
def pos(database, monkeypatch):
    if not (SEEDS / "catalog.json").exists():
        pytest.skip("mock-pos seed files not found (run from the repository checkout)")
    from services import pos_client

    fake = FakePos()
    for name in ("catalog", "customers", "stock", "prices", "post_order", "health", "admin"):
        monkeypatch.setattr(pos_client, name, getattr(fake, name))
    return fake


# ---------------------------------------------------------------- app + seeded catalog
@pytest.fixture
def app_env(pos):
    """Seed reference data + catalog once per test (cheap: 62 SKU) and use deterministic fake embeddings."""
    from ai import embedding, llm
    from config import runtime
    from db.database import SessionLocal
    from services import retrieval, seed

    from config import settings

    embedding.set_provider_for_tests(embedding.FakeEmbedding())
    llm.set_provider_for_tests(None)
    runtime["ai_fail_mode"] = False
    saved_auth = (settings.demo_password, settings.auth_required)
    settings.demo_password, settings.auth_required = "test-only-password", False  # simulated login on, enforcement off
    from sqlalchemy import text

    with SessionLocal() as db:
        # every test starts with no sessions/quotes/events (the fake POS also restarts its order numbers)
        db.execute(text("TRUNCATE order_sessions, decision_events, ai_invocations, connector_attempts RESTART IDENTITY CASCADE"))
        db.commit()
        seed.ensure_reference(db)
        seed.sync_from_pos(db)
        retrieval.reindex(db, only_missing=True)
    yield pos
    settings.demo_password, settings.auth_required = saved_auth
    runtime["ai_fail_mode"] = False
    embedding.set_provider_for_tests(None)
    llm.set_provider_for_tests(None)


@pytest.fixture
def client(app_env):
    from fastapi.testclient import TestClient

    import main

    return TestClient(main.app, raise_server_exceptions=False)  # no `with`: skips the real startup hooks


# ---------------------------------------------------------------- helpers shared by integration tests
class Counter:
    """Drives the At-Counter flow the way a staff member does."""

    def __init__(self, client):
        self.c = client
        self.base = "/api/v1"

    def call(self, method, path, **kw):
        r = self.c.request(method, self.base + path, **kw)
        return r

    def open(self, text, input_type="paste_text"):
        sid = self.call("POST", "/sessions", json={"input_type": input_type, "market": "DK"}).json()["session_id"]
        r = self.call("POST", f"/sessions/{sid}/ingest", json={"text": text})
        assert r.status_code == 200, r.text
        return sid

    def analyze(self, sid):
        r = self.call("POST", f"/sessions/{sid}/analyze")
        assert r.status_code == 200, r.text
        return r.json()

    def view(self, sid):
        return self.call("GET", f"/sessions/{sid}").json()

    def resolve_all(self, sid, fallback_sku="SKU-DK-4595-480"):
        """Fix every blocker like an associate: give a missing quantity/unit, then keep/choose a SKU."""
        for _ in range(3):
            v = self.view(sid)
            todo = [l for l in v["lines"] if l["line_status"] == "NEEDS_CLARIFICATION" or not (l.get("conversion") or {}).get("selling_quantity")]
            if not todo:
                return v
            for l in todo:
                n = l["line_no"]
                parsed = l.get("parsed") or {}
                if parsed.get("quantity") is None or parsed.get("unit") is None:
                    self.call("PATCH", f"/sessions/{sid}/lines/{n}",
                              json={"requested_qty": parsed.get("quantity") or 1, "requested_unit": parsed.get("unit") or "piece"})
                    l = next(x for x in self.view(sid)["lines"] if x["line_no"] == n)
                sku = l.get("final_sku") or ((l.get("match") or {}).get("candidates") or [{}])[0].get("sku") or fallback_sku
                r = self.call("PUT", f"/sessions/{sid}/lines/{n}/selection", json={"sku": sku, "decision": "SKU_KEPT" if l.get("final_sku") else "SKU_EDITED"})
                assert r.status_code == 200, r.text
        return self.view(sid)

    def confirm(self, sid):
        return self.call("POST", f"/sessions/{sid}/confirm", json={})


@pytest.fixture
def counter(client):
    return Counter(client)


ORDER = "120 m timber 45x95 C24\n5 poser cement 25 kg\n10 x 4.8m timber 45x95 C24"
