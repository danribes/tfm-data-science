"""Corpus ingestion — resumable, one document at a time.

Run:  .venv/bin/python -m rag.ingest --collection libros
      .venv/bin/python -m rag.ingest --all --limit 2      (smoke test first)

Each document is committed atomically before the next begins. Unchanged source
hashes are skipped; changed sources replace the old document and all its indexes
within the same collection. A failed/interrupted document retains its previous
complete version and can be retried; earlier documents remain committed.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Iterator

from rag import config, embed, extract, store


_BOOK_METADATA_FIELDS = (
    "source_url", "download_url", "authors", "year", "edition", "publisher", "language",
    "license", "availability", "retrieved_at", "downloaded_at", "accessed_at",
    "sha256", "note", "notes",
)


def _books() -> Iterator[dict]:
    """Indexable manifest rows, including optional source/bibliographic metadata.

    Older manifests need only their existing columns. Availability and license
    remain separate, explicit source statements: a downloadable PDF is not
    automatically assigned an open license.
    """
    if not config.BOOKS_MANIFEST.exists():
        print(f"!! sin manifiesto: {config.BOOKS_MANIFEST}", file=sys.stderr)
        return
    with config.BOOKS_MANIFEST.open(encoding="utf-8", newline="") as manifest:
        for row in csv.DictReader(manifest):
            if row.get("include", "").strip().lower() not in {"si", "sí", "yes", "true"}:
                continue
            path = config.BOOKS_DIR / row["file"]
            if not path.exists():
                print(f"!! falta el fichero: {row['file']}", file=sys.stderr)
                continue
            meta = {"topic": row.get("topic", "")}
            for field in _BOOK_METADATA_FIELDS:
                value = (row.get(field) or "").strip()
                if value:
                    meta[field] = value
            yield {"path": path, "title": Path(row["file"]).stem,
                   "collection": "libros", "meta": meta}


def _crack23() -> Iterator[dict]:
    """Transcripts and summaries. Tagged as opinion at the collection level."""
    for sub, kind in (("markdown", "transcripcion"), ("summaries", "resumen")):
        d = config.CRACK_DIR / sub
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.md")):
            yield {"path": path, "title": path.stem, "collection": "crack23",
                   "meta": {"kind": kind}}


def _metodo() -> Iterator[dict]:
    """The project's own method docs — lets the chat cite its own provenance."""
    repo = Path(__file__).resolve().parents[1]
    for rel in ("README.md", "docs/MEMORIA_TFM.md", "docs/RESULTS.md",
                "docs/METHODOLOGY_CHANGES.md", "docs/REPRODUCIBILITY.md",
                "docs/superpowers/specs", "docs/superpowers/plans"):
        p = repo / rel
        if p.is_file():
            yield {"path": p, "title": p.stem, "collection": "metodo",
                   "meta": {"document_status": "current"}}
        elif p.is_dir():
            for f in sorted(p.rglob("*.md")):
                yield {"path": f, "title": f.stem, "collection": "metodo",
                       "meta": {"document_status": "historical_design"}}


def _defensa_tfm() -> Iterator[dict]:
    """The TFM defense guide and methodological Q&A collection."""
    repo = Path(__file__).resolve().parents[1]
    p = repo / "docs" / "DEFENSA_TFM.md"
    if p.is_file():
        yield {"path": p, "title": p.stem, "collection": "defensa_tfm", "meta": {"topic": "defensa"}}


SOURCES = {"libros": _books, "crack23": _crack23, "metodo": _metodo, "defensa_tfm": _defensa_tfm}


