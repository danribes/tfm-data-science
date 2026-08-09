"""Hybrid retrieval: FTS5 lexical + sqlite-vec dense, fused with RRF.

Neither half is redundant. Economics questions mix precise terminology — "prima
de riesgo", "regla de Okun", "multiplicador fiscal" — where exact-token matching
wins, with conceptual questions where only embeddings find the right passage.
Reciprocal-rank fusion combines the two rankings without needing the scores to
be on a comparable scale, which they are not.

Retrieval is always scoped to a collection. That is a correctness property, not
an optimisation: a textbook and a YouTube transcript must never be ranked
against each other.
"""
from __future__ import annotations

import re
import sqlite3
import struct
from dataclasses import dataclass, asdict
from typing import Sequence

from rag import config, embed, store


@dataclass(frozen=True)
class Passage:
    chunk_id: int
    text: str
    title: str
    collection: str
    authority: str
    page: int | None
    section: str | None
    score: float
    lexical_rank: int | None
    dense_rank: int | None

    def cite(self) -> str:
        bits = [self.title]
        if self.section:
            bits.append(self.section)
        if self.page:
            bits.append(f"p. {self.page}")
        return " · ".join(bits)

    def to_dict(self) -> dict:
        return {**asdict(self), "cita": self.cite()}


#: FTS5 treats a bare query as a match expression, so user text like
#: "¿qué pasa si r > g?" would be a syntax error. Quoting each token turns the
#: query into a safe OR of literals.
_TOKEN = re.compile(r"\w+", re.UNICODE)


def _fts_query(text: str) -> str:
    toks = [t for t in _TOKEN.findall(text.lower()) if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in toks[:32])


def _lexical(con: sqlite3.Connection, query: str, collection: str,
             limit: int) -> list[int]:
    expr = _fts_query(query)
    if not expr:
        return []
    rows = con.execute(
        "SELECT c.id FROM chunks_fts f"
        " JOIN chunks c ON c.id = f.rowid"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE chunks_fts MATCH ? AND d.collection = ?"
        " ORDER BY bm25(chunks_fts) LIMIT ?",
        (expr, collection, limit),
    ).fetchall()
    return [r[0] for r in rows]


def _dense(con: sqlite3.Connection, query: str, collection: str,
           limit: int) -> list[int]:
    vec = embed.embed_query(query)
    blob = struct.pack(f"{len(vec)}f", *vec)
    # Over-fetch then filter by collection: vec0 KNN cannot join in its own
    # WHERE clause, so a collection with few chunks would otherwise come back
    # empty when another collection dominates the global neighbourhood.
    rows = con.execute(
        "SELECT v.chunk_id FROM chunks_vec v"
        " JOIN chunks c ON c.id = v.chunk_id"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE v.embedding MATCH ? AND k = ? AND d.collection = ?",
        (blob, limit * 4, collection),
    ).fetchall()
    return [r[0] for r in rows][:limit]


def _rrf(rankings: Sequence[tuple[Sequence[int], float]],
         k: int = config.RRF_K) -> dict[int, float]:
    """Weighted reciprocal-rank fusion.

    Weights matter here rather than being a tuning nicety: see config.W_DENSE
    for why an unweighted fusion mis-routes every Spanish query in this corpus.
    """
    scores: dict[int, float] = {}
    for ranking, weight in rankings:
        for pos, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + weight / (k + pos + 1)
    return scores


def search(query: str, collection: str = "libros", top_k: int | None = None,
           con: sqlite3.Connection | None = None) -> list[Passage]:
    """Hybrid search within one collection, best first."""
    if collection not in config.COLLECTIONS:
        raise ValueError(f"colección desconocida: {collection!r}")

    own = con is None
    con = con or store.connect()
    try:
        k = top_k or config.TOP_K
        lex = _lexical(con, query, collection, config.CANDIDATES)
        den = _dense(con, query, collection, config.CANDIDATES)
        if not lex and not den:
            return []

        fused = _rrf([(den, config.W_DENSE), (lex, config.W_LEXICAL)])
        lex_pos = {cid: i for i, cid in enumerate(lex)}
        den_pos = {cid: i for i, cid in enumerate(den)}
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        if not ranked:
            return []

        # Fetch metadata for the whole candidate pool, because the per-document
        # cap below needs to know each chunk's book before choosing the top k.
        ids = [cid for cid, _ in ranked]
        placeholders = ",".join("?" * len(ids))
        rows = {
            r[0]: r for r in con.execute(
                f"SELECT c.id, c.text, c.page, c.section, d.title, d.collection, d.id"
                f" FROM chunks c JOIN documents d ON d.id = c.doc_id"
                f" WHERE c.id IN ({placeholders})", ids)
        }

        authority = config.COLLECTIONS[collection]["authority"]
        out: list[Passage] = []
        per_doc: dict[int, int] = {}
        overflow: list[Passage] = []

        for cid, score in ranked:
            r = rows.get(cid)
            if not r:
                continue
            p = Passage(
                chunk_id=cid, text=r[1], title=r[4], collection=r[5],
                authority=authority, page=r[2], section=r[3], score=round(score, 6),
                lexical_rank=lex_pos.get(cid), dense_rank=den_pos.get(cid),
            )
            doc_id = r[6]
            if per_doc.get(doc_id, 0) < config.MAX_PER_DOCUMENT:
                per_doc[doc_id] = per_doc.get(doc_id, 0) + 1
                out.append(p)
                if len(out) >= k:
                    return out
            else:
                overflow.append(p)

        # Only if diversity could not fill k (a genuinely single-source topic)
        # do we fall back to the capped-out passages.
        out.extend(overflow[: max(0, k - len(out))])
        return out
    finally:
        if own:
            con.close()


def search_all(query: str, collections: Sequence[str] | None = None,
               per_collection: int = 4) -> dict[str, list[Passage]]:
    """Search several collections, keeping the results separated by source."""
    con = store.connect()
    try:
        names = collections or list(config.COLLECTIONS)
        return {n: search(query, n, per_collection, con=con) for n in names}
    finally:
        con.close()


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "¿por qué sube la deuda cuando r supera a g?"
    for coll, hits in search_all(q).items():
        print(f"\n=== {coll} ({config.COLLECTIONS[coll]['authority']}) ===")
        for h in hits:
            print(f"  [{h.score:.4f}] {h.cite()}")
            print(f"      {h.text[:160].replace(chr(10), ' ')}…")
