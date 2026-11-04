"""Idempotently embed catalog products that do not have an embedding yet."""

import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import Base, SessionLocal, engine
from db.models import Product
from services.embeddings import EmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


def product_embedding_text(product: Product) -> str:
    specs = json.dumps(product.technical_specs or {}, ensure_ascii=False, sort_keys=True)
    return f"SKU {product.sku}. {product.name}. Category: {product.category}. Specifications: {specs}"


def reindex_missing_products(db: Session, provider: EmbeddingProvider, batch_size: int = 64) -> int:
    products = db.query(Product).filter(Product.embedding.is_(None)).order_by(Product.id).all()
    indexed = 0
    for offset in range(0, len(products), batch_size):
        batch = products[offset:offset + batch_size]
        vectors = provider.embed([product_embedding_text(product) for product in batch])
        if len(vectors) != len(batch):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        for product, vector in zip(batch, vectors):
            product.embedding = vector
        db.commit()
        indexed += len(batch)
    return indexed


def reindex_catalog_if_configured(db: Session) -> int:
    provider = get_embedding_provider()
    if provider is None:
        logger.warning("OPENAI_API_KEY is not set; catalog embeddings are not indexed")
        return 0
    return reindex_missing_products(db, provider)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding vector(384)"))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_products_embedding_hnsw "
            "ON products USING hnsw (embedding vector_cosine_ops)"
        ))
    with SessionLocal() as session:
        count = reindex_catalog_if_configured(session)
        logger.info("Indexed %s catalog products", count)
