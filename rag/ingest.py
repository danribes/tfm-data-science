"""Corpus ingestion — resumable, one document at a time.

Run:  .venv/bin/python -m rag.ingest --collection libros
      .venv/bin/python -m rag.ingest --all --limit 2      (smoke test first)

Design constraint: this must survive being killed. Each document is committed
before the next begins and keyed by content hash, so a re-run skips what is
already in and picks up where it stopped. There is no "start over" cost.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Iterator

from rag import config, embed, extract, store


def _books() -> Iterator[dict]:
    """Indexable rows of CORPUS_MANIFEST.csv, in manifest order."""
    if not config.BOOKS_MANIFEST.exists():
        print(f"!! sin manifiesto: {config.BOOKS_MANIFEST}", file=sys.stderr)
        return
    for row in csv.DictReader(open(config.BOOKS_MANIFEST, encoding="utf-8")):
        if row.get("include", "").strip().lower() not in {"si", "sí", "yes", "true"}:
            continue
        path = config.BOOKS_DIR / row["file"]
        if not path.exists():
            print(f"!! falta el fichero: {row['file']}", file=sys.stderr)
            continue
        yield {"path": path, "title": Path(row["file"]).stem,
               "collection": "libros", "meta": {"topic": row.get("topic", "")}}


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
    for rel in ("README.md", "docs/superpowers/specs", "docs/superpowers/plans"):
        p = repo / rel
        if p.is_file():
            yield {"path": p, "title": p.stem, "collection": "metodo", "meta": {}}
        elif p.is_dir():
            for f in sorted(p.rglob("*.md")):
                yield {"path": f, "title": f.stem, "collection": "metodo", "meta": {}}


SOURCES = {"libros": _books, "crack23": _crack23, "metodo": _metodo}


def ingest_document(con, doc: dict, *, force: bool = False) -> tuple[int, str]:
    """Returns (chunks_written, status)."""
    path: Path = doc["path"]
    sha = extract.sha256_file(path)

    if store.document_exists(con, sha):
        if not force:
            return 0, "ya-indexado"
        store.delete_document(con, sha)

    pages = (extract.pdf_pages(path) if path.suffix.lower() == ".pdf"
             else extract.markdown_pages(path))

    doc_id = store.add_document(
        con, collection=doc["collection"], title=doc["title"],
        source_path=str(path), sha256=sha, pages=0, meta=doc.get("meta"),
    )

    written = 0
    max_page = 0
    batch: list[dict] = []

    def flush() -> None:
        nonlocal written, batch
        if not batch:
            return
        vectors = embed.embed_passages([c["text"] for c in batch])
        written += store.add_chunks(con, doc_id, batch, vectors)
        con.commit()          # commit per batch: a kill loses at most one batch
        batch = []

    try:
        for ch in extract.chunk_pages(pages):
            max_page = max(max_page, ch.get("page") or 0)
            batch.append(ch)
            if len(batch) >= config.BATCH_SIZE * 4:
                flush()
        flush()
    except Exception:
        # Leave nothing half-written: a partial document would be silently
        # under-retrieved forever.
        con.rollback()
        store.delete_document(con, sha)
        raise

    if not written:
        # A document that yielded no text is not ingested, it only looks
        # ingested: the row counts towards "473 documentos" while no search can
        # ever reach it. Scanned PDFs with no text layer land here — every page
        # loads and every page is empty. Dropping the row keeps the count
        # honest and lets a later run retry the file, because the sha is what
        # `document_exists` checks.
        con.rollback()
        store.delete_document(con, sha)
        con.commit()
        return 0, "sin-texto"

    con.execute("UPDATE documents SET pages=? WHERE id=?", (max_page, doc_id))
    con.commit()
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
