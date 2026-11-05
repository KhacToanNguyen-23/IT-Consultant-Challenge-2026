"""MVP-FR-007/008: an item that is not in the catalog must not be 'matched' to an unrelated SKU."""
import pytest

from services import matcher, parser


def _p(sku, name, category, specs, aliases=None, unit="piece"):
    return {"sku": sku, "name": name, "category": category, "technical_specs": specs, "aliases": aliases or {},
            "selling_unit": unit, "unit_price": 10.0, "pack_size": None}


CATALOG = [
    _p("T24", "Konstruktionstræ 45x95 C24 4.8m", "timber", {"cross_section_mm": "45x95", "strength_grade": "C24"}),
    _p("G-MR", "Gipsplade vådrum 12.5mm", "gypsum", {"thickness_mm": 12.5, "board_type": "moisture"}),
    _p("C-STD", "Cement standard 25kg", "cement", {"bag_weight_kg": 25, "product_type": "cement"}),
    _p("I-95", "Rockwool FlexiBatts 95mm", "insulation", {"thickness_mm": 95}),
]


def _offered(text, semantic=None):
    attrs = dict(parser.extract_attributes(text))
    attrs["category"] = parser.detect_category(text)
    return matcher.match(text, attrs, CATALOG, semantic)


@pytest.mark.parametrize("text", ["skruer 5x50", "blahblah ukendt ting", "gipsskruer 3,5x35", "søm 4x100", "wood screws 4x40"])
@pytest.mark.parametrize("vector_mode", [False, True])
def test_items_outside_the_catalog_get_no_suggestion(text, vector_mode):
    # In vector mode every SKU looks "close" (cosine 0.8 -> score 0.9): the lexical anchor must still stop it.
    semantic = {p["sku"]: 0.8 for p in CATALOG} if vector_mode else None
    assert _offered(text, semantic) == []


@pytest.mark.parametrize("text,category", [("gipsskruer 3,5x35", None), ("skruer til træ", None), ("gips 12.5 vådrum", "gypsum")])
def test_accessories_are_not_read_as_a_catalog_category(text, category):
    assert parser.detect_category(text) == category


def test_lines_with_a_detected_category_are_unchanged():
    top = _offered("timber 45x95 C24")[0]
    assert top["sku"] == "T24"


def test_uncategorised_line_that_shares_a_catalog_word_is_still_offered():
    # No category keyword, but "Konstruktionstræ" is literally in the SKU name -> keep the suggestion for human review
    got = _offered("Konstruktionstræ", {p["sku"]: 0.7 for p in CATALOG})
    assert got and got[0]["sku"] == "T24" and got[0]["band"] != "HIGH"


GYPSUM = [
    _p("G-MR", "Gipsplade vådrum 12.5mm", "gypsum", {"thickness_mm": 12.5, "board_type": "moisture"}),
    _p("G-FIRE", "Brandgipsplade 12.5mm", "gypsum", {"thickness_mm": 12.5, "board_type": "fire"}),
    _p("G-STD", "Gipsplade standard 12.5mm", "gypsum", {"thickness_mm": 12.5, "board_type": "standard"}),
]


@pytest.mark.parametrize("text,sku", [("Moisture board 12.5mm", "G-MR"), ("wet room board 12.5mm", "G-MR"),
                                      ("Fire board 12.5 mm", "G-FIRE")])
def test_english_gypsum_phrasing_is_recognised_so_board_type_is_a_hard_rule(text, sku):
    assert parser.detect_category(text) == "gypsum"
    attrs = dict(parser.extract_attributes(text))
    attrs["category"] = "gypsum"
    # vector mode where the WRONG board looks closest: the board_type must-match still decides
    semantic = {"G-MR": 0.70, "G-FIRE": 0.80, "G-STD": 0.75}
    top = matcher.match(text, attrs, GYPSUM, semantic)
    assert top and top[0]["sku"] == sku and all(c["sku"] == sku for c in top[:1])
    assert {c["sku"] for c in top} == {sku}  # the other two board types are excluded, never offered
