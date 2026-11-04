"""Catalog full-text search (manual fallback, MVP-FR-003), customers, health, demo toggles (FR-033)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.common import ApiError
from config import runtime
from db.database import get_db
from db.models import Customer
from ai.embedding import status as embedding_status
from services import pipeline, pos_client, seed
from services.matcher import MUST_MATCH, _tokens

router = APIRouter(prefix="/api/v1", tags=["Catalog & admin"])


@router.get("/catalog/search")
def search(q: str = "", category: Optional[str] = None, limit: int = Query(20, le=50), db: Session = Depends(get_db)):
    products = pipeline.load_products(db).values()
    qt = _tokens(q)
    scored = []
    for p in products:
        if category and p["category"] != category:
            continue
        hay = " ".join([p["sku"], p["name"], p["category"], " ".join(str(v) for v in p["technical_specs"].values()),
                        " ".join(a for v in p["aliases"].values() for a in v)])
        ht = _tokens(hay)
        hit = sum(1 for t in qt if t in ht or any(h.startswith(t) for h in ht)) if qt else 1
        if hit:
            scored.append((hit, p))
    scored.sort(key=lambda x: (-x[0], x[1]["sku"]))
    return {"items": [{"sku": p["sku"], "name": p["name"], "category": p["category"], "selling_unit": p["selling_unit"],
                       "unit_price": p["unit_price"], "currency": p["currency"],
                       "key_specs": {k: p["technical_specs"].get(k) for k in MUST_MATCH.get(p["category"], [])}}
                      for _, p in scored[:limit]], "next_cursor": None}


@router.get("/customers")
def customers(db: Session = Depends(get_db)):
    return {"items": [{"client_id": c.client_id, "customer_type": c.customer_type, "discount_tier": c.discount_tier}
                      for c in db.query(Customer).order_by(Customer.customer_type, Customer.client_id).all()]}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        dbs = "up"
    except Exception:
        dbs = "down"
    pos = pos_client.health()
    mock = "down" if pos.get("status") != "ok" else ("fail_mode" if pos.get("fail_mode") else "up")
    degraded = dbs != "up" or mock != "up" or runtime["ai_fail_mode"] or embedding_status()["status"] != "up"
    return {"status": "degraded" if degraded else "healthy", "database": dbs, "embedding": embedding_status(),
            "llm": "disabled", "mock_pos": mock, "ai_fail_mode": runtime["ai_fail_mode"],
            "pos_fail_mode": bool(pos.get("fail_mode"))}


class FailModes(BaseModel):
    ai: Optional[bool] = None
    pos: Optional[bool] = None


@router.post("/admin/fail-modes")
def fail_modes(body: FailModes):
    """Demo toggles — two independent fail modes (MVP-FR-033)."""
    if body.ai is not None:
        runtime["ai_fail_mode"] = body.ai
    if body.pos is not None:
        try:
            pos_client.admin("fail-mode", {"enabled": body.pos})
        except Exception:
            raise ApiError(503, "POS_UNAVAILABLE", "Không gọi được mock-pos")
    return {"ai_fail_mode": runtime["ai_fail_mode"], "pos_fail_mode": pos_client.health().get("fail_mode")}


class Mutate(BaseModel):
    sku: str
    on_hand: Optional[float] = None
    unit_price: Optional[float] = None


@router.post("/admin/pos-mutate")
def pos_mutate(body: Mutate):
    """Demo: change simulated price/stock so Flow 2 reopen shows a before→after diff (MVP-FR-025)."""
    try:
        return pos_client.admin("mutate", body.model_dump(exclude_none=True))
    except Exception:
        raise ApiError(503, "POS_UNAVAILABLE", "Không gọi được mock-pos hoặc SKU sai")


@router.post("/admin/pos-reset")
def pos_reset():
    return pos_client.admin("reset", {})


@router.post("/admin/sync-catalog")
def sync_catalog(db: Session = Depends(get_db)):
    return seed.sync_from_pos(db)
