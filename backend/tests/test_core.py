"""Unit tests for the deterministic core (SRS v2 §11.2). Run: docker compose exec backend pytest -q"""
import json
from pathlib import Path

import pytest

from config import settings
from db.models import SessionLine
from services import connector, conversion, matcher, parser, pii, pipeline

_SEEDS = [Path("/seeds/catalog.json"), Path(__file__).resolve().parents[2] / "mock-pos" / "seeds" / "catalog.json"]
_found = next((p for p in _SEEDS if p.exists()), None)
CATALOG = json.loads(_found.read_text(encoding="utf-8")) if _found else None


@pytest.fixture(scope="module")
def products():
    if CATALOG is None:
        pytest.skip("mock-pos seeds not mounted")
    return {p["sku"]: p for p in CATALOG["items"]}


# ---------- PII (MVP-FR-002) ----------
@pytest.mark.parametrize("raw,masked", [
    ("mail kunde@firma.dk tak", "mail [EMAIL] tak"),
    ("Ring på +45 22 33 44 55.", "Ring på [PHONE]."),
    ("tlf 22334455", "tlf [PHONE]"),
    ("+46 70-123 45 67", "[PHONE]"),
])
def test_pii_masks_email_and_phone(raw, masked):
    assert pii.mask(raw) == masked


@pytest.mark.parametrize("keep", ["Timber 45x95 C24 - 120 m", "Gips 12.5mm 10 plader", "Rockwool 95mm 2.88 m2"])
def test_pii_does_not_mask_material_dimensions(keep):
    assert pii.mask(keep) == keep


# ---------- parser / units (FR-005, FR-011) ----------
@pytest.mark.parametrize("line,qty,unit,name", [
    ("Timber 45x95 C24 - 120 m", 120, "linear_metre", "Timber 45x95 C24"),
    ("10 stk timber 45x95 C24", 10, "piece", "timber 45x95 C24"),
    ("Rockwool FlexiBatts 95mm - 15 pk", 15, "pack", "Rockwool FlexiBatts 95mm"),
    ("Isolering 95mm 60 m2", 60, "square_metre", "Isolering 95mm"),
    ("Murmørtel 25kg - 5 sække", 5, "bag", "Murmørtel 25kg"),
    ("Gips vådrum 12,5mm: 10 plader", 10, "board", "Gips vådrum 12,5mm"),
    ("Våtromsplate 12.5 mm 8 plater", 8, "board", "Våtromsplate 12.5 mm"),
    ("Reglar 45x95 C24, 30 st", 30, "piece", "Reglar 45x95 C24"),
])
def test_parse_quantity_and_unit(line, qty, unit, name):
    r = parser.parse_line(line)
    assert (r.quantity, r.unit, r.item_text, r.status) == (qty, unit, name, "OK")


def test_n_x_l_is_pieces_of_length_with_review_flag():
    r = parser.parse_line("Terrassebræt 28x120 trykimp 10 x 4.2m")
    assert (r.quantity, r.unit, r.length_m) == (10, "piece", 4.2)
    assert "n_x_l_review" in r.warnings


def test_unknown_unit_is_kept_raw_and_flagged():
    r = parser.parse_line("Cement 25 kg 4 spande")
    assert r.unit is None and r.unit_raw == "spande" and "unknown_unit" in r.warnings


def test_unreadable_line_is_kept():
    assert parser.parse_line("???").status == "UNREADABLE"


def test_email_signature_and_contact_lines_are_not_rows():
    text = pii.mask("Hej,\nRing på +45 22 33 44 55.\nTimber 45x95 C24 - 120 m\n\nMvh\nJens Hansen\nVejen 4")
    rows = parser.split_text(text)
    assert [r.item_text for r in rows] == ["Timber 45x95 C24"]


