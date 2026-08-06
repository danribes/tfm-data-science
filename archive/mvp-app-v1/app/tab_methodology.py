import streamlit as st

from data.panel_builder import load_catalog
from engine.satellite import OKUN_COEFFICIENT, PHILLIPS_SLOPE
from engine.scenario import BASELINE_DEFAULTS, BASELINE_INDICATOR_LABELS
from personas.mortgage_banker import MORTGAGE_SPREAD_PP, DEFAULT_RISK_UNEMPLOYMENT_WEIGHT, DEFAULT_RISK_RATE_WEIGHT


def render(panel, coverage, stress_model, scenario=None):
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
    engine_constants = {
        f"Okun coefficient ({OKUN_COEFFICIENT})": "calibrated default (literature range 0.3-0.5), not country-specific",
        f"Phillips slope ({PHILLIPS_SLOPE})": "calibrated default, not country-specific",
        f"Mortgage spread ({MORTGAGE_SPREAD_PP} pp)": "calibrated default, not country-specific",
        "Default-risk weights": (
            f"unemployment={DEFAULT_RISK_UNEMPLOYMENT_WEIGHT}, rate={DEFAULT_RISK_RATE_WEIGHT} "
            "-- calibrated defaults, not empirically fit"
        ),
    }
    for key, default_value in BASELINE_DEFAULTS.items():
        engine_constants[f"{BASELINE_INDICATOR_LABELS[key]} baseline default ({default_value})"] = (
            "generic calibration default, used only when the real indicator is unavailable for "
            "the country"
        )
    st.write(engine_constants)

    st.subheader("Baseline calibration for this country")
    if scenario is not None:
        baseline_rows = []
        for key, label in BASELINE_INDICATOR_LABELS.items():
            if key in scenario.baseline_years:
                year = scenario.baseline_years[key]
                value = panel[key].values[year] if panel.get(key) and panel[key].available else None
                baseline_rows.append({
                    "indicator": label,
                    "year used": year,
                    "value": value,
                    "source": "country data",
                })
            else:
                baseline_rows.append({
                    "indicator": label,
                    "year used": "N/A",
                    "value": BASELINE_DEFAULTS[key],
                    "source": "generic calibration default (country data unavailable)",
                })
        st.dataframe(baseline_rows)
        st.caption(
            "These are the seven baseline indicators the scenario engine reads at the start year "
            "before applying scenario levers. 'source: country data' rows show the year of the "
            "most recent observation on record -- not necessarily recent."
        )

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
        "- Under current engine wiring, the final-debt objective responds only to the "
        "primary-balance lever; the tax-wedge, indexation, and wage-bill levers move the "
        "fiscal-space and income objectives, not the debt path.\n"
        "- Plain-English scenario parsing (design spec section 4.5, a text box that would parse a "
        "natural-language scenario description into lever settings when an ANTHROPIC_API_KEY is "
        "set) is not implemented in this MVP; LLM narratives are.\n"
        "- All outputs on every tab are conditional projections under user-chosen levers, not "
        "forecasts, advice, or buy/sell/vote-style recommendations.\n"
    )
