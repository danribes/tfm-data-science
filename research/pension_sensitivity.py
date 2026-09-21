"""Sensibilidad de la deuda a la indexación de las pensiones.

Este canal es, con diferencia, el más potente del motor: la productividad,
recorriendo todo su rango, mueve la deuda de 2050 unos 17 puntos de PIB; la
indexación la mueve más de 140 entre sus dos extremos. Conviene publicar la
curva entera en lugar de dos o tres puntos, por dos razones.

La primera es que un lector que mueve la palanca merece saber si está en una
zona plana o en una pendiente. La segunda es que la relación no es lineal: el gasto extra se arrastra año a
año y se capitaliza al tipo efectivo menos el crecimiento, de modo que la
pendiente sube de 48 a 65 puntos de deuda por punto de indexación entre un
extremo y el otro. Interpolar entre los extremos se equivoca en hasta 6,8
puntos, un 4,8 % del recorrido.

No es una estimación. Es la aritmética del motor bajo un supuesto contable: un
punto de PIB de gasto es un punto menos de saldo primario, sin respuesta de
política ni efectos de segunda ronda sobre actividad o recaudación.
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.constants import BASE_LEVERS, ENGINE_VERSION, VINTAGE
from engine.levers import LEVER_SPECS, Levers
from engine.spain import Y1, run_scenario

ROOT = Path(__file__).resolve().parents[1]
SPEC = next(s for s in LEVER_SPECS if s["id"] == "idx")
STEP = 0.1


def _grid() -> list[float]:
    n = round((SPEC["max"] - SPEC["min"]) / STEP)
    return [round(SPEC["min"] + i * STEP, 10) for i in range(n + 1)]


def evaluate() -> dict:
    base = run_scenario(Levers())
    k = Y1 - 2026
    filas = []
    for v in _grid():
        s = run_scenario(Levers(idx=v))
        filas.append({
            "idx": v,
            "debt_2050": s["b"][k],
            "debt_delta": s["b"][k] - base["b"][k],
            "pens_2050": s["pens"][k],
            "pens_delta": s["pens"][k] - base["pens"][k],
            "saldo_2050": s["saldo"][k],
        })
    # Pendiente local en el punto de referencia: cuánto añade a la deuda de
    # 2050 un décima de punto más de indexación, ahí donde está la palanca hoy.
    i0 = next(i for i, r in enumerate(filas) if abs(r["idx"] - BASE_LEVERS["idx"]) < 1e-9)
    pend = (filas[i0 + 1]["debt_2050"] - filas[i0 - 1]["debt_2050"]) / (2 * STEP)
    return {
        "vintage": VINTAGE,
        "engine_version": ENGINE_VERSION,
        "computed_not_advice": True,
        "channel": "accounting",
        "channel_note": ("Un punto de PIB de gasto en pensiones es un punto menos "
                         "de saldo primario. Sin respuesta de política ni efectos "
                         "de segunda ronda sobre actividad o recaudación."),
        "lever": {"id": "idx", "name": SPEC["nm"], "unit": SPEC["unit"],
                  "min": SPEC["min"], "max": SPEC["max"], "base": BASE_LEVERS["idx"]},
        "slope_at_base_pp_per_point": pend,
        "span_pp": filas[-1]["debt_2050"] - filas[0]["debt_2050"],
        "rows": filas,
    }


if __name__ == "__main__":
    out = ROOT / "docs/eval/pension-indexation-sensitivity.json"
    data = evaluate()
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  recorrido total: {data['span_pp']:.1f} pp de PIB")
    print(f"  pendiente en el punto de referencia: {data['slope_at_base_pp_per_point']:.1f} pp por punto de indexación")
    for r in data["rows"][::5]:
        print(f"   idx {r['idx']:>5.1f}  deuda {r['debt_2050']:7.1f}  Δ {r['debt_delta']:+7.1f}  pensiones {r['pens_2050']:6.2f}")
