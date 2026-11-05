"""MVP-FR-031: the three KPI queries run on the real schema and never divide by zero (integration, see conftest)."""
import pytest

from scripts import kpi


def test_all_three_queries_are_present():
    assert set(kpi.load_queries()) == {"time_to_serve", "substitution_acceptance", "zero_touch"}


def test_kpis_on_an_empty_database_return_nulls_not_errors(app_env):
    from db.database import SessionLocal

    with SessionLocal() as db:
        out = kpi.run_all(db)
    assert out["time_to_serve"]["confirmed_sessions"] == 0 and out["time_to_serve"]["median_seconds"] is None
    assert out["substitution_acceptance"]["acceptance_rate"] is None  # no stock-outs yet -> NULL, not a division error
    assert out["zero_touch"]["confirmed_lines"] == 0 and out["zero_touch"]["zero_touch_rate"] is None


def test_kpis_count_real_confirmed_sessions_and_accepted_substitutions(counter, app_env):
    from db.database import SessionLocal

    sid = counter.open("120 m timber 45x95 C24\n10 plader gips vådrum 12.5 mm")
    counter.analyze(sid)
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125", "decision": "SKU_EDITED"})
    counter.call("PUT", f"/sessions/{sid}/lines/2/selection", json={"sku": "SKU-GYP-MR-125-B", "decision": "SUBSTITUTION_ACCEPTED"})
    counter.resolve_all(sid)
    assert counter.confirm(sid).status_code == 200
    with SessionLocal() as db:
        out = kpi.run_all(db)
    assert out["time_to_serve"]["confirmed_sessions"] == 1 and out["time_to_serve"]["under_2m_rate"] == 1
    sub = out["substitution_acceptance"]
    assert sub["total_stockouts"] >= 1 and sub["accepted"] == 1 and 0 < float(sub["acceptance_rate"]) <= 1
    zt = out["zero_touch"]
    assert zt["confirmed_lines"] == 2 and zt["zero_touch_lines"] <= 1  # the substituted line was touched
