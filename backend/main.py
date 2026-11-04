import csv
import io
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import Base, SessionLocal, engine, get_db
from db.models import Product, QuoteSession
from db.seed import seed_products
from schemas import QuoteConfirmRequest, QuoteConfirmResponse, QuoteItem, QuoteParseResponse, SubstituteItem
from services.matcher import match_items
from services.parser import extract_lines

pending_quotes: dict[str, QuoteParseResponse] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_products(db)
    yield


app = FastAPI(title="SiteDesk Core API", description="AI-Assisted Trade Counter Engine for Company A (DK/NO/SE)", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str


@app.get("/", tags=["General"])
def root():
    return {"message": "Welcome to SiteDesk Core API", "docs_url": "/docs", "version": "1.0.0"}


@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"
    return {"status": "healthy", "service": "SiteDesk FastAPI Backend", "database": db_status}


@app.post("/api/quote/parse", response_model=QuoteParseResponse, tags=["Quote"])
async def parse_quote(file: UploadFile | None = File(default=None, description="PDF, XLSX, or CSV material list"), raw_text: str | None = Form(default=None, description="Pasted list, one item per line"), db: Session = Depends(get_db)):
    """Extract and match a list. Send multipart/form-data with exactly one input."""
    started = time.perf_counter()
    raw_lines = await extract_lines(file, raw_text)
    try:
        matches = match_items(raw_lines, db)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    items = [QuoteItem(line_no=m.line_no, raw_text=m.raw_text, qty=m.qty, unit=m.unit, matched_sku=m.product.sku, matched_name=m.product.name, confidence=m.confidence, stock_status="in_stock" if m.product.stock_qty > 0 else "out_of_stock", substitutes=[SubstituteItem(sku=p.sku, name=p.name, confidence=score) for p, score in m.substitutes]) for m in matches]
    response = QuoteParseResponse(quote_id=f"Q-{uuid4().hex[:12].upper()}", processing_time_seconds=round(time.perf_counter() - started, 4), items=items)
    # Short-lived MVP review state; use Redis/drafts only if multi-worker deployment is introduced.
    pending_quotes[response.quote_id] = response
    return response


@app.post("/api/quote/confirm", response_model=QuoteConfirmResponse, tags=["Quote"])
def confirm_quote(request: QuoteConfirmRequest, db: Session = Depends(get_db)):
    parsed = pending_quotes.get(request.quote_id)
    if not parsed:
        raise HTTPException(404, "Unknown or expired quote_id; parse the quote again.")
    if len({item.line_no for item in request.items}) != len(request.items):
        raise HTTPException(422, "Each line_no may be confirmed only once.")
    parsed_by_line = {item.line_no: item for item in parsed.items}
    if any(item.line_no not in parsed_by_line for item in request.items):
        raise HTTPException(422, "One or more line_no values do not belong to this quote.")
    skus = {item.final_sku for item in request.items}
    by_sku = {p.sku: p for p in db.query(Product).filter(Product.sku.in_(skus)).all()}
    missing = sorted(skus - set(by_sku))
    if missing:
        raise HTTPException(422, f"Unknown final_sku: {', '.join(missing)}")

    order_id = f"ORD-{uuid4().hex[:12].upper()}"
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["order_id", "line_no", "sku", "name", "qty", "unit", "unit_price", "line_total"])
    persisted_items, unchanged = [], 0
    for chosen in sorted(request.items, key=lambda item: item.line_no):
        product, source = by_sku[chosen.final_sku], parsed_by_line[chosen.line_no]
        line_total = round(chosen.qty * product.price, 2)
        writer.writerow([order_id, chosen.line_no, product.sku, product.name, chosen.qty, product.selling_unit, f"{product.price:.2f}", f"{line_total:.2f}"])
        unchanged += product.sku == source.matched_sku
        persisted_items.append({"line_no": chosen.line_no, "raw_text": source.raw_text, "matched_sku": source.matched_sku, "final_sku": product.sku, "qty": chosen.qty, "unit": product.selling_unit, "unit_price": product.price, "line_total": line_total})
    exported_data = output.getvalue()
    db.add(QuoteSession(quote_id=request.quote_id, processing_time_seconds=parsed.processing_time_seconds, zero_touch_ratio=unchanged / len(request.items), items_data={"order_id": order_id, "export_format": "csv", "items": persisted_items, "exported_data": exported_data}))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This quote has already been confirmed.") from exc
    pending_quotes.pop(request.quote_id, None)
    return QuoteConfirmResponse(order_id=order_id, exported_data=exported_data)
