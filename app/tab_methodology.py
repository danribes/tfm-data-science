import streamlit as st

from data.panel_builder import load_catalog
from engine.satellite import OKUN_COEFFICIENT, PHILLIPS_SLOPE
from personas.mortgage_banker import MORTGAGE_SPREAD_PP, DEFAULT_RISK_UNEMPLOYMENT_WEIGHT, DEFAULT_RISK_RATE_WEIGHT


def render(panel, coverage, stress_model):
    st.header("Data & Methodology")

    st.subheader("Indicator coverage for this country")
    catalog = load_catalog()
    rows = []
    for key, spec in catalog.items():
        result = panel.get(key)
        rows.append({
            "indicator": spec["label"],
            "source": spec["sources"][0]["type"],
            "available": bool(result.available) if result else False,
            "note": spec.get("note", ""),
        })
    st.dataframe(rows)
    st.metric("Overall coverage", f"{coverage*100:.0f}%")

    st.subheader("Engine constants")
    st.write({
        f"Okun coefficient ({OKUN_COEFFICIENT})": "calibrated default (literature range 0.3-0.5), not country-specific",
        f"Phillips slope ({PHILLIPS_SLOPE})": "calibrated default, not country-specific",
        f"Mortgage spread ({MORTGAGE_SPREAD_PP} pp)": "calibrated default, not country-specific",
        "Default-risk weights": (
            f"unemployment={DEFAULT_RISK_UNEMPLOYMENT_WEIGHT}, rate={DEFAULT_RISK_RATE_WEIGHT} "
            "-- calibrated defaults, not empirically fit"
        ),
    })

    st.subheader("ML fiscal-stress model")
    if stress_model.available:
        try:
            st.markdown(open("models/METRICS.md").read())
        except FileNotFoundError:
            st.info("Model available, but models/METRICS.md was not found.")
        st.caption(
            "This score is a directional pattern-matching signal against historical cross-country "
            "debt-distress episodes -- not a validated predictor. See the metrics above (trained on "
            "a small, heavily imbalanced panel) before treating it as anything beyond a qualitative "
            "input."
        )
    else:
        st.warning(f"Model unavailable: {stress_model.load_error}")

    st.subheader("Known gaps & limitations")
    st.markdown(
        "- COFOG-derived spending indicators (public wage bill, security, welfare, pensions, house "
        "prices) are EU/OECD-only -- most non-EU/OECD countries will show N/A for these.\n"
        "- No rent-price data source is integrated -- rental yield always shows N/A in this MVP.\n"
        "- The baseline scenario projects the primary balance from the lever default (0%), not the "
        "country's most recently observed fiscal stance -- a documented simplification of this "
        "MVP's debt-dynamics engine.\n"
        "- The fiscal-space allocator's category splits (health / education / welfare / "
        "public-wage-bill / security / infrastructure / public-investment) are an illustrative "
        "split of an aggregate spending total, driven by user-set shares -- not independently "
        "sourced per category.\n"
        "- Model Lab's Pareto explorer combines welfare-spend and public-wage-bill "
        "objectives into one social-spending-pressure objective (see engine/pareto.py).\n"
        "- All outputs on every tab are conditional projections under user-chosen levers, not "
        "forecasts, advice, or buy/sell/vote-style recommendations.\n"
    )
