"""RAG layer: chunking, store, hybrid retrieval and the endpoints.

Deliberately no network and no GPU. Embeddings are stubbed with a deterministic
fake so the suite runs anywhere and in milliseconds — what is under test is the
plumbing (schema, fusion, collection isolation, citation), not the quality of a
particular embedding model, which belongs in a golden-question eval instead.
"""
from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag import config, extract, retrieve, store

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_corpus(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "isolated.db")
    def no_model():
        raise AssertionError("Unit tests must stub embeddings instead of loading a model")
    monkeypatch.setattr("rag.embed.get_model", no_model)


def fake_vector(text: str, dim: int = config.EMBED_DIM) -> list[float]:
    """Deterministic unit-norm pseudo-embedding derived from the text."""
    h = hashlib.sha256(text.encode()).digest()
    raw = [(h[i % len(h)] - 128) / 128.0 for i in range(dim)]
    norm = sum(v * v for v in raw) ** 0.5 or 1.0
    return [v / norm for v in raw]


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """An isolated corpus with two collections that must never mix."""
    con = store.connect(tmp_path / "t.db")
    store.init_schema(con)

    monkeypatch.setattr("rag.embed.embed_passages",
                        lambda texts, batch_size=None: [fake_vector(t) for t in texts])
    monkeypatch.setattr("rag.embed.embed_query", lambda t: fake_vector(t))

    def add(collection, title, sha, texts):
        doc = store.add_document(con, collection=collection, title=title,
                                 source_path=f"/x/{sha}", sha256=sha, pages=1)
        chunks = [{"ordinal": i, "page": 1, "section": "Cap. 1", "text": t}
                  for i, t in enumerate(texts)]
        store.add_chunks(con, doc, chunks, [fake_vector(t) for t in texts])
        con.commit()

    add("libros", "Mankiw - Principios", "sha-libro", [
        "La deuda publica crece cuando el tipo de interes supera al crecimiento nominal.",
        "El multiplicador fiscal mide cuanto se expande el producto ante un aumento del gasto.",
        "La regla de Okun relaciona la brecha del producto con el desempleo observado.",
    ])
    add("crack23", "Canal - gráficas 62", "sha-canal", [
        "La deuda publica esta disparada y nadie dice nada sobre el tipo de interes.",
    ])
    yield con
    con.close()


# ---- chunking ---------------------------------------------------------------

def test_clean_page_strips_running_furniture():
    assert extract.clean_page("42\nEl PIB nominal crece\nCHAPTER 3") == "El PIB nominal crece"


def test_chunker_drops_fragments_below_the_floor():
    pages = iter([(1, "corto")])
    assert list(extract.chunk_pages(pages)) == []


def test_chunker_splits_long_text_with_overlap():
    # Must exceed CHUNK_TOKENS * CHARS_PER_TOKEN (3.200 chars) to force a split;
    # anything shorter legitimately stays a single chunk.
    sentence = "El saldo primario determina la senda de la deuda publica. "
    para = (sentence * 200).strip()
    assert len(para) > config.CHUNK_TOKENS * config.CHARS_PER_TOKEN
    chunks = list(extract.chunk_pages(iter([(1, para)])))
    assert len(chunks) >= 2
    assert all(len(c["text"]) <= config.MAX_CHUNK_CHARS for c in chunks)
    assert [c["ordinal"] for c in chunks] == list(range(len(chunks)))


def test_chunker_carries_the_last_heading_as_section():
    text = "# Capitulo 4 La deuda\n\n" + ("Contenido suficiente para pasar el minimo. " * 12)
    chunks = list(extract.chunk_pages(iter([(1, text)])))
    assert chunks and "Capitulo 4" in (chunks[0]["section"] or "")


def test_sha256_is_stable_and_streaming(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"economia" * 1000)
    assert extract.sha256_file(p) == extract.sha256_file(p)
    assert len(extract.sha256_file(p)) == 64


# ---- store ------------------------------------------------------------------

def test_document_exists_drives_resumability(db):
    assert store.document_exists(db, "sha-libro")
    assert not store.document_exists(db, "sha-desconocido")


def test_stats_counts_per_collection(db):
    st = store.stats(db)
    assert st["documents"] == 2
    assert st["by_collection"]["libros"]["chunks"] == 3
    assert st["by_collection"]["crack23"]["chunks"] == 1


def test_delete_document_removes_chunks_and_indexes(db):
    store.delete_document(db, "sha-libro")
    st = store.stats(db)
    assert "libros" not in st["by_collection"] or st["by_collection"]["libros"]["chunks"] == 0
    assert db.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0] == 1


