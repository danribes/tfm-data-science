"""Ablación LLM: ¿difieren los resultados con y sin la capa ML/DL + RAG?

Requisito del tutor hecho experimento: el LLM debe limitarse a EXPLICAR los
resultados que producen las matemáticas (ML/DL); un LLM a pelo NO debería
poder reproducir los números del sistema. Diseño (mismo LLM en ambos brazos,
única variable = la capa de conocimiento):

- Brazo A — LLM SOLO: kimi-k2.6 sin contexto, "da tu mejor estimación".
- Brazo B — LLM + RAG: mismo modelo, mismos parámetros, con los pasajes
  recuperados del corpus del proyecto (los resultados de la capa ML/DL).
- Verdad — el valor calculado por el sistema (capa gold / motores).

12 preguntas cuya respuesta es una SALIDA del sistema (backtests, Monte Carlo,
paneles, fronteras): imposibles de saber sin el sistema, triviales de citar
con él. Métrica: |error relativo| y acierto dentro de tolerancia por brazo.

Salida: gold/gold_ablacion_llm.csv + tabla impresa.

    python3 analysis/ablacion_llm.py     (~2-3 min; requiere KIMI_API_KEY)
"""
from __future__ import annotations

import json
import re
import sys
import time

import pandas as pd
import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "app"))
from rag_assistant import ENGINES, _api_key, chunk_docs, retrieve  # noqa: E402

from backtest_t1 import GOLD  # noqa: E402

ENGINE = "gemini"
FECHA = "2026-07-19"

# (id, pregunta, verdad calculada por el sistema, tolerancia relativa)
PREGUNTAS = [
    ("ratio_2024", "En el proyecto 'El precio de lo público' (TFM, España): ¿cuál es el "
     "ratio de asequibilidad de vivienda NACIONAL en 2024, definido como índice IPV/salarios "
     "con base 2015=1? Un solo número.", 1.26, 0.05),
    ("ratio_2027", "Según el pronóstico del modelo de ese proyecto, ¿qué valor alcanza ese "
     "ratio nacional en 2027Q4 en el escenario central de salarios +2 % anual?", 1.64, 0.05),
    ("mase_drift", "En la validación rolling-origin 2019Q4–2023Q4 del proyecto, ¿qué MASE "
     "medio a horizonte ≤4 trimestres obtuvo el modelo drift (el campeón)?", 0.395, 0.10),
    ("deuda_2050", "En el simulador de deuda del proyecto (aritmética r−g con presión "
     "demográfica), ¿qué deuda pública española en % del PIB proyecta el escenario CENTRAL "
     "para 2050?", 224, 0.08),
    ("deuda_sin_demo", "¿Y el contrafactual SIN presión demográfica en 2050 (% PIB)?", 127, 0.08),
    ("deuda_2070_mc", "En el Monte Carlo del proyecto a 2070 (4.000 trayectorias), ¿cuál es "
     "la MEDIANA de deuda española en % del PIB del escenario central?", 409, 0.10),
    ("esfuerzo_2024", "Según la cuota hipotecaria teórica del proyecto (90 m², LTV 80 %, "
     "25 años, Euríbor 2024 +1 pp), ¿qué porcentaje del salario bruto supone la cuota "
     "NACIONAL en 2024?", 41.6, 0.10),
    ("gasto_1900", "Según la serie histórica empalmada del proyecto, ¿qué gasto público "
     "(% PIB, perímetro AAPP) tenía España en 1900?", 11.0, 0.15),
    ("residual_esp", "En la frontera sanitaria A1 del proyecto (164 países, LOOCV), ¿cuántos "
     "años de esperanza de vida tiene España POR ENCIMA de lo esperado para su renta y "
     "gasto (el residual)?", 2.72, 0.25),
    ("bienestar_2050", "En los sobres de bienestar del proyecto, con crecimiento de renta "
     "del 1 % anual, ¿qué variación porcentual de la mortalidad infantil (<5) respecto a la "
     "senda base da el modelo para 2050? (número negativo)", -12.3, 0.20),
    ("beta65", "En el motor de proyección del proyecto, ¿cuál es la elasticidad estimada "
     "del gasto en pensiones respecto a la cuota de población 65+ (β65, panel UE)?", 0.912, 0.15),
    ("spearman_suelo", "En el panel internacional del proyecto (40 países), ¿cuál es la "
     "correlación de Spearman entre el ratio precio/renta de la vivienda y el crecimiento "
     "del suelo artificial 2000–2022?", 0.01, None),  # tolerancia absoluta especial
]