def ingest_document(con, doc: dict, *, force: bool = False) -> tuple[int, str]:
    """Atomically replace a collection/source path; return (chunks, status).

    The schema still has global content-hash uniqueness. Identical content
    owned by a different source is reported explicitly and never deleted.
    Paths use the source manifest's spelling, preserving existing index keys.
    """
    path: Path = doc["path"]
    sha = extract.sha256_file(path)
    collection, source_path = doc["collection"], str(path)
    existing = con.execute(
        "SELECT id, sha256 FROM documents WHERE collection=? AND source_path=?",
        (collection, source_path),
    ).fetchall()
    if len(existing) == 1 and existing[0][1] == sha and not force:
        return 0, "ya-indexado"
    owner = con.execute("SELECT id FROM documents WHERE sha256=?", (sha,)).fetchone()
    if owner and owner[0] not in {row[0] for row in existing}:
        raise ValueError("El contenido ya pertenece a otra fuente o colección; no se modifica su índice.")

    # A savepoint also works when the caller already owns an outer transaction.
    # Never commit individual batches: that would expose partial replacements
    # and make a failed embedding erase the last working version.
    con.execute("SAVEPOINT rag_ingest_document")
    written = 0
    max_page = 0
    batch: list[dict] = []

    def flush() -> None:
        nonlocal written, batch
        if not batch:
            return
        vectors = embed.embed_passages([c["text"] for c in batch])
        if len(vectors) != len(batch):
            raise ValueError("El lote de embeddings está incompleto")
        written += store.add_chunks(con, doc_id, batch, vectors)
        batch = []

    try:
        for old_id, _ in existing:
            store.delete_document_id(con, old_id, commit=False)
        doc_id = store.add_document(
            con, collection=collection, title=doc["title"], source_path=source_path,
            sha256=sha, pages=0, meta=doc.get("meta"), commit=False,
        )
        pages = (extract.pdf_pages(path) if path.suffix.lower() == ".pdf"
                 else extract.markdown_pages(path))
        for ch in extract.chunk_pages(pages):
            max_page = max(max_page, ch.get("page") or 0)
            batch.append(ch)
            if len(batch) >= config.BATCH_SIZE * 4:
                flush()
        flush()
        if not written:
            # Empty extraction must not erase a previous usable version.
            con.execute("ROLLBACK TO SAVEPOINT rag_ingest_document")
            con.execute("RELEASE SAVEPOINT rag_ingest_document")
            return 0, "sin-texto"
        con.execute("UPDATE documents SET pages=? WHERE id=?", (max_page, doc_id))
        con.execute("RELEASE SAVEPOINT rag_ingest_document")
    except BaseException:
        # Includes KeyboardInterrupt: the interactive retry has the same
        # atomic behavior as SQLite recovery after a terminated process.
        con.execute("ROLLBACK TO SAVEPOINT rag_ingest_document")
        con.execute("RELEASE SAVEPOINT rag_ingest_document")
        raise
    return written, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingesta del corpus RAG")
    ap.add_argument("--collection", choices=sorted(SOURCES), action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, help="solo N documentos (prueba)")
    ap.add_argument("--force", action="store_true", help="re-indexar existentes")
    ap.add_argument("--stats", action="store_true", help="solo mostrar estado")
    args = ap.parse_args()

    con = store.connect()
    store.init_schema(con)

    if args.stats:
        st = store.stats(con)
        print(f"documentos {st['documents']} · fragmentos {st['chunks']}")
        for coll, v in sorted(st["by_collection"].items()):
            print(f"  {coll}: {v['documents']} docs, {v['chunks']} fragmentos")
        return 0

    names = args.collection or (sorted(SOURCES) if args.all else ["libros"])
    docs = [d for n in names for d in SOURCES[n]()]
    if args.limit:
        docs = docs[: args.limit]

    print(f"modelo {config.MODEL_NAME} · dispositivo {config.resolve_device()} "
          f"· batch {config.BATCH_SIZE}")

    # Load the model before touching the corpus. A model that cannot load fails
    # identically on all 452 documents, which previously burned 14 minutes to
    # produce 451 copies of the same error and an empty database.
    try:
        model = embed.get_model()
        dim = model.get_sentence_embedding_dimension()
    except Exception as exc:
        print(f"!! el modelo no carga: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if dim != config.EMBED_DIM:
        print(f"!! dimensión {dim} ≠ EMBED_DIM {config.EMBED_DIM}: el índice "
              f"vectorial se creó para otra dimensión. Borra la base o ajusta "
              f"EVO_RAG_DIM.", file=sys.stderr)
        return 2

    print(f"{len(docs)} documentos en {names}\n")

    total, failed, t0 = 0, 0, time.time()
    for i, d in enumerate(docs, 1):
        label = d["title"][:64]
        print(f"[{i}/{len(docs)}] {label}", flush=True)
        try:
            n, status = ingest_document(con, d, force=args.force)
        except KeyboardInterrupt:
            print("\ninterrumpido — lo ya indexado se conserva")
            break
        except Exception as exc:
            failed += 1
            print(f"    ERROR {type(exc).__name__}: {exc}", flush=True)
            continue
        total += n
        print(f"    {status}" + (f" · {n} fragmentos" if n else ""), flush=True)
        embed._free_cuda()      # between documents, not between batches

    dt = time.time() - t0
    st = store.stats(con)
    print(f"\n{total} fragmentos nuevos en {dt:.0f}s · fallos {failed}")
    print(f"total: {st['documents']} documentos, {st['chunks']} fragmentos")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
