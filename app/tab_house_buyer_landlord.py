import streamlit as st

from personas.house_buyer_landlord import build_buy_to_live_view, build_buy_to_let_view


def render(scenario, panel):
    st.header("House-buyer / Landlord view")
    mode = st.radio("I am a...", ["Buy-to-live", "Buy-to-let"], horizontal=True)

    years = [p.year for p in scenario.debt_path]
    rate_path = [p.interest_rate_pct for p in scenario.debt_path]

    if mode == "Buy-to-live":
        home_price = st.number_input("Home price", min_value=20_000, value=250_000, step=10_000)
        down_payment_pct = st.slider("Down payment (%)", 0, 50, 20)
        loan_term_years = st.slider("Loan term (years)", 5, 40, 25, key="buy_to_live_loan_term_years")
        monthly_income = st.number_input("Monthly household income (0 = skip)", min_value=0, value=0, step=100)

        views = build_buy_to_live_view(
            rate_path, years, home_price, down_payment_pct, loan_term_years,
            monthly_income or None,
        )
        st.line_chart({"Monthly payment": {v.year: v.monthly_payment for v in views}})
        if views[-1].payment_to_income_pct is not None:
            st.metric("Payment-to-income", f"{views[-1].payment_to_income_pct:.1f}%")
        else:
            st.info("Enter monthly household income above to see payment-to-income ratio.")
    else:
        house_price_result = panel["house_price_index"]
        if not house_price_result.available:
            st.warning("N/A -- house price data not available for this country")
            return

        views = build_buy_to_let_view(house_price_result.values, years)
        st.line_chart({
            "House price index": {v.year: v.house_price_index for v in views if v.house_price_index is not None},
        })
        if views[-1].house_price_growth_pct is not None:
            st.metric("Cumulative house price growth", f"{views[-1].house_price_growth_pct:.1f}%")
        st.info(f"Rental yield: {views[-1].rental_yield_pct}")
