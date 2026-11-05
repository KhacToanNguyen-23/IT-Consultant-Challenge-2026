"""LLM safety rails (SRS v2 §5) and i18n. No network: FakeLLM returns canned replies."""
import json
import uuid

import pytest

import i18n
from ai import llm
from db.models import SessionLine
from services import parser, pipeline


class _DB:
    def __init__(self):
        self.added = []

    def add(self, o):
        self.added.append(o)


@pytest.fixture(autouse=True)
def reset_llm():
    yield
    llm.set_provider_for_tests(None)


def _line(text):
    return SessionLine(line_id=uuid.uuid4(), session_id=uuid.uuid4(), line_no=1, raw_customer_input=text,
                       parsed_name=text, parse_status="OK", attributes={})


def _enrich(text, *responses):
    llm.set_provider_for_tests(llm.FakeLLM(list(responses)))
    l, db = _line(text), _DB()
    attrs = {l.line_id: pipeline.line_attrs(l)}
    info = pipeline.enrich_with_llm(db, [l], attrs)
    return attrs[l.line_id], info, db


def test_llm_disabled_by_default_without_key():
    llm.set_provider_for_tests(None)
    assert llm.extract_attributes("Moisture board 12.5mm", None) is None


def test_llm_fills_category_and_type_with_evidence():
    # a phrasing the rules cannot classify (the rules do recognise "Moisture board", so it no longer needs the LLM)
    reply = json.dumps({"category": "gypsum", "board_type": "moisture", "thickness_mm": 12.5,
                        "evidence": {"category": "wallboard", "board_type": "bathroom", "thickness_mm": "12.5mm"}})
    attrs, info, db = _enrich("Bathroom wallboard 12.5mm", reply)
    assert attrs["category"] == "gypsum" and attrs["board_type"] == "moisture"
    assert "category" in attrs["_llm"] and info["llm_calls"] == 1
    assert db.added and db.added[0].step == "llm_attribute_extraction" and db.added[0].input_tokens == 10


def test_llm_cannot_invent_a_grade_without_evidence():
    reply = json.dumps({"category": "timber", "strength_grade": "C24", "evidence": {"strength_grade": "C24"}})
    attrs, _, db = _enrich("Regel 45x95", reply)
    assert "strength_grade" not in attrs  # "C24" does not occur in the line → dropped
    assert "dropped=" in db.added[0].status and "strength_grade" in db.added[0].status


def test_llm_value_must_agree_with_its_evidence():
    out, dropped = llm.validate({"thickness_mm": 15, "evidence": {"thickness_mm": "12.5mm"}}, "Gips 12.5mm")
    assert out == {} and dropped == ["thickness_mm"]


def test_rules_win_over_llm():
    # evidence is valid ("15mm" occurs), but the rules already read 12.5 → the LLM value is ignored
    reply = json.dumps({"thickness_mm": 15, "evidence": {"thickness_mm": "15mm"}})
    attrs, _, _ = _enrich("Gips 12.5mm eller 15mm", reply)
    assert attrs["thickness_mm"] == 12.5 and "_llm" not in attrs


def test_invalid_json_gets_one_repair_retry():
    good = json.dumps({"category": "gypsum", "evidence": {"category": "plasterboard"}})
    p = llm.FakeLLM(["not json at all", good])
    llm.set_provider_for_tests(p)
    r = llm.extract_attributes("plasterboard 12.5mm", None)
    assert r["status"] == "repaired" and r["attrs"]["category"] == "gypsum" and len(p.calls) == 2


def test_invalid_json_twice_falls_back_to_rules():
    r = None
    llm.set_provider_for_tests(llm.FakeLLM(["nope", "still nope"]))
    r = llm.extract_attributes("plasterboard 12.5mm", None)
    assert r["attrs"] == {} and r["status"].startswith("error")


def test_transport_error_is_not_retried():
    p = llm.FakeLLM([TimeoutError("slow"), "{}"])
    llm.set_provider_for_tests(p)
    r = llm.extract_attributes("x 12mm", None)
    assert len(p.calls) == 1 and r["status"] == "error:TimeoutError"


def test_llm_not_called_for_clear_lines():
    p = llm.FakeLLM([])
    llm.set_provider_for_tests(p)
    l = _line("Timber 45x95 C24")
    attrs = {l.line_id: pipeline.line_attrs(l)}
    info = pipeline.enrich_with_llm(_DB(), [l], attrs)
    assert p.calls == [] and info["llm_calls"] == 0


def test_llm_receives_masked_text_only():
    from services import pii
    masked = pii.mask("Ring +45 22 33 44 55 gips 12.5mm kunde@firma.dk")
    p = llm.FakeLLM(["{}"])
    llm.set_provider_for_tests(p)
    llm.extract_attributes(masked, None)
    sent = p.calls[0][1]
    assert "22 33 44 55" not in sent and "kunde@firma.dk" not in sent


# ---------------- i18n ----------------
def test_translations_both_languages():
    i18n.set_lang("vi")
    assert i18n.t("blk_clarify") == "cần làm rõ/chọn SKU"
    i18n.set_lang("en")
    assert i18n.t("unresolved_confirm", n=2).startswith("2 line")
    i18n.set_lang("xx")
    assert i18n.lang() == "en"


def test_stored_codes_render_in_current_language():
    stored = i18n.code("conv_unconvertible", unit="bag", su="board")
    i18n.set_lang("en")
    assert i18n.render(stored) == "Cannot convert bag → board"
    i18n.set_lang("vi")
    assert i18n.render(stored) == "Không quy đổi được bag → board"
    assert i18n.render("legacy free text") == "legacy free text"
    i18n.set_lang("en")


def test_every_key_has_both_languages():
    assert all(set(v) == {"en", "vi"} for v in i18n.M.values())
