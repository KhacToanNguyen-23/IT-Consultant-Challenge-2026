"""mock-pos [SIMULATED] — stands in for Company A's POS/ERP/PIM/WMS (SRS v2 §7.3).

State is in-memory and reloaded from ./seeds on start or POST /admin/reset.
/admin/* endpoints exist only for demo (mutate price/stock for the Flow 2 diff, toggle FAIL_MODE).
"""
import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

SEED_DIR = Path(__file__).parent / "seeds"

app = FastAPI(title="mock-pos [simulated]", version="0.1.0")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class State:
    def __init__(self) -> None:
        self.reset()
        self.fail_mode = os.getenv("FAIL_MODE", "false").lower() == "true"

    def reset(self) -> None:
        catalog = json.loads((SEED_DIR / "catalog.json").read_text(encoding="utf-8"))
        extra = json.loads((SEED_DIR / "stock_customers.json").read_text(encoding="utf-8"))
        self.catalog_version = catalog["catalog_version"]
        self.items = {i["sku"]: copy.deepcopy(i) for i in catalog["items"]}
        self.store_id = extra["store_id"]
        now = _now()
        self.stock = {sku: {"on_hand": qty, "updated_at": now} for sku, qty in extra["stock"].items()}
        self.customers = {c["client_id"]: c for c in extra["customers"]}
        self.tiers = {t["tier_code"]: t for t in extra["discount_tiers"]}
        self.orders: dict[str, dict] = {}  # idempotency_key -> {hash, response}
        self.order_seq = 122


S = State()


def _fail():
    return JSONResponse(status_code=503, content={"error": {"code": "POS_SIMULATED_FAILURE", "message": "mock-pos FAIL_MODE is enabled"}})


def _not_found(what: str):
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": f"{what} not found"}})


@app.get("/health")
def health():
    return {"status": "ok", "fail_mode": S.fail_mode, "simulated": True}


@app.get("/catalog")
def catalog(market: str = "DK", limit: int = Query(50, le=50), cursor: Optional[str] = None):
    if S.fail_mode:
        return _fail()
    skus = sorted(S.items)
    start = int(cursor or 0)
    page = skus[start:start + limit]
    nxt = str(start + limit) if start + limit < len(skus) else None
    return {"items": [S.items[s] for s in page], "next_cursor": nxt, "catalog_version": S.catalog_version}


@app.get("/stock")
def stock(sku: list[str] = Query(...), store_id: str = "DK-CPH-04"):
    if S.fail_mode:
        return _fail()
    if len(sku) > 50:
        return JSONResponse(status_code=422, content={"error": {"code": "TOO_MANY_SKUS", "message": "max 50"}})
    out = []
    for s in sku:
        if s not in S.stock:
            return _not_found(f"SKU {s}")
        out.append({"sku": s, **S.stock[s]})
    return {"items": out}


@app.get("/prices")
def prices(sku: list[str] = Query(...)):
    """Live list price (used by Flow 2 reopen diff)."""
    if S.fail_mode:
        return _fail()
    return {"items": [{"sku": s, "unit_price": S.items[s]["unit_price"], "currency": S.items[s]["currency"]} for s in sku if s in S.items]}


@app.get("/customers")
def customers_list():
    if S.fail_mode:
        return _fail()
    return {"items": list(S.customers.values()), "discount_tiers": list(S.tiers.values())}


@app.get("/customers/{client_id}")
def customer(client_id: str):
    if S.fail_mode:
        return _fail()
    c = S.customers.get(client_id)
    return c if c else _not_found("customer")


@app.post("/orders")
async def orders(request: Request, idempotency_key: Optional[str] = Header(None)):
    if S.fail_mode:
        return _fail()
    body = await request.body()
    payload = json.loads(body or b"{}")
    key = idempotency_key or payload.get("order_session_id")
    if not key:
        return JSONResponse(status_code=422, content={"error": {"code": "MISSING_IDEMPOTENCY_KEY", "message": "Idempotency-Key required"}})
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    if key in S.orders:
        prev = S.orders[key]
        if prev["hash"] != h:
            return JSONResponse(status_code=409, content={"error": {"code": "IDEMPOTENCY_MISMATCH", "message": "payload differs"}})
        return JSONResponse(status_code=200, content=prev["response"])
    if payload.get("client_id") not in S.customers:
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_CLIENT", "message": "unknown client"}})
    for li in payload.get("line_items", []):
        if li.get("final_sku") not in S.items or not (li.get("quantity") or 0) > 0:
            return JSONResponse(status_code=422, content={"error": {"code": "INVALID_LINE", "message": f"line {li.get('line_no')}"}})
    S.order_seq += 1
    resp = {"pos_order_ref": f"POS-{payload.get('store_id', 'DK')[:2]}-{S.order_seq:06d}", "status": "accepted", "received_at": _now()}
    S.orders[key] = {"hash": h, "response": resp}
    return JSONResponse(status_code=201, content=resp)


# ---------- demo-only admin ----------
class FailModeBody(BaseModel):
    enabled: bool


class MutateBody(BaseModel):
    sku: str
    on_hand: Optional[float] = None
    unit_price: Optional[float] = None


@app.post("/admin/fail-mode")
def set_fail_mode(body: FailModeBody):
    S.fail_mode = body.enabled
    return {"fail_mode": S.fail_mode}


@app.post("/admin/mutate")
def mutate(body: MutateBody):
    if body.sku not in S.items:
        return _not_found("SKU")
    if body.on_hand is not None:
        S.stock[body.sku] = {"on_hand": body.on_hand, "updated_at": _now()}
    if body.unit_price is not None:
        S.items[body.sku]["unit_price"] = body.unit_price
    return {"sku": body.sku, "on_hand": S.stock[body.sku]["on_hand"], "unit_price": S.items[body.sku]["unit_price"]}


@app.post("/admin/reset")
def reset():
    fm = S.fail_mode
    S.reset()
    S.fail_mode = fm
    return {"reset": True}
