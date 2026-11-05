"""SRS §15.3 chip order (max 4 per line) and golden attribute extraction for the five seeded categories."""
import uuid

import pytest

from db.models import SessionLine
from services import parser, pipeline

PRODUCTS = {
    "T": {"sku": "T", "category": "timber", "name": "t", "unit_price": 1, "currency": "DKK", "pack_size": None, "selling_unit": "piece_4.8m",
          "technical_specs": {"length_m": 4.8, "strength_grade": "C24", "cross_section_mm": "45x95", "treatment": ["ntr"]}},
    "G": {"sku": "G", "category": "gypsum", "name": "g", "unit_price": 1, "currency": "DKK", "pack_size": None, "selling_unit": "sheet",
          "technical_specs": {"brand": "Gyproc", "moisture_resistant": True, "board_type": "moisture", "thickness_mm": 12.5}},
    "I": {"sku": "I", "category": "insulation", "name": "i", "unit_price": 1, "currency": "DKK", "pack_size": 2.88, "selling_unit": "pack",
          "technical_specs": {"brand": "Rockwool", "material": "stone_wool", "thickness_mm": 95}},
    "C": {"sku": "C", "category": "cement", "name": "c", "unit_price": 1, "currency": "DKK", "pack_size": None, "selling_unit": "bag",
          "technical_specs": {"product_type": "mortar", "bag_weight_kg": 25}},
    "D": {"sku": "D", "category": "decking", "name": "d", "unit_price": 1, "currency": "DKK", "pack_size": None, "selling_unit": "piece_4.2m",
          "technical_specs": {"length_m": 4.2, "treatment": ["pressure_treated"], "cross_section_mm": "28x120"}},
}


def _chips(sku):
    line = SessionLine(line_id=uuid.uuid4(), session_id=uuid.uuid4(), line_no=1, raw_customer_input="x", parsed_name="x",
                       parse_status="OK", attributes={}, original_sku=sku, final_sku=sku, line_status="MATCHED")
    return [c["attr"] for c in pipeline.serialize_line(line, PRODUCTS)["chips"]]


@pytest.mark.parametrize("sku,expected", [
    ("T", ["cross_section_mm", "strength_grade", "length_m", "treatment"]),
    ("G", ["thickness_mm", "board_type"]),
    ("I", ["thickness_mm", "material", "pack_coverage"]),
    ("C", ["bag_weight_kg", "product_type"]),
    ("D", ["cross_section_mm", "treatment", "length_m"]),
])
def test_chips_follow_the_srs_order_for_each_category(sku, expected):
    got = _chips(sku)
    assert got == expected and len(got) <= 4


def test_insulation_pack_coverage_chip_shows_square_metres_per_pack():
    line = SessionLine(line_id=uuid.uuid4(), session_id=uuid.uuid4(), line_no=1, raw_customer_input="x", parsed_name="x",
                       parse_status="OK", attributes={}, original_sku="I", final_sku="I", line_status="MATCHED")
    chips = pipeline.serialize_line(line, PRODUCTS)["chips"]
    assert chips[-1] == {"attr": "pack_coverage", "value": "2.88 m²/pk", "tone": "slate"}


@pytest.mark.parametrize("text,expected", [
    ("45x95 C24 timber", {"category": "timber", "cross_section_mm": "45x95", "strength_grade": "C24"}),
    ("Konstruktionstræ 45 x 95 c18", {"category": "timber", "cross_section_mm": "45x95", "strength_grade": "C18"}),
    ("gips vådrum 12,5 mm", {"category": "gypsum", "thickness_mm": 12.5, "board_type": "moisture"}),
    ("Fire board 12.5 mm", {"category": "gypsum", "thickness_mm": 12.5, "board_type": "fire"}),
    ("Rockwool 95 mm isolering", {"category": "insulation", "thickness_mm": 95, "brand": "Rockwool"}),
    ("cement 25 kg", {"category": "cement", "bag_weight_kg": 25.0, "product_type": "cement"}),
    ("hurtigcement 25 kg", {"category": "cement", "bag_weight_kg": 25.0, "product_type": "rapid_cement"}),
    ("terrassebræt 28x120 trykimpr.", {"category": "decking", "cross_section_mm": "28x120", "treatment": ["pressure_treated"]}),
])
def test_golden_attributes_are_extracted_by_rules(text, expected):
    got = parser.extract_attributes(text)
    assert {k: got.get(k) for k in expected} == expected


@pytest.mark.parametrize("text,absent", [("45x95 timber", "strength_grade"), ("gips 12.5 mm", "board_type"), ("cement", "bag_weight_kg")])
def test_attributes_the_customer_did_not_state_are_not_invented(text, absent):
    assert absent not in parser.extract_attributes(text)
