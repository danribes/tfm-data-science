"""Atomic source refresh on a synthetic SQLite/FTS/vector index, offline."""
from __future__ import annotations

import pytest

from rag import config, embed, extract, ingest, store


@pytest.fixture()
def corpus(tmp_path, monkeypatch):
    con = store.connect(tmp_path / "test.db")
    store.init_schema(con, dim=4)
    monkeypatch.setattr(embed, "embed_passages", lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts])
    source = tmp_path / "method.md"
    source.write_text("legacytoken una explicación anterior del método. " * 12)
    doc = {"path": source, "title": "Method", "collection": "metodo", "meta": {}}
    assert ingest.ingest_document(con, doc)[1] == "ok"
    yield con, source, doc
    con.close()


def snapshot(con):
    return {
        "documents": con.execute("SELECT * FROM documents ORDER BY id").fetchall(),
        "chunks": con.execute("SELECT * FROM chunks ORDER BY id").fetchall(),
        "vectors": con.execute("SELECT chunk_id, embedding FROM chunks_vec ORDER BY chunk_id").fetchall(),
        "legacy_fts": con.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH 'legacytoken'").fetchall(),
    }


def add_other(con, collection, source, title, sha):
    doc_id = store.add_document(con, collection=collection, title=title,
                                source_path=source, sha256=sha, pages=1)
    store.add_chunks(con, doc_id, [{"ordinal": 0, "page": 1, "text": "unrelatedtoken " * 30}],
                     [[0.0, 1.0, 0.0, 0.0]])
    con.commit()
    return doc_id


def test_unchanged_source_skips_extraction_and_embeddings(corpus, monkeypatch):
    con, _, doc = corpus
    before = snapshot(con)
    def unexpected(*args, **kwargs):
        raise AssertionError("unchanged content must not be processed")
    monkeypatch.setattr(embed, "embed_passages", unexpected)
    monkeypatch.setattr(extract, "markdown_pages", unexpected)
    assert ingest.ingest_document(con, doc) == (0, "ya-indexado")
    assert snapshot(con) == before


def test_changed_source_replaces_text_fts_vectors_and_preserves_other_sources(corpus):
    con, source, doc = corpus
    old_ids = [row[0] for row in con.execute("SELECT id FROM chunks")]
    # The same spelling in another collection and another path in this
    # collection must both survive the scoped replacement.
    other_ids = [add_other(con, "defensa_tfm", str(source), "Other collection", "other-sha"),
                 add_other(con, "metodo", "/different-source.md", "Other path", "different-sha")]
    other_rows = con.execute("SELECT * FROM documents WHERE id IN (?,?)", other_ids).fetchall()
    source.write_text("replacementtoken explicación revisada y vigente del método. " * 12)
    assert ingest.ingest_document(con, doc)[1] == "ok"
    assert con.execute("SELECT count(*) FROM documents WHERE collection='metodo' AND source_path=?",
                       (str(source),)).fetchone()[0] == 1
    assert con.execute("SELECT sha256 FROM documents WHERE collection='metodo' AND source_path=?",
                       (str(source),)).fetchone()[0] == extract.sha256_file(source)
    assert con.execute("SELECT * FROM documents WHERE id IN (?,?)", other_ids).fetchall() == other_rows
    assert con.execute("SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'legacytoken'").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'replacementtoken'").fetchone()[0] == 1
    for old_id in old_ids:
        assert con.execute("SELECT 1 FROM chunks WHERE id=?", (old_id,)).fetchone() is None
        assert con.execute("SELECT 1 FROM chunks_vec WHERE chunk_id=?", (old_id,)).fetchone() is None
    assert con.execute("SELECT count(*) FROM chunks_vec").fetchone()[0] == 3
    assert con.execute("SELECT count(*) FROM chunks_fts").fetchone()[0] == 3


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_failed_later_batch_rolls_back_the_complete_replacement(corpus, monkeypatch, failure):
    con, source, doc = corpus
    before = snapshot(con)
    source.write_text("replacementtoken " * 100)
    monkeypatch.setattr(config, "BATCH_SIZE", 1)
    monkeypatch.setattr(extract, "chunk_pages", lambda pages: iter(
        {"ordinal": i, "page": 1, "text": "replacementtoken " * 30} for i in range(5)))
    calls = 0
    def fail_second_batch(texts):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise failure("synthetic failure after a completed batch")
        return [[0.0, 0.0, 1.0, 0.0] for _ in texts]
    monkeypatch.setattr(embed, "embed_passages", fail_second_batch)
    with pytest.raises(failure):
        ingest.ingest_document(con, doc)
    assert calls == 2
    assert snapshot(con) == before
    assert con.execute("SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'replacementtoken'").fetchone()[0] == 0


