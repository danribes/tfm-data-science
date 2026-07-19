"""DL global entrenado en 1.760 series regionales extranjeras (Ruta 1) vs drift.

Diseño declarado ANTES de mirar resultados:
- Corpus: hpi_regional_global.csv (FHFA metro+estado, Zillow, UK) — series
  ESPAÑOLAS JAMÁS en el entrenamiento.
- Corte temporal: solo ventanas cuyo objetivo termina ≤2019Q3 (anterior al
  primer origen de validación) → el modelo no ha visto nada posterior a los
  orígenes desde ninguna geografía.
- Muestra: ventana de 16 Δlog trimestrales (clip ±0,15) → cabeza multi-salida
  con el Δlog ACUMULADO a h=1..8. Red: MLP 16→128→128→64→8, dropout 0,1,
  pérdida MAE, Adam. Es la apuesta "ha visto morir docenas de booms
  (EE. UU./UK 1968–2019)": si algo puede anticipar giros, es esto.
- Contest: parrilla idéntica (orígenes 2019Q4–2023Q4, h=1–8, test intocable,
  ≥12/17 CCAA a h≤4). Derrota → se declara y producción no cambia.

    python3 analysis/dl_global_t1.py   (~3 min CPU)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from backtest_t1 import OUT, backtest, load_series, summarize

PROCESSED = OUT.parents[2] / "storage" / "processed"
W, H = 16, 8
CORTE = 2019 * 4 + 3  # 2019Q3 en índice anyo*4+quarter
SEED = 42


def ventanas_entrenamiento() -> tuple[np.ndarray, np.ndarray]:
    d = pd.read_csv(PROCESSED / "hpi_regional_global.csv")
    d["p"] = d.anyo * 4 + d.quarter
    X, Y = [], []
    for _, g in d.groupby("serie"):
        g = g.sort_values("p")
        v = np.log(g.valor.values)
        p = g.p.values
        # exigir contigüidad trimestral estricta
        if len(v) < W + H + 1 or (np.diff(p) != 1).any():
            continue
        dl = np.clip(np.diff(v), -0.15, 0.15)
        for i in range(W, len(dl) - H + 1):
            if p[i + H] > CORTE:  # el objetivo completo debe acabar ≤2019Q3
                break
            X.append(dl[i - W:i])
            Y.append(np.cumsum(dl[i:i + H]))
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


def entrena(X: np.ndarray, Y: np.ndarray) -> nn.Module:
    torch.manual_seed(SEED)
    net = nn.Sequential(nn.Linear(W, 128), nn.ReLU(), nn.Dropout(0.1),
                        nn.Linear(128, 128), nn.ReLU(), nn.Dropout(0.1),
                        nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, H))
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    ds = torch.utils.data.TensorDataset(torch.tensor(X), torch.tensor(Y))
    dl = torch.utils.data.DataLoader(ds, batch_size=1024, shuffle=True)
    net.train()
    for epoca in range(8):
        tot = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            loss = nn.functional.l1_loss(net(xb), yb)
            loss.backward()
            opt.step()
            tot += float(loss) * len(xb)
        print(f"  época {epoca + 1}: MAE {tot / len(ds):.5f}")
    net.eval()
    return net


def make_forecaster(net: nn.Module):
    def forecaster(train: pd.Series, h: int) -> list[float]:
        v = np.log(train.astype(float).values)
        if len(v) < W + 1:
            return [np.nan] * h
        dl = np.clip(np.diff(v), -0.15, 0.15)[-W:]
        with torch.no_grad():
            cum = net(torch.tensor(dl, dtype=torch.float32).unsqueeze(0))[0].numpy()
        return [float(np.exp(v[-1] + cum[k])) for k in range(h)]

    return forecaster


def main() -> None:
    X, Y = ventanas_entrenamiento()
    print(f"entrenamiento: {len(X):,} ventanas (objetivos ≤2019Q3, series extranjeras)")
    net = entrena(X, Y)
    df = backtest(load_series(), {"dl_global": make_forecaster(net)})
    df.to_csv(OUT / "dl_global_errores.csv", index=False)
    print(summarize(df).pivot(index="h", columns="metodo", values="MASE").round(3).to_string())

    be = pd.read_csv(OUT / "backtest_errores.csv")
    drift_ccaa = (be[(be.metodo == "drift") & (be.h <= 4)].assign(m=lambda d: d.ae / d.scale)
                  .groupby("ccaa")["m"].mean())
    cand = df[df.h <= 4].assign(m=lambda d: d.ae / d.scale).groupby("ccaa")["m"].mean()
    comp = (cand < drift_ccaa).drop(labels=["Nacional"], errors="ignore")
    print(f"\nCriterio reforzado: dl_global bate al drift en {int(comp.sum())}/17 CCAA "
          f"(MASE h<=4 {cand.mean():.3f} vs drift {drift_ccaa.mean():.3f})")
    c58 = df[df.h.between(5, 8)].assign(m=lambda d: d.ae / d.scale).m.mean()
    d58 = be[(be.metodo == "drift") & (be.h.between(5, 8))].assign(m=lambda d: d.ae / d.scale).m.mean()
    print(f"h5-8: dl_global {c58:.3f} vs drift {d58:.3f} (informativo)")


if __name__ == "__main__":
    main()
