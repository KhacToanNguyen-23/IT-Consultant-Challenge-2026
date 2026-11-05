"""MVP-FR-011 / SRS §15.2: unit dictionary DA/NO/SV/EN, canonical names, and the bare-"m" rule."""
import pytest

from services import conversion, parser

# (language, raw unit as the customer writes it, canonical unit)
SRS_UNITS = [
    ("DA", "stk", "piece"), ("NO", "stk", "piece"), ("SV", "st", "piece"), ("EN", "pcs", "piece"), ("EN", "piece", "piece"),
    ("DA", "pk", "pack"), ("DA", "pakke", "pack"), ("NO", "pakke", "pack"), ("SV", "förp", "pack"), ("SV", "paket", "pack"),
    ("EN", "pack", "pack"),
    ("DA", "lbm", "linear_metre"), ("NO", "løpemeter", "linear_metre"), ("SV", "lpm", "linear_metre"),
    ("EN", "linear metre", "linear_metre"),
    ("DA", "m2", "square_metre"), ("DA", "m²", "square_metre"), ("NO", "kvm", "square_metre"), ("EN", "sqm", "square_metre"),
    ("DA", "sæk", "bag"), ("NO", "sekk", "bag"), ("SV", "säck", "bag"), ("EN", "bag", "bag"),
    ("DA", "plade", "sheet"), ("NO", "plate", "sheet"), ("SV", "skiva", "sheet"), ("EN", "sheet", "sheet"),
    ("DA", "palle", "pallet"), ("NO", "pall", "pallet"), ("SV", "pall", "pallet"), ("EN", "pallet", "pallet"),
]


@pytest.mark.parametrize("lang,raw,canonical", SRS_UNITS)
def test_srs_unit_dictionary_maps_to_canonical_unit(lang, raw, canonical):
    row = parser.parse_line(f"12 {raw} gips 12.5 mm")
    assert row.quantity == 12
    assert row.unit == canonical, f"{lang}: {raw!r} -> {row.unit!r}"
    assert row.unit_raw is not None and "missing_unit" not in row.warnings and "unknown_unit" not in row.warnings


def test_legacy_board_word_is_still_accepted_as_sheet():
    assert parser.normalize_unit("board") == "sheet"
    assert parser.normalize_unit("boards") == "sheet"


@pytest.mark.parametrize("text", ["120 m timber 45x95 C24", "30 m terrasse 28x120 trykimpr."])
def test_bare_m_is_linear_metre_for_length_sold_categories(text):
    row = parser.parse_line(text)
    assert row.unit == "linear_metre" and "ambiguous_unit_m" not in row.warnings


def test_bare_m_is_not_guessed_outside_length_sold_categories():
    row = parser.parse_line("20 m isolering 95 mm")
    assert row.unit is None
    assert "ambiguous_unit_m" in row.warnings and "unknown_unit" not in row.warnings
    assert row.unit_raw == "m"  # raw value is kept (SRS: store raw, flag for review)


def test_explicit_length_units_are_never_ambiguous():
    row = parser.parse_line("20 lbm isolering 95 mm")
    assert row.unit == "linear_metre" and "ambiguous_unit_m" not in row.warnings


def _sku(selling_unit, pack=None):
    return {"selling_unit": selling_unit, "pack_size": pack}


@pytest.mark.parametrize("selling_unit", ["sheet", "board"])
def test_sheet_conversion_accepts_both_canonical_and_legacy_names(selling_unit):
    out = conversion.convert(12, "sheet", _sku(selling_unit))
    assert out["selling_qty"] == 12 and out["blocked_reason"] is None


def test_pallet_is_recognised_but_never_converted_by_guessing():
    out = conversion.convert(2, "pallet", _sku("bag"))
    assert out["selling_qty"] is None and out["blocked_reason"]
