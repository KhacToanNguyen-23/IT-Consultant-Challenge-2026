"""Sync catalog/customers/tiers from mock-pos into the SiteDesk DB.  Usage: python -m scripts.seed"""
from db.database import SessionLocal, init_db
from services import seed

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        seed.ensure_reference(db)
        print(seed.sync_from_pos(db))
