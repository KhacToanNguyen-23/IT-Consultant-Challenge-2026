"""AI Gateway — LLMProvider (MVP-FR-006 fallback, MVP-FR-034). SRS v2 §5 prompts.

Used ONLY for ambiguous lines after the rules: category unknown or a must-match attribute missing.
Safety (the LLM may help, never decide):
  * input is PII-masked text (email/phone) — never the raw source
  * strict JSON; one repair retry; then rules-only
  * every returned value must cite an evidence substring that really occurs in the line, and the value
    must be consistent with that evidence → an LLM cannot invent "C24" for "regel 45x95"
  * LLM values never override what the rules already extracted
  * no LLM rerank of SKUs (v2)
Config (env only): LLM_PROVIDER=openai_compatible|fake|none, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY.
Missing key/base URL → disabled (health shows llm=disabled), the counter works unchanged.
"""
import json
import logging
import os
import re
import time
from typing import Optional

log = logging.getLogger("sitedesk.llm")

ATTR_SYSTEM = ("You extract building-material attributes from ONE customer order line. The input is PII-masked. "
               "Extract only attributes that are explicitly written: dimensions, strength grade, thickness, material, "
               "treatment, length, brand, category, board type, product type, bag weight. Never guess, never upgrade a grade "
               "or certification, use null when not written. Every non-null field MUST have an exact substring of the line "
               "in `evidence`. Reply with JSON only.")
ATTR_SCHEMA = {
    "category": "timber|gypsum|insulation|cement|decking|null",
    "dimensions_mm": {"width": "number|null", "height": "number|null"},
    "strength_grade": "C14|C16|C18|C24|C30|null",
    "thickness_mm": "number|null",
    "board_type": "standard|moisture|fire|impact|null",
    "product_type": "cement|rapid_cement|white_cement|mortar|lime_mortar|concrete|tile_adhesive|grout|levelling|render|null",
    "bag_weight_kg": "number|null",
    "treatment": ["pressure_treated|ntr_ab|thermo|hardwood|composite"],
    "length_m": "number|null",
    "brand": "string|null",
    "evidence": {"<field>": "exact substring of the line"},
}
CATEGORIES = {"timber", "gypsum", "insulation", "cement", "decking"}
ENUMS = {
    "board_type": {"standard", "moisture", "fire", "impact"},
    "product_type": {"cement", "rapid_cement", "white_cement", "mortar", "lime_mortar", "concrete", "tile_adhesive",
                     "grout", "levelling", "render"},
    "strength_grade": {"C14", "C16", "C18", "C24", "C30"},
}
TREATMENTS = {"pressure_treated", "ntr_ab", "thermo", "hardwood", "composite"}


class LLMProvider:
    name = "base"

    def complete_json(self, system: str, user: str) -> tuple[str, dict]:
        """Returns (raw_text, usage{input_tokens, output_tokens})."""
        raise NotImplementedError


class OpenAICompatible(LLMProvider):
    name = "openai_compatible"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: float = 8.0) -> None:
        import httpx

        self.model = model
        self.client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout,
                                   headers={"Authorization": f"Bearer {api_key}"})

    def complete_json(self, system, user):
        body = {"model": self.model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        r = self.client.post("/chat/completions", json=body)
        if r.status_code == 400 and "response_format" in r.text:  # some compatible servers lack JSON mode
            body.pop("response_format")
            r = self.client.post("/chat/completions", json=body)
        r.raise_for_status()
        d = r.json()
        u = d.get("usage") or {}
        return d["choices"][0]["message"]["content"], {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0)}


class FakeLLM(LLMProvider):
    """Tests: returns queued responses (str) or raises queued exceptions."""
    name = "fake"

    def __init__(self, responses: list):
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system, user):
        self.calls.append((system, user))
        r = self.responses.pop(0) if self.responses else "{}"
        if isinstance(r, Exception):
            raise r
        return r, {"input_tokens": 10, "output_tokens": 5}


_provider: Optional[LLMProvider] = None
_configured = False


def get() -> Optional[LLMProvider]:
    global _provider, _configured
    if not _configured:
        _configured = True
        kind = os.getenv("LLM_PROVIDER", "openai_compatible")
        base, model, key = os.getenv("LLM_BASE_URL", ""), os.getenv("LLM_MODEL", ""), os.getenv("LLM_API_KEY", "")
        if kind == "openai_compatible" and base and model and key:
            _provider = OpenAICompatible(base, model, key, float(os.getenv("LLM_TIMEOUT_SECONDS", "8")))
    return _provider


