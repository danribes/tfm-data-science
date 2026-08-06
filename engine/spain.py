"""Spain semi-structural engine — faithful Python port of v16 `run(L)`
(docs/superpowers/plans/references/v16-engine-extract.md S1, L95-175).

Deviation semantics: the baseline freezes the vintage (gold central scenario +
V0 KPIs); the engine computes deviations from it. The baseline is NOT a
prediction. Debt identity: b_t = b_{t-1}(1+i)/(1+g) − sp, anchored to
gold_escenarios_deuda.csv (central). Variable names mirror the JS on purpose.
"""
from __future__ import annotations

from engine import constants as c
from engine.levers import Levers

Y0 = 2026
Y1 = 2050
N_YEARS = Y1 - Y0 + 1          # 25
YEARS = list(range(Y0, Y1 + 1))

# v16 R keys, in template order (extract L97-100)
SERIES_KEYS = [
    "lvl", "u", "pi", "g", "gnom", "wnom", "wreal", "wrealIdx", "b", "ief",
    "int", "pb", "saldo", "ipv", "precio", "cuota", "salmes", "salario", "esf",
    "pens", "dep", "arop", "edu", "d1", "nomreal", "p2", "d3", "p51", "gtot",
    "bls", "temp", "ujuv", "auton", "hip", "sobre", "bono", "spread", "r",
    "deficitAbs", "vida",
]


def french(principal: float, annual_rate_pct: float, n_months: int) -> float:
    """French amortization monthly payment (extract L93)."""
    i = annual_rate_pct / 1200.0
    return principal * i / (1 - (1 + i) ** (-n_months))


