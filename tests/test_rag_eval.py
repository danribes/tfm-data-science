"""Tests for the RAG evaluation harness and the advice guardrail.

The harness itself is tested against a small synthetic corpus, not the real
one: the real corpus lives outside the repository (copyrighted books never go
in git), so a test that needed it would be skipped on every machine but this
one — which is the same as not having it.

The scores the harness produces on the real corpus are deliberately NOT
asserted here. They belong to the corpus and the model, they move when either
moves, and pinning them would turn a measurement into a thing to be satisfied.
They are printed by `python -m rag.evaluate` and quoted in the commit.
"""
from __future__ import annotations

import pytest

from rag import chat, config, evaluate, golden, store


# ---- the golden set has to be well-formed before it can measure anything ----

def test_every_answerable_question_names_a_document():
    for q in golden.ANSWERABLE:
        assert q.expect_docs, f"{q.id} no dice qué documento debería salir"
        assert q.topic, f"{q.id} sin tema"


def test_unanswerable_questions_name_no_document():
    """They are scored by what the chat says, not by what surfaces. Giving one
    an expected document would quietly move it into the wrong metric."""
    for q in golden.UNANSWERABLE:
        assert not q.expect_docs, f"{q.id} es incontestable pero espera un documento"
    assert len(golden.UNANSWERABLE) >= 3


def test_question_ids_are_unique():
    ids = [q.id for q in golden.GOLDEN]
    assert len(ids) == len(set(ids))


def test_expected_terms_are_alternatives_not_bare_strings():
    """A bare string would silently match character by character. It also used
    to make the harness measure the language of the source instead of the
    topic: Ramey-Zubairy never writes "multiplicador"."""
    for q in golden.GOLDEN:
        for forms in q.expect_terms:
            assert isinstance(forms, tuple), f"{q.id}: {forms!r} no es una tupla"
            assert forms and all(isinstance(f, str) for f in forms)


def test_every_collection_is_exercised():
    covered = {q.collection for q in golden.GOLDEN}
    assert covered == set(config.COLLECTIONS)


# ---- the metrics, on a corpus small enough to reason about ------------------

@pytest.fixture()
def tiny(tmp_path, monkeypatch):
    """Three documents, one chunk each, no embeddings — enough to test the
    scoring arithmetic and the corpus audit without a model on the GPU."""
    con = store.connect(tmp_path / "t.db")
    store.init_schema(con, dim=4)
    for title, text in [("Manual de Micro", "la elasticidad de la demanda"),
                        ("Informe Anual", "la economia espanola en 2023")]:
        cur = con.execute(
            "INSERT INTO documents (collection, title, source_path, sha256)"
            " VALUES ('libros', ?, ?, ?)", (title, f"/{title}", title))
        con.execute("INSERT INTO chunks (doc_id, ordinal, text) VALUES (?, 0, ?)",
                    (cur.lastrowid, text))
    # A document ingested with nothing in it: the failure the audit exists for.
    con.execute("INSERT INTO documents (collection, title, source_path, sha256)"
                " VALUES ('libros', 'Vacio', '/v', 'v')")
    con.commit()
    con.close()
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    return tmp_path / "t.db"


def test_audit_reports_a_document_with_no_chunks(tiny):
    out = evaluate.audit_corpus(tiny)
    assert out["documents"] == 3
    assert [d["title"] for d in out["empty_documents"]] == ["Vacio"]
    assert out["clean"] is False


def test_audit_flags_an_incomplete_index(tiny):
    """Both retrievers must see every chunk. A shortfall means half the hybrid
    is searching less than it claims — invisible without this check."""
    out = evaluate.audit_corpus(tiny)
    assert out["chunks"] == 2
    assert out["embeddings"] == 0          # the fixture writes no vectors
    assert out["embeddings_complete"] is False
    assert out["fts_complete"] is True


def test_reciprocal_rank_is_the_inverse_of_the_rank():
    r = evaluate.QuestionResult(id="x", topic="t", collection="libros",
                                rank=4, n_passages=8)
    assert r.hit is True
    assert r.rr == pytest.approx(0.25)


def test_a_miss_scores_zero_not_a_small_number():
    """rank 0 means never found. Treating it as a large rank would let a
    retriever that misses everything still post a non-zero MRR."""
    r = evaluate.QuestionResult(id="x", topic="t", collection="libros",
                                rank=0, n_passages=8)
    assert r.hit is False
    assert r.rr == 0.0


def test_term_recall_is_one_when_nothing_was_asked_for():
    r = evaluate.QuestionResult(id="x", topic="t", collection="libros",
                                rank=1, n_passages=8)
    assert r.term_recall == 1.0