def test_empty_replacement_keeps_previous_complete_version(corpus):
    con, source, doc = corpus
    before = snapshot(con)
    source.write_text("")
    assert ingest.ingest_document(con, doc) == (0, "sin-texto")
    assert snapshot(con) == before


def test_force_cannot_delete_content_owned_by_another_collection(corpus, tmp_path):
    con, source, _ = corpus
    before = snapshot(con)
    same_content = tmp_path / "copy.md"
    same_content.write_bytes(source.read_bytes())
    other = {"path": same_content, "title": "Copy", "collection": "defensa_tfm", "meta": {}}
    with pytest.raises(ValueError, match="otra fuente o colección"):
        ingest.ingest_document(con, other, force=True)
    assert snapshot(con) == before


def test_previous_duplicate_versions_of_same_path_are_cleaned(corpus):
    con, source, doc = corpus
    add_other(con, "metodo", str(source), "An older version", "older-source-hash")
    # Even with an unchanged current hash, legacy duplicates must be removed.
    assert ingest.ingest_document(con, doc)[1] == "ok"
    assert con.execute("SELECT count(*) FROM documents").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM chunks_vec").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'unrelatedtoken'").fetchone()[0] == 0


def test_book_manifest_optional_provenance_survives_ingestion(tmp_path, monkeypatch):
    import csv
    import json

    source = tmp_path / "Methods reference.md"
    source.write_text("A complete methods reference with useful source attribution. " * 12)
    manifest = tmp_path / "CORPUS_MANIFEST.csv"
    row = {"file": source.name, "mb": "0.01", "sha256_16": "unused",
           "topic": "statistical_learning", "include": "si", "note": "",
           "source_url": "https://example.org/author/reference.pdf",
           "download_url": "https://example.org/author/reference.pdf",
           "authors": "Author One; Author Two", "year": "2023", "edition": "1",
           "publisher": "Academic Publisher", "language": "en",
           "license": "", "availability": "author-hosted PDF; no reuse license stated",
           "retrieved_at": "2026-09-20", "downloaded_at": "2026-09-20",
           "accessed_at": "2026-09-20", "sha256": extract.sha256_file(source), "notes": ""}
    with manifest.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    monkeypatch.setattr(config, "BOOKS_DIR", tmp_path)
    monkeypatch.setattr(config, "BOOKS_MANIFEST", manifest)
    monkeypatch.setattr(embed, "embed_passages", lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts])
    documents = list(ingest._books())
    assert len(documents) == 1
    document = documents[0]
    assert document["collection"] == "libros"
    assert "license" not in document["meta"]  # Downloadability does not infer a license.
    con = store.connect(tmp_path / "test.db")
    try:
        store.init_schema(con, dim=4)
        assert ingest.ingest_document(con, document)[1] == "ok"
        meta, sha = con.execute("SELECT meta, sha256 FROM documents").fetchone()
        metadata = json.loads(meta)
        for field in ingest._BOOK_METADATA_FIELDS:
            if row[field]:
                assert metadata[field] == row[field]
        assert metadata["topic"] == "statistical_learning"
        assert sha == extract.sha256_file(source)  # Full content hash is computed locally.
    finally:
        con.close()


def test_legacy_book_manifest_remains_compatible(tmp_path, monkeypatch):
    source = tmp_path / "Old reference.md"
    source.write_text("Existing source")
    manifest = tmp_path / "CORPUS_MANIFEST.csv"
    manifest.write_text("file,mb,sha256_16,topic,include,note\n"
                        "Old reference.md,0.1,oldhash,methods,si,legacy\n")
    monkeypatch.setattr(config, "BOOKS_DIR", tmp_path)
    monkeypatch.setattr(config, "BOOKS_MANIFEST", manifest)
    documents = list(ingest._books())
    assert documents == [{"path": source, "title": "Old reference", "collection": "libros",
                          "meta": {"topic": "methods", "note": "legacy"}}]
