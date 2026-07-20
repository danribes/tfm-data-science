"""Test del experimento de ablación LLM: la capa ML/DL+RAG debe marcar la diferencia."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"


def test_ablacion_llm():
    d = pd.read_csv(GOLD / "gold_ablacion_llm.csv")
    assert len(d) >= 10, "al menos 10 preguntas de benchmark"
    hits_rag, hits_solo = int(d.acierto_rag.sum()), int(d.acierto_solo.sum())
    # el requisito del tutor, como aserción: el LLM con la capa del sistema debe
    # reproducir los resultados; sin ella, no. Si esto falla, el TFM tiene un problema.
    assert hits_rag >= 0.8 * len(d), f"RAG solo acierta {hits_rag}/{len(d)}"
    assert hits_rag - hits_solo >= 0.5 * len(d), (
        f"la capa no diferencia: solo={hits_solo}, rag={hits_rag}")
    # los errores del brazo con RAG deben ser mucho menores donde ambos contestan
    ambos = d[d.err_solo.notna() & d.err_rag.notna()]
    if len(ambos) >= 3:
        assert ambos.err_rag.median() < ambos.err_solo.median()