def test_summary_averages_over_questions_and_lists_the_misses():
    rep = evaluate.RetrievalReport([
        evaluate.QuestionResult("a", "micro", "libros", rank=1, n_passages=8),
        evaluate.QuestionResult("b", "micro", "libros", rank=0, n_passages=8),
        evaluate.QuestionResult("c", "dsa", "libros", rank=2, n_passages=8),
    ])
    s = rep.summary()
    assert s["overall"]["hit_rate"] == pytest.approx(2 / 3)
    assert s["overall"]["mrr"] == pytest.approx((1 + 0 + 0.5) / 3)
    assert s["overall"]["top1"] == pytest.approx(1 / 3)
    assert s["misses"] == ["b"]
    assert s["by_topic"]["micro"]["n"] == 2
    assert s["by_topic"]["dsa"]["hit_rate"] == 1.0


def test_accent_and_case_do_not_decide_a_hit():
    assert evaluate._fold("Análisis de la DEUDA") == "analisis de la deuda"


# ---- the guardrail, in both directions -------------------------------------

@pytest.mark.parametrize("question", golden.ADVICE_PROBES)
def test_personal_advice_is_refused(question):
    assert chat.refusal_for(question), question


@pytest.mark.parametrize("question", golden.ADVICE_ALLOWED)
def test_economics_questions_are_not_refused(question):
    """The expensive failure mode. A guardrail that swallows "how does the
    Euribor feed through to mortgages" has not made the library safer."""
    assert chat.refusal_for(question) is None, question


def test_the_refusal_offers_the_question_it_would_answer():
    """A bare "no" teaches the reader nothing and invites a rephrase designed
    to slip past. The refusal names the version of the question that works."""
    text = chat.refusal_for("¿Me compro un piso?")
    assert text is not None
    assert "no doy consejo" in text.lower()
    assert "reformula" in text.lower()


def test_guardrail_runs_before_retrieval_and_returns_no_passages():
    """Passages beside a refusal would read as evidence for the advice that
    was just declined."""
    ans = chat.ask("Dame una cartera concreta para invertir mis ahorros")
    assert ans.passages == []
    assert ans.grounded is False
    assert ans.provider is None


def test_streamed_refusal_emits_empty_passages_then_done():
    events = list(chat.stream("¿Debería hipotecarme a tipo fijo o variable?"))
    names = [name for name, _ in events]
    assert names == ["passages", "done"]
    assert events[0][1] == {"passages": [], "grounded": False}
    assert "consejo" in events[1][1]["answer"].lower()
    assert events[1][1]["grounded"] is False


def test_guardrail_evaluation_scores_both_directions():
    out = evaluate.evaluate_guardrail()
    assert out["probes"] == len(golden.ADVICE_PROBES)
    assert out["allowed"] == len(golden.ADVICE_ALLOWED)
    assert out["leaked"] == []
    assert out["false_positives"] == []
    assert out["clean"] is True


# ---- ingest must not record a document it could not read -------------------

def test_a_document_with_no_extractable_text_is_not_recorded(tmp_path, monkeypatch):
    """A scanned PDF with no text layer loads every page and returns nothing.
    Before this guard the row survived with zero chunks: counted in the corpus
    total, reachable by no search. Dropping it also lets a later run retry the
    file, since `document_exists` keys on the sha."""
    from rag import extract, ingest

    con = store.connect(tmp_path / "t.db")
    store.init_schema(con, dim=4)
    src = tmp_path / "escaneado.pdf"
    src.write_bytes(b"%PDF-1.4 sin capa de texto")

    monkeypatch.setattr(extract, "pdf_pages", lambda p: iter(()))
    written, status = ingest.ingest_document(
        con, {"path": src, "title": "Escaneado", "collection": "libros", "meta": {}})

    assert written == 0
    assert status == "sin-texto"
    assert con.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
    con.close()


def test_a_document_with_text_is_recorded(tmp_path, monkeypatch):
    """The other half of the guard: a readable file must still land."""
    from rag import embed, extract, ingest

    con = store.connect(tmp_path / "t.db")
    store.init_schema(con, dim=4)
    src = tmp_path / "legible.pdf"
    src.write_bytes(b"%PDF-1.4 con texto")

    page = (1, "una pagina con suficiente texto para pasar el minimo " * 12)
    monkeypatch.setattr(extract, "pdf_pages", lambda p: iter([page]))
    monkeypatch.setattr(embed, "embed_passages", lambda ts: [[0.0, 0.0, 0.0, 1.0]] * len(ts))

    written, status = ingest.ingest_document(
        con, {"path": src, "title": "Legible", "collection": "libros", "meta": {}})

    assert status == "ok" and written > 0
    assert con.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
    con.close()
