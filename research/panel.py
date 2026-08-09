"""Estimation panels assembled from the frozen gold slice.

Nothing here fetches. Every panel is built from `data/gold/`, so an estimate is
reproducible from the same vintage the engine runs on — a result that could not
be recomputed from the committed data would be worth very little to a reviewer.

What the vintage can and cannot support is stated in `IDENTIFIABLE` below. That
list is not an apology: knowing which of the engine's constants the data can
actually speak to, and why the others cannot be identified, is part of the
result.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"

#: Constants the frozen panels can speak to, and the ones they cannot.
#: The blockers are econometric, not clerical — writing them down stops the
#: next person re-attempting an estimate the data cannot deliver.
IDENTIFIABLE: dict[str, str] = {
    "IPV_LR": "sí — crecimiento medio del IPV en el panel CCAA (20 regiones × 77 trimestres)",
    "IPV_REV": "sí — reversión del IPV a su tendencia, AR(1) sobre la desviación",
    "PB_PERSIST": "sí — persistencia del saldo primario en el panel de 18 países (1960+)",
    "E_IPV_R": ("no — el Euríbor es nacional y el panel es regional: sin variación "
                "transversal en el tipo, el efecto no se separa del efecto temporal común"),
    "OKUN": "no — el vintage no trae paro regional ni brecha del producto",
    "KAPPA": "no — no hay serie de expectativas de inflación en el corte congelado",
    "MULT": ("no — haría falta un shock fiscal identificado (narrativo o instrumental); "
             "exp_gdp y rev_gdp son endógenos al ciclo"),
    "E_R": "no — sin serie de PIB por país en el corte, sólo gasto e ingreso",
}


@dataclass(frozen=True)
class Panel:
    """A tidy balanced-ish panel: rows of (unit, time, **values)."""
    name: str
    unit_key: str
    time_key: str
    rows: list[dict]

    @property
    def units(self) -> list[str]:
        return sorted({r[self.unit_key] for r in self.rows})

    def column(self, key: str) -> list[float]:
        return [r[key] for r in self.rows if r.get(key) is not None]

    def __len__(self) -> int:
        return len(self.rows)

    def describe(self) -> str:
        times = sorted({r[self.time_key] for r in self.rows})
        return (f"{self.name}: {len(self.units)} unidades × {len(times)} periodos "
                f"= {len(self.rows)} obs ({times[0]}–{times[-1]})")


def _f(value: str) -> float | None:
    """Parse a gold cell; blanks and NA become None rather than 0.0."""
    v = (value or "").strip()
    if v in ("", "NA", "nan", "None"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def housing_panel() -> Panel:
    """CCAA quarterly house prices, CPI and wages — the best-powered panel here.

    `t` is a running quarter index so lags are well defined across year ends.
    Rows without a house-price observation are dropped: they cannot contribute
    to any estimate and keeping them would silently bias the lag structure.
    """
    rows: list[dict] = []
    with open(GOLD / "gold_ccaa_trimestral.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ipv = _f(r["ipv"])
            if ipv is None:
                continue
            year, q = int(r["anyo"]), int(r["quarter"])
            rows.append({
                "ccaa": r["ccaa"],
                "t": year * 4 + (q - 1),
                "year": year,
                "quarter": q,
                "ipv": ipv,
                "ipc": _f(r["ipc"]),
                "salario": _f(r.get("salario_anual", "")),
                "asequibilidad": _f(r.get("ratio_asequibilidad", "")),
            })
    rows.sort(key=lambda r: (r["ccaa"], r["t"]))
    return Panel("vivienda CCAA", "ccaa", "t", rows)


def fiscal_panel(since: int = 1960) -> Panel:
    """Cross-country public spending and revenue as % of GDP.

    The series runs to 1700, but pre-modern fiscal states are a different
    object entirely; the default window starts at 1960 and the cut is explicit
    rather than buried in a filter.
    """
    rows: list[dict] = []
    with open(GOLD / "gold_fiscal_historico.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            year = int(r["year"])
            if year < since:
                continue
            exp, rev = _f(r["exp_gdp"]), _f(r["rev_gdp"])
            if exp is None or rev is None:
                continue
            rows.append({
                "iso3": r["iso3"],
                "t": year,
                "year": year,
                "exp_gdp": exp,
                "rev_gdp": rev,
                # Revenue minus spending: a primary-balance proxy. It is not the
                # primary balance — interest is not netted out of exp_gdp — and
                # the naming keeps that visible.
                "balance_proxy": rev - exp,
            })
    rows.sort(key=lambda r: (r["iso3"], r["t"]))
    return Panel("fiscal 18 países", "iso3", "t", rows)


def yoy(panel: Panel, key: str, periods: int) -> Panel:
    """Add `{key}_yoy` as the percentage change over `periods`, within unit."""
    by_unit: dict[str, list[dict]] = {}
    for r in panel.rows:
        by_unit.setdefault(r[panel.unit_key], []).append(r)

    out: list[dict] = []
    for unit_rows in by_unit.values():
        by_t = {r[panel.time_key]: r for r in unit_rows}
        for r in unit_rows:
            prev = by_t.get(r[panel.time_key] - periods)
            new = dict(r)
            if prev and prev.get(key) and r.get(key) is not None:
                new[f"{key}_yoy"] = (r[key] / prev[key] - 1.0) * 100.0
            else:
                new[f"{key}_yoy"] = None
            out.append(new)
    out.sort(key=lambda r: (r[panel.unit_key], r[panel.time_key]))
    return Panel(panel.name, panel.unit_key, panel.time_key, out)
