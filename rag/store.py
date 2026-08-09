"""SQLite store: chunk text, FTS5 lexical index, and sqlite-vec dense index.

One file, three indexes, no daemon. At ~17k chunks this is instant, and it
means the copyrighted books never leave the machine — the whole corpus is a
single file the user controls.

The schema is resumable on purpose: `documents.sha256` is unique, so a re-run
skips books already ingested instead of duplicating them. An ingest killed by
an OOM can simply be restarted.
"""
from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path
from typing import Iterable, Sequence

import sqlite_vec

from rag import config


def _pack(vec: Sequence[float]) -> bytes:
    """sqlite-vec expects raw little-endian float32."""
    return struct.pack(f"{len(vec)}f", *vec)


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path or config.DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.enable_load_extension(True)
    sqlite_vec.load(con)
    con.enable_load_extension(False)
    con.execute("PRAGMA journal_mode=WAL")
    # Bounded cache: the default can grow unhelpfully large mid-ingest.
    con.execute("PRAGMA cache_size=-64000")   # 64 MB
    return con


def init_schema(con: sqlite3.Connection, dim: int = config.EMBED_DIM) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY,
            collection  TEXT NOT NULL,
            title       TEXT NOT NULL,
            source_path TEXT NOT NULL,
            sha256      TEXT NOT NULL UNIQUE,
            pages       INTEGER,
            meta        TEXT,
            ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id       INTEGER PRIMARY KEY,
            doc_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            ordinal  INTEGER NOT NULL,
            page     INTEGER,
            section  TEXT,
            text     TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
        """
    )
    # FTS5 gives the lexical half of hybrid retrieval. Economics queries carry
    # precise terminology ("prima de riesgo", "Okun") where exact-token matching
    # beats embeddings, so this is not redundant with the vector index.
    con.executescript(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text, content='chunks', content_rowid='id', tokenize='unicode61'
        );
        """
    )
    con.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0("
        f"  chunk_id INTEGER PRIMARY KEY, embedding float[{dim}])"
    )
    con.commit()


# ---- writes -----------------------------------------------------------------

def document_exists(con: sqlite3.Connection, sha256: str) -> bool:
    return con.execute(
        "SELECT 1 FROM documents WHERE sha256 = ?", (sha256,)
    ).fetchone() is not None


def add_document(con: sqlite3.Connection, *, collection: str, title: str,
                 source_path: str, sha256: str, pages: int,
                 meta: dict | None = None) -> int:
    cur = con.execute(
        "INSERT INTO documents(collection, title, source_path, sha256, pages, meta)"
        " VALUES(?,?,?,?,?,?)",
        (collection, title, source_path, sha256, pages,
         json.dumps(meta or {}, ensure_ascii=False)),
    )
    con.commit()
    return int(cur.lastrowid)


def add_chunks(con: sqlite3.Connection, doc_id: int,
               chunks: Iterable[dict], embeddings: Sequence[Sequence[float]]) -> int:
    """Insert a batch of chunks with their vectors. Caller commits."""
    n = 0
    for ch, emb in zip(chunks, embeddings):
        cur = con.execute(
            "INSERT INTO chunks(doc_id, ordinal, page, section, text)"
            " VALUES(?,?,?,?,?)",
            (doc_id, ch["ordinal"], ch.get("page"), ch.get("section"), ch["text"]),
        )
        cid = int(cur.lastrowid)
        con.execute("INSERT INTO chunks_fts(rowid, text) VALUES(?,?)", (cid, ch["text"]))
        con.execute("INSERT INTO chunks_vec(chunk_id, embedding) VALUES(?,?)",
                    (cid, _pack(emb)))
        n += 1
    return n


def delete_document(con: sqlite3.Connection, sha256: str) -> None:
    """Remove a document and everything derived from it (for re-ingest)."""
    row = con.execute("SELECT id FROM documents WHERE sha256=?", (sha256,)).fetchone()
    if not row:
        return
    doc_id = row[0]
    ids = [r[0] for r in con.execute("SELECT id FROM chunks WHERE doc_id=?", (doc_id,))]
    for cid in ids:
        con.execute("DELETE FROM chunks_fts WHERE rowid=?", (cid,))
        con.execute("DELETE FROM chunks_vec WHERE chunk_id=?", (cid,))
    con.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
    con.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    con.commit()


# ---- reads ------------------------------------------------------------------

def stats(con: sqlite3.Connection) -> dict:
    out = {"documents": 0, "chunks": 0, "by_collection": {}}
    out["documents"] = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    out["chunks"] = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    for coll, docs, chs in con.execute(
        "SELECT d.collection, COUNT(DISTINCT d.id), COUNT(c.id)"
        " FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id"
        " GROUP BY d.collection"
    ):
        out["by_collection"][coll] = {"documents": docs, "chunks": chs}
    return out