def run_scenario(levers: Levers) -> dict[str, list[float]]:
    L, B, V0 = levers, c.BASE_LEVERS, c.V0
    central, olddep = c.load_central(), c.load_olddep()
    R: dict[str, list[float]] = {k: [] for k in SERIES_KEYS}

    bono = L.r + c.TERM + L.prima / 100
    shock = (-(L.sp - B["sp"]) - c.E_R * (L.r - B["r"])
             + c.E_EXT * (L.ext - B["ext"]) - c.E_PM * (L.pm - B["pm"]))
    u_star_dev = c.A_Z * L.z + c.A_TAU * L.tau - c.A_LAM * (L.lam - B["lam"])

    lvl = 0.0; pi_dev = 0.0; di = 0.0
    b = central[Y0 - 1]["deuda"]                      # 105.6 (2025)
    sal_idx = 1.0; wr_idx = 1.0; pens_fac = 1.0; nom_idx = 1.0
    precio = V0["precio"]

    for k in range(N_YEARS):
        y = Y0 + k
        gc = central[y]
        prev = lvl
        lvl = c.RHO * lvl + (1 - c.RHO) * c.MULT * shock       # GDP level deviation (%)
        gap_u = c.OKUN * lvl                                    # slack: u below u*
        u = V0["u"] + u_star_dev - gap_u
        pi_dev = (c.THETA * pi_dev + c.KAPPA * gap_u
                  + c.GAMMA * (L.pm - B["pm"]) * c.PM_DECAY ** k)
        pi = V0["pi"] + pi_dev
        g = V0["g"] + (lvl - prev) + (L.lam - B["lam"])
        gnom = gc["g_nominal"] + (g - V0["g"]) + pi_dev

        # debt identity b_t = b_{t-1}(1+i)/(1+g) − sp, with 14 %/yr refinancing
        di = di + c.REFI * ((bono - V0["bono"]) - di)
        ief = gc["r_efectivo"] + di
        pb = gc["pb"] + L.sp - gc["presion_demog"] * L.dem
        b_prev = b
        b = b_prev * (1 + ief / 100) / (1 + gnom / 100) - pb
        intr = b_prev * ief / 100
        saldo = pb - intr

        # wage setting (WS)
        wnom = pi + L.lam + c.PHI * gap_u
        wreal = wnom - pi
        if k > 0:
            sal_idx *= 1 + wnom / 100
            wr_idx *= 1 + wreal / 100

        # housing
        ipv = (c.IPV_LR + (V0["ipv"] - c.IPV_LR) * c.IPV_REV ** k
               - c.E_IPV_R * (L.r - B["r"]) + c.E_IPV_G * (g - V0["g"]))
        if k > 0:
            precio *= 1 + ipv / 100
        cuota = french(precio * 0.8, L.r + c.DIFF, 300)
        salmes = V0["salmes"] * sal_idx
        esf = cuota / salmes * 100

        # pensions: mechanical identity pension x number / GDP
        if k > 0:
            pens_fac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100)
            nom_idx *= 1 + L.idx / 100
        dep_idx = 1 + (olddep[y] / olddep[Y0] - 1) * (1 + L.dem)
        dep = olddep[Y0] * dep_idx
        pens = V0["pens"] * dep_idx * pens_fac

        R["lvl"].append(lvl); R["u"].append(u); R["pi"].append(pi); R["g"].append(g)
        R["gnom"].append(gnom); R["wnom"].append(wnom); R["wreal"].append(wreal)
        R["wrealIdx"].append(wr_idx * 100); R["b"].append(b); R["ief"].append(ief)
        R["int"].append(intr); R["pb"].append(pb); R["saldo"].append(saldo)
        R["deficitAbs"].append(abs(min(0.0, saldo)))
        R["ipv"].append(ipv); R["precio"].append(precio); R["cuota"].append(cuota)
        R["salmes"].append(salmes); R["salario"].append(V0["salario"] * sal_idx)
        R["esf"].append(esf); R["pens"].append(pens); R["dep"].append(dep)
        R["nomreal"].append(nom_idx * 100)
        R["arop"].append(V0["arop"] + 0.55 * (u - V0["u"]) + 0.90 * L.sp)
        R["edu"].append(V0["edu"] - 0.090 * L.sp)
        R["d1"].append(V0["d1"] - 0.240 * L.sp)
        R["p2"].append(V0["p2"] - 0.125 * L.sp)
        R["d3"].append(V0["d3"] - 0.031 * L.sp)
        R["p51"].append(V0["p51"] - 0.145 * L.sp)
        R["gtot"].append(V0["gtot"] - 1.0 * L.sp)
        R["bls"].append(V0["bls"] + 12 * (L.r - B["r"]) + 2.5 * (u - V0["u"]))
        R["temp"].append(V0["temp"] + 0.25 * (u - V0["u"]) - 1.5 * L.z)
        R["ujuv"].append(c.RJUV * u)
        R["auton"].append(V0["auton"] + 0.12 * (u - V0["u"]) - 0.40 * (g - V0["g"]))
        R["hip"].append(max(0.0, V0["hip"] * (1 - 1.6 * (esf / (V0["cuota"] / V0["salmes"] * 100) - 1))))
        R["sobre"].append(V0["sobre"] + 0.18 * (esf - V0["cuota"] / V0["salmes"] * 100))
        R["bono"].append(bono); R["spread"].append(L.prima); R["r"].append(L.r)
        R["vida"].append(V0["vida"])
    return R


def baseline() -> dict[str, list[float]]:
    """The frozen-vintage baseline: all levers at base (cheap: 25 iterations)."""
    return run_scenario(Levers())