def test_attributes_rules():
    a = parser.extract_attributes("Konstruktionstræ 45x95 C18")
    assert a["category"] == "timber" and a["cross_section_mm"] == "45x95" and a["strength_grade"] == "C18"
    g = parser.extract_attributes("Brandgips 15mm")
    assert g["category"] == "gypsum" and g["board_type"] == "fire" and g["thickness_mm"] == 15
    d = parser.extract_attributes("Terrassebræt 28x120 NTR/AB")
    assert d["category"] == "decking" and set(d["treatment"]) == {"pressure_treated", "ntr_ab"}
    c = parser.extract_attributes("Fliseklæb 20kg")
    assert c["category"] == "cement" and c["product_type"] == "tile_adhesive" and c["bag_weight_kg"] == 20


# ---------- conversion (FR-012/013) ----------
TIMBER_48 = {"selling_unit": "piece_4.8m", "pack_size": 4.8}
INSUL = {"selling_unit": "pack", "pack_size": 2.88}


def test_conversion_exact_and_ceil():
    c = conversion.convert(120, "linear_metre", TIMBER_48)
    assert c["selling_qty"] == 25 and not c["rounded"]
    c = conversion.convert(60, "square_metre", INSUL)
    assert c["selling_qty"] == 21 and c["rounded"]


def test_conversion_never_guesses():
    assert conversion.convert(60, "square_metre", {"selling_unit": "pack", "pack_size": None})["blocked_reason"]
    assert conversion.convert(10, None, TIMBER_48)["blocked_reason"]
    assert conversion.convert(10, "piece", TIMBER_48, length_hint=4.2)["blocked_reason"]  # N x 4.2m vs 4.8m SKU


# ---------- matcher: hard rules, bands, gap (FR-007/008/009) ----------
def test_band_boundaries():
    assert matcher.band(0.9001) == "HIGH"
    assert matcher.band(0.90) == "REVIEW"  # exactly 0.90 is NOT high
    assert matcher.band(0.80) == "REVIEW"
    assert matcher.band(0.7999) == "LOW"


def test_c18_is_never_matched_as_c24(products):
    attrs = parser.extract_attributes("Timber 45x95 C18")
    cands = matcher.match("Timber 45x95 C18", attrs, list(products.values()))
    assert cands and all(products[c["sku"]]["technical_specs"]["strength_grade"] == "C18" for c in cands)


def test_must_mismatch_excluded_even_with_high_semantic(products):
    attrs = parser.extract_attributes("Timber 45x95 C24")
    sem = {"SKU-DK-4595-C18-480": 0.99, "SKU-DK-4595-480": 0.80}  # vector prefers the wrong grade
    cands = matcher.match("Timber 45x95 C24", attrs, list(products.values()), sem)
    assert [c["sku"] for c in cands] == ["SKU-DK-4595-480"]


def test_missing_must_attribute_never_high(products):
    attrs = parser.extract_attributes("Regel 45x95")  # no grade
    cands = matcher.match("Regel 45x95", attrs, list(products.values()), {"SKU-DK-4595-480": 0.99, "SKU-DK-4595-C18-480": 0.7})
    assert cands[0]["band"] != "HIGH" and "strength_grade" in cands[0]["reasons"]["missing"]


def test_gap_rule_caps_top1(products):
    attrs = parser.extract_attributes("Gips vådrum 12.5mm")
    cands = matcher.match("Gips vådrum 12.5mm", attrs, list(products.values()), {"SKU-GYP-MR-125": 0.95, "SKU-GYP-MR-125-B": 0.94})
    assert cands[0]["score"] <= 0.89 and cands[0]["reasons"]["ambiguous"]


def test_optional_mismatch_penalised_with_reason(products):
    attrs = parser.extract_attributes("Isover 95mm")
    cands = matcher.match("Isover 95mm", attrs, list(products.values()), {"SKU-ISOVER-095": 0.9, "SKU-RW-095": 0.9})
    rw = next(c for c in cands if c["sku"] == "SKU-RW-095")
    assert "brand" in rw["reasons"]["mismatched"] and cands[0]["sku"] == "SKU-ISOVER-095"


# ---------- alternatives + line states (FR-010/014/015/016/039) ----------
def _line(text, qty, unit, products):
    l = SessionLine(line_no=1, raw_customer_input=text, parsed_name=text, requested_qty=qty, requested_unit=unit,
                    parse_status="OK", attributes={}, candidates=[], resolved=False)
    pipeline.match_line(l, products)
    return l


