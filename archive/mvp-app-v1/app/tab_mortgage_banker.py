import streamlit as st

from personas.mortgage_banker import build_mortgage_dashboard
from personas.narrative import render_narrative


def render(scenario, panel):
    st.header("Mortgage Banker view")

    loan_principal = st.number_input("Loan principal", min_value=10_000, value=200_000, step=10_000)
    loan_term_years = st.slider("Loan term (years)", 5, 40, 25, key="mortgage_loan_term_years")

    years = [p.year for p in scenario.debt_path]
    rate_path = [p.interest_rate_pct for p in scenario.debt_path]
    baseline_unemployment = scenario.unemployment_path_pct[0] if scenario.unemployment_path_pct else 0.0

    views = build_mortgage_dashboard(
        rate_path, scenario.unemployment_path_pct, years,
        loan_principal, loan_term_years, baseline_unemployment,
    )

    st.subheader("Projected mortgage rate & monthly payment")
    st.line_chart({"Mortgage rate (%)": {v.year: v.mortgage_rate_pct for v in views}})
    st.line_chart({"Monthly payment": {v.year: v.monthly_payment for v in views}})

    st.subheader("Default-risk proxy (calibrated default weights, not empirically fit)")
    st.line_chart({"Default-risk proxy": {v.year: v.default_risk_proxy for v in views}})

    st.caption(render_narrative(
        "mortgage_banker",
        scenario_summary=f"mortgage rate reaches {views[-1].mortgage_rate_pct:.2f}% by {views[-1].year}",
        year=views[-1].year, rate=views[-1].mortgage_rate_pct,
        payment=views[-1].monthly_payment, risk=views[-1].default_risk_proxy,
    ))
