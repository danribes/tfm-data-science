"""Capa GOLD (Entrega 3): dos paneles con tests.

1. gold_panel_anual  — país×año (UE~40): gasto por función y tipo, ingresos,
   deuda, outcomes, controles, migración, WWBI. Largo + vista ancha para ML.
2. gold_ccaa_trimestral — CCAA×trimestre: IPV (3 tipos), IPC, salario
   (anual→trimestral con flag), ratio de asequibilidad (base 2015=100).

Flags de outlier documentados: superbonus IT (GF06 2021-23), COVID 2020-22,
negativos por venta neta de activos.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from base import GOLD, PROCESSED

ISO3_TO_2 = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY", "CZE": "CZ",
    "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "EL",
    "HUN": "HU", "IRL": "IE", "ITA": "IT", "LVA": "LV", "LTU": "LT", "LUX": "LU",
    "MLT": "MT", "NLD": "NL", "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK",
    "SVN": "SI", "ESP": "ES", "SWE": "SE", "ISL": "IS", "NOR": "NO", "CHE": "CH",
    "GBR": "UK",
}


def p(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED / f"{name}.csv")


# ---------- panel anual UE ----------

def build_panel() -> pd.DataFrame:
    rows = []

    gov = p("gov_10a_exp").query("unit=='PC_GDP'")
    for cofog in ["TOTAL"] + [f"GF{i:02d}" for i in range(1, 11)] + ["GF0601", "GF1006"]:
        sub = gov.query("cofog==@cofog and na_item=='TE'")
        rows.append(sub.assign(variable=f"te_{cofog.lower()}")[["geo", "year", "variable", "value"]])
    for na, vn in [("D1", "wages"), ("P2", "goods"), ("D3", "subsidies"), ("D62", "benefits"),
                   ("D9", "captransf"), ("P51G", "gfcf")]:
        sub = gov.query("cofog=='TOTAL' and na_item==@na")
        rows.append(sub.assign(variable=vn)[["geo", "year", "variable", "value"]])

    rev = p("gov_revenue_deficit")
    for na, vn in [("TR", "revenue"), ("B9", "deficit"), ("D2REC", "tax_production"),
                   ("D5REC", "tax_income"), ("D61REC", "social_contrib")]:
        sub = rev.query("na_item==@na")
        rows.append(sub.rename(columns={"time": "year"}).assign(variable=vn)[["geo", "year", "variable", "value"]])

    simple = [
        ("gov_debt", "debt"), ("silc_overburden", "overburden"), ("silc_overcrowding", "overcrowding"),
        ("arop_post", "arop_post"), ("arop_pre_nopensions", "arop_pre_nopens"), ("gini", "gini"),
        ("gdp_pc_pps", "gdp_pc_pps"), ("population", "population"), ("life_expectancy_e0", "e0"),
        ("immigration", "immigration"), ("emigration", "emigration"),
        ("social_protection_exp", "socprot_exp"), ("recycling_rate", "recycling"),
        # cierre de huecos F2.0 (2026-07-18)
        ("unemployment_eu", "unemployment"), ("interest_paid", "interest"),
        ("pensions_oldage", "pensions_oldage"),
    ]
    for name, vn in simple:
        df = p(name)
        tcol = "time" if "time" in df.columns else "year"
        if name == "avoidable_mortality":
            continue
        rows.append(df.rename(columns={tcol: "year"}).assign(variable=vn)[["geo", "year", "variable", "value"]])

    mort = p("avoidable_mortality")
    for m, vn in [("TRT", "mort_treatable"), ("PRVT", "mort_preventable")]:
        sub = mort.query("mortalit==@m")
        rows.append(sub.rename(columns={"time": "year"}).assign(variable=vn)[["geo", "year", "variable", "value"]])

    ww = p("wwbi")
    ww["geo"] = ww["iso3"].map(ISO3_TO_2)
    ww = ww.dropna(subset=["geo"])
    wmap = {"BI.EMP.TOTL.PB.ZS": "pub_emp_share", "BI.WAG.TOTL.GD.ZS": "wagebill_gdp",
            "BI.WAG.TOTL.PB.ZS": "wagebill_exp", "BI.WAG.PREM.PB": "wage_premium"}
    for code, vn in wmap.items():
        sub = ww.query("indicator==@code")
        rows.append(sub.assign(variable=vn)[["geo", "year", "variable", "value"]])

    # fuentes iso3 en formato largo (variable ya nombrada): confusores GHO + WDI extras
    for name in ("gho_confounders", "wdi_extras"):
        df = p(name)
        df["geo"] = df["iso3"].map(ISO3_TO_2)
        rows.append(df.dropna(subset=["geo"])[["geo", "year", "variable", "value"]])

    # estructura de edad: share ≥65 desde demo_pjanbroad
    br = p("population_broad_age")
    piv = br.pivot_table(index=["geo", "time"], columns="age", values="value").reset_index()
    piv["pop65_share"] = piv["Y_GE65"] / (piv["Y_LT15"] + piv["Y15-64"] + piv["Y_GE65"]) * 100
    rows.append(piv.rename(columns={"time": "year"}).assign(variable="pop65_share")
                [["geo", "year", "variable", "pop65_share"]].rename(columns={"pop65_share": "value"}))

    panel = pd.concat(rows, ignore_index=True)
    panel["year"] = panel["year"].astype(int)
    panel = panel.dropna(subset=["value"])
    panel = panel[~panel.geo.isin(["EA19", "EA20", "EU27_2020", "EU28", "EA"])]

    # flags documentados
    panel["flag"] = ""
    m_sb = (panel.geo == "IT") & (panel.variable.isin(["te_gf06", "te_gf0601"])) & panel.year.between(2021, 2023)
    panel.loc[m_sb, "flag"] = "superbonus"
    panel.loc[panel.year.between(2020, 2022), "flag"] = panel.loc[panel.year.between(2020, 2022), "flag"].where(
        panel.loc[panel.year.between(2020, 2022), "flag"] != "", "covid")
    panel.loc[panel.value < 0, "flag"] = "neg_asset_sale"

    pk = ["geo", "year", "variable"]
    assert panel.duplicated(subset=pk).sum() == 0, "PK duplicada en panel"
    return panel


def build_panel_wide(panel: pd.DataFrame) -> pd.DataFrame:
    wide = panel.pivot_table(index=["geo", "year"], columns="variable", values="value").reset_index()
    # derivadas de composición (plan §2): capital vs corriente
    if {"captransf", "gfcf", "te_total"} <= set(wide.columns):
        wide["capital"] = wide["gfcf"].fillna(0) + wide["captransf"].fillna(0)
        wide["current"] = wide["te_total"] - wide["capital"]
        wide["capital_share"] = wide["capital"] / wide["te_total"]
    if {"immigration", "emigration", "population"} <= set(wide.columns):
        wide["net_migration_rate"] = (wide["immigration"] - wide["emigration"]) / wide["population"] * 1000
    return wide


# ---------- panel CCAA trimestral ----------

Q = {19: 1, 20: 2, 21: 3, 22: 4}


def build_ccaa() -> pd.DataFrame:
    ipv = p("ine_ipv_q")
    parts = ipv["nombre"].str.split(". ", n=2, expand=True)
    ipv["ccaa"], ipv["tipo"] = parts[0].str.strip(), parts[1].str.strip()
    ipv["quarter"] = ipv["periodo"].map(Q)
    ipv = ipv.dropna(subset=["quarter", "valor"])
    ipv_w = ipv.pivot_table(index=["ccaa", "anyo", "quarter"], columns="tipo", values="valor").reset_index()
    ipv_w = ipv_w.rename(columns={"General": "ipv", "Vivienda nueva": "ipv_nueva", "Vivienda segunda mano": "ipv_segunda"})

    ipc = p("ine_ipc")
    parts = ipc["nombre"].str.split(".", n=1, expand=True)
    ipc["ccaa"] = parts[0].str.strip()
    ipc["quarter"] = ((ipc["periodo"] - 1) // 3 + 1).astype(int)
    ipc_q = ipc.groupby(["ccaa", "anyo", "quarter"], as_index=False)["valor"].mean().rename(columns={"valor": "ipc"})

    sal = p("ine_salarios")
    sal = sal[sal["nombre"].str.contains("Ambos sexos") & sal["nombre"].str.contains("Media")]
    parts = sal["nombre"].str.split(".", n=2, expand=True)
    sal["ccaa"] = parts[1].str.strip().str.replace("Total Nacional", "Nacional")
    sal_a = sal.groupby(["ccaa", "anyo"], as_index=False)["valor"].mean().rename(columns={"valor": "salario_anual"})

    df = ipv_w.merge(ipc_q, on=["ccaa", "anyo", "quarter"], how="left")
    df["ccaa"] = df["ccaa"].str.replace("Total Nacional", "Nacional")
    df = df.merge(sal_a, on=["ccaa", "anyo"], how="left")
    df["salario_flag"] = np.where(df["salario_anual"].notna(), "observado", "faltante")
    # interpolación del salario al último año disponible (provisional)
    df = df.sort_values(["ccaa", "anyo", "quarter"])
    df["salario_anual"] = df.groupby("ccaa")["salario_anual"].ffill()
    df.loc[(df["salario_flag"] == "faltante") & df["salario_anual"].notna(), "salario_flag"] = "provisional_ffill"

    # ratio de asequibilidad, ambas series rebasadas a 2015=100
    base = df[df.anyo == 2015].groupby("ccaa")[["ipv", "salario_anual"]].mean().rename(
        columns={"ipv": "ipv_b", "salario_anual": "sal_b"})
    df = df.merge(base, on="ccaa", how="left")
    df["ipv_idx15"] = df["ipv"] / df["ipv_b"] * 100
    df["salario_idx15"] = df["salario_anual"] / df["sal_b"] * 100
    df["ratio_asequibilidad"] = df["ipv_idx15"] / df["salario_idx15"]

    pk = ["ccaa", "anyo", "quarter"]
    assert df.duplicated(subset=pk).sum() == 0, "PK duplicada en gold CCAA"
    return df


def smoke(panel: pd.DataFrame, wide: pd.DataFrame, ccaa: pd.DataFrame) -> None:
    es = wide.query("geo=='ES' and year==2023")
    assert len(es) == 1 and abs(float(es["te_gf06"].iloc[0]) - 0.5) < 0.2, "ancla ES GF06"
    assert 35 < float(es["revenue"].iloc[0]) < 48, f"ingresos ES 2023: {es['revenue'].iloc[0]}"
    n_ccaa = ccaa["ccaa"].nunique()
    assert n_ccaa >= 18, f"CCAA insuficientes: {n_ccaa}"
    r = ccaa.query("ccaa=='Nacional' and anyo==2024")["ratio_asequibilidad"].mean()
    assert 1.0 < r < 2.0, f"ratio asequibilidad nacional 2024 raro: {r}"
    print(f"SMOKE GOLD OK — panel {len(panel)} filas ({panel.geo.nunique()} geos, "
          f"{panel.variable.nunique()} vars), wide {wide.shape}, ccaa {len(ccaa)} filas ({n_ccaa} territorios); "
          f"ratio ES nacional 2024={r:.2f}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    GOLD.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    wide = build_panel_wide(panel)
    ccaa = build_ccaa()
    smoke(panel, wide, ccaa)
    panel.to_csv(GOLD / "gold_panel_anual.csv", index=False)
    wide.to_csv(GOLD / "gold_panel_wide.csv", index=False)
    ccaa.to_csv(GOLD / "gold_ccaa_trimestral.csv", index=False)
    print("→ storage/gold/: gold_panel_anual.csv, gold_panel_wide.csv, gold_ccaa_trimestral.csv")
