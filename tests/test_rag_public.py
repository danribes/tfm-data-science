"""Public documentation retrieval runs offline without the private RAG stack."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from api import main as api_main
from rag import chat, config, public_corpus, retrieve, store


@pytest.fixture
def source_root(tmp_path):
    root = tmp_path / "project"
    subjects = {
        "README.md": "Presentación general del proyecto de escenarios fiscales.",
        "docs/MEMORIA_TFM.md": "Memoria y justificación de la metodología científica.",
        "docs/RESULTS.md": "Resultados cuantitativos y límites de los contrastes.",
        "docs/METHODOLOGY_CHANGES.md": "Correcciones contables para la deuda nominal y el crecimiento.",
        "docs/REPRODUCIBILITY.md": "Reproducibilidad mediante semillas y versiones congeladas.",
        "docs/DEFENSA_TFM.md": "Defensa ante el tribunal y decisiones del trabajo académico.",
    }
    for relative, subject in subjects.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n\n" + (subject + " ") * 12, encoding="utf-8")
    return root


@pytest.fixture
def public_runtime(source_root, tmp_path, monkeypatch):
    path = tmp_path / "public.db"
    public_corpus.build(source_root, path)
    monkeypatch.setattr(config, "PUBLIC_MODE", True)
    monkeypatch.setattr(config, "RETRIEVAL_MODE", "lexical")
    monkeypatch.setattr(config, "CORPUS_SCOPE", "public_project_docs")
    monkeypatch.setattr(config, "DEFAULT_COLLECTION", "metodo")
    monkeypatch.setattr(config, "DB_PATH", path)
    monkeypatch.setattr(config, "COLLECTIONS", {
        "metodo": {"label": "Método", "authority": "propio", "note": "Documentación pública; BM25."},
        "defensa_tfm": {"label": "Defensa", "authority": "propio", "note": "Guía propia; BM25."},
    })
    monkeypatch.setattr(chat, "PROVIDERS", [])
    return path


def test_public_build_allowlists_sources_and_records_provenance(source_root, tmp_path):
    (source_root / "private-book.md").write_text("PRIVATE-CANARY " * 40)
    path = tmp_path / "public.db"
    result = public_corpus.build(source_root, path)
    assert result["documents"] == 6
    with sqlite3.connect(path) as con:
        rows = con.execute("SELECT source_path,sha256,meta,ingested_at FROM documents").fetchall()
        assert {r[0] for r in rows} == set(public_corpus.ALLOWED_SOURCES)
        for relative, digest, meta, timestamp in rows:
            assert digest == hashlib.sha256((source_root / relative).read_bytes()).hexdigest()
            assert json.loads(meta)["authority"] == "propio"
            assert timestamp is None  # no fabricated or nondeterministic ingestion timestamp
        assert con.execute("SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH 'PRIVATE'").fetchone()[0] == 0
        assert con.execute("SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH 'deuda'").fetchone()[0] > 0
        assert con.execute("SELECT name FROM sqlite_master WHERE name='chunks_vec'").fetchone() is None
        assert con.execute("SELECT COUNT(*) FROM documents WHERE pages IS NOT NULL").fetchone()[0] == 0
        assert con.execute("SELECT COUNT(*) FROM chunks WHERE page IS NOT NULL").fetchone()[0] == 0


def test_public_build_is_deterministic(source_root, tmp_path):
    first, second = tmp_path / "first.db", tmp_path / "second.db"
    a = public_corpus.build(source_root, first)
    b = public_corpus.build(source_root, second)
    assert a == b
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize("relative", ["../private.md", "/tmp/private.md", "econ_pdfs/book.pdf", "docs/../README.md"])
def test_public_source_rejects_paths_outside_allowlist(source_root, relative):
    with pytest.raises(ValueError):
        public_corpus._source_path(source_root.resolve(), relative)


def test_public_source_rejects_file_symlink(source_root, tmp_path):
    source = source_root / "README.md"
    elsewhere = tmp_path / "private.md"
    source.rename(elsewhere)
    source.symlink_to(elsewhere)
    with pytest.raises(ValueError, match="simbólicos"):
        public_corpus.build(source_root, tmp_path / "public.db")


def test_public_source_rejects_directory_symlink(source_root, tmp_path):
    docs = source_root / "docs"
    elsewhere = tmp_path / "elsewhere"
    docs.rename(elsewhere)
    docs.symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="simbólicos"):
        public_corpus.build(source_root, tmp_path / "public.db")


def test_failed_build_preserves_existing_index(source_root, tmp_path):
    path = tmp_path / "public.db"
    public_corpus.build(source_root, path)
    before = path.read_bytes()
    (source_root / "docs/RESULTS.md").write_text("")
    with pytest.raises(ValueError, match="indexable"):
        public_corpus.build(source_root, path)
    assert path.read_bytes() == before


def test_manifest_cannot_add_private_source(source_root, tmp_path, monkeypatch):
    manifest = json.loads(public_corpus.MANIFEST.read_text())
    manifest["sources"][0]["path"] = "private-book.md"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(public_corpus, "MANIFEST", path)
    with pytest.raises(ValueError, match="exactamente"):
        public_corpus.build(source_root, tmp_path / "public.db")


def test_public_builder_and_retrieval_need_only_stdlib(source_root, tmp_path):
    """-S removes site-packages: sqlite_vec, torch and requests are unavailable."""
    repo = Path(__file__).resolve().parents[1]
    path = tmp_path / "slim.db"
    env = {**os.environ, "PYTHONPATH": str(repo), "EVO_RAG_MODE": "public_lexical", "EVO_RAG_DB": str(path)}
    script = """