def _stock(products, **over):
    s = {sku: {"on_hand": 100, "updated_at": "2026-11-04T08:00:00Z"} for sku in products}
    for k, v in over.items():
        s[k.replace("_", "-")]["on_hand"] = v
    return s


def test_partial_stock_proposes_only_safe_alternatives(products):
    l = _line("Gips vådrum 12.5mm", 10, "board", products)
    l.original_sku = l.final_sku = "SKU-GYP-MR-125"
    l.resolved = True
    stock = _stock(products, **{"SKU_GYP_MR_125": 4})
    pipeline.evaluate(l, products, stock)
    assert l.stock_status == "PARTIAL" and l.line_status == "SUBSTITUTE_PROPOSED"
    alt_types = {products[a["sku"]]["technical_specs"]["board_type"] for a in l.alternatives}
    assert alt_types == {"moisture"} and len(l.alternatives) <= 2  # never a standard board for a wet room


def test_higher_grade_allowed_as_alternative_lower_never(products):
    l = _line("Timber 45x120 C24", 120, "linear_metre", products)
    stock = _stock(products, **{"SKU_DK_45120_480": 0})
    pipeline.evaluate(l, products, stock)
    skus = [a["sku"] for a in l.alternatives]
    assert "SKU-DK-45120-C30-480" in skus
    assert all(products[s]["technical_specs"]["strength_grade"] in ("C24", "C30") for s in skus)


def test_no_safe_substitute_means_backorder_not_blocker(products):
    l = _line("Murmørtel 25kg", 5, "bag", products)
    pipeline.evaluate(l, products, _stock(products, **{"SKU_MORT_25": 0}))
    assert l.alternatives == [] and l.fulfillment_action == "backorder"
    assert pipeline.blockers([l]) == []


def test_final_sku_only_changes_after_customer_accepts(products):
    l = _line("Rockwool FlexiBatts 95mm", 15, "pack", products)
    stock = _stock(products, **{"SKU_RW_095": 5})
    pipeline.evaluate(l, products, stock)
    assert l.final_sku == "SKU-RW-095" and l.line_status == "SUBSTITUTE_PROPOSED"
    assert pipeline.blockers([l])  # Confirm blocked until customer decides


def test_unknown_unit_blocks_confirm(products):
    l = _line("Cement standard 25kg", 4, None, products)
    pipeline.evaluate(l, products, _stock(products))
    assert l.line_status == "NEEDS_CLARIFICATION" and pipeline.blockers([l])


# ---------- CSV fallback (§7.4) ----------
def test_csv_formula_injection_and_format():
    payload = {"order_session_id": "SD-1", "quote_id": None, "store_id": "DK-CPH-04", "client_id": "C-1",
               "confirmed_by_associate": "EMP-1", "processing_time_seconds": 84,
               "line_items": [{"line_no": 1, "raw_customer_input": "=HYPERLINK(\"x\")", "final_sku": "SKU-1",
                               "quantity": 2.0, "selling_unit": "bag", "confidence_score": 0.95, "fulfillment_action": "direct_pick"}]}
    out = connector.to_csv(payload)
    assert out.startswith("﻿") and out.splitlines()[0].count(";") == len(connector.CSV_HEADER) - 1
    assert "'=HYPERLINK" in out


def test_thresholds_from_config():
    assert (settings.high_threshold, settings.review_threshold, settings.ambiguity_gap) == (0.90, 0.80, 0.05)


def test_chips_compare_raw_values_not_display_labels(products):
    l = _line("Gips vådrum 12.5mm", 10, "board", products)
    l.original_sku = l.final_sku = "SKU-GYP-MR-125"
    pipeline.evaluate(l, products, _stock(products))
    chips = {c["attr"]: c for c in pipeline.serialize_line(l, products)["chips"]}
    assert chips["board_type"]["tone"] == "emerald" and chips["board_type"]["value"] == "vådrum"
    assert "moisture_resistant" not in chips  # not shown twice
