"""(Re)embed every active product. Run after changing EMBEDDING_MODEL or the catalog.
Usage: python -m scripts.reindex_catalog [--missing-only]"""
import sys
import time

from ai import embedding
from db.database import SessionLocal
from services import retrieval

if __name__ == "__main__":
    t = time.perf_counter()
    with SessionLocal() as db:
        n = retrieval.reindex(db, only_missing="--missing-only" in sys.argv)
    print(f"reindexed {n} products with {embedding.status()} in {time.perf_counter() - t:.1f}s")