JSON_ORDEN = ('Responde SOLO con JSON: {"valor": <numero>}. Sin unidades, sin texto extra. '
              'Si no lo sabes, da tu mejor estimación numérica (no respondas null).')


def _llama(messages: list[dict], max_tokens: int = 1500) -> str:
    """kimi es un reasoner: en preguntas difíciles quema el presupuesto en
    reasoning_content y deja content vacío (finish_reason=length). Se da
    presupuesto amplio y, si aun así no emite, se lee su razonamiento — ahí
    está su estimación genuina (comprobado en vivo)."""
    cfg = ENGINES[ENGINE]
    for intento in range(3):
        try:
            r = requests.post(f"{cfg['base']}/chat/completions",
                              headers={"Authorization": f"Bearer {_api_key(cfg['key_env'])}"},
                              json={"model": cfg["model"], "messages": messages,
                                    "max_tokens": max_tokens},
                              timeout=180)
            r.raise_for_status()
            msg = r.json()["choices"][0]["message"]
            return (msg.get("content") or "") or (msg.get("reasoning_content") or "")[-800:]
        except Exception:
            if intento == 2:
                raise
            time.sleep(10)
    return ""


def _numero(texto: str) -> float | None:
    m = re.search(r'"valor"\s*:\s*(-?\d+[.,]?\d*)', texto)
    if not m:
        m = re.search(r"(-?\d+[.,]\d+|-?\d+)", texto)
    return float(m.group(1).replace(",", ".")) if m else None


def brazo_solo(pregunta: str) -> float | None:
    return _numero(_llama([
        {"role": "system", "content": "Eres un economista experto en finanzas públicas y "
         "vivienda en España. NO tienes acceso a documentos ni datos externos."},
        {"role": "user", "content": f"{pregunta}\n\n{JSON_ORDEN}"}], max_tokens=8000))


def brazo_rag(chunks, pregunta: str) -> float | None:
    pasajes = retrieve(chunks, pregunta, k=4)
    ctx = "\n\n".join(f"[{i+1}] {p['fuente']} § {p['seccion']}\n{p['texto'][:1200]}"
                      for i, (_, p) in enumerate(pasajes))
    return _numero(_llama([
        {"role": "system", "content": "Responde EXCLUSIVAMENTE con números que aparezcan en "
         "los pasajes proporcionados. Son los resultados calculados del sistema."},
        {"role": "user", "content": f"PASAJES:\n{ctx}\n\nPREGUNTA: {pregunta}\n\n{JSON_ORDEN}"}]))


def main() -> None:
    chunks = chunk_docs()
    filas = []
    for qid, pregunta, verdad, tol in PREGUNTAS:
        a = brazo_solo(pregunta)
        b = brazo_rag(chunks, pregunta)
        def _err(v):
            if v is None:
                return None
            return abs(v - verdad) if tol is None else abs(v - verdad) / abs(verdad)
        def _ok(v):
            e = _err(v)
            if e is None:
                return False
            return e <= 0.05 if tol is None else e <= tol  # tol abs 0,05 para el Spearman
        filas.append({"id": qid, "verdad": verdad, "llm_solo": a, "llm_rag": b,
                      "err_solo": _err(a), "err_rag": _err(b),
                      "acierto_solo": _ok(a), "acierto_rag": _ok(b)})
        print(f"  {qid:16s} verdad {verdad:>8} | solo {str(a):>10} ({'OK' if _ok(a) else 'x'}) "
              f"| rag {str(b):>10} ({'OK' if _ok(b) else 'x'})")
        time.sleep(2)

    d = pd.DataFrame(filas)
    d["fecha_ejecucion"], d["engine"] = FECHA, ENGINES[ENGINE]["model"]
    d.to_csv(GOLD / "gold_ablacion_llm.csv", index=False)
    n = len(d)
    print(f"\nRESULTADO: LLM solo acierta {int(d.acierto_solo.sum())}/{n}; "
          f"LLM+RAG acierta {int(d.acierto_rag.sum())}/{n}")
    rel = d[d.err_solo.notna() & d.err_rag.notna() & (d.id != "spearman_suelo")]
    print(f"|error relativo| solo: mediana {rel.err_solo.median():.0%} "
          f"(rango {rel.err_solo.min():.0%}–{rel.err_solo.max():.0%}) "
          f"vs rag: mediana {rel.err_rag.median():.0%}")
    print("→ gold_ablacion_llm.csv")


if __name__ == "__main__":
    main()
