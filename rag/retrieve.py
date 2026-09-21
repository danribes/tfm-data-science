"""Hybrid retrieval: FTS5 lexical + sqlite-vec dense, fused with RRF.

Neither half is redundant. Economics questions mix precise terminology — "prima
de riesgo", "regla de Okun", "multiplicador fiscal" — where exact-token matching
wins, with conceptual questions where only embeddings find the right passage.
Reciprocal-rank fusion combines the two rankings without needing the scores to
be on a comparable scale, which they are not.

Retrieval never ranks one authority against another. That is a correctness
property, not an optimisation: a textbook and a YouTube transcript must never
compete in the same list. Every passage carries its own collection and
authority so the citation always says where it came from.

Only the academic corpus answers by default. An earlier version fused the
manuals with the project's own documentation, but the bulk of that
documentation was development notes, so a question about economics came back
citing an implementation plan as if it were bibliography. A piece of work
cannot cite itself as authority.
"""
from __future__ import annotations

import contextvars
import re
import sqlite3
import struct
from dataclasses import dataclass, asdict
from typing import Sequence

from rag import config, glossary, store


#: Si el sondeo denso cayó durante la consulta en curso.
#:
#: `search` devuelve una lista de pasajes y muchos sitios dependen de eso, así
#: que el aviso viaja aparte en lugar de cambiar el tipo de retorno. Es una
#: variable de contexto y no un global porque el servidor atiende varias
#: peticiones a la vez: un booleano de módulo mezclaría la degradación de una
#: consulta con la de otra.
_DEGRADED: contextvars.ContextVar[list[bool] | None] = contextvars.ContextVar(
    "rag_degraded", default=None)


def _note_degraded() -> None:
    box = _DEGRADED.get()
    if box is not None:
        box[0] = True


@dataclass(frozen=True)
class Retrieval:
    """Los pasajes y, con ellos, con qué recuperador se obtuvieron.

    Existe porque `retrieval_mode` en la respuesta era el valor estático de la
    configuración: decía «hybrid» mientras se servía BM25, y el despliegue
    estuvo semanas así sin que nada lo delatara. Un campo que informa de la
    intención en vez del hecho es peor que no tenerlo.
    """
    passages: list[Passage]
    degraded: bool

    @property
    def mode(self) -> str:
        """Lo que de verdad respondió esta consulta."""
        if config.PUBLIC_MODE:
            return "lexical"
        return "lexical_degraded" if self.degraded else "hybrid"


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
        # `citable` viaja con el pasaje y no lo pone cada llamante: se anadio
        # primero solo en el chat y /rag/search siguio devolviendo todo como
        # citable, que es justo el error que este campo existe para evitar.
        return {**asdict(self), "cita": self.cite(),
                "citable": config.is_citable(self.collection)}


#: FTS5 treats a bare query as a match expression, so user text like
#: "¿qué pasa si r > g?" would be a syntax error. Quoting each token turns the
#: query into a safe OR of literals.
_TOKEN = re.compile(r"\w+", re.UNICODE)


def _fts_query(text: str) -> str:
    toks = [t for t in _TOKEN.findall(text.lower()) if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in toks[:32])


def _lexical(con: sqlite3.Connection, query: str, collection: str,
             limit: int) -> list[int]:
    # BM25 cannot cross a language, so a Spanish question can never reach an
    # English textbook without the English terms being in the query.
    expr = _fts_query(glossary.expand(query) if config.USE_GLOSSARY else query)
    if not expr:
        return []
    # Algunas colecciones sólo citan parte de sus documentos: ver
    # config.CITABLE_DOCS. El filtro va en las dos mitades del recuperador,
    # porque dejarlo en una sola haría que el documento excluido apareciera por
    # la otra.
    extra, titulos = config.citable_clause(collection)
    rows = con.execute(
        "SELECT c.id FROM chunks_fts f"
        " JOIN chunks c ON c.id = f.rowid"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE chunks_fts MATCH ? AND d.collection = ?" + extra +
        " ORDER BY bm25(chunks_fts) LIMIT ?",
        (expr, collection, *titulos, limit),
    ).fetchall()
    return [r[0] for r in rows]