# ---- retrieval --------------------------------------------------------------

def test_search_finds_the_relevant_passage(db):
    hits = retrieve.search("tipo de interes y crecimiento", "libros", 3, con=db)
    assert hits
    assert "tipo de interes" in hits[0].text.lower()


def test_search_never_leaks_across_collections(db):
    """The correctness property: a textbook and a channel never co-rank."""
    for h in retrieve.search("deuda publica tipo de interes", "libros", 5, con=db):
        assert h.collection == "libros"
    for h in retrieve.search("deuda publica tipo de interes", "crack23", 5, con=db):
        assert h.collection == "crack23"


def test_passages_carry_the_authority_of_their_collection(db):
    assert retrieve.search("deuda", "libros", 2, con=db)[0].authority == "academico"
    assert retrieve.search("deuda", "crack23", 2, con=db)[0].authority == "opinion"


def test_citation_includes_title_section_and_page(db):
    cite = retrieve.search("multiplicador fiscal", "libros", 1, con=db)[0].cite()
    assert "Mankiw" in cite and "Cap. 1" in cite and "p. 1" in cite


def test_hybrid_records_both_rankings(db):
    hits = retrieve.search("regla de Okun desempleo", "libros", 3, con=db)
    assert any(h.lexical_rank is not None for h in hits)
    assert any(h.dense_rank is not None for h in hits)


def test_query_with_fts_metacharacters_does_not_crash(db):
    """User text is not an FTS5 expression; '¿r > g?' must not raise."""
    assert isinstance(retrieve.search("¿que pasa si r > g? (AND OR)", "libros", 3, con=db), list)


def test_unknown_collection_is_rejected(db):
    with pytest.raises(ValueError):
        retrieve.search("x", "no_existe", con=db)


def test_search_all_keeps_sources_separated(db, monkeypatch):
    # sqlite3.Connection.close is read-only, so hand search_all a thin proxy
    # whose close() is a no-op instead of patching the connection itself.
    class KeepOpen:
        def __init__(self, con): self._con = con
        def __getattr__(self, name): return getattr(self._con, name)
        def close(self): pass

    monkeypatch.setattr("rag.store.connect", lambda path=None: KeepOpen(db))
    res = retrieve.search_all("deuda publica", ["libros", "crack23"], 2)
    assert set(res) == {"libros", "crack23"}
    for coll, hits in res.items():
        assert all(h.collection == coll for h in hits)


# ---- endpoints --------------------------------------------------------------

def test_collections_endpoint_lists_everything_when_nothing_is_restricted():
    """Con el corpus abierto, el listado anuncia las cuatro colecciones."""
    ids = {c["id"] for c in client.get("/rag/collections").json()["collections"]}
    assert ids == {"libros", "metodo", "defensa_tfm", "crack23"}


def test_collections_endpoint_hides_the_restricted_ones_when_gated(monkeypatch):
    """Advertising a collection nobody can read is an invitation to try."""
    monkeypatch.setattr("rag.config.RESTRICTED_COLLECTIONS",
                        frozenset({"libros", "crack23"}))
    ids = {c["id"] for c in client.get("/rag/collections").json()["collections"]}
    assert ids == {"metodo", "defensa_tfm"}


def test_the_open_corpus_needs_no_credential():
    """Lo que la decisión de abrir el corpus significa, dicho como prueba."""
    for coll in ("libros", "crack23", "metodo", "defensa_tfm"):
        r = client.post("/rag/search", json={"query": "phillips", "collection": coll})
        assert r.status_code != 401, coll


def test_collections_endpoint_lists_everything_for_a_reviewer(gated, monkeypatch):
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    body = client.get("/rag/collections", headers={"X-Rag-Token": "t0ken"}).json()
    ids = {c["id"]: c for c in body["collections"]}
    assert set(ids) == {"libros", "metodo", "defensa_tfm", "crack23"}
    assert ids["libros"]["authority"] == "academico"
    assert ids["defensa_tfm"]["authority"] == "defensa"
    assert ids["crack23"]["authority"] == "opinion"


