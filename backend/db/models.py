"""ORM models following SRS v2 §6.1 DDL (money = Numeric, never Float)."""
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .database import Base

SESSION_STATUSES = ("DRAFT", "PARSED", "ANALYZED", "REVIEW_REQUIRED", "READY_TO_CONFIRM", "CONFIRMED",
                    "SENT_OR_EXPORTED", "POS_ACCEPTED", "NEEDS_MANUAL")
LINE_STATUSES = ("NEEDS_CLARIFICATION", "MATCHED", "UNIT_CONVERTED", "SUBSTITUTE_PROPOSED", "CUSTOMER_ACCEPTED")
QUOTE_STATUSES = ("SAVED", "SENT", "PREPARING", "CONFIRMED", "EXPIRED", "CANCELLED")

session_status = Enum(*SESSION_STATUSES, name="session_status")
line_status = Enum(*LINE_STATUSES, name="line_status")
quote_status = Enum(*QUOTE_STATUSES, name="quote_status")


class Store(Base):
    __tablename__ = "stores"
    store_id = Column(String(32), primary_key=True)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), nullable=False)
    timezone = Column(Text, nullable=False)


class DemoUser(Base):
    __tablename__ = "demo_users"
    user_id = Column(String(32), primary_key=True)
    store_id = Column(String(32), ForeignKey("stores.store_id"))
    display_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class DiscountTier(Base):
    __tablename__ = "discount_tiers"
    tier_code = Column(Text, primary_key=True)
    market = Column(String(2), nullable=False)
    discount_rate = Column(Numeric(6, 5), nullable=False)
    valid_from = Column(Date, nullable=False)
    simulated = Column(Boolean, nullable=False, default=True)
    __table_args__ = (CheckConstraint("discount_rate BETWEEN 0 AND 1"),)


class Customer(Base):
    __tablename__ = "customers"
    client_id = Column(String(64), primary_key=True)
    customer_type = Column(Text, nullable=False)
    discount_tier = Column(Text, nullable=False)
    store_id = Column(String(32), ForeignKey("stores.store_id"))
    __table_args__ = (CheckConstraint("customer_type IN ('B2B','B2C_WalkIn')"),)