def _dense(con: sqlite3.Connection, query: str, collection: str,
           limit: int, text: str | None = None) -> list[int]:
    from rag import embed

    vec = embed.embed_query(text if text is not None else query)
    blob = struct.pack(f"{len(vec)}f", *vec)
    # Over-fetch then filter by collection: vec0 KNN cannot join in its own
    # WHERE clause, so a collection with few chunks would otherwise come back
    # empty when another collection dominates the global neighbourhood.
    extra, titulos = config.citable_clause(collection)
    rows = con.execute(
        "SELECT v.chunk_id FROM chunks_vec v"
        " JOIN chunks c ON c.id = v.chunk_id"
        " JOIN documents d ON d.id = c.doc_id"
        " WHERE v.embedding MATCH ? AND k = ? AND d.collection = ?" + extra,
        (blob, limit * 4, collection, *titulos),
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
        if weight <= 0:
            continue
        for pos, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + weight / (k + pos + 1)
    return scores


def search_reported(query: str, collection: str | None = None,
                    top_k: int | None = None,
                    con: sqlite3.Connection | None = None) -> Retrieval:
    """`search`, diciendo además con qué recuperador se respondió.

    Se ofrece aparte en lugar de cambiar `search`: una decena de sitios esperan
    una lista de pasajes, y la cadena de citación no gana nada envolviéndola.
    Quien publica una respuesta al lector —la API— usa ésta.
    """
    caja = [False]
    ficha = _DEGRADED.set(caja)
    try:
        passages = search(query, collection, top_k, con=con)
    finally:
        _DEGRADED.reset(ficha)
    return Retrieval(passages=passages, degraded=caja[0])


def search(query: str, collection: str | None = None, top_k: int | None = None,
           con: sqlite3.Connection | None = None) -> list[Passage]:
    """Search one collection using the explicitly configured retrieval mode."""
    collection = config.DEFAULT_COLLECTION if collection is None else collection
    if collection not in config.COLLECTIONS:
        raise ValueError(f"colección desconocida: {collection!r}")
    own = con is None
    con = con or store.connect()
    try:
        k = top_k or config.TOP_K
        lex = (_lexical(con, query, collection, config.CANDIDATES)
               if config.PUBLIC_MODE or config.W_LEXICAL > 0 else [])

        def dense_or_lexical(text: str | None = None) -> list[int]:
            """A dense probe that cannot take the whole query down with it.

            When the encoder is hosted, retrieval gains a network dependency,
            and a timeout there must not turn a working corpus into an error
            page. The lexical half still answers. It answers worse, and
            `degraded` on the response says so rather than letting a quietly
            halved system look healthy.
            """
            nonlocal degraded
            try:
                return _dense(con, query, collection, config.CANDIDATES, text=text)
            except Exception:
                degraded = True
                return []

        degraded = False
        den = (dense_or_lexical()
               if not config.PUBLIC_MODE and config.W_DENSE > 0 else [])

        # A second dense probe, in English only.
        #
        # Appending the translation to the Spanish query does not work: fifteen
        # Spanish tokens drown three English ones and the vector barely moves.
        # Embedding the terminology on its own gives the English literature a
        # full-strength ranking of its own, which fusion can then weigh against
        # the Spanish one instead of averaging the two into neither.
        terms = (glossary.english_terms(query)
                 if not config.PUBLIC_MODE and config.USE_GLOSSARY else [])
        den_en = (dense_or_lexical(text=", ".join(terms))
                  if not config.PUBLIC_MODE and terms and config.W_DENSE_EN > 0
                  else [])
        if degraded:
            # A los registros de quien opera el servicio, y al que pregunta:
            # `search_reported` lo recoge y la API lo publica por consulta.
            _note_degraded()
            print("rag: dense probe unavailable, answering lexically",
                  file=__import__("sys").stderr)

        if not lex and not den and not den_en:
            return []

        fused = _rrf([(den, config.W_DENSE), (den_en, config.W_DENSE_EN),
                      (lex, 1.0 if config.PUBLIC_MODE else config.W_LEXICAL)])
        lex_pos = {cid: i for i, cid in enumerate(lex)}
        den_pos = {cid: i for i, cid in enumerate(den)}
        for cid, i in ((c, i) for i, c in enumerate(den_en)):
            den_pos.setdefault(cid, i)
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
