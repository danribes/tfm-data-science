"""Dashboard MVP — "Dinero público → Resultados".

Lee la capa gold directamente (sin depender de la API) y muestra las cuatro
piezas del bloque analítico con su incertidumbre SIEMPRE visible.

    streamlit run app/dashboard.py
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"
FIGS = ROOT / "docs" / "figures"

BLUE, GREEN, ORANGE, VIOLET, RED, GRIS = "#2a78d6", "#008300", "#eb6834", "#4a3aa7", "#e34948", "#9a9992"

st.set_page_config(page_title="Dinero público → Resultados", page_icon="📊", layout="wide")
st.title("Dinero público → Resultados")
st.caption("TFM Máster en Data Science (Evolve) · Daniel Ribes · la banda es la parte "
           "informativa del pronóstico; los límites de método, en cada pestaña")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(GOLD / name)


tab1, tab2, tab3, tab4 = st.tabs(
    ["🏠 Asequibilidad CCAA", "🗺️ Atlas fiscal", "⚕️ Rendimiento A1", "📉 Deuda: escenarios D1"])

# ---------- 1. Asequibilidad ----------
with tab1:
    q = load("gold_ccaa_trimestral.csv")
    fc = load("gold_forecast_ccaa.csv")
    c1, c2 = st.columns([1, 3])
    with c1:
        terr = st.selectbox("Territorio", sorted(fc.ccaa.unique()),
                            index=sorted(fc.ccaa.unique()).index("Nacional"))
        esc = st.radio("Escenario salarial (mueve el ratio, no el IPV)",
                       ["central_salarios_2pct", "salarios_0pct", "salarios_4pct"])
        d = fc[(fc.ccaa == terr) & (fc.escenario == esc)].sort_values("h")
        r24 = load("gold_asequibilidad_ccaa.csv").query("ccaa==@terr and anyo==2024")
        if not r24.empty:
            st.metric("Ratio asequibilidad 2024 (2015=100)",
                      f"{r24.ratio_asequibilidad.iloc[0]:.2f}")
        st.metric(f"Ratio proyectado {d.periodo_pred.iloc[-1]}",
                  f"{d.ratio_aseq_pred.iloc[-1]:.2f}")
        st.caption("Indicador APROXIMADO de evolución relativa (feedback del tutor); "
                   "modelo drift, ganador del protocolo completo — ver docs/test_final_t1.md")
    with c2:
        hist = q[q.ccaa == terr].sort_values(["anyo", "quarter"])
        hist["t"] = hist.anyo.astype(str) + "Q" + hist.quarter.astype(str)
        fig = go.Figure()
        fig.add_scatter(x=hist.t, y=hist.ipv_idx15, name="IPV observado (2015=100)",
                        line=dict(color=BLUE, width=2))
        fig.add_scatter(x=d.periodo_pred, y=d.pi_95_high, line=dict(width=0), showlegend=False)
        fig.add_scatter(x=d.periodo_pred, y=d.pi_95_low, fill="tonexty",
                        fillcolor="rgba(42,120,214,0.10)", line=dict(width=0), name="banda 95 %")
        fig.add_scatter(x=d.periodo_pred, y=d.pi_80_high, line=dict(width=0), showlegend=False)
        fig.add_scatter(x=d.periodo_pred, y=d.pi_80_low, fill="tonexty",
                        fillcolor="rgba(42,120,214,0.22)", line=dict(width=0), name="banda 80 %")
        fig.add_scatter(x=d.periodo_pred, y=d.ipv_pred, name="pronóstico drift",
                        line=dict(color=BLUE, width=2, dash="dash"))
        fig.update_layout(height=430, margin=dict(t=30, b=10),
                          title=f"{terr}: IPV observado y abanico empírico 2026–2027")
        st.plotly_chart(fig, use_container_width=True)

# ---------- 2. Atlas ----------
with tab2:
    st.markdown("16 figuras, España frente a la mediana mundial (GMD/JST, 202 países) o al "
                "panel europeo. Lectura completa en `docs/atlas.md`.")
    atlas_figs = sorted((FIGS / "atlas").glob("*.png"))
    sel = st.select_slider("Figura", options=[p.stem for p in atlas_figs], value="b03_vivienda_publica_vs_total")
    st.image(str(FIGS / "atlas" / f"{sel}.png"), use_container_width=True)

# ---------- 3. Rendimiento A1 ----------
with tab3:
    r = load("gold_rendimiento_pais.csv")
    st.markdown("**No es una liga.** Residual LOOCV de esperanza de vida con intervalo 90 % "
                "por cuartil de renta; solo 16/164 países salen de su banda. `docs/rendimiento_a1.md`.")
    colores = dict(zip(sorted(r.grupo_renta.unique()), [BLUE, GREEN, ORANGE, VIOLET]))
    fig = go.Figure()
    for g, d in r.groupby("grupo_renta"):
        fig.add_scatter(x=d.gasto, y=d.residual, mode="markers", name=g,
                        marker=dict(color=colores[g], size=7),
                        error_y=dict(type="data", array=d.semiancho_90, thickness=0.8),
                        text=d.iso3, hovertemplate="%{text}: %{y:+.1f} años (gasto %{x:.1f} %PIB)")
    fig.add_hline(y=0, line_color=GRIS)
    esp = r[r.iso3 == "ESP"]
    fig.add_annotation(x=esp.gasto.iloc[0], y=esp.residual.iloc[0], text="<b>ESP</b>", showarrow=True)
    fig.update_layout(height=480, xaxis_title="gasto sanitario público 2010–14 (% PIB)",
                      yaxis_title="años de e0 sobre lo esperado", margin=dict(t=20))
    st.plotly_chart(fig, use_container_width=True)

# ---------- 4. Escenarios de deuda ----------
with tab4:
    e = load("gold_escenarios_deuda.csv")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown("**Palancas (senda propia)** — elegir es política, no estadística")
        r_mkt = st.slider("Tipo de mercado (%)", 2.0, 6.0, 3.5, 0.25)
        g_real = st.slider("Crecimiento real (%)", 0.0, 3.0, 1.3, 0.1)
        pb_extra = st.slider("Ajuste del saldo primario (pp)", -2.0, 4.0, 0.0, 0.25)
        demog = st.checkbox("Presión demográfica (motor de proyección)", True)
    with c2:
        fig = go.Figure()
        cols = {"central": BLUE, "sin_demografia": GRIS, "consolidacion": GREEN,
                "inversion": ORANGE, "tipos_altos": RED, "crecimiento": "#1baf7a"}
        for k, dd in e.groupby("escenario"):
            fig.add_scatter(x=dd.year, y=dd.deuda, name=k, line=dict(color=cols.get(k, GRIS), width=1.6,
                            dash="dash" if k == "sin_demografia" else "solid"))
        # senda propia: misma aritmética r−g que analysis/escenarios_d1.py
        pres = (e[e.escenario == "central"].set_index("year")["presion_demog"]
                if demog else pd.Series(0.0, index=range(2024, 2051)))
        d, r_ef = 105.2, 2.4 / 105.2 * 100
        propia = []
        for y in range(2024, 2051):
            r_ef += (r_mkt - r_ef) / 8
            pb = -0.9 - float(pres.get(y, 0.0)) + pb_extra
            d = d * (1 + r_ef / 100) / (1 + (g_real + 2.0) / 100) - pb
            propia.append(d)
        fig.add_scatter(x=list(range(2024, 2051)), y=propia, name="TU SENDA",
                        line=dict(color="#0b0b0b", width=3))
        fig.add_hline(y=60, line_dash="dot", line_color=GRIS,
                      annotation_text="60 % Maastricht")
        fig.update_layout(height=470, yaxis_title="deuda pública (% PIB)", margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Tu senda termina 2050 en {propia[-1]:.0f} % del PIB. Aritmética determinista "
                   "sin retroalimentaciones: mapa de sensibilidades, no pronóstico (docs/escenarios_d1.md).")
