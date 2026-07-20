"""Tests del asistente RAG (app/rag_assistant.py) — todo offline."""
import pathlib
import sys

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from rag_assistant import (DEFAULT_ENGINE, ENGINES, FALLBACK_ENGINES, SYSTEM,  # noqa: E402
                           chunk_docs, retrieve)


def test_registro_de_motores():
    assert DEFAULT_ENGINE == "gemini" and DEFAULT_ENGINE in ENGINES
    for cfg in ENGINES.values():
        assert {"base", "model", "key_env", "max_tokens"} <= set(cfg)
        assert cfg["max_tokens"] >= 300  # gotcha de los razonadores
    # la reserva son motores reales y distintos del primario
    assert FALLBACK_ENGINES and all(e in ENGINES for e in FALLBACK_ENGINES)
    assert DEFAULT_ENGINE not in FALLBACK_ENGINES


@pytest.fixture(scope="module")
def chunks():
    return chunk_docs()


def test_corpus_no_trivial(chunks):
    assert len(chunks) > 150
    assert all(c["n_car"] >= 200 for c in chunks)


def test_corpus_excluye_old_y_defensa(chunks):
    fuentes = {c["fuente"] for c in chunks}
    assert not any("_old" in f or "defensa" in f for f in fuentes)


def test_manifest_contract():
    m = pd.read_csv(ROOT / "storage" / "gold" / "gold_corpus_manifest.csv")
    for col in ["id", "fuente", "seccion", "n_car"]:
        assert col in m.columns
    assert m.id.is_unique and len(m) > 150


def test_retrieval_encuentra_el_test_final(chunks):
    res = retrieve(chunks, "por qué el modelo de producción es el drift y no el GBM")
    fuentes = [c["fuente"] for _, c in res]
    # el contenido de candidatos_t1/test_final/backtest vive ahora en el compendio de vivienda
    assert any("RESULTADOS_VIVIENDA" in f or "METODOLOGIA" in f for f in fuentes)


def test_retrieval_encuentra_pensiones(chunks):
    res = retrieve(chunks, "elasticidad de las pensiones al envejecimiento share65")
    assert res, "debe recuperar algo"
    textos = " ".join(c["texto"] for _, c in res)
    assert "0,91" in textos or "0.91" in textos


def test_prompt_prohibe_inventar_numeros():
    assert "textualmente" in SYSTEM and "narras" in SYSTEM
