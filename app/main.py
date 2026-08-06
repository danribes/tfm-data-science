import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from data.cache import DiskCache
from data.country_list import load_country_list
from data.panel_builder import build_country_panel, coverage_score
from engine.scenario import ScenarioLevers, run_scenario
from engine.ml_stress_score import FiscalStressModel
from app import tab_retiree, tab_mortgage_banker, tab_house_buyer_landlord, tab_model_lab, tab_methodology

st.set_page_config(page_title="Sovereign Fiscal Scenario Explorer", layout="wide")


def _init_session_state():
    if "country_iso3" not in st.session_state:
        st.session_state.country_iso3 = "ESP"
    if "levers" not in st.session_state:
        st.session_state.levers = ScenarioLevers()


def main():
    _init_session_state()
    cache = DiskCache()
    stress_model = FiscalStressModel()

    countries = load_country_list()
    country_names = {c["iso3"]: c["name"] for c in countries}
    sorted_iso3 = sorted(country_names)

    st.sidebar.title("Country & scenario")
    default_index = (
        sorted_iso3.index(st.session_state.country_iso3)
        if st.session_state.country_iso3 in country_names else 0
    )
    selected_iso3 = st.sidebar.selectbox(
        "Country", options=sorted_iso3, format_func=lambda iso3: country_names[iso3], index=default_index,
    )
    st.session_state.country_iso3 = selected_iso3

    force_refresh = st.sidebar.button("Refresh data")
    panel = build_country_panel(selected_iso3, cache=cache, force_refresh=force_refresh)
    score = coverage_score(panel)
    if score < 0.6:
        st.sidebar.warning(
            f"Limited data coverage for this country ({score*100:.0f}%) -- several metrics "
            "will show as unavailable."
        )
    else:
        st.sidebar.caption(f"Data coverage: {score*100:.0f}%")

    levers = st.session_state.levers
    levers.horizon_years = st.sidebar.slider("Horizon (years)", 1, 25, levers.horizon_years)
    levers.tax_wedge_delta_pp = st.sidebar.slider(
        "Tax wedge delta (pp)", -5.0, 5.0, levers.tax_wedge_delta_pp)
    levers.primary_balance_target_pct = st.sidebar.slider(
        "Primary balance target (% GDP)", -4.0, 4.0, levers.primary_balance_target_pct)
    levers.indexation_delta_pp = st.sidebar.slider(
        "Pension/wage indexation delta (pp)", -1.5, 1.0, levers.indexation_delta_pp)

    scenario = run_scenario(selected_iso3, panel, levers)

    corruption = panel["corruption_control"]
    corruption_latest = corruption.values[max(corruption.values)] if corruption.available else 0.0
    stress_result = stress_model.score({
        "debt_gdp": scenario.debt_path[-1].debt_gdp_pct,
        "gdp_growth": scenario.debt_path[-1].growth_rate_pct,
        "inflation": scenario.inflation_path_pct[-1] if scenario.inflation_path_pct else 0.0,
        "unemployment": scenario.unemployment_path_pct[-1] if scenario.unemployment_path_pct else 0.0,
        "real_interest_rate": scenario.debt_path[-1].interest_rate_pct,
        "net_lending_borrowing": scenario.debt_path[-1].primary_balance_pct,
        "corruption_control": corruption_latest,
    })

    tabs = st.tabs(["Retiree", "Mortgage Banker", "House-buyer/Landlord", "Model Lab", "Data & Methodology"])
    with tabs[0]:
        tab_retiree.render(scenario, stress_result, panel)
    with tabs[1]:
        tab_mortgage_banker.render(scenario, panel)
    with tabs[2]:
        tab_house_buyer_landlord.render(scenario, panel)
    with tabs[3]:
        tab_model_lab.render(selected_iso3, panel, levers)
    with tabs[4]:
        tab_methodology.render(panel, score, stress_model)


if __name__ == "__main__":
    main()
