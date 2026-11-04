from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .database import Base

class Product(Base):
    """Catalog items from PIM/WMS"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    selling_unit = Column(String(50), nullable=False)
    unit_multiplier = Column(Float, default=1.0)
    price = Column(Float, nullable=False)
    stock_qty = Column(Integer, default=0)
    technical_specs = Column(JSON, default=dict)

class StoreDictionary(Base):
    """Self-learning trade slang dictionary (FR-07)"""
    __tablename__ = "store_dictionary"

    id = Column(Integer, primary_key=True, index=True)
    raw_phrase = Column(String(255), unique=True, index=True, nullable=False)
    mapped_sku = Column(String(50), nullable=False)
    confidence_boost = Column(Float, default=0.95)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuoteSession(Base):
    """Quote & Telemetry Session (FR-06 & FR-07)"""
    __tablename__ = "quote_sessions"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String(50), unique=True, index=True, nullable=False)
    store_id = Column(String(50), default="DK-CPH-04")
    client_id = Column(String(50), default="C-88921")
    processing_time_seconds = Column(Float, default=0.0)
    zero_touch_ratio = Column(Float, default=0.0)
    items_data = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
