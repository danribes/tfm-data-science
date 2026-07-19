"""Modelo fundacional de series temporales (Chronos) contra el protocolo T1.

Ruta 2 de la expansión DL: Chronos-Bolt (Amazon), preentrenado sobre millones
de series, aplicado TAL CUAL (zero-shot, sin ajuste) a los niveles del IPV por
CCAA. Misma parrilla que todos los candidatos: orígenes 2019Q4–2023Q4, h=1–8,
test 2024+ intocable, criterio = batir al drift en ≥12/17 CCAA a h≤4.

CAVEAT DECLARADO: el corpus de preentrenamiento de Chronos no es auditable
desde aquí; si contiene series inmobiliarias que solapan la ventana de
validación, el zero-shot tendría información indirecta del período. Se declara
como limitación (afecta a favor del candidato, no del campeón — un candidato
que aun así pierda, pierde con más motivo).

    python3 analysis/foundation_t1.py   (~2 min CPU)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from backtest_t1 import OUT, backtest, load_series, summarize

MODELO = "amazon/chronos-bolt-small"


def make_chronos():
    from chronos import BaseChronosPipeline

    pipe = BaseChronosPipeline.from_pretrained(MODELO, device_map="cpu", torch_dtype=torch.float32)

    def forecaster(train: pd.Series, h: int) -> list[float]:
        ctx = torch.tensor(train.astype(float).values, dtype=torch.float32).unsqueeze(0)
        q, _ = pipe.predict_quantiles(ctx, h, [0.5])
        return [float(v) for v in q[0, :, 0]]

    return forecaster


def main() -> None:
    series = load_series()
    df = backtest(series, {"chronos": make_chronos()})
    df.to_csv(OUT / "foundation_errores.csv", index=False)
    summ = summarize(df)
    print(summ.pivot(index="h", columns="metodo", values="MASE").round(3).to_string())

    be = pd.read_csv(OUT / "backtest_errores.csv")
    drift_ccaa = (be[(be.metodo == "drift") & (be.h <= 4)].assign(m=lambda d: d.ae / d.scale)
                  .groupby("ccaa")["m"].mean())
    cand = (df[df.h <= 4].assign(m=lambda d: d.ae / d.scale).groupby("ccaa")["m"].mean())
    comp = (cand < drift_ccaa).drop(labels=["Nacional"], errors="ignore")
    print(f"\nCriterio reforzado: chronos ({MODELO}) bate al drift en {int(comp.sum())}/17 CCAA "
          f"(MASE h<=4 {cand.mean():.3f} vs drift {drift_ccaa.mean():.3f})")
    c58 = df[df.h.between(5, 8)].assign(m=lambda d: d.ae / d.scale).m.mean()
    d58 = be[(be.metodo == "drift") & (be.h.between(5, 8))].assign(m=lambda d: d.ae / d.scale).m.mean()
    print(f"h5-8: chronos {c58:.3f} vs drift {d58:.3f} (informativo)")


if __name__ == "__main__":
    main()
