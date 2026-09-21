"""Incertidumbre paramétrica de la cadena de vivienda.

`RESULTS.md` dice de las bandas Monte Carlo: «No incluye toda la incertidumbre
paramétrica ni cambios estructurales». Este módulo cierra la primera mitad de
esa frase donde de verdad se puede cerrar.

El abanico de deuda simula la identidad contable con choques AR(1) sobre tipos,
crecimiento y saldo primario. Ninguna de sus constantes está estimada: son
calibraciones, y sus bandas no pueden llevar incertidumbre paramétrica sin
cambiar antes el modelo de deuda. La cadena de vivienda sí: `IPV_LR` e
`IPV_REV` son los dos únicos parámetros del motor que vienen de una estimación,
y traen error típico e intervalo del panel de 19 unidades.

Así que aquí la proyección de precio deja de tratar dos números estimados como
si se conocieran exactamente. La banda que sale no es un intervalo predictivo
—no hay cobertura empírica demostrada, y la muestra y el modelo siguen
limitando lo que puede afirmarse— sino la respuesta a una pregunta concreta y
contestable: *dado lo que el panel deja fijado sobre estos dos parámetros,
¿cuánto se mueve la proyección?*

Dos decisiones que conviene no perder:

  · Los parámetros se sortean **una vez por trayectoria**, no un valor nuevo
    cada año. Un parámetro es una incógnita fija, no un choque: si se
    resortease en cada periodo se promediaría solo y la banda saldría
    artificialmente estrecha.

  · `IPV_REV` es una fracción que revierte por año y vive en (0, 1). Se trunca
    por rechazo, no recortando al borde: recortar amontona masa en 0 y 1 y
    deforma justo las colas que interesan.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine import constants as c
from engine.levers import Levers
from engine.spain import Y0, run_scenario

#: Los dos parámetros del motor que salen de una estimación, con su error
#: típico. Cualquier otro es calibración y no tiene distribución que sortear.
ESTIMATED = ("IPV_LR", "IPV_REV")

PCT_LEVELS = (5, 25, 50, 75, 95)

#: Los mismos 4.000 sorteos que el abanico de deuda, y por la misma razón: con
#: menos, la anchura de la banda todavía se mueve entre semillas. Medido sobre
#: 30 semillas, la desviación típica del ancho p5–p95 en 2050 baja del 2,83 %
#: con 1.000 sorteos al 1,56 % con 4.000 —el 1/√n que toca—, y la corrida
#: entera cuesta menos de un segundo. Conviene medir esa dispersión con la
#: desviación típica sobre muchas semillas: el rango entre unas pocas es él
#: mismo tan ruidoso que llega a subir cuando n sube.
N_DRAWS_DEFAULT = 4000
SEED_DEFAULT = 42


@dataclass(frozen=True)
class ParametricBand:
    series: str
    years: list[int]
    point: list[float]                      # la proyección con los valores puntuales
    percentiles: dict[str, list[float]]
    n_draws: int
    seed: int
    #: Lo que el panel deja fijado, para poder citarlo junto a la banda.
    params: dict[str, dict[str, float]]

    def width(self, year: int) -> float:
        """Anchura p5–p95 en un año, en las unidades de la serie."""
        i = self.years.index(year)
        return self.percentiles["p95"][i] - self.percentiles["p5"][i]


def _spec(name: str) -> dict[str, float]:
    row = c.load_estimated().get(name)
    if not row:
        raise KeyError(f"{name} no está en data/gold/estimated_params.json")
    return {"value": float(row["value"]), "se": float(row["se"]),
            "ci_low": float(row["ci_low"]), "ci_high": float(row["ci_high"]),
            # n son observaciones y n_units las unidades del panel: 1.387
            # trimestres repartidos entre 19 comunidades no es «un panel de
            # 1.387 unidades», y la ficha llegó a decirlo.
            "n": int(row["n"]), "n_units": int(row["n_units"])}


def _draw(rng: np.random.Generator, spec: dict[str, float], n: int,
          low: float | None = None, high: float | None = None) -> np.ndarray:
    """Normal(valor, se), truncada por rechazo cuando el parámetro tiene dominio.

    El rechazo mantiene la forma de la normal dentro del dominio. Recortar al
    borde apilaría masa en los extremos, que es exactamente donde se lee la
    banda.
    """
    out = rng.normal(spec["value"], spec["se"], n)
    if low is None and high is None:
        return out
    for _ in range(64):
        bad = np.zeros(n, dtype=bool)
        if low is not None:
            bad |= out <= low
        if high is not None:
            bad |= out >= high
        if not bad.any():
            return out
        out[bad] = rng.normal(spec["value"], spec["se"], int(bad.sum()))
    raise RuntimeError("el truncamiento no converge: revisa el dominio del parámetro")


def parametric_band(levers: Levers = Levers(), series: str = "precio", *,
                    n_draws: int = N_DRAWS_DEFAULT, seed: int = SEED_DEFAULT,
                    last_year: int | None = None) -> ParametricBand:
    """Banda de la serie sorteando IPV_LR e IPV_REV de su distribución estimada.

    Determinista dada la semilla. Con `n_draws=0` devuelve la proyección
    puntual y percentiles vacíos, que es el modo de comparación: la banda
    actual de parámetros fijos sigue disponible sin tocar nada.
    """
    if n_draws < 0:
        raise ValueError("n_draws no puede ser negativo")
    lr, rev = _spec("IPV_LR"), _spec("IPV_REV")
    point = run_scenario(levers)[series]
    years = [Y0 + k for k in range(len(point))]
    if last_year is not None:
        keep = years.index(last_year) + 1
        years, point = years[:keep], point[:keep]

    params = {"IPV_LR": lr, "IPV_REV": rev}
    if n_draws == 0:
        return ParametricBand(series=series, years=years, point=list(point),
                              percentiles={f"p{p}": [] for p in PCT_LEVELS},
                              n_draws=0, seed=seed, params=params)

    rng = np.random.default_rng(seed)
    # Un sorteo por trayectoria, mantenido los 25 años: es un parámetro, no un choque.
    lr_draws = _draw(rng, lr, n_draws)
    rev_draws = _draw(rng, rev, n_draws, low=0.0, high=1.0)

    runs = np.empty((n_draws, len(years)), dtype=float)
    for i in range(n_draws):
        path = run_scenario(levers, ipv_lr=float(lr_draws[i]),
                            ipv_rev=float(rev_draws[i]))[series]
        runs[i] = path[:len(years)]

    q = np.percentile(runs, PCT_LEVELS, axis=0)
    return ParametricBand(
        series=series, years=years, point=list(point),
        percentiles={f"p{p}": [float(v) for v in q[j]] for j, p in enumerate(PCT_LEVELS)},
        n_draws=n_draws, seed=seed, params=params)
