import streamlit as st

from engine.pareto import compute_pareto_frontier


def render(country_iso3, panel, levers):
    st.header("Model Lab")
    st.caption(
        "NSGA-II multi-objective search over 4 policy levers against 3 objectives: final debt/GDP; "
        "health+education funding; welfare+public-wage-bill spending (combined into one "
        "social-spending-pressure objective for tractability). The funding/spending objectives are "
        "illustrative splits of an aggregate fiscal-space total -- not independently sourced per "
        "category. Frontier points are conditional projections to explore trade-offs, not "
        "recommendations."
    )

    if st.button("Compute Pareto frontier"):
        with st.spinner("Running NSGA-II..."):
            frontier = compute_pareto_frontier(country_iso3, panel, levers)
        st.session_state["pareto_frontier"] = frontier

    frontier = st.session_state.get("pareto_frontier")
    if not frontier:
        st.info("Click 'Compute Pareto frontier' to generate the trade-off explorer.")
        return

    rows = [{**p.levers, **p.objectives} for p in frontier]
    st.dataframe(rows)

    options = list(range(len(frontier)))
    chosen = st.selectbox(
        "Load frontier point into scenario controls", options,
        format_func=lambda i: f"Point {i}: debt/GDP={frontier[i].objectives['final_debt_gdp_pct']:.1f}%",
    )
    if st.button("Load selected point"):
        point = frontier[chosen]
        levers.tax_wedge_delta_pp = point.levers["tax_wedge_delta_pp"]
        levers.primary_balance_target_pct = point.levers["primary_balance_target_pct"]
        levers.indexation_delta_pp = point.levers["indexation_delta_pp"]
        st.success("Levers updated -- see sidebar.")
