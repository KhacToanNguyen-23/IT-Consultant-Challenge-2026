"""Hybrid SKU matcher (MVP-FR-007/008/009) — SRS v2 §5.

Normal mode   : candidates = pgvector top-10 (e5-small cosine), semantic = clamp((cos+1)/2, 0, 1)
Degraded mode : (AI fail / model not ready) candidates = whole category, semantic = rules + token overlap
Both modes then apply the same hard rules:
  * must-match mismatch  → candidate removed (never auto-selected, never suggested)
  * must-match missing   → no penalty, but capped below the high band → NEEDS_CLARIFICATION
  * optional mismatch    → ×0.95 each, floor 0.80, with reason
  * top1 - top2 < 0.05   → top1 capped at 0.89 (ambiguous)
No LLM rerank (v2).
"""
import re
from typing import Optional

from config import settings

MUST_MATCH = {
    "timber": ["cross_section_mm", "strength_grade"],
    "gypsum": ["thickness_mm", "board_type"],
    "insulation": ["thickness_mm"],
    "cement": ["bag_weight_kg", "product_type"],
    "decking": ["cross_section_mm", "treatment"],
}
OPTIONAL = ["length_m", "brand"]
GRADE_RANK = {"C14": 14, "C16": 16, "C18": 18, "C24": 24, "C30": 30}
ALIAS_BOOST = 0.03


def _tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^0-9a-zæøåäö]+", s.lower()) if len(t) >= 2}


def token_overlap(query: str, product: dict) -> float:
    """Degraded-mode signal (no AI): share of query tokens found in name/aliases."""
    q = _tokens(query)
    if not q:
        return 0.0
    names = product["name"] + " " + " ".join(a for v in (product.get("aliases") or {}).values() for a in v)
    return len(q & _tokens(names)) / len(q)


def alias_hit(query: str, product: dict) -> bool:
    low = f" {query.lower()} "
    return any(f" {a.lower()}" in low for v in (product.get("aliases") or {}).values() for a in v)


def _eq(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-6
    return str(a).lower() == str(b).lower()


def compare_must(attr: str, req, cand, for_alternative: bool = False) -> Optional[bool]:
    """True=ok, False=mismatch (excluded). Alternatives may be equal-or-better (ordered/capability attrs)."""
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


def match(query: str, attrs: dict, products: list[dict], semantic: Optional[dict[str, float]] = None) -> list[dict]:
    """semantic: {sku: cosine} from vector top-k, or None for degraded (rules) mode."""
    req_cat = attrs.get("category")
    by_sku = {p["sku"]: p for p in products}
    pool = [by_sku[s] for s in semantic if s in by_sku] if semantic is not None else products
    ranked = []
    for p in pool:
        if req_cat and p["category"] != req_cat:
            continue
        specs = p.get("technical_specs") or {}
        must = MUST_MATCH.get(p["category"], [])
        matched, missing, excluded = [], [], False
        for a in must:
            if a not in attrs:
                missing.append(a)
            elif compare_must(a, attrs[a], specs.get(a)):
                matched.append(a)
            else:
                excluded = True
                break
        if excluded:
            continue
        optional_mis = []
        for a in OPTIONAL:
            if a in attrs and a in specs:
                (matched if _eq(attrs[a], specs[a]) else optional_mis).append(a)
        if semantic is not None:
            base = max(0.0, min(1.0, (semantic[p["sku"]] + 1) / 2))
            mode = "embedding"
        else:  # degraded: rules + token overlap
            overlap = token_overlap(query, p)
            must_frac = len([m for m in matched if m in must]) / len(must) if must else 0.5
            base = 0.70 + 0.10 * overlap + 0.20 * must_frac if req_cat else 0.40 + 0.40 * overlap
            mode = "rules"
        boosted = alias_hit(query, p)
        base = min(1.0, base + (ALIAS_BOOST if boosted else 0.0))
        score = base * max(0.80, 0.95 ** len(optional_mis))
        if missing:
            score = min(score, settings.high_threshold - 0.01)  # missing attr never reaches high band
        ranked.append({"sku": p["sku"], "name": p["name"], "category": p["category"], "score": round(score, 4),
                       "mode": mode,
                       "reasons": {"matched": matched, "mismatched": optional_mis, "missing": missing,
                                   **({"alias": True} if boosted else {})}})
    ranked.sort(key=lambda c: (-c["score"], c["sku"]))
    if len(ranked) >= 2 and ranked[0]["score"] - ranked[1]["score"] < settings.ambiguity_gap:
        ranked[0]["score"] = min(ranked[0]["score"], 0.89)
        ranked[0]["reasons"]["ambiguous"] = True
    for c in ranked:
        c["band"] = band(c["score"])
    return ranked[:3]
