"""Sensitivity of the regional housing mean to shared time dependence.

The primary table clusters by region. Here whole quarterly cross sections move
together in a circular moving-block bootstrap, preserving common national
movements and dependence within each block. Regions are fixed, not resampled.
This is a sensitivity analysis conditional on each observed window; resampling
a historical crash and recovery does not identify a structural long-run mean.

    python -m research.housing_robustness
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from research import estimate, panel, validate

SEED = 42
N_BOOT = 500
BLOCK_LENGTHS = (4, 8, 12)
OUT = Path(__file__).resolve().parents[1] / "docs" / "eval" / "housing-robustness.json"


def synchronized_block_mean(rows: list[dict], *, key: str = "ipv_yoy",
                            block_length: int = 8, n_boot: int = N_BOOT,
                            seed: int = SEED) -> dict:
    """Bootstrap a pooled mean by resampling contiguous quarterly cross sections.

    Quarter sums and counts are sufficient for this mean: resampling their pair
    retains every observed region together and preserves weights if coverage
    differs by quarter. Circular blocks make each observed quarter equally
    likely to appear. The boundary joins the window's end back to its beginning,
    an assumption disclosed in the report, not a newly observed transition.
    """
    if block_length < 1 or n_boot < 2:
        raise ValueError("block_length must be positive and n_boot at least 2")
    usable = [r for r in rows if r.get(key) is not None and np.isfinite(r[key])]
    by_t: dict[int, list[float]] = {}
    for r in usable:
        by_t.setdefault(r["t"], []).append(float(r[key]))
    times = sorted(by_t)
    if len(times) < block_length:
        raise ValueError("window must contain at least one complete block")
    if any(b - a != 1 for a, b in zip(times, times[1:])):
        raise ValueError("quarter timeline must be consecutive before resampling")

    totals = np.array([sum(by_t[t]) for t in times])
    counts = np.array([len(by_t[t]) for t in times])
    n_t = len(times)
    n_blocks = (n_t + block_length - 1) // block_length
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n_t, size=(n_boot, n_blocks))
    indices = ((starts[:, :, None] + np.arange(block_length)) % n_t)
    indices = indices.reshape(n_boot, -1)[:, :n_t]
    boot = totals[indices].sum(axis=1) / counts[indices].sum(axis=1)
    lo, hi = np.quantile(boot, [0.05, 0.95])
    return {
        "mean": float(totals.sum() / counts.sum()),
        "se": float(boot.std(ddof=1)),
        "ci_low": float(lo), "ci_high": float(hi),
        "confidence": 0.90, "interval": "percentile",
        "block_quarters": block_length, "n_boot": n_boot, "seed": seed,
        "n": len(usable), "n_quarters": n_t,
        "n_regions": len({r["ccaa"] for r in usable}),
    }


def run() -> dict:
    housing = panel.yoy(panel.housing_panel(), "ipv", periods=4)
    usable = [r for r in housing.rows if r["ipv_yoy"] is not None]
    windows = [("2007–2026 · muestra completa", usable)]
    windows.extend((label, [r for r in usable if y0 <= r["year"] <= y1])
                   for label, y0, y1 in validate.IPV_WINDOWS)
    results = []
    for label, rows in windows:
        primary = estimate.pooled_mean(rows, "ipv_yoy", "ccaa", name=label)
        assert primary is not None
        first, last = min(r["t"] for r in rows), max(r["t"] for r in rows)
        results.append({
            "window": label,
            "observations_from": f"{first // 4}Q{first % 4 + 1}",
            "observations_to": f"{last // 4}Q{last % 4 + 1}",
            "primary_region_clustered": primary.to_dict(),
            "synchronized_time_blocks": [
                synchronized_block_mean(rows, block_length=b) for b in BLOCK_LENGTHS
            ],
        })
    source = panel.GOLD / "gold_ccaa_trimestral.csv"
    return {
        "source": "data/gold/gold_ccaa_trimestral.csv",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "regions": "17 CCAA + Ceuta y Melilla; Nacional excluido",
        "estimand": "media del crecimiento interanual observado; % a/a",
        "method": "bootstrap circular por bloques de trimestres sincronizados entre regiones",
        "windows": results,
        "interpretation": (
            "Sensibilidad complementaria: no sustituye las bandas primarias. "
            "Mantiene fijas las regiones observadas y remuestrea el tiempo, "
            "conservando la covariación nacional y la dependencia dentro de "
            "bloques de 4, 8 y 12 trimestres. Las bandas son condicionales a "
            "la ventana y a estos supuestos; no son intervalos de predicción "
            "ni validan una tendencia estructural de largo plazo."),
        "limitations": [
            "El bootstrap por bloques supone estabilidad dentro de cada ventana; "
            "la muestra completa mezcla una crisis y una recuperación.",
            "Los bloques circulares unen artificialmente el final con el inicio "
            "de la ventana y no preservan dependencia más allá de su longitud.",
            "500 réplicas permiten una comprobación acotada; los extremos de las "
            "bandas tienen error Monte Carlo y no justifican precisión fina.",
        ],
    }


def main() -> None:
    result = run()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for window in result["windows"]:
        print(window["window"])
        primary = window["primary_region_clustered"]
        print(f"  regiones: {primary['coef']:.2f} [{primary['ci_low']:.2f}, {primary['ci_high']:.2f}]")
        for b in window["synchronized_time_blocks"]:
            print(f"  bloques {b['block_quarters']:2d}: [{b['ci_low']:.2f}, {b['ci_high']:.2f}]")


if __name__ == "__main__":
    main()
