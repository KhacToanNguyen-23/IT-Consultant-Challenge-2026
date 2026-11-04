"""Vector retrieval: embed customer lines (batch) → pgvector cosine top-k per line (MVP-FR-007)."""
import logging
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai import embedding
from config import runtime
from db.models import Product

log = logging.getLogger("sitedesk.retrieval")
TOP_K = 10


def available() -> bool:
    return embedding.get() is not None and not runtime["ai_fail_mode"]


def semantic_candidates(db: Session, queries: list[str], categories: list[Optional[str]], k: int = TOP_K) -> tuple[list[Optional[dict]], dict]:
    """Returns ([{sku: cosine}|None per query], timings). None entries → caller uses rules fallback."""
    timings = {"embed_ms": 0.0, "vector_ms": 0.0, "mode": "rules"}
    provider = embedding.get()
    if provider is None or runtime["ai_fail_mode"] or not queries:
        return [None] * len(queries), timings
    try:
        t = time.perf_counter()
        vecs = provider.embed_queries(queries)
        timings["embed_ms"] = round((time.perf_counter() - t) * 1000, 1)
        t = time.perf_counter()
        out = []
        for vec, cat in zip(vecs, categories):
            dist = Product.embedding.cosine_distance(vec)
            stmt = select(Product.sku, dist.label("d")).where(Product.active.is_(True), Product.embedding.is_not(None))
            if cat:
                stmt = stmt.where(Product.category == cat)
            rows = db.execute(stmt.order_by(dist).limit(k)).all()
            out.append({r.sku: 1.0 - float(r.d) for r in rows} if rows else None)
        timings["vector_ms"] = round((time.perf_counter() - t) * 1000, 1)
        timings["mode"] = "embedding"
        return out, timings
    except Exception as e:  # noqa: BLE001 — AI failure must never stop the counter
        log.warning("vector retrieval failed, using rules fallback: %s", e)
        db.rollback()
        timings["mode"] = "rules_after_error"
        return [None] * len(queries), timings


def reindex(db: Session, only_missing: bool = False) -> int:
    """Embed catalog passages into products.embedding (scripts/reindex_catalog.py, startup hook)."""
    from services.pipeline import product_dict

    provider = embedding.get() or embedding.load()
    if provider is None:
        raise RuntimeError(f"embedding provider unavailable: {embedding.status()}")
    q = db.query(Product).filter(Product.active.is_(True))
    if only_missing:
        q = q.filter(Product.embedding.is_(None))
    prods = q.all()
    if not prods:
        return 0
    vecs = provider.embed_passages([embedding.product_passage(product_dict(p)) for p in prods])
    for p, v in zip(prods, vecs):
        p.embedding = v
    db.commit()
    return len(prods)