def test_collections_endpoint_survives_a_missing_corpus(monkeypatch):
    monkeypatch.setattr("rag.store.connect",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no db")))
    r = client.get("/rag/collections")
    assert r.status_code == 200
    assert r.json()["total_chunks"] == 0


def test_search_endpoint_rejects_unknown_collection():
    r = client.post("/rag/search", json={"query": "deuda", "collection": "nope"})
    assert r.status_code == 422


def test_search_endpoint_validates_query_length():
    assert client.post("/rag/search", json={"query": "x"}).status_code == 422


def test_chat_endpoint_rejects_unknown_collection():
    r = client.post("/rag/chat", json={"question": "¿que es la deuda?",
                                       "collection": "nope"})
    assert r.status_code == 422


def test_chat_refuses_to_answer_without_passages(monkeypatch):
    """An uncited answer is worse than none — it looks sourced and is not."""
    monkeypatch.setattr("rag.retrieve.search", lambda *a, **k: [])
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    r = client.post("/rag/chat", json={"question": "¿que dice sobre la fusion fria?"},
                    headers={"X-Rag-Token": "t0ken"})
    body = r.json()
    assert r.status_code == 200
    assert body["grounded"] is False
    assert body["passages"] == []
    assert "no cubre" in body["answer"].lower()


# ---- the reviewer token ------------------------------------------------------
#
# El despliegue sirve hoy el corpus abierto: RESTRICTED_COLLECTIONS está vacío
# por decisión del autor. La maquinaria de la verja sigue en el código y estas
# pruebas la siguen ejerciendo, rearmándola en la propia prueba. Borrarlas
# porque la política actual no las usa dejaría sin red el día que se vuelva a
# cerrar, que es justo cuando importa que funcione.


@pytest.fixture
def gated(monkeypatch):
    """Vuelve a cerrar libros y crack23 durante la prueba."""
    monkeypatch.setattr("rag.config.RESTRICTED_COLLECTIONS",
                        frozenset({"libros", "crack23"}))

def test_restricted_collections_need_the_token(gated, monkeypatch):
    """The books are third-party copyright; only an evaluator should reach them."""
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    for path, payload in (
        ("/rag/search", {"query": "curva de Phillips", "collection": "libros"}),
        ("/rag/chat", {"question": "¿qué es la curva de Phillips?", "collection": "libros"}),
    ):
        assert client.post(path, json=payload).status_code == 401, path
        ok = client.post(path, json=payload, headers={"X-Rag-Token": "t0ken"})
        assert ok.status_code != 401, path


def test_an_unset_token_locks_rather_than_opens(gated, monkeypatch):
    """Forgetting to configure it must not publish the corpus.

    The dangerous default is the one where a missing secret means "no check".
    """
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "")
    r = client.post("/rag/search", json={"query": "phillips", "collection": "libros"})
    assert r.status_code == 401
    assert client.post("/rag/search", json={"query": "phillips", "collection": "libros"},
                       headers={"X-Rag-Token": ""}).status_code == 401


def test_a_wrong_token_is_refused(gated, monkeypatch):
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    for bad in ("t0keN", "t0ke", "t0kenn", "", "otro"):
        r = client.post("/rag/search", json={"query": "phillips", "collection": "libros"},
                        headers={"X-Rag-Token": bad})
        assert r.status_code == 401, bad


def test_surrounding_whitespace_is_tolerated(gated, monkeypatch):
    """A token arrives pasted from an email, and often with a space attached.

    Trimming costs nothing — no one guesses a secret by adding whitespace — and
    the alternative is an evaluator locked out by an invisible character.
    """
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    r = client.post("/rag/search", json={"query": "phillips", "collection": "libros"},
                    headers={"X-Rag-Token": "  t0ken \n"})
    assert r.status_code != 401


def test_the_project_documents_stay_open(gated, monkeypatch):
    """Gating the books must not gate the app's own documentation."""
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    for coll in ("metodo", "defensa_tfm"):
        r = client.post("/rag/search", json={"query": "motor", "collection": coll})
        assert r.status_code != 401, coll


def test_bearer_header_also_carries_the_token(gated, monkeypatch):
    """One credential, whichever endpoint serves the corpus.

    The interface already sends Authorization: Bearer to a tunnelled corpus;
    accepting it here means an evaluator is not handed two different
    instructions depending on where the books happen to live that week.
    """
    monkeypatch.setattr("rag.config.REVIEWER_TOKEN", "t0ken")
    r = client.post("/rag/search", json={"query": "phillips", "collection": "libros"},
                    headers={"Authorization": "Bearer t0ken"})
    assert r.status_code != 401
    bad = client.post("/rag/search", json={"query": "phillips", "collection": "libros"},
                      headers={"Authorization": "Bearer otro"})
    assert bad.status_code == 401
