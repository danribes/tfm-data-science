"""Analog search engine tests (spec §6.1)."""
import pytest
from engine.analog import (
    ANALOG_PANEL, find_analogs, debt_payable_verdict, structural_diffs,
)
from engine.levers import Levers, preset_levers


def test_analog_panel_schema():
    required = [
        "iso3", "year", "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
        "gdp_growth", "unemployment", "inflation", "r_minus_g",
        "emu_member", "fx_regime", "ext_debt_share", "democracy",
        "trade_openness", "tfp_growth_5y", "labor_prod_growth_5y",
    ]
    for col in required:
        assert col in ANALOG_PANEL.columns, f"missing column: {col}"
    assert ANALOG_PANEL["debt_gdp"].notna().all(), "null debt_gdp in panel"
    assert len(ANALOG_PANEL[ANALOG_PANEL["iso3"] != "ESP"]) >= 100


def test_analog_no_spain():
    matches = find_analogs(Levers(), horizon=10)
    assert all(m["iso3"] != "ESP" for m in matches)


def test_analog_search_returns_3():
    for levers in [Levers(), preset_levers("S7")]:
        matches = find_analogs(levers, horizon=10)
        assert len(matches) == 3
        assert [m["rank"] for m in matches] == [1, 2, 3]


def test_analog_outcome_truncation():
    # Use a match with high year (near 2023) — it should flag truncated=True
    # on points beyond the panel's last year.
    matches = find_analogs(Levers(), horizon=24)
    for m in matches:
        if m["match_year"] >= 2018:
            truncated_points = [p for p in m["outcome"] if p["truncated"]]
            assert len(truncated_points) > 0, (
                f"expected truncated points for {m['iso3']} {m['match_year']}"
            )


def test_analog_diff_directions():
    matches = find_analogs(Levers(), horizon=10)
    valid = {"converge", "diverge", "neutral"}
    for m in matches:
        for d in m["diffs"]:
            assert d["direction"] in valid, (
                f"invalid direction {d['direction']!r} in {d['dimension']}"
            )


def test_dominant_lever_bonus():
    # Moving prima (risk premium) far from baseline should shift ranking
    # toward high-yield episodes (episodes where interest_rate_10y was high).
    base_matches = find_analogs(Levers(), horizon=10)
    high_prima = Levers(prima=350.0)  # 350pb spread — far from baseline
    stressed_matches = find_analogs(high_prima, horizon=10)
    # At least one match should differ (ranking changes or episodes differ)
    base_ids = {(m["iso3"], m["match_year"]) for m in base_matches}
    stressed_ids = {(m["iso3"], m["match_year"]) for m in stressed_matches}
    assert base_ids != stressed_ids, "high prima should change analog ranking"


def test_r_minus_g_in_outcome():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        for pt in m["outcome"]:
            if not pt["truncated"]:
                assert "r_minus_g" in pt
                assert isinstance(pt["r_minus_g"], float)


def test_debt_payable_verdict_auto():
    assert debt_payable_verdict(-1.2) == "auto"   # r < g by >0.5pp


def test_debt_payable_verdict_surplus():
    assert debt_payable_verdict(1.8) == "requires_surplus"  # r > g by >0.5pp


def test_debt_payable_verdict_borderline():
    assert debt_payable_verdict(0.3) == "borderline"   # |r-g| ≤ 0.5
    assert debt_payable_verdict(-0.4) == "borderline"


def test_tfp_diff_present():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        dims = {d["dimension"] for d in m["diffs"]}
        assert "tfp_trend" in dims
        assert "labor_productivity" in dims


def test_match_snapshot_has_r_minus_g():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        assert "r_minus_g" in m["match_snapshot"]
        assert len(m["match_snapshot"]) == 7