# --------------------------------------------------------------------------
# The 12 v15/v16 personas — static config verbatim from the v16 `const P`
# array (extract S2, L516-841). Spanish copy is NOT translated. reds from
# extract S7.1 (L1613-1648). `series_keys` = the persona's historical chart
# series in kpis_perfiles.json; `extra` = engine keys its narrative reads
# beyond the five outs.
PERSONAS: list[dict] = [
    {"id": "01", "pill": "💼 Bonista", "foot": "💼 bonista",
     "h1": "💼 Inversor en bonos: ¿me pagarán los 10 años?",
     "meta": "ecb_bono10y_es.csv · ecb_bono10y_de.csv · eurostat_gov_debt_es.csv · eurostat_gov_deficit_es.csv · interest_paid.csv · gold_escenarios_deuda.csv",
     "hot": ["r", "prima", "sp", "dem"], "series_keys": ["bono10y_es_5a"],
     "outs": [{"k": "bono", "lab": "Bono 10A España"}, {"k": "spread", "lab": "Spread ES–DE"},
              {"k": "b", "lab": "Deuda pública"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "int", "lab": "Intereses / PIB"}],
     "headline": "b", "extra": [],
     "reds": [
         {"t": "Deuda > 105 %PIB", "thr": 105.0, "k": "b", "cmp": "gt", "d": 1, "x": "narrativa crack23 [comentario]"},
         {"t": "Deuda > 120 %PIB", "thr": 120.0, "k": "b", "cmp": "gt", "d": 1, "x": "techo COVID 2020: 119,3 [hist]"},
         {"t": "Bono 10A > 7 %", "thr": 7.0, "k": "bono", "cmp": "gt", "d": 2, "x": "zona rescate: crisis 2012 [hist]"}]},
    {"id": "02", "pill": "🏦 Banca", "foot": "🏦 banca hipotecaria",
     "h1": "🏦 Banco hipotecario: ¿a quién presto, a qué tipo y con qué mora esperada?",
     "meta": "ecb_euribor12m.csv · bls_criterios_vivienda.csv · ine_hipotecas_ccaa.csv · eurostat_hpi_q_es.csv · gold_cuota_teorica.csv",
     "hot": ["r", "z", "tau", "ext"], "series_keys": ["euribor12m_5a"],
     "outs": [{"k": "r", "lab": "Euríbor 12m"}, {"k": "bls", "lab": "BLS endurecimiento"},
              {"k": "hip", "lab": "Nueva producción"}, {"k": "ipv", "lab": "Precio vivienda a/a"},
              {"k": "cuota", "lab": "Cuota mediana"}],
     "headline": "cuota", "extra": ["u", "esf"],
     "reds": [
         {"t": "IPV real a/a > 10 %", "thr": 10.0, "k": "ipvreal", "cmp": "gt", "d": 1, "x": "burbuja 2004-07 [hist] · IPV nominal − IPCA"},
         {"t": "BLS endurecimiento > 20 %", "thr": 20.0, "k": "bls", "cmp": "gt", "d": 0, "x": "nivel de contracción de crédito [hist]"},
         {"t": "Paro > 15 % (motor de mora)", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "último nivel visto en 2021-07 (15,2) [hist]"}]},
    {"id": "03", "pill": "🔑 Comprador", "foot": "🔑 comprador de vivienda",
     "h1": "🔑 Comprador de vivienda: ¿qué esfuerzo me exige el techo?",
     "meta": "gold_cuota_teorica.csv · ine_salarios.csv (EAES) · ecb_euribor12m.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv",
     "hot": ["r", "lam", "z", "pm"], "series_keys": ["vivienda_precio_yoy_5a"],
     "outs": [{"k": "precio", "lab": "Precio mediano CCAA"}, {"k": "cuota", "lab": "Cuota mediana"},
              {"k": "esf", "lab": "Esfuerzo cuota/renta"}, {"k": "ipv", "lab": "Precio vivienda a/a"},
              {"k": "sobre", "lab": "Sobrecarga vivienda"}],
     "headline": "esf", "extra": [],
     "reds": [
         {"t": "Esfuerzo cuota/renta > 35 %", "thr": 35.0, "k": "esf", "cmp": "gt", "d": 1, "x": "regla prudencial [regla]"},
         {"t": "Sobrecarga > 40 % renta", "thr": 15.0, "k": "sobre", "cmp": "gt", "d": 1, "x": "definición Eurostat · muerde al flujo nuevo [UE]"},
         {"t": "IPV a/a > 10 %", "thr": 10.0, "k": "ipv", "cmp": "gt", "d": 1, "x": "burbuja 2004-07 [hist]"}]},
    {"id": "04", "pill": "🚀 Emprendedor", "foot": "🚀 emprendedor",
     "h1": "🚀 ¿Aguanta el ciclo lo que tarda mi empresa en nacer?",
     "meta": "eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv · wb_self_employment.csv",
     "hot": ["r", "ext", "pm", "sp"], "series_keys": ["pib_yoy_5a"],
     "outs": [{"k": "g", "lab": "Ciclo · PIB real"}, {"k": "u", "lab": "Paro · talento"},
              {"k": "pi", "lab": "IPCA · coste inputs"}, {"k": "r", "lab": "Euríbor · financiación"},
              {"k": "auton", "lab": "Autoempleo"}],
     "headline": "g", "extra": ["lvl"],
     "reds": [
         {"t": "PIB a/a < 0 %", "thr": 0.0, "k": "g", "cmp": "lt", "d": 1, "x": "recesión técnica [regla]"},
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "episodio 2022: pico 10,7 % (jul-2022) [hist]"},
         {"t": "Euríbor 12m > 4 %", "thr": 4.0, "k": "r", "cmp": "gt", "d": 2, "x": "techo del ciclo de subidas 2023 [hist]"}]},
    {"id": "05", "pill": "🏛️ Funcionario", "foot": "🏛️ funcionario",
     "h1": "🏛️ ¿Mi nómina real sobrevive al ajuste que viene?",
     "meta": "gov_10a_exp.csv · eurostat_gov_deficit_es.csv · eurostat_gov_debt_es.csv · eurostat_hicp_manr_es.csv",
     "hot": ["sp", "idx", "pm", "dem"], "series_keys": ["deficit_pib_hist"],
     "outs": [{"k": "d1", "lab": "Masa salarial D1"}, {"k": "nomreal", "lab": "Poder de compra nómina"},
              {"k": "pi", "lab": "IPCA · erosión"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "gtot", "lab": "Gasto total AAPP"}],
     "headline": "nomreal", "extra": [],
     "reds": [
         {"t": "Déficit > 3 % PIB", "thr": -3.0, "k": "saldo", "cmp": "lt", "d": 1, "x": "procedimiento de déficit excesivo [regla UE]"},
         {"t": "Deuda > 105 % PIB", "thr": 105.0, "k": "b", "cmp": "gt", "d": 1, "x": "umbral narrativo, no legal [comentario]"},
         {"t": "Poder de compra < 100", "thr": 100.0, "k": "nomreal", "cmp": "lt", "d": 1, "x": "congelaciones y recortes 2010-15 [hist]"}]},
    {"id": "06", "pill": "🗳️ Político", "foot": "🗳️ político (decisor honesto)",
     "h1": "🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?",
     "meta": "eurostat_gov_debt_es · eurostat_gov_deficit_es · eurostat_une_rt_m_es · eurostat_gdp_q_es · interest_paid · gold_escenarios_deuda",
     "hot": ["sp", "r", "tau", "z", "lam", "dem"], "series_keys": ["deficit_pib_hist"],
     "outs": [{"k": "b", "lab": "Deuda pública"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "u", "lab": "Paro total"}, {"k": "g", "lab": "PIB real"},
              {"k": "int", "lab": "Intereses"}],
     "headline": "b", "extra": [],
     "reds": [
         {"t": "Deuda > 120 % PIB", "thr": 120.0, "k": "b", "cmp": "gt", "d": 1, "x": "techo COVID 2020: 119,3 [hist]"},
         {"t": "Déficit > 3 % PIB", "thr": -3.0, "k": "saldo", "cmp": "lt", "d": 1, "x": "regla fiscal UE [regla UE]"},
         {"t": "Paro > 15 %", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "coste social del ajuste [hist]"}]},
    {"id": "07", "pill": "🕳️ Corrupto", "foot": "🕳️ político corrupto · sátira de transparencia",
     "h1": "🕳️ ¿Dónde no mira nadie? — las partidas con más discrecionalidad, señaladas para quien SÍ mira",
     "meta": "gov_10a_exp.csv (P2 · D3 · P51G) · interest_paid.csv",
     "hot": ["sp", "dem"], "series_keys": ["inversion_publica_pib_hist"],
     "outs": [{"k": "p2", "lab": "Consumo intermedio P2"}, {"k": "d3", "lab": "Subvenciones D3"},
              {"k": "p51", "lab": "Inversión pública P51G"}, {"k": "gtot", "lab": "Gasto total"},
              {"k": "int", "lab": "Intereses D41"}],
     "headline": "p51", "extra": [],
     "reds": [
         {"t": "Contratos menores · adjudicación", "thr": None, "k": None, "cmp": None, "d": None, "x": "la señal vive a nivel de contrato — sin serie pública [hueco de datos]"},
         {"t": "WGI control de la corrupción", "thr": None, "k": None, "cmp": None, "d": None, "x": "API archivada: descarga manual en govindicators.org [hueco de datos]"},
         {"t": "Inversión pública < 2 % PIB", "thr": 2.0, "k": "p51", "cmp": "lt", "d": 2, "x": "cruzada en 2016-17 (2,0): obra parada = renegociación [hist]"}]},
    {"id": "08", "pill": "🧒 Infancia", "foot": "🧒 infancia",
     "h1": "🧒 ¿Qué país hereda quien hoy tiene 8 años?",
     "meta": "eurostat_arop_child_es · eurostat_gov_edu_es · eurostat_gov_debt_es · gold_projections · gold_escenarios_deuda",
     "hot": ["sp", "dem", "z", "lam"], "series_keys": ["arop_infantil_hist"],
     "outs": [{"k": "arop", "lab": "AROP infantil (<16)"}, {"k": "edu", "lab": "Gasto en educación"},
              {"k": "b", "lab": "Deuda heredada"}, {"k": "dep", "lab": "Dependencia 65+"},
              {"k": "vida", "lab": "Esperanza de vida"}],
     "headline": "b", "extra": ["int"],
     "reds": [
         {"t": "AROP infantil > 25 %", "thr": 25.0, "k": "arop", "cmp": "gt", "d": 1, "x": "peor cuartil UE — cruzada de forma persistente [UE]"},
         {"t": "Educación < 4,8 % PIB (UE27)", "thr": 4.8, "k": "edu", "cmp": "lt", "d": 2, "x": "0,7 pp por debajo de la media UE27 [UE]"},
         {"t": "Dependencia > 50/100", "thr": 50.0, "k": "dep", "cmp": "gt", "d": 1, "x": "sin precedente histórico [hist inédito]"}]},
    {"id": "09", "pill": "🌅 Jubilado", "foot": "🌅 jubilado",
     "h1": "🌅 ¿Mi pensión sigue al IPC — y quién la paga en 2035?",
     "meta": "eurostat_pensions_pcgdp_es.csv · eurostat_hicp_manr_es.csv · gold_projections.csv · life_expectancy_e0.csv",
     "hot": ["idx", "dem", "pm", "sp"], "series_keys": ["hicp_es_5a"],
     "outs": [{"k": "pens", "lab": "Gasto en pensiones"}, {"k": "nomreal", "lab": "Poder de compra"},
              {"k": "pi", "lab": "IPCA · la referencia"}, {"k": "dep", "lab": "Dependencia 65+"},
              {"k": "vida", "lab": "Esperanza de vida"}],
     "headline": "pens", "extra": [],
     "reds": [
         {"t": "Gasto pensiones > 15 % PIB", "thr": 15.0, "k": "pens", "cmp": "gt", "d": 2, "x": "nunca alcanzado en la serie [hist inédito]"},
         {"t": "Dependencia 65+ > 50/100", "thr": 50.0, "k": "dep", "cmp": "gt", "d": 1, "x": "se cruza entre 2035 y 2050 [hist inédito]"},
         {"t": "Poder de compra < 100", "thr": 100.0, "k": "nomreal", "cmp": "lt", "d": 1, "x": "la palanca ι es la que decide, no el IPC [regla]"}]},
    {"id": "10", "pill": "🎓 Joven", "foot": "🎓 joven que entra al mercado laboral",
     "h1": "🎓 ¿Primer contrato o cola del paro — y podré irme de casa?",
     "meta": "eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv · ine_salarios.csv",
     "hot": ["z", "tau", "ext", "r", "sp"], "series_keys": ["paro_juvenil_5a", "paro_total_5a"],
     "outs": [{"k": "ujuv", "lab": "Paro juvenil <25"}, {"k": "temp", "lab": "Temporalidad"},
              {"k": "ipv", "lab": "Precio vivienda a/a"}, {"k": "sobre", "lab": "Sobrecarga vivienda"},
              {"k": "salario", "lab": "Salario medio"}],
     "headline": "ujuv", "extra": ["u"],
     "reds": [
         {"t": "Paro juvenil > 40 %", "thr": 40.0, "k": "ujuv", "cmp": "gt", "d": 1, "x": "cota del ciclo anterior; 2013 la superó [hist]"},
         {"t": "Temporalidad > 25 %", "thr": 25.0, "k": "temp", "cmp": "gt", "d": 1, "x": "la serie vivió sobre ese nivel hasta 2022-Q1 [hist]"},
         {"t": "IPV > +10 % a/a", "thr": 10.0, "k": "ipv", "cmp": "gt", "d": 1, "x": "cinco trimestres seguidos >10 % en la serie [hist]"}]},
    {"id": "11", "pill": "📋 Indefinido", "foot": "📋 trabajador indefinido",
     "h1": "📋 ¿Crece mi salario por encima del IPC?",
     "meta": "ine_salarios.csv · eurostat_hicp_manr_es.csv · eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_gdp_q_es.csv",
     "hot": ["lam", "z", "pm", "tau"], "series_keys": ["hicp_es_5a"],
     "outs": [{"k": "wrealIdx", "lab": "Salario real acumulado"}, {"k": "salario", "lab": "Salario medio"},
              {"k": "pi", "lab": "IPCA · el listón"}, {"k": "u", "lab": "Paro total"},
              {"k": "temp", "lab": "Temporalidad"}],
     "headline": "wrealIdx", "extra": [],
     "reds": [
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "cruzado en 2022-23: el salario real cayó [hist]"},
         {"t": "Paro > 15 %", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "por encima, el poder de negociación se hunde [hist]"},
         {"t": "Salario real < 100", "thr": 100.0, "k": "wrealIdx", "cmp": "lt", "d": 1, "x": "pérdida acumulada desde 2026 [aritmética]"}]},
    {"id": "12", "pill": "🧾 Autónomo", "foot": "🧾 autónomo",
     "h1": "🧾 ¿Caja, cuota y ciclo — en qué orden me golpean?",
     "meta": "wb_self_employment.csv · eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv",
     "hot": ["r", "pm", "ext", "sp"], "series_keys": ["autoempleo_hist"],
     "outs": [{"k": "auton", "lab": "Autoempleo"}, {"k": "g", "lab": "Ciclo · demanda"},
              {"k": "pi", "lab": "IPCA · coste inputs"}, {"k": "r", "lab": "Euríbor · póliza"},
              {"k": "u", "lab": "Paro · repliegue"}],
     "headline": "g", "extra": [],
     "reds": [
         {"t": "PIB a/a < 0 %", "thr": 0.0, "k": "g", "cmp": "lt", "d": 1, "x": "recesión técnica [regla]"},
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "episodio 2022: pico 10,7 % [hist]"},
         {"t": "Euríbor 12m > 4 %", "thr": 4.0, "k": "r", "cmp": "gt", "d": 2, "x": "techo del ciclo de subidas 2023 [hist]"}]},
]

PERSONA_IDS = [p["id"] for p in PERSONAS]


def persona_dependents(scenario: dict[str, list[float]]) -> dict[str, dict]:
    """Per-persona headline series (spec §4.1): dict keyed by the 12 persona ids."""
    out: dict[str, dict] = {}
    for p in PERSONAS:
        keys = [o["k"] for o in p["outs"]] + [p["headline"]] + p["extra"]
        seen: list[str] = []
        for k in keys:
            if k not in seen:
                seen.append(k)
        out[p["id"]] = {"pill": p["pill"], "headline": p["headline"],
                        "series": {k: scenario[k] for k in seen}}
    return out
