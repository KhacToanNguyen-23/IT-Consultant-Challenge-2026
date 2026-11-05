"""MVP-FR-021: the store remembers manual SKU choices after Confirm, can forget them, and never bypasses hard rules."""
from services import dictionary, matcher, parser


def test_phrase_normalisation_ignores_case_punctuation_and_spacing():
    assert dictionary.normalize_phrase("Reglar 45x95,  C24!") == dictionary.normalize_phrase("reglar 45x95 c24") == "reglar 45x95 c24"
    assert dictionary.normalize_phrase(None) == "" and dictionary.normalize_phrase("  ") == ""


def _p(sku, name, specs):
    return {"sku": sku, "name": name, "category": "timber", "technical_specs": specs, "aliases": {}, "selling_unit": "piece", "unit_price": 1.0, "pack_size": None}


A = _p("T24", "Konstruktionstræ 45x95 C24", {"cross_section_mm": "45x95", "strength_grade": "C24"})
B = _p("T24-B", "Konstruktionstræ 45x95 C24 brand B", {"cross_section_mm": "45x95", "strength_grade": "C24"})
C18 = _p("T18", "Konstruktionstræ 45x95 C18", {"cross_section_mm": "45x95", "strength_grade": "C18"})


def _rank(text, boosts=None):
    attrs = dict(parser.extract_attributes(text))
    attrs["category"] = parser.detect_category(text)
    return matcher.match(text, attrs, [A, B, C18], {"T24": 0.80, "T24-B": 0.80, "T18": 0.80}, boosts)


def test_a_learned_mapping_breaks_a_tie_between_equal_candidates():
    plain = _rank("45x95 C24 timber")
    assert plain[0]["reasons"].get("ambiguous") and plain[0]["score"] <= 0.89  # two equal candidates are capped
    boosted = _rank("45x95 C24 timber", {"T24-B": 0.05})
    assert boosted[0]["sku"] == "T24-B" and boosted[0]["reasons"].get("dictionary") is True
    assert boosted[0]["score"] > boosted[1]["score"]


def test_a_mapping_can_never_revive_a_candidate_that_breaks_a_hard_rule():
    got = _rank("45x95 C24 timber", {"T18": 0.20})  # even the maximum boost on a wrong grade
    assert "T18" not in [c["sku"] for c in got]


def test_boost_is_capped_at_the_srs_maximum():
    assert dictionary.MAX_BOOST == 0.20 and dictionary.DEFAULT_BOOST == 0.05


# ------------------------------------------------------------------ integration (needs Postgres, see conftest)
def _confirm_with_manual_choice(counter, text="45x95 timber", sku="SKU-DK-4595-C18-480"):
    sid = counter.open(text)
    counter.analyze(sid)
    counter.call("PATCH", f"/sessions/{sid}/lines/1", json={"requested_qty": 5, "requested_unit": "piece"})
    assert counter.call("PUT", f"/sessions/{sid}/lines/1/selection", json={"sku": sku, "decision": "SKU_EDITED"}).status_code == 200
    return sid


def test_nothing_is_recorded_before_confirm_and_the_manual_choice_is_recorded_after(counter, app_env):
    sid = _confirm_with_manual_choice(counter)
    assert counter.call("GET", "/store-dictionary").json()["items"] == []  # not before Confirm
    assert counter.confirm(sid).status_code == 200
    items = counter.call("GET", "/store-dictionary").json()["items"]
    assert [(i["normalized_phrase"], i["mapped_sku"], i["active"], i["boost"]) for i in items] == [("45x95 timber", "SKU-DK-4595-C18-480", True, 0.05)]


def test_kept_suggestions_and_substitutions_are_not_recorded(counter, app_env):
    sid = counter.open("120 m timber 45x95 C24\n10 plader gips vådrum 12.5 mm")
    counter.analyze(sid)
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"})
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125-B", "decision": "SUBSTITUTION_ACCEPTED"})
    counter.resolve_all(sid)
    counter.confirm(sid)
    phrases = {i["mapped_sku"] for i in counter.call("GET", "/store-dictionary").json()["items"]}
    assert "SKU-GYP-MR-125-B" not in phrases  # the customer asked for something else; never learn the substitute


def test_removing_a_mapping_makes_it_inactive_and_it_is_not_silently_relearned(counter, app_env):
    counter.confirm(_confirm_with_manual_choice(counter))
    entry = counter.call("GET", "/store-dictionary").json()["items"][0]
    r = counter.call("DELETE", f"/store-dictionary/{entry['id']}")
    assert r.status_code == 200 and r.json()["active"] is False and r.json()["deactivated_by"] == "EMP-1042"
    counter.confirm(_confirm_with_manual_choice(counter))  # same manual choice again
    items = counter.call("GET", "/store-dictionary").json()["items"]
    assert len(items) == 1 and items[0]["active"] is False  # respected, not re-created


def test_unknown_mapping_id_is_a_404(counter, app_env):
    r = counter.call("DELETE", "/store-dictionary/999999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_a_learned_mapping_is_applied_to_the_next_session(counter, app_env):
    counter.confirm(_confirm_with_manual_choice(counter))
    sid = counter.open("45x95 timber")
    line = counter.analyze(sid)["lines"][0]
    cand = {c["sku"]: c for c in line["match"]["candidates"]}
    assert cand["SKU-DK-4595-C18-480"]["reasons"].get("dictionary") is True


def test_gap_of_exactly_the_threshold_is_not_capped_srs_fr_009():
    # floating point made 0.95 - 0.90 = 0.0499999..., which used to cap a clear winner below the runner-up
    top = _rank("45x95 C24 timber", {"T24-B": 0.05})
    assert top[0]["score"] == 0.95 and top[1]["score"] == 0.9
    assert not top[0]["reasons"].get("ambiguous")
