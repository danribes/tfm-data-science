"""Stress test del sistema: preguntas de usuario real contra los artefactos.

Cada pregunta se responde con lo que el sistema PUEDE calcular, se reframea si
es normativa (Bloque D: menú, no prescripción) y se declara el hueco si los
datos no existen. Los números impresos aquí alimentan docs/stress_test_qa.md.

    python3 analysis/stress_test.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from backtest_t1 import GOLD
from escenarios_d1 import BASE, presion_demografica, simula

PROCESSED = GOLD.parent / "processed"
ROOT = GOLD.parents[1]


def q1_deuda_mundial():
    print("\n" + "=" * 70)
    print("Q1 · Evolución de la deuda a un año vista, países del mundo (WEO)")
    w = pd.read_csv(PROCESSED / "weo_fiscal_totals.csv").query("variable=='debt'")
    piv = w.pivot_table(index="iso3", columns="year", values="value")
    d = (piv[2027] - piv[2026]).dropna().sort_values()
    print(f"países con proyección 2026→2027: {len(d)}; sube la deuda en "
          f"{(d > 0).sum()} ({(d > 0).mean():.0%}), baja en {(d < 0).sum()}")
    print("mayores subidas (pp de PIB):", d.tail(5).round(1).to_dict())
    print("mayores bajadas (pp de PIB):", d.head(5).round(1).to_dict())
    grandes = ["ESP", "USA", "FRA", "DEU", "ITA", "GBR", "JPN", "CHN"]
    print("grandes economías:", {g: round(float(d.get(g, np.nan)), 1) for g in grandes})
    print("NOTA: son las proyecciones del FMI (ancla C1-Modo 3 del plan) servidas")
    print("por el pipeline, no un modelo propio; la aritmética r−g propia existe solo")
    print("para España (calibrada con tipo efectivo e intereses observados).")


def q2_impuestos_10pct():
    print("\n" + "=" * 70)
    print("Q2 · '¿Qué gastos recortar para bajar al 10% de impuestos en 10 años?'")
    print("REFRAME (Bloque D): el sistema no elige recortes; cuantifica el tamaño")
    print("del cambio y da el menú COFOG — la elección es política.")
    p = pd.read_csv(GOLD / "gold_panel_anual.csv").query("geo=='ES' and year==2023")
    v = p.set_index("variable")["value"]
    print(f"ES 2023: ingresos {v['revenue']:.1f} %PIB, gasto {v['te_total']:.1f} %PIB")
    print(f"→ objetivo 10 %: recortar {v['te_total'] - 10:.1f} pp de PIB de gasto (un {1 - 10 / v['te_total']:.0%})")
    gf = {"GF10 protección social": v["te_gf10"], "GF07 sanidad": v["te_gf07"],
          "GF09 educación": v["te_gf09"], "GF01 servicios generales": v["te_gf01"],
          "GF04 asuntos económicos": v["te_gf04"], "GF03 orden público": v["te_gf03"],
          "GF02 defensa": v["te_gf02"], "resto (GF05/06/08)": v["te_gf05"] + v["te_gf06"] + v["te_gf08"]}
    print("menú COFOG (todo junto suma el gasto):", {k: round(x, 1) for k, x in gf.items()})
    print(f"suma de TODA la protección social + sanidad + educación: "
          f"{v['te_gf10'] + v['te_gf07'] + v['te_gf09']:.1f} pp — aún insuficiente")
    c = pd.read_csv(GOLD / "gold_century_fiscal.csv").query("variable=='exp_gdp'")
    med1900 = c[c.year.between(1900, 1910)].value.median()
    hoy = c[c.year == 2023].groupby("iso3").value.mean()
    print(f"contexto histórico (atlas B1): un Estado del 10 % ≈ la mediana mundial de "
          f"1900–1910 ({med1900:.1f} %PIB); hoy solo {(hoy <= 12).sum()} de "
          f"{hoy.notna().sum()} países gastan ≤12 %PIB")


def q3_suelo_vivienda():
    print("\n" + "=" * 70)
    print("Q3 · '¿Cuánta superficie hace falta para eliminar el déficit de vivienda en 10 años?'")
    pr = pd.read_csv(GOLD / "gold_projections.csv").query("geo=='ES' and variant=='BSL'")
    pop = pr.set_index("year")["population"]
    dpop = pop.loc[2035] - pop.loc[2025]
    TAM_HOGAR = 2.5          # supuesto declarado (INE ~2,5 personas/hogar)
    DEFICIT = 600_000        # supuesto EXTERNO declarado (orden del déficit BdE)
    REPO = 40_000            # reposición/deterioro anual, supuesto conservador
    hogares_nuevos = dpop / TAM_HOGAR
    total = DEFICIT + hogares_nuevos + REPO * 10
    anual = total / 10
    print(f"población ES BSL 2025→2035: {dpop / 1e6:+.2f} M → ~{hogares_nuevos / 1e3:.0f} mil hogares nuevos")
    print(f"viviendas necesarias en 10 años ≈ déficit {DEFICIT / 1e3:.0f}k + hogares "
          f"{hogares_nuevos / 1e3:.0f}k + reposición {REPO * 10 / 1e3:.0f}k = {total / 1e6:.2f} M "
          f"(~{anual / 1e3:.0f} mil/año)")
    M2_VIV, EDIF = 110, 0.9  # m² construidos/vivienda; m² suelo por m² edificado (declarados)
    ha_ano = anual * M2_VIV * EDIF / 10_000
    print(f"superficie: ~{anual * M2_VIV / 1e6:.1f} M m² edificados/año ≈ {ha_ano:,.0f} ha de "
          f"suelo/año ({ha_ano * 10 / 1e3:.1f} mil ha en la década)")
    lic = pd.read_csv(PROCESSED / "mitma_licencias_ccaa.csv")
    nac = lic.groupby("anyo").viv_nueva.sum()
    print(f"factibilidad histórica (licencias MITMA): hoy ~{nac.loc[2022]:,.0f} viviendas/año "
          f"licenciadas; pico 2006 = {nac.loc[2006]:,.0f} → el objetivo (~{anual / 1e3:.0f}k/año) "
          f"es {anual / nac.loc[2022]:.1f}x el ritmo actual y {anual / nac.loc[2006]:.0%} del pico")
    print("HUECO DECLARADO: el pipeline no tiene serie propia de déficit ni de suelo")
    print("finalista; déficit, tamaño de hogar, m²/vivienda y edificabilidad son supuestos")
    print("declarados — esto es aritmética de orden de magnitud, no un modelo.")


def q4_sanidad():
    print("\n" + "=" * 70)
    print("Q4 · Sanidad: '¿cuánta esperanza de vida compra +1 pp de PIB en gasto?'")
    r = pd.read_csv(GOLD / "gold_rendimiento_pais.csv")
    import numpy as np
    from sklearn.linear_model import LinearRegression
    X = pd.DataFrame({"gasto": r.gasto, "lg": np.log(r.gdp_pc)})
    m = LinearRegression().fit(X, r.e0)
    boots = []
    rng = np.random.default_rng(42)
    for _ in range(500):
        i = rng.integers(0, len(r), len(r))
        boots.append(LinearRegression().fit(X.iloc[i], r.e0.iloc[i]).coef_[0])
    lo, hi = np.percentile(boots, [5, 95])
    print(f"asociación condicional a la renta: +1 pp de gasto ↔ {m.coef_[0]:+.2f} años de e0 "
          f"(IC90 bootstrap [{lo:+.2f}, {hi:+.2f}])")
    print("LECTURA HONESTA (A1): la renta domina; la asociación del gasto es de segundo")
    print("orden y NO es causal (retardos mitigan, no resuelven). El sistema se niega a")
    print("prometer 'años por punto de PIB'.")


def q5_educacion():
    print("\n" + "=" * 70)
    print("Q5 · Educación: '¿rendimiento del gasto educativo?'")
    p = pd.read_csv(GOLD / "gold_panel_anual.csv")
    es = p.query("geo=='ES' and variable=='te_gf09'").set_index("year")["value"]
    med = p[p.variable == "te_gf09"].groupby("year")["value"].median()
    print(f"gasto ES en educación: {es.loc[2023]:.1f} %PIB (mediana panel {med.loc[2023]:.1f}); "
          f"1995: {es.loc[1995]:.1f}")
    print("HUECO DECLARADO: el pipeline no tiene outcomes educativos (PISA está en la")
    print("lista deferred con ruta). Un A1-educación sería la misma maquinaria con PISA")
    print("como outcome — trabajo futuro identificado, no improvisable hoy.")


def q6_infraestructuras():
    print("\n" + "=" * 70)
    print("Q6 · Infraestructuras: 'volver a la FBCF pública del 5 % — ¿qué cuesta en deuda?'")
    cero = lambda y: 0.0
    central = simula("central", 3.5, 1.3, cero)
    plan = simula("fbcf5", 3.5, 1.3, lambda y: -2.0 if y <= 2035 else 0.0)
    d0, d1 = central.query("year==2050").deuda.iloc[0], plan.query("year==2050").deuda.iloc[0]
    print(f"+2 pp de FBCF 2025–2035 a deuda: {d1:.0f} %PIB en 2050 vs {d0:.0f} central "
          f"(+{d1 - d0:.0f} pp)")
    print("Si el crecimiento respondiera (+0,3 pp permanentes, supuesto ilustrativo):")
    plan_g = simula("fbcf5_g", 3.5, 1.6, lambda y: -2.0 if y <= 2035 else 0.0)
    print(f"  → {plan_g.query('year==2050').deuda.iloc[0]:.0f} %PIB en 2050 — la apuesta es esa")
    print("El simulador NO modela la retroalimentación inversión→crecimiento (declarado):")
    print("muestra el coste bruto y deja la elasticidad como palanca explícita.")


def q7_empleados_publicos():
    print("\n" + "=" * 70)
    print("Q7 · '¿Y si se reduce un 10 % el empleo público?'")
    p = pd.read_csv(GOLD / "gold_panel_anual.csv").query("geo=='ES'")
    wages = p[p.variable == "wages"].query("year==2023").value.iloc[0]
    emp = p[p.variable == "pub_emp_share"].value.max()
    ahorro = wages * 0.10
    cero = lambda y: 0.0
    central = simula("central", 3.5, 1.3, cero)
    rec = simula("rec10", 3.5, 1.3, lambda y: ahorro if y >= 2026 else 0.0)
    d0, d1 = central.query("year==2050").deuda.iloc[0], rec.query("year==2050").deuda.iloc[0]
    print(f"masa salarial D1 ES 2023: {wages:.1f} %PIB; empleo público ≈ {emp:.1%} del empleo")
    print(f"−10 % de plantilla ≈ ahorro {ahorro:.1f} pp de PIB/año (si el salario medio no cambia)")
    print(f"en la senda de deuda: {d1:.0f} %PIB en 2050 vs {d0:.0f} central ({d1 - d0:+.0f} pp)")
    print(f"contexto: la presión demográfica añade +{presion_demografica().loc[2050]:.1f} pp/año en")
    print("2050 — el ahorro cubre menos de una quinta parte. NO modelado (declarado): efectos")
    print("sobre servicios, paro y demanda; ~350 mil empleos son economía real, no una celda.")


def q8_pensiones():
    print("\n" + "=" * 70)
    print("Q8 · Pensiones: '¿qué ajuste neutraliza el envejecimiento?'")
    dm = presion_demografica()
    print(f"presión pensiones+sanidad (motor, BSL): +{dm.loc[2035]:.1f} pp en 2035, "
          f"+{dm.loc[2050]:.1f} pp en 2050")
    pars = json.load(open(ROOT / "api" / "models" / "projection_params.json"))
    b, se = pars["pensions"]["beta"][0], pars["pensions"]["se_cluster"][0]
    print(f"elasticidad al 65+: {b:.2f} ± {se:.2f} (SE agrupado) — para neutralizarla sin")
    print("recortar habría que compensar con crecimiento del PIB, empleo o migración")
    print("(la variante HMIGR de la banda D1 es exactamente ese experimento).")


if __name__ == "__main__":
    q1_deuda_mundial()
    q2_impuestos_10pct()
    q3_suelo_vivienda()
    q4_sanidad()
    q5_educacion()
    q6_infraestructuras()
    q7_empleados_publicos()
    q8_pensiones()