def set_provider_for_tests(p: Optional[LLMProvider]) -> None:
    global _provider, _configured
    _provider, _configured = p, True


def status() -> str:
    return get().name if get() else "disabled"


# ---------------- extraction with evidence checks ----------------
def _parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)  # tolerate ```json fences
    if not m:
        raise ValueError("no JSON object")
    d = json.loads(m.group())
    if not isinstance(d, dict):
        raise ValueError("not an object")
    return d


def _num(s) -> Optional[float]:
    try:
        return float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _nums_in(s: str) -> list[float]:
    return [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", s)]


def validate(raw: dict, line: str) -> tuple[dict, list[str]]:
    """Keep only values backed by evidence that occurs in the line and agrees with the value."""
    low = line.lower()
    ev = raw.get("evidence") or {}
    if not isinstance(ev, dict):
        ev = {}
    out, dropped = {}, []

    def evidence_for(*fields) -> Optional[str]:
        for f in fields:
            e = ev.get(f)
            if isinstance(e, str) and e.strip() and e.strip().lower() in low:
                return e.strip()
        return None

    def keep(field, value, ok):
        if value in (None, "", [], {}):
            return
        if ok:
            out[field] = value
        else:
            dropped.append(field)

    cat = raw.get("category")
    keep("category", cat, cat in CATEGORIES and evidence_for("category") is not None)

    dims = raw.get("dimensions_mm") or {}
    if isinstance(dims, dict) and dims.get("width") and dims.get("height"):
        w, h = _num(dims["width"]), _num(dims["height"])
        e = evidence_for("dimensions_mm", "cross_section_mm", "dimensions")
        ok = bool(e and w and h and w in _nums_in(e) and h in _nums_in(e))
        keep("cross_section_mm", f"{w:g}x{h:g}" if w and h else None, ok)

    g = str(raw.get("strength_grade") or "").upper() or None
    e = evidence_for("strength_grade")
    keep("strength_grade", g, bool(g in ENUMS["strength_grade"] and e and g.lower() in e.lower()))

    for f in ("thickness_mm", "bag_weight_kg", "length_m"):
        v = _num(raw.get(f)) if raw.get(f) is not None else None
        e = evidence_for(f)
        keep(f, v, bool(v and e and v in _nums_in(e)))

    for f in ("board_type", "product_type"):
        v = raw.get(f)
        keep(f, v, v in ENUMS[f] and evidence_for(f) is not None)

    tr = raw.get("treatment")
    if isinstance(tr, str):
        tr = [tr]
    if tr:
        tr = [x for x in tr if x in TREATMENTS]
        keep("treatment", tr or None, evidence_for("treatment") is not None)

    b = raw.get("brand")
    keep("brand", b, bool(isinstance(b, str) and b.lower() in low))
    return out, dropped


def extract_attributes(masked_line: str, category_hint: Optional[str]) -> Optional[dict]:
    """Returns {"attrs", "dropped", "usage", "latency_ms", "status"} or None when the LLM is disabled."""
    p = get()
    if p is None:
        return None
    user = json.dumps({"category_hint": category_hint, "masked_line": masked_line, "output_schema": ATTR_SCHEMA}, ensure_ascii=False)
    t0 = time.perf_counter()
    usage = {"input_tokens": 0, "output_tokens": 0}
    raw, status = None, "ok"
    for attempt in range(2):  # one repair retry
        try:
            text, u = p.complete_json(ATTR_SYSTEM if attempt == 0 else ATTR_SYSTEM + " Your previous reply was not valid JSON. Reply with ONE JSON object only.", user)
            usage = {k: usage[k] + u.get(k, 0) for k in usage}
            raw = _parse_json(text)
            status = "ok" if attempt == 0 else "repaired"
            break
        except Exception as e:  # noqa: BLE001 — invalid JSON / timeout / HTTP error → rules-only
            status = f"error:{type(e).__name__}"
            log.warning("LLM attribute extraction attempt %d failed: %s", attempt + 1, e)
            if not isinstance(e, ValueError):
                break  # transport errors are not retried (keep the 3 s budget)
    latency = int((time.perf_counter() - t0) * 1000)
    if raw is None:
        return {"attrs": {}, "dropped": [], "usage": usage, "latency_ms": latency, "status": status}
    attrs, dropped = validate(raw, masked_line)
    return {"attrs": attrs, "dropped": dropped, "usage": usage, "latency_ms": latency, "status": status}
