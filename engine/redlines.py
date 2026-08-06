"""v12 empirically-anchored red lines as data + evaluator (spec §4.5).

Thresholds and anchors from design/v12_limites_fuentes.md (extract S7.2,
L1655-1691). Statuses are COMPUTED from the scenario — never hand-written
(v16 'semáforo vivo' rule). near = within 10 % of the threshold (spec §4.5;
v16's statusOf used 12 % — the spec overrides for this global evaluator).
"""
from __future__ import annotations

NEAR_FRACTION = 0.10
_ZERO_THRESHOLD_BAND = 0.5   # pp — absolute near-band for the g < 0 line

RED_LINES: list[dict] = [
    {"id": "bono_rescate", "label": "Bono 10A > 7 %", "series": "bono",
     "threshold": 7.0, "cmp": "gt",
     "source": "zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012 [hist]"},
    {"id": "paro_record", "label": "Paro > 26,9 %", "series": "u",
     "threshold": 26.9, "cmp": "gt",
     "source": "máximo histórico ES (T1-2013) [hist]"},
    {"id": "deficit_maastricht", "label": "Déficit > 3 % PIB", "series": "saldo",
     "threshold": -3.0, "cmp": "lt", "source": "umbral Maastricht [regla UE]"},
    {"id": "deficit_suelo_2009", "label": "Déficit > 11,3 % PIB", "series": "saldo",
     "threshold": -11.3, "cmp": "lt", "source": "suelo 2009: ES −11,3 % PIB [hist]"},
    {"id": "deuda_105", "label": "Deuda > 105 % PIB", "series": "b",
     "threshold": 105.0, "cmp": "gt",
     "source": "crack23: «deuda brutal que ya está por encima del 105 %» [comentario]"},
    {"id": "deuda_120", "label": "Deuda > 120 % PIB", "series": "b",
     "threshold": 120.0, "cmp": "gt", "source": "≈ pico COVID ES 2020: 119,3 [hist]"},
    {"id": "inflacion_10", "label": "Inflación > 10 %", "series": "pi",
     "threshold": 10.0, "cmp": "gt",
     "source": "ola inflacionaria 2022: ES pico 10,8 % jul-2022 [hist]"},
    {"id": "esfuerzo_40", "label": "Esfuerzo vivienda > 40 %", "series": "esf",
     "threshold": 40.0, "cmp": "gt",
     "source": "definición Eurostat de sobrecarga (housing cost overburden) [UE]"},
    {"id": "pobreza_infantil_30", "label": "Pobreza infantil > 30 %", "series": "arop",
     "threshold": 30.0, "cmp": "gt",
     "source": "ES 27–28 % crónico, 30 % en picos post-2013; media UE ≈19 % [hist]"},
]


def evaluate_redlines(scenario: dict[str, list[float]], k: int) -> list[dict]:
    """Evaluate every red line at year index k. Returns computed statuses."""
    out = []
    for rl in RED_LINES:
        value = scenario[rl["series"]][k]
        thr = rl["threshold"]
        crossed = value > thr if rl["cmp"] == "gt" else value < thr
        band = NEAR_FRACTION * abs(thr) if thr != 0 else _ZERO_THRESHOLD_BAND
        status = "crossed" if crossed else ("near" if abs(value - thr) <= band else "safe")
        out.append({"id": rl["id"], "label": rl["label"], "series": rl["series"],
                    "value": value, "threshold": thr, "cmp": rl["cmp"],
                    "status": status, "source": rl["source"]})
    return out
