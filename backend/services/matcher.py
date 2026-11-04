"""Hybrid SKU matcher (MVP-FR-007/008/009) — hard rules + score bands.

PLACEHOLDER SEMANTIC SIGNAL: `semantic_score()` currently uses token overlap so the UI/flows run
end-to-end. AI owner replaces it with pgvector top-10 on multilingual-e5-small embeddings
(semantic = clamp((cosine+1)/2, 0, 1)). The hard-rule / penalty / band / gap logic below follows
SRS v2 §5 and should stay as is.
"""
import re
from typing import Optional

from config import settings

MUST_MATCH = {
    "timber": ["cross_section_mm", "strength_grade"],
    "gypsum": ["thickness_mm", "moisture_resistant"],
    "insulation": ["thickness_mm"],
    "cement": ["bag_weight_kg", "product_type"],
    "decking": ["cross_section_mm", "treatment"],
}
OPTIONAL = ["length_m", "brand"]
GRADE_RANK = {"C14": 14, "C16": 16, "C18": 18, "C24": 24, "C30": 30}


def _tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^0-9a-zæøåäö]+", s.lower()) if len(t) >= 2}


def semantic_score(query: str, product: dict) -> float:
    """TODO(AI owner): replace with embedding cosine from pgvector."""
    q = _tokens(query)
    if not q:
        return 0.0
    names = product["name"] + " " + " ".join(a for v in (product.get("aliases") or {}).values() for a in v)
    return len(q & _tokens(names)) / len(q)


def _eq(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return str(a).lower() == str(b).lower()


def compare_must(attr: str, req, cand, for_alternative: bool = False) -> Optional[bool]:
    """True=ok, False=mismatch(excluded), None=cannot compare."""
    if cand is None:
        return False
    if attr == "strength_grade":
        if for_alternative:
            r, c = GRADE_RANK.get(str(req).upper()), GRADE_RANK.get(str(cand).upper())
            return r is not None and c is not None and c >= r
        return _eq(req, cand)
    if attr == "moisture_resistant":
        return (not req) or bool(cand)
    if attr == "treatment":
        return set(req or []) <= set(cand or [])
    return _eq(req, cand)


def band(score: float) -> str:
    if score > settings.high_threshold:
        return "HIGH"
    if score >= settings.review_threshold:
        return "REVIEW"
    return "LOW"


def match(query: str, attrs: dict, products: list[dict]) -> list[dict]:
    req_cat = attrs.get("category")
    ranked = []
    for p in products:
        if req_cat and p["category"] != req_cat:
            continue
        specs = p.get("technical_specs") or {}
        must = MUST_MATCH.get(p["category"], [])
        matched, mismatched, missing = [], [], []
        excluded = False
        for a in must:
            if a not in attrs:
                missing.append(a)
                continue
            if compare_must(a, attrs[a], specs.get(a)):
                matched.append(a)
            else:
                mismatched.append(a)
                excluded = True
        if excluded:
            continue  # must-match mismatch never auto-selected or suggested
        optional_mis = []
        for a in OPTIONAL:
            if a in attrs and a in specs and not _eq(attrs[a], specs[a]):
                optional_mis.append(a)
            elif a in attrs and a in specs:
                matched.append(a)
        overlap = semantic_score(query, p)
        if req_cat and must:
            semantic = 0.70 + 0.10 * overlap + 0.20 * (len([m for m in matched if m in must]) / len(must))
        else:
            semantic = 0.40 + 0.40 * overlap
        penalty = max(0.80, 0.95 ** len(optional_mis))
        score = min(1.0, max(0.0, semantic)) * penalty
        if missing:
            score = min(score, settings.high_threshold - 0.01)  # missing attr never in high band
        ranked.append({
            "sku": p["sku"], "name": p["name"], "category": p["category"], "score": round(score, 4),
            "reasons": {"matched": matched, "mismatched": optional_mis, "missing": missing},
        })
    ranked.sort(key=lambda c: (-c["score"], c["sku"]))
    if len(ranked) >= 2 and ranked[0]["score"] - ranked[1]["score"] < settings.ambiguity_gap:
        ranked[0]["score"] = min(ranked[0]["score"], 0.89)
        ranked[0]["reasons"]["ambiguous"] = True
    for c in ranked:
        c["band"] = band(c["score"])
    return ranked[:3]
