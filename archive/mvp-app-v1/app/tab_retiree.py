import streamlit as st

from personas.retiree import build_retiree_dashboard
from personas.narrative import render_narrative


def render(scenario, stress_result, panel):
    st.header("Retiree view")

    baseline_health = None
    if panel["health_exp_gdp"].available:
        baseline_health = panel["health_exp_gdp"].values[max(panel["health_exp_gdp"].values)]

    dashboard = build_retiree_dashboard(scenario, stress_result, baseline_health)

    years = [y.year for y in dashboard.years]
    real_index = [y.real_pension_index for y in dashboard.years]
    st.subheader("Pension purchasing power (real, base=100 today)")
    st.line_chart({"Real pension index": dict(zip(years, real_index))})

    if stress_result.available:
        st.metric(
            "Fiscal stress score (0-100)", f"{stress_result.score:.0f}",
            help=(
                "Directional pattern-matching signal vs. historical cross-country debt-distress "
                "episodes -- not a validated predictor. Trained on a small, heavily imbalanced "
                "historical panel (see Data & Methodology tab); a conditional projection input, "
                "not a certified forecast or recommendation."
            ),
        )
    else:
        st.info(f"Fiscal stress model unavailable: {stress_result.error}")

    adequacy = dashboard.years[-1].health_funding_adequacy_pct
    if adequacy is not None:
        st.metric(
            f"Health funding adequacy in {years[-1]} vs. today", f"{adequacy:.0f}%",
            help=(
                "Compares the health share of the fiscal-space allocator's user-set spending split "
                "against baseline health expenditure. That category split is an illustrative split "
                "of an aggregate -- not independently sourced per category."
            ),
        )
    else:
        st.info("N/A -- not available for this country")

    st.caption(render_narrative(
        "retiree",
        scenario_summary=f"real pension index reaches {real_index[-1]:.1f} by {years[-1]}",
        year=years[-1], real_index=real_index[-1],
        adequacy=f"{adequacy:.0f}%" if adequacy is not None else "N/A",
    ))
