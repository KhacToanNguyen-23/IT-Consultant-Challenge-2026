"""Rules-first line parser (MVP-FR-001/003/004/005/006/011).

AI owner: an optional LLM parse/attribute step can be added in ai/ and called from pipeline when
rules leave a line ambiguous; rules must keep working when AI_FAIL_MODE=true.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional

# MVP-FR-011 unit dictionary DA/NO/SV/EN (draft per SRS §15.2 — dev must verify)
UNIT_MAP = {
    "stk": "piece", "stk.": "piece", "styk": "piece", "stykker": "piece", "st": "piece", "st.": "piece",
    "styck": "piece", "pcs": "piece", "pc": "piece", "piece": "piece", "pieces": "piece",
    "m": "linear_metre", "lbm": "linear_metre", "lm": "linear_metre", "meter": "linear_metre", "metre": "linear_metre",
    "m2": "square_metre", "m²": "square_metre", "kvm": "square_metre", "sqm": "square_metre",
    "pk": "pack", "pk.": "pack", "pakke": "pack", "pakker": "pack", "pack": "pack", "packs": "pack", "paket": "pack",
    "sæk": "bag", "sække": "bag", "sekk": "bag", "sekker": "bag", "säck": "bag", "säckar": "bag", "bag": "bag", "bags": "bag",
    "plade": "board", "plader": "board", "plate": "board", "plater": "board", "skiva": "board", "skivor": "board",
    "board": "board", "boards": "board",
}
UNIT_TOKEN = r"[A-Za-zæøåÆØÅäöÄÖ²2.]+"
NUM = r"\d+(?:[.,]\d+)?"

# order matters: more specific groups first ("terrassebræt" before generic "træ")
CATEGORY_KEYWORDS = {
    "decking": ["terrasse", "terrassebræt", "deck", "trall", "terrassebord", "komposit"],
    "gypsum": ["gips", "gypsum", "vådrum", "våtrom", "våtrum", "drywall", "plasterboard", "brandplade", "brannplate", "brandskiva"],
    "insulation": ["isolering", "isolasjon", "insulation", "rockwool", "isover", "knauf", "batts", "mineraluld", "stenuld",
                   "glasuld", "steinull", "glassull", "stenull", "glasull"],
    "cement": ["cement", "sement", "mørtel", "mortel", "murbruk", "mortar", "beton", "fliseklæb", "flislim", "tile adhesive",
               "fugemasse", "grout", "flydespartel", "avretting", "flytspackel", "puds", "filtsand", "kalkbruk"],
    "timber": ["træ", "trae", "tre ", "trä", "timber", "regel", "reglar", "lægte", "laegte", "lekte", "läkt", "konstruktionstræ",
               "virke", "planke", "stud", "c24", "c18", "c30", "c16", "c14"],
}
MOISTURE_WORDS = ["vådrum", "våtrom", "våtrum", "moisture", "wet room", "fugt", "mr "]
BOARD_TYPE_WORDS = {  # gypsum must-match "type"
    "moisture": MOISTURE_WORDS,
    "fire": ["brandgips", "brandplade", "brannplate", "brandskiva", "fire board", "fireboard", "fire-rated", "brandsikker"],
    "impact": ["robust", "slagfast", "impact"],
    "standard": ["standard", "normal", "almindelig", "alm.", "vanlig"],
}
TREATMENT_WORDS = {"pressure_treated": ["trykimp", "imprægneret", "impregnert", "impregnerad", "pressure", "tryckimp", " ntr", "ntr/ab"],
                   "ntr_ab": ["ntr", "ntr/ab", " ab "],
                   "thermo": ["thermo", "termo"],
                   "hardwood": ["hårdttræ", "hårdt træ", "hardwood", "hardved", "hårdträ"],
                   "composite": ["komposit", "composite", "kompositt"]}
PRODUCT_TYPE_WORDS = {  # cement group must-match "type"; more specific first
    "rapid_cement": ["hurtigcement", "rapid", "hurtighærdende"],
    "white_cement": ["hvid cement", "white cement", "hvit sement", "vit cement"],
    "lime_mortar": ["kalkmørtel", "kalkbruk", "lime mortar"],
    "mortar": ["mørtel", "mortel", "murbruk", "mortar", "murmørtel"],
    "concrete": ["beton", "betong", "concrete", "tørbeton"],
    "tile_adhesive": ["fliseklæb", "flislim", "tile adhesive", "fliselim"],
    "grout": ["fugemasse", "grout", "fugmassa", " fug "],
    "levelling": ["flydespartel", "avretting", "flytspackel", "self-levelling", "levelling"],
    "render": ["puds", "filtsand", "render", "puts"],
    "cement": ["cement", "sement"],
}


def _num(s: str) -> float:
    return float(s.replace(",", "."))


@dataclass
class ParsedRow:
    line_no: int
    source_text: str
    source_start: int
    source_end: int
    item_text: Optional[str]
    quantity: Optional[float]
    unit_raw: Optional[str]
    unit: Optional[str]
    status: str  # OK | UNREADABLE
    warnings: list = field(default_factory=list)
    length_m: Optional[float] = None


def normalize_unit(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return UNIT_MAP.get(raw.strip().lower())


def parse_line(text: str, line_no: int = 1, start: int = 0) -> ParsedRow:
    src = text.strip()
    row = ParsedRow(line_no, src, start, start + len(text), None, None, None, None, "OK")
    if len(re.findall(r"[A-Za-zæøåÆØÅäöÄÖ]", src)) < 3:
        row.status = "UNREADABLE"
        row.warnings.append("no_material_text")
        return row
    body = src.lstrip("-•*·").strip()
    body = re.sub(r"^\d+[.)]\s+", "", body)  # "1. " / "2) " list numbering

    # N x L  (e.g. "10 x 4.8m timber 45x95" / "timber 45x95 10 x 4,8 m")
    nxl = re.search(rf"(?<![\dx×])(\d+)\s*[x×]\s*({NUM})\s*m\b", body, re.I)
    if nxl:
        row.quantity = float(nxl.group(1))
        row.length_m = _num(nxl.group(2))
        row.unit_raw = nxl.group(0)
        row.unit = "piece"
        row.warnings.append("n_x_l_review")
        body = (body[:nxl.start()] + body[nxl.end():]).strip(" -–:,")
    else:
        # trailing quantity: "... - 120 m", "...: 15 pk", "..., 30 stk"
        m = re.search(rf"(?:^|[\s\-–:,(])({NUM})\s*({UNIT_TOKEN})?\s*\)?\s*$", body)
        lead = re.match(rf"^({NUM})\s*({UNIT_TOKEN})?\s+(.+)$", body)
        spec_unit = m and (m.group(2) or "").lower().rstrip(".") in {"mm", "cm", "kg"}
        if m and not spec_unit and not re.search(r"[x×]\s*$", body[:m.start(1)]):
            row.quantity = _num(m.group(1))
            row.unit_raw = m.group(2)
            body = body[:m.start()].strip(" -–:,(")
        elif lead:
            row.quantity = _num(lead.group(1))
            unit_candidate = lead.group(2)
            if unit_candidate and normalize_unit(unit_candidate):
                row.unit_raw = unit_candidate
                body = lead.group(3)
            else:
                body = (unit_candidate + " " if unit_candidate else "") + lead.group(3)
        row.unit = normalize_unit(row.unit_raw)
        if row.unit_raw and not row.unit:
            row.warnings.append("unknown_unit")
    if row.quantity is None:
        row.warnings.append("missing_quantity")
    elif row.unit is None and "unknown_unit" not in row.warnings:
        row.warnings.append("missing_unit")
    row.item_text = body.strip() or None
    if not row.item_text:
        row.status = "UNREADABLE"
    return row


SIGNOFF_RE = re.compile(r"^(mvh|m\.v\.h|med venlig(?:\s+hilsen)?|venlig hilsen|vennlig hilsen|med vennlig hilsen|med vänliga hälsningar|"
                        r"vänliga hälsningar|hälsningar|hilsen|best regards|kind regards|regards|br|vh)\b[,.!]?\s*$", re.I)


def split_text(text: str) -> list[ParsedRow]:
    """One row per material line. Skips mail headers/greetings and contact lines; stops at the sign-off so the
    signature (names, titles, addresses) is never turned into rows."""
    rows, pos, n = [], 0, 0
    for raw in text.splitlines(keepends=True):
        stripped = raw.strip()
        if SIGNOFF_RE.match(stripped):
            break
        if stripped and not _is_header(stripped) and not _is_contact(stripped):
            n += 1
            rows.append(parse_line(raw.rstrip("\r\n"), n, pos))
        pos += len(raw)
    return rows


def _is_header(line: str) -> bool:
    low = line.lower()
    return bool(re.match(r"^(subject|emne|ämne|from|fra|från|to|til|till|hej|hi|dear|kære|mvh|med venlig|best regards|vh|tak|thanks)\b", low)) \
        or low.startswith("[email]") or low.startswith("[phone]")


def _is_contact(line: str) -> bool:
    return "[PHONE]" in line or "[EMAIL]" in line


def rows_from_table(content: bytes, filename: str) -> str:
    """XLSX/CSV → one text line per row (cells joined). Keeps the pipeline single-path."""
    name = filename.lower()
    lines = []
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        for r in wb.active.iter_rows(values_only=True):
            cells = [str(c).strip() for c in r if c is not None and str(c).strip()]
            if cells:
                lines.append(" ".join(cells))
    else:
        txt = content.decode("utf-8-sig", errors="replace")
        dialect = csv.Sniffer().sniff(txt[:2048], delimiters=",;\t") if txt.strip() else csv.excel
        for r in csv.reader(io.StringIO(txt), dialect):
            cells = [c.strip() for c in r if c.strip()]
            if cells:
                lines.append(" ".join(cells))
    # drop an obvious header row
    if lines and re.search(r"\b(vare|item|produkt|product|beskrivelse|description|antal|qty|quantity)\b", lines[0], re.I) and not re.search(r"\d", lines[0]):
        lines = lines[1:]
    return "\n".join(lines)


def pdf_text(content: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


# ---------- attribute extraction (rules) ----------
def detect_category(text: str) -> Optional[str]:
    low = f" {text.lower()} "
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in low for w in words):
            return cat
    if re.search(r"\b\d{2}\s*[x×]\s*\d{2,3}\b", low):
        return "timber"
    return None


def extract_attributes(text: str, length_hint: Optional[float] = None) -> dict:
    low = f" {text.lower()} "
    attrs: dict = {}
    cat = detect_category(text)
    if cat:
        attrs["category"] = cat
    cs = re.search(r"\b(\d{2,3})\s*[x×]\s*(\d{2,3})\b(?!\s*(?:[.,]\d+)?\s*m\b)", low)
    if cs:
        attrs["cross_section_mm"] = f"{cs.group(1)}x{cs.group(2)}"
    g = re.search(r"\bc(14|16|18|24|30)\b", low)
    if g:
        attrs["strength_grade"] = f"C{g.group(1)}"
    th = re.search(rf"\b({NUM})\s*mm\b", low)
    if th and not cs:
        attrs["thickness_mm"] = _num(th.group(1))
    ln = re.search(rf"\b({NUM})\s*m\b", low)
    if ln:
        attrs["length_m"] = _num(ln.group(1))
    elif length_hint:
        attrs["length_m"] = length_hint
    kg = re.search(r"\b(\d+)\s*kg\b", low)
    if kg:
        attrs["bag_weight_kg"] = float(kg.group(1))
    if any(w in low for w in MOISTURE_WORDS):
        attrs["moisture_resistant"] = True
    if cat == "gypsum":
        bt = next((t for t, words in BOARD_TYPE_WORDS.items() if any(w in low for w in words)), None)
        if bt:
            attrs["board_type"] = bt
    if cat == "decking":
        treat = [k for k, words in TREATMENT_WORDS.items() if any(w in low for w in words)]
        if treat:
            attrs["treatment"] = treat
    if cat == "cement":
        pt = next((t for t, words in PRODUCT_TYPE_WORDS.items() if any(w in low for w in words)), None)
        if pt:
            attrs["product_type"] = pt
    for brand in ["rockwool", "isover", "knauf", "gyproc"]:
        if brand in low:
            attrs["brand"] = brand.capitalize() if brand != "rockwool" else "Rockwool"
    return attrs
