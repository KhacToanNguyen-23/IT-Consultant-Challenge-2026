import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from db.models import Product


@dataclass
class MatchResult:
    line_no: int
    raw_text: str
    qty: float
    unit: str
    product: Product
    confidence: float
    substitutes: list[tuple[Product, float]]


UNITS = "bag|bags|box|boxes|sheet|sheets|piece|pieces|pack|packs|bucket|buckets|kg|m|l"


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9.]+", value.lower()))


def _parse_qty_unit(line: str) -> tuple[float, str]:
    match = re.match(rf"^\s*(\d+(?:\.\d+)?)\s*(?:x\s*)?({UNITS})?\b", line, re.I)
    if not match:
        return 1.0, "piece"
    unit = (match.group(2) or "piece").lower()
    return float(match.group(1)), unit


def _name_score(raw: str, product: Product) -> float:
    left, right = _normalise(raw), _normalise(product.name)
    sequence = SequenceMatcher(None, left, right).ratio()
    left_tokens, right_tokens = set(left.split()), set(right.split())
    overlap = len(left_tokens & right_tokens) / max(1, len(right_tokens))
    substring = 1.0 if left in right or right in left else 0.0
    return round(min(1.0, 0.55 * sequence + 0.35 * overlap + 0.10 * substring), 3)


def _substitute_score(source: Product, candidate: Product) -> float:
    if source.category != candidate.category:
        return 0.0
    source_specs, candidate_specs = source.technical_specs or {}, candidate.technical_specs or {}
    keys = set(source_specs) | set(candidate_specs)
    spec_score = sum(source_specs.get(key) == candidate_specs.get(key) for key in keys) / max(1, len(keys))
    price_score = 1 - min(abs(source.price - candidate.price) / max(source.price, 0.01), 1)
    return round(0.85 * spec_score + 0.15 * price_score, 3)


def match_items(raw_lines: list[str], db: Session) -> list[MatchResult]:
    """MVP lexical matcher.

    AI ENGINEER SWAP SEAM: replace this function's name matching with LLM parsing
    plus FAISS/ChromaDB vector search. Keep MatchResult and the API schemas stable.
    Runtime substitutions should continue to use technical_specs, not a table.
    """
    products = db.query(Product).order_by(Product.sku).all()
    if not products:
        raise RuntimeError("Product catalog is empty; run python -m db.seed")
    results = []
    for line_no, raw in enumerate(raw_lines, 1):
        qty, unit = _parse_qty_unit(raw)
        product, score = max(((product, _name_score(raw, product)) for product in products), key=lambda pair: pair[1])
        substitutes: list[tuple[Product, float]] = []
        if product.stock_qty <= 0:
            candidates = [(candidate, _substitute_score(product, candidate)) for candidate in products
                          if candidate.sku != product.sku and candidate.stock_qty > 0]
            substitutes = sorted((pair for pair in candidates if pair[1] > 0), key=lambda pair: pair[1], reverse=True)[:2]
        results.append(MatchResult(line_no, raw, qty, unit, product, score, substitutes))
    return results
