from typing import Literal

from pydantic import BaseModel, Field


class SubstituteItem(BaseModel):
    sku: str
    name: str
    confidence: float = Field(ge=0, le=1)


class QuoteItem(BaseModel):
    line_no: int
    raw_text: str
    qty: float = Field(gt=0)
    unit: str
    matched_sku: str
    matched_name: str
    confidence: float = Field(ge=0, le=1)
    stock_status: Literal["in_stock", "out_of_stock"]
    substitutes: list[SubstituteItem]


class QuoteParseResponse(BaseModel):
    quote_id: str
    processing_time_seconds: float
    items: list[QuoteItem]


class ConfirmItem(BaseModel):
    line_no: int = Field(gt=0)
    final_sku: str
    qty: float = Field(gt=0)


class QuoteConfirmRequest(BaseModel):
    quote_id: str
    items: list[ConfirmItem] = Field(min_length=1)


class QuoteConfirmResponse(BaseModel):
    order_id: str
    export_format: Literal["csv"] = "csv"
    exported_data: str
