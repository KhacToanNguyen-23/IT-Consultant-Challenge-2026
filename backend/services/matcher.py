import logging
import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from db.models import Product
from services.embeddings import get_embedding_provider

logger = logging.getLogger(__name__)


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
STRENGTH_RANK = {grade: rank for rank, grade in enumerate(("C14", "C16", "C18", "C24", "C30"))}
MUST_MATCH = {
    "timber": {"cross_section", "strength_grade"},
    "gypsum": {"thickness_mm", "type"},
    "cement_mortar": {"bag_weight", "type", "grade"},
    "insulation": {"thickness_mm"},
    "decking": {"cross_section", "treatment"},
}


def _normalise(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9.]+", value.lower()))


def _parse_qty_unit(line: str) -> tuple[float, str]:
    match = re.match(rf"^\s*(\d+(?:\.\d+)?)\s*(?:x\s*)?({UNITS})?\b", line, re.I)
    if not match:
        return 1.0, "piece"
    return float(match.group(1)), (match.group(2) or "piece").lower()


def _name_score(raw: str, product: Product) -> float:
    left, right = _normalise(raw), _normalise(product.name)
    sequence = SequenceMatcher(None, left, right).ratio()
    left_tokens, right_tokens = set(left.split()), set(right.split())
    overlap = len(left_tokens & right_tokens) / max(1, len(right_tokens))
    substring = 1.0 if left in right or right in left else 0.0
    return round(min(1.0, 0.55 * sequence + 0.35 * overlap + 0.10 * substring), 3)


def _legacy_substitute_score(source: Product, candidate: Product) -> float:
    if source.category != candidate.category:
        return 0.0
    source_specs, candidate_specs = source.technical_specs or {}, candidate.technical_specs or {}
    keys = set(source_specs) | set(candidate_specs)
    spec_score = sum(source_specs.get(key) == candidate_specs.get(key) for key in keys) / max(1, len(keys))
    price_score = 1 - min(abs(source.price - candidate.price) / max(source.price, 0.01), 1)
    return round(0.85 * spec_score + 0.15 * price_score, 3)


def _canonical_section(value: str) -> str:
    numbers = re.findall(r"\d+(?:\.\d+)?", value)
    return "x".join(f"{float(number):g}" for number in numbers[:2])


def _extract_attributes(raw: str, category: str) -> dict[str, Any]:
    text = raw.lower()
    attrs: dict[str, Any] = {}
    section = re.search(r"\b(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:mm)?\b", raw, re.I)
    if section:
        attrs["cross_section"] = _canonical_section(section.group(0))

    if category == "timber":
        grade = re.search(r"\bC(?:14|16|18|24|30)\b", raw, re.I)
        if grade:
            attrs["strength_grade"] = grade.group(0).upper()
    elif category == "gypsum":
        thickness = re.search(r"\b(6\.5|9\.5|12\.5|15)(?:\s*mm|\s*x)", raw, re.I)
        if thickness:
            attrs["thickness_mm"] = float(thickness.group(1))
        type_terms = (("moisture_resistant", ("moisture", "wet room", "vådrum", "chống ẩm")),
                      ("fire_resistant", ("fire", "brand", "chống cháy")),
                      ("acoustic", ("acoustic", "sound", "cách âm")),
                      ("flexible", ("flexible", "bend", "uốn")),
                      ("standard", ("standard", "regular", "tiêu chuẩn")))
        for value, terms in type_terms:
            if any(term in text for term in terms):
                attrs["type"] = value
                break
    elif category == "cement_mortar":
        weight = re.search(r"\b(\d+(?:\.\d+)?)\s*kg\b", raw, re.I)
        if weight:
            attrs["bag_weight"] = float(weight.group(1))
        grade = re.search(r"\b(32\.5N|42\.5N|42\.5R|52\.5N|M5|M10|R3|R4|GP|CT-C25|CT-C30)\b", raw, re.I)
        if grade:
            attrs["grade"] = grade.group(1).upper()
        type_terms = (("rapid_cement", ("rapid", "fast set", "đông nhanh")),
                      ("white_cement", ("white cement", "xi măng trắng")),
                      ("portland_cement", ("portland", "cement", "xi măng")),
                      ("masonry_mortar", ("masonry mortar", "mørtel", "vữa xây")),
                      ("repair_mortar", ("repair mortar", "vữa sửa")),
                      ("render_mortar", ("render mortar", "plaster mortar", "vữa trát")),
                      ("floor_screed", ("floor screed", "screed", "vữa cán nền")))
        for value, terms in type_terms:
            if any(term in text for term in terms):
                attrs["type"] = value
                break
    elif category == "insulation":
        thickness = re.search(r"\b(\d+(?:\.\d+)?)\s*mm\b", raw, re.I)
        if thickness:
            attrs["thickness_mm"] = float(thickness.group(1))
        for value, terms in (("mineral_wool", ("mineral", "rock wool", "stenuld")),
                             ("glass_wool", ("glass wool", "glasuld")), ("pir", ("pir",))):
            if any(term in text for term in terms):
                attrs["type"] = value
                break
    elif category == "decking":
        treatments = set()
        treatment_terms = {"pressure_treated": ("pressure treated", "impregnated", "tẩm áp lực"),
                           "heat_treated": ("heat treated", "thermowood", "nhiệt"),
                           "water_repellent": ("water repellent", "waterproof", "chống nước"),
                           "rot_resistant": ("rot resistant", "chống mục"),
                           "uv_resistant": ("uv resistant", "chống uv"),
                           "untreated": ("untreated", "chưa xử lý")}
        for value, terms in treatment_terms.items():
            if any(term in text for term in terms):
                treatments.add(value)
        if treatments:
            attrs["treatment"] = treatments
    return attrs


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), abs_tol=0.01)
    return left == right