import json, sys
from pathlib import Path
from rag.public_corpus import build
build(Path(sys.argv[1]), Path(sys.argv[2]))
from rag import chat, config, retrieve, store
assert config.RETRIEVAL_MODE == 'lexical'
assert config.DEFAULT_COLLECTION == 'metodo'
assert set(config.COLLECTIONS) == {'metodo', 'defensa_tfm'}
hits = retrieve.search('deuda nominal')
assert hits and hits[0].authority == 'propio'
assert all(h.dense_rank is None for h in hits)
chat.PROVIDERS = []
assert chat.ask('deuda nominal').passages
assert list(chat.stream('deuda nominal'))[-1][0] == 'done'
assert not {'rag.embed', 'torch', 'sentence_transformers', 'sqlite_vec'} & sys.modules.keys()
print(json.dumps({'hits': len(hits), 'mode': config.MODE}))
"""
    result = subprocess.run([sys.executable, "-S", "-c", script, str(source_root), str(path)],
                            env=env, cwd=repo, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hits"] > 0


def test_public_retrieval_isolated_and_never_calls_dense(public_runtime, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("public mode must not invoke dense retrieval")
    monkeypatch.setattr(retrieve, "_dense", unexpected)
    # Default hybrid weights remain positive: public mode itself must gate both probes.
    assert config.W_DENSE > 0 and config.W_DENSE_EN > 0
    hits = retrieve.search("deuda nominal")
    assert hits and all(p.collection == "metodo" for p in hits)
    assert all(p.dense_rank is None and p.authority == "propio" for p in hits)
    assert hits[0].cite() and "Correcciones" in hits[0].title
    assert all(p.page is None and " · p. " not in p.cite() for p in hits)
    assert hits[0].section == "# METHODOLOGY_CHANGES"
    assert hits[0].cite() == f"{hits[0].title} · # METHODOLOGY_CHANGES"
    assert retrieve.search("tribunal", "metodo") == []
    assert retrieve.search("tribunal", "defensa_tfm")
    with pytest.raises(ValueError):
        retrieve.search("deuda", "libros")


def test_public_store_is_read_only_and_never_creates_missing_index(public_runtime, tmp_path):
    con = store.connect()
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            con.execute("DELETE FROM documents")
    finally:
        con.close()
    absent = tmp_path / "absent" / "corpus.db"
    with pytest.raises(sqlite3.OperationalError):
        store.connect(absent)
    assert not absent.parent.exists()


def test_public_store_rejects_unmarked_private_database(public_runtime, tmp_path):
    private = tmp_path / "private.db"
    with sqlite3.connect(private) as con:
        con.execute("CREATE TABLE private_data (value TEXT)")
    with pytest.raises(sqlite3.OperationalError):
        store.connect(private)


def test_public_collections_default_search_and_eval_contract(public_runtime):
    client = TestClient(api_main.app)
    body = client.get("/rag/collections").json()
    assert body["retrieval_mode"] == "lexical"
    assert body["corpus_scope"] == "public_project_docs"
    assert body["default_collection"] == "metodo"
    assert body["total_documents"] == 6
    assert {c["id"] for c in body["collections"]} == {"metodo", "defensa_tfm"}
    response = client.post("/rag/search", json={"query": "deuda nominal"})
    assert response.status_code == 200
    assert response.json()["collection"] == "metodo"
    assert response.json()["passages"][0]["authority"] == "propio"
    assert client.post("/rag/search", json={"query": "deuda", "collection": "libros"}).status_code == 422
    evaluation = client.get("/rag/eval").json()
    assert evaluation["available"] is False
    assert "no evalúan" in evaluation["note"]


def test_public_chat_and_sse_return_passages_without_provider(public_runtime):
    client = TestClient(api_main.app)
    response = client.post("/rag/chat", json={"question": "deuda nominal"})
    assert response.status_code == 200
    body = response.json()
    assert body["collection"] == "metodo" and body["passages"]
    assert body["provider"] is None and body["model"] is None
    assert "pasajes" in body["answer"]
    stream = client.post("/rag/chat/stream", json={"question": "deuda nominal"})
    assert stream.status_code == 200
    assert "event: passages" in stream.text and "event: done" in stream.text
    assert '"collection": "metodo"' in stream.text
    for endpoint in ("/rag/chat", "/rag/chat/stream"):
        assert client.post(endpoint, json={"question": "deuda", "collection": "libros"}).status_code == 422


def test_public_empty_retrieval_abstains(public_runtime):
    result = chat.ask("zzzxnonexistent")
    assert result.passages == [] and result.grounded is False
    assert "no cubre" in result.text


def test_public_startup_does_not_warm_model(public_runtime, monkeypatch):
    import threading
    monkeypatch.setattr(threading, "Thread", lambda *a, **k: pytest.fail("No public model warmup"))
    api_main._warm_embedder()