class Product(Base):
    __tablename__ = "products"
    sku = Column(String(64), primary_key=True)
    market = Column(String(2), nullable=False)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False, index=True)
    selling_unit = Column(Text, nullable=False)
    pack_size = Column(Numeric(14, 4))
    currency = Column(String(3), nullable=False)
    unit_price = Column(Numeric(14, 2), nullable=False)
    technical_specs = Column(JSONB, nullable=False, default=dict)
    aliases = Column(JSONB, nullable=False, default=dict)
    active = Column(Boolean, nullable=False, default=True)
    embedding = Column(Vector(384))  # filled by scripts/reindex_catalog.py (AI owner)
    catalog_version = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StockSnapshot(Base):
    __tablename__ = "stock_snapshots"
    store_id = Column(String(32), ForeignKey("stores.store_id"), primary_key=True)
    sku = Column(String(64), ForeignKey("products.sku"), primary_key=True)
    on_hand = Column(Numeric(14, 3), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class OrderSession(Base):
    __tablename__ = "order_sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_session_id = Column(String(64), unique=True, nullable=False)
    store_id = Column(String(32), ForeignKey("stores.store_id"))
    user_id = Column(String(32), ForeignKey("demo_users.user_id"))
    client_id = Column(String(64), ForeignKey("customers.client_id"))
    status = Column(session_status, nullable=False, default="DRAFT")
    input_type = Column(Text, nullable=False)
    market = Column(String(2), nullable=False, default="DK")
    language_hint = Column(String(2))
    masked_source = Column(Text)
    source_delete_at = Column(DateTime(timezone=True))
    ai_fail_mode = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    processing_started_at = Column(DateTime(timezone=True))
    processing_finished_at = Column(DateTime(timezone=True))
    push_status = Column(Text)
    fulfillment_reference = Column(Text, unique=True)
    pos_order_ref = Column(Text)
    csv_object_key = Column(Text)
    stage_timings = Column(JSONB, nullable=False, default=dict)  # FR-030 thin: last analyze timings (ms)


class SessionLine(Base):
    __tablename__ = "session_lines"
    line_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("order_sessions.session_id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False)
    source_start = Column(Integer)
    source_end = Column(Integer)
    raw_customer_input = Column(Text, nullable=False)
    parsed_name = Column(Text)
    requested_qty = Column(Numeric(14, 4))
    requested_unit = Column(Text)
    unit_raw = Column(Text)
    parse_status = Column(Text, nullable=False)
    parse_warnings = Column(JSONB, nullable=False, default=list)
    line_status = Column(line_status, nullable=False, default="NEEDS_CLARIFICATION")
    attributes = Column(JSONB, nullable=False, default=dict)
    original_sku = Column(String(64), ForeignKey("products.sku"))
    final_sku = Column(String(64), ForeignKey("products.sku"))
    match_score = Column(Numeric(5, 4))
    score_band = Column(Text)
    reasons = Column(JSONB, nullable=False, default=list)
    candidates = Column(JSONB, nullable=False, default=list)
    alternatives = Column(JSONB, nullable=False, default=list)
    selling_qty = Column(Numeric(14, 4))
    selling_unit = Column(Text)
    conversion_formula = Column(Text)
    conversion_block_reason = Column(Text)
    rounded = Column(Boolean, nullable=False, default=False)
    stock_status = Column(Text)
    on_hand = Column(Numeric(14, 3))
    stock_updated_at = Column(DateTime(timezone=True))
    fulfillment_action = Column(Text)
    associate_edited = Column(Boolean, nullable=False, default=False)
    resolved = Column(Boolean, nullable=False, default=False)
    manually_added = Column(Boolean, nullable=False, default=False)
    customer_accepted_substitution_at = Column(DateTime(timezone=True))
    substitution_rejection_reason = Column(Text)
    __table_args__ = (UniqueConstraint("session_id", "line_no"),
                      CheckConstraint("match_score BETWEEN 0 AND 1"))


class Quote(Base):
    __tablename__ = "quotes"
    quote_id = Column(String(32), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("order_sessions.session_id"), unique=True)
    client_id = Column(String(64), ForeignKey("customers.client_id"))
    status = Column(quote_status, nullable=False, default="SAVED")
    customer_confirmed_at = Column(DateTime(timezone=True))
    customer_confirmed_by = Column(String(64))
    valid_until = Column(Date, nullable=False)
    applied_discount_tier = Column(Text, nullable=False)
    price_source = Column(Text, nullable=False)
    price_captured_at = Column(DateTime(timezone=True), nullable=False)
    status_changed_by = Column(String(32))
    status_changed_at = Column(DateTime(timezone=True))
    created_by = Column(String(32), ForeignKey("demo_users.user_id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class QuoteLineSnapshot(Base):
    __tablename__ = "quote_line_snapshots"
    quote_id = Column(String(32), ForeignKey("quotes.quote_id", ondelete="CASCADE"), primary_key=True)
    line_id = Column(UUID(as_uuid=True), ForeignKey("session_lines.line_id"), primary_key=True)
    sku = Column(String(64), ForeignKey("products.sku"))
    quantity = Column(Numeric(14, 4))
    unit_price = Column(Numeric(14, 2), nullable=False)  # net of discount tier at capture time
    list_unit_price = Column(Numeric(14, 2))
    on_hand = Column(Numeric(14, 3), nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False)


class StoreDictionary(Base):
    __tablename__ = "store_dictionary"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(String(32), ForeignKey("stores.store_id"))
    normalized_phrase = Column(Text, nullable=False)
    mapped_sku = Column(String(64), ForeignKey("products.sku"))
    boost = Column(Numeric(4, 3), nullable=False, default=0.05)
    source_line_id = Column(UUID(as_uuid=True), ForeignKey("session_lines.line_id"))
    created_by = Column(String(32), ForeignKey("demo_users.user_id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    active = Column(Boolean, nullable=False, default=True)
    deactivated_by = Column(String(32), ForeignKey("demo_users.user_id"))
    deactivated_at = Column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("store_id", "normalized_phrase", "mapped_sku"),)


class DecisionEvent(Base):
    __tablename__ = "decision_events"
    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("order_sessions.session_id", ondelete="CASCADE"))
    line_id = Column(UUID(as_uuid=True), ForeignKey("session_lines.line_id", ondelete="CASCADE"))
    event_type = Column(Text, nullable=False, index=True)
    actor_id = Column(String(32))
    suggested_sku = Column(String(64))
    selected_sku = Column(String(64))
    match_score = Column(Numeric(5, 4))
    reason_code = Column(Text)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AiInvocation(Base):
    __tablename__ = "ai_invocations"
    invocation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("order_sessions.session_id", ondelete="CASCADE"))
    line_id = Column(UUID(as_uuid=True), ForeignKey("session_lines.line_id", ondelete="CASCADE"))
    step = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False)
    status = Column(Text, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConnectorAttempt(Base):
    __tablename__ = "connector_attempts"
    attempt_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("order_sessions.session_id", ondelete="CASCADE"))
    mode = Column(Text, nullable=False)
    idempotency_key = Column(Text, nullable=False)
    request_hash = Column(Text, nullable=False)
    http_status = Column(Integer)
    result_ref = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