def _satisfies_constraints(category: str, required: dict[str, Any], specs: dict[str, Any]) -> bool:
    for key in MUST_MATCH[category]:
        if key not in required:
            continue
        candidate = specs.get(key)
        if candidate is None:
            return False
        if key == "strength_grade":
            if STRENGTH_RANK.get(str(candidate).upper(), -1) < STRENGTH_RANK.get(str(required[key]).upper(), 999):
                return False
        elif key == "treatment":
            if not set(required[key]).issubset(set(candidate if isinstance(candidate, list) else [candidate])):
                return False
        elif key == "cross_section":
            if _canonical_section(str(candidate)) != _canonical_section(str(required[key])):
                return False
        elif not _equal(candidate, required[key]):
            return False
    return True


def _penalty(category: str, requested: dict[str, Any], specs: dict[str, Any]) -> float:
    optional_keys = set(requested) - MUST_MATCH[category]
    mismatches = sum(not _equal(requested[key], specs.get(key)) for key in optional_keys)
    return max(0.80, 0.95 ** mismatches)


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
    return max(0.0, min(1.0, dot / norm if norm else 0.0))


def _as_vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    return value.tolist() if hasattr(value, "tolist") else list(value)


def _rank_semantic(raw: str, query_vector: list[float], products: list[Product]) -> list[tuple[Product, float]]:
    ranked: list[tuple[Product, float]] = []
    for product in products:
        if product.category not in MUST_MATCH:
            continue
        vector = _as_vector(product.embedding)
        if vector is None:
            continue
        requested = _extract_attributes(raw, product.category)
        specs = product.technical_specs or {}
        if not _satisfies_constraints(product.category, requested, specs):
            continue
        score = min(1.0, _cosine(query_vector, vector) * _penalty(product.category, requested, specs))
        ranked.append((product, score))
    return sorted(ranked, key=lambda pair: pair[1], reverse=True)[:3]


def _substitutes(source: Product, products: list[Product]) -> list[tuple[Product, float]]:
    source_vector = _as_vector(source.embedding)
    if source_vector is None:
        return []
    required = source.technical_specs or {}
    ranked = []
    for candidate in products:
        candidate_vector = _as_vector(candidate.embedding)
        if candidate.sku == source.sku or candidate.stock_qty <= 0 or candidate.category != source.category or candidate_vector is None:
            continue
        specs = candidate.technical_specs or {}
        if not _satisfies_constraints(source.category, required, specs):
            continue
        score = min(1.0, _cosine(source_vector, candidate_vector) * _penalty(source.category, required, specs))
        ranked.append((candidate, round(score, 3)))
    return sorted(ranked, key=lambda pair: pair[1], reverse=True)[:2]


def _legacy_match(raw_lines: list[str], products: list[Product]) -> list[MatchResult]:
    results = []
    for line_no, raw in enumerate(raw_lines, 1):
        qty, unit = _parse_qty_unit(raw)
        product, score = max(((product, _name_score(raw, product)) for product in products), key=lambda pair: pair[1])
        substitutes = []
        if product.stock_qty <= 0:
            candidates = [(candidate, _legacy_substitute_score(product, candidate)) for candidate in products
                          if candidate.sku != product.sku and candidate.stock_qty > 0]
            substitutes = sorted((pair for pair in candidates if pair[1] > 0),
                                 key=lambda pair: pair[1], reverse=True)[:2]
        results.append(MatchResult(line_no, raw, qty, unit, product, score, substitutes))
    return results


def match_items(raw_lines: list[str], db: Session) -> list[MatchResult]:
    """Match with OpenAI embeddings, falling back to the legacy lexical matcher on AI failure."""
    products = db.query(Product).order_by(Product.sku).all()
    if not products:
        raise RuntimeError("Product catalog is empty; run python -m db.seed")
    try:
        provider = get_embedding_provider()
        if provider is None:
            logger.warning("OPENAI_API_KEY is missing; using lexical SKU matcher fallback")
            return _legacy_match(raw_lines, products)
        if not any(product.embedding is not None for product in products):
            logger.warning("Catalog has no embeddings; using lexical SKU matcher fallback")
            return _legacy_match(raw_lines, products)
        query_vectors = provider.embed(raw_lines)
        if len(query_vectors) != len(raw_lines):
            raise RuntimeError("Embedding provider returned an unexpected number of query vectors")
        results = []
        for line_no, (raw, query_vector) in enumerate(zip(raw_lines, query_vectors), 1):
            ranked = _rank_semantic(raw, query_vector, products)
            if not ranked:
                logger.warning("No semantic candidate survived hard constraints for line %s; using lexical fallback", line_no)
                results.extend(_legacy_match([raw], products))
                results[-1].line_no = line_no
                continue
            product, score = ranked[0]
            # A close runner-up is ambiguous and must never enter the >0.90 auto-select band.
            if len(ranked) > 1 and score - ranked[1][1] < 0.05:
                score = min(score, 0.89)
            qty, unit = _parse_qty_unit(raw)
            substitutes = _substitutes(product, products) if product.stock_qty <= 0 else []
            results.append(MatchResult(line_no, raw, qty, unit, product, round(score, 3), substitutes))
        return results
    except Exception as exc:
        logger.warning("Semantic matcher failed; using lexical matcher for this request: %s", exc, exc_info=True)
        return _legacy_match(raw_lines, products)
