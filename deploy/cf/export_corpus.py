"""Export the local corpus.db into the two shapes Cloudflare needs.

Vectorize holds the dense side and D1 the text plus its FTS5 index, because
retrieval quality here comes from fusing both and Vectorize alone is dense-only.

The vectors are exported verbatim: they were produced by intfloat/multilingual-e5-large
and a query embedded by any other model is not comparable to them, so the Worker
must embed queries with that same model rather than a Workers AI one.

Usage:
    python deploy/cf/export_corpus.py --out /tmp/cf-export
    python deploy/cf/export_corpus.py --out /tmp/cf-export --collections metodo defensa_tfm
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from rag import store

# Vectorize rejects inserts above 1000 vectors; one shard per request.
SHARD = 1000


def unpack(blob: bytes) -> list[float]:
    """sqlite-vec stores raw little-endian float32."""
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--collections", nargs="*", default=None,
                    help="default: every collection in the database")
    args = ap.parse_args()

    out: Path = args.out
    (out / "vectors").mkdir(parents=True, exist_ok=True)
    con = store.connect()

    where, params = "", []
    if args.collections:
        where = f" WHERE d.collection IN ({','.join('?' * len(args.collections))})"
        params = list(args.collections)

    rows = con.execute(
        "SELECT c.id, c.text, c.page, c.section, d.collection, d.title"
        " FROM chunks c JOIN documents d ON d.id = c.doc_id"
        f"{where} ORDER BY c.id",
        params,
    ).fetchall()
    print(f"{len(rows):,} chunks")

    vecs = dict(con.execute("SELECT chunk_id, embedding FROM chunks_vec").fetchall())
    print(f"{len(vecs):,} vectors in the index")

    # D1 seed: text, citation fields and the FTS5 mirror.
    ddl = out / "schema.sql"
    ddl.write_text(
        "CREATE TABLE IF NOT EXISTS chunks (\n"
        "  id INTEGER PRIMARY KEY,\n"
        "  collection TEXT NOT NULL,\n"
        "  title TEXT NOT NULL,\n"
        "  page INTEGER,\n"
        "  section TEXT,\n"
        "  text TEXT NOT NULL\n"
        ");\n"
        "CREATE INDEX IF NOT EXISTS chunks_collection ON chunks(collection);\n"
        "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(\n"
        "  text, content='chunks', content_rowid='id', tokenize='unicode61'\n"
        ");\n",
        encoding="utf-8",
    )

    def sql_str(v: object) -> str:
        if v is None:
            return "NULL"
        return "'" + str(v).replace("'", "''") + "'"

    n_missing = 0
    with (out / "chunks.sql").open("w", encoding="utf-8") as fh:
        fh.write("BEGIN TRANSACTION;\n")
        for cid, text, page, section, collection, title in rows:
            fh.write(
                "INSERT OR REPLACE INTO chunks (id,collection,title,page,section,text)"
                f" VALUES ({cid},{sql_str(collection)},{sql_str(title)},"
                f"{'NULL' if page is None else int(page)},{sql_str(section)},{sql_str(text)});\n"
            )
        fh.write("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild');\n")
        fh.write("COMMIT;\n")

    shard, written = [], 0
    def flush(idx: int) -> None:
        if not shard:
            return
        p = out / "vectors" / f"vectors-{idx:05d}.ndjson"
        with p.open("w", encoding="utf-8") as fh:
            for line in shard:
                fh.write(line + "\n")
        shard.clear()

    for cid, _text, page, section, collection, _title in rows:
        blob = vecs.get(cid)
        if blob is None:
            n_missing += 1
            continue
        shard.append(json.dumps({
            "id": str(cid),
            "values": unpack(blob),
            "metadata": {"collection": collection,
                         "page": page or 0,
                         "section": (section or "")[:200]},
        }, ensure_ascii=False))
        written += 1
        if len(shard) >= SHARD:
            flush(written // SHARD)
    flush(written // SHARD + 1)

    print(f"wrote {written:,} vectors in {len(list((out / 'vectors').glob('*.ndjson')))} shards")
    if n_missing:
        print(f"WARNING: {n_missing:,} chunks had no vector and were skipped")
    print(f"out: {out}")


if __name__ == "__main__":
    main()
