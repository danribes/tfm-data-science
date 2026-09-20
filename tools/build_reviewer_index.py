"""Build the reviewer index: every collection, lexical retrieval only.

    PYTHONPATH=. python tools/build_reviewer_index.py --out /tmp/reviewer.db

The deployed Space runs without torch, sentence-transformers or sqlite-vec, so
the dense half of the local corpus cannot be used there and shipping it would
add ninety megabytes of unreadable bytes. This copies the chunk text and
rebuilds the FTS5 index, and nothing else.

That makes the reviewer index a *different retrieval system* from the local
one: BM25 alone, where the documented hit@8 was measured with hybrid fusion.
Anyone reading results from it should know that, and the README says so.

The output holds third-party copyrighted text. It is never committed. It is
served openly on the current deployment by explicit decision of the author;
RESTRICTED_COLLECTIONS in rag/config.py is what puts it back behind a token.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from rag import config


def build(source: Path, out: Path, *, lexical_only: bool = False) -> dict:
    if out.exists():
        out.unlink()
    out.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(out)
    try:
        dst.executescript("""
            CREATE TABLE documents (
              id INTEGER PRIMARY KEY, collection TEXT NOT NULL, title TEXT NOT NULL,
              source_path TEXT NOT NULL, sha256 TEXT NOT NULL, pages INTEGER,
              meta TEXT, ingested_at TEXT
            );
            CREATE TABLE chunks (
              id INTEGER PRIMARY KEY, doc_id INTEGER NOT NULL REFERENCES documents(id),
              ordinal INTEGER NOT NULL, page INTEGER, section TEXT, text TEXT NOT NULL
            );
            CREATE INDEX chunks_doc ON chunks(doc_id);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
              text, content='chunks', content_rowid='id', tokenize='unicode61'
            );
        """)
        docs = src.execute(
            "SELECT id, collection, title, source_path, sha256, pages, meta, ingested_at"
            " FROM documents").fetchall()
        dst.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)", docs)

        rows = src.execute(
            "SELECT id, doc_id, ordinal, page, section, text FROM chunks").fetchall()
        dst.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?)", rows)
        dst.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        dst.commit()
        dst.execute("VACUUM")
        dst.commit()

        if not lexical_only:
            # A plain copy: re-embedding 21.000 chunks to move them would be
            # hours of GPU for bytes that already exist and are identical.
            import sqlite_vec
            dst.enable_load_extension(True)
            sqlite_vec.load(dst)
            dst.enable_load_extension(False)
            dst.execute("CREATE VIRTUAL TABLE chunks_vec USING vec0("
                        f"chunk_id INTEGER PRIMARY KEY, embedding float[{config.EMBED_DIM}])")
            src.enable_load_extension(True)
            sqlite_vec.load(src)
            src.enable_load_extension(False)
            vecs = src.execute("SELECT chunk_id, embedding FROM chunks_vec").fetchall()
            dst.executemany("INSERT INTO chunks_vec(chunk_id, embedding) VALUES (?,?)", vecs)
            dst.commit()

        by: dict[str, int] = {}
        for coll, n in dst.execute(
                "SELECT d.collection, COUNT(*) FROM chunks c"
                " JOIN documents d ON d.id = c.doc_id GROUP BY 1"):
            by[coll] = n
        return {"documents": len(docs), "chunks": len(rows), "by_collection": by}
    finally:
        src.close()
        dst.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=config.DB_PATH)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--lexical-only", action="store_true",
                    help="omit the vectors: smaller, and a different retriever")
    args = ap.parse_args()

    if not args.source.is_file():
        print(f"no corpus at {args.source}")
        return 1
    stats = build(args.source, args.out, lexical_only=args.lexical_only)
    size = args.out.stat().st_size / 1e6
    print(f"{args.out}  {size:.0f} MB")
    print(f"  {stats['documents']} documents, {stats['chunks']} chunks")
    for coll, n in sorted(stats["by_collection"].items()):
        print(f"    {coll:14} {n}")
    print("  lexical only — BM25, a different retriever from the local one"
          if args.lexical_only else
          "  vectors included — same hybrid retrieval as local, given HF_TOKEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
