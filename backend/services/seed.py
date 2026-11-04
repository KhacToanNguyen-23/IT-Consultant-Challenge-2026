"""Bootstrap reference data: store + demo user (DB-side) and catalog/customers synced from mock-pos.

TODO(data owner): replace with scripts/seed.py using backend/seeds/* (60-80 SKU, SRS §6.3) + reindex embeddings.
"""
import logging
from datetime import date

from sqlalchemy.orm import Session

from config import settings
from db.models import Customer, DemoUser, DiscountTier, Product, Store
from services import pos_client

log = logging.getLogger("sitedesk.seed")


def ensure_reference(db: Session) -> None:
    if not db.get(Store, settings.default_store):
        db.add(Store(store_id=settings.default_store, country="DK", currency="DKK", timezone="Europe/Copenhagen"))
        db.flush()
    if not db.get(DemoUser, settings.default_user):
        # Mock login is cut (SRS §0.3 rule 2): one hard-coded associate, no usable password.
        db.add(DemoUser(user_id=settings.default_user, store_id=settings.default_store,
                        display_name="Demo Associate", password_hash="!disabled"))
    db.commit()


def sync_from_pos(db: Session) -> dict:
    items, version = pos_client.catalog()
    seen = set()
    for i in items:
        seen.add(i["sku"])
        p = db.get(Product, i["sku"])
        if p is None:
            p = Product(sku=i["sku"])
            db.add(p)
        text_changed = (p.name, p.category, p.technical_specs, p.aliases) != (
            i["name"], i["category"], i.get("technical_specs") or {}, i.get("aliases") or {})
        p.market = settings.default_market
        p.name, p.category, p.selling_unit = i["name"], i["category"], i["selling_unit"]
        p.pack_size, p.currency, p.unit_price = i.get("pack_size"), i["currency"], i["unit_price"]
        p.technical_specs, p.aliases = i.get("technical_specs") or {}, i.get("aliases") or {}
        p.catalog_version, p.active = version, True
        if text_changed:
            p.embedding = None  # re-embedded by the reindex hook
    for p in db.query(Product).filter(Product.active.is_(True)).all():
        if p.sku not in seen:
            p.active = False  # removed from source catalog; kept for FK history
    data = pos_client.customers()
    for t in data.get("discount_tiers", []):
        db.merge(DiscountTier(tier_code=t["tier_code"], market=t["market"], discount_rate=t["discount_rate"],
                              valid_from=date.fromisoformat(t["valid_from"]), simulated=t.get("simulated", True)))
    for c in data["items"]:
        db.merge(Customer(client_id=c["client_id"], customer_type=c["type"], discount_tier=c["discount_tier"],
                          store_id=settings.default_store))
    db.commit()
    return {"products": len(items), "customers": len(data["items"]), "catalog_version": version}
