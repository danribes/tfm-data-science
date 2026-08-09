"""Scoring the retriever against the golden set, and the corpus against itself.

The chat was built and shipped without any measurement of whether it retrieves
the right thing. That is the weakest claim in the whole project: a RAG that is
never scored is indistinguishable from a RAG that works, right up until someone
asks it a question in front of a tribunal.

Three things are measured here, and they fail independently:

  retrieval  — does the document that should answer the question actually
               surface, and how far down the list
  isolation  — does a collection boundary hold, so an opinion channel never
               ranks alongside a textbook
  integrity  — is the corpus itself sound: no document ingested with zero
               chunks, no chunk without an embedding

Numbers are reported, never asserted. A weak score is information about the
corpus and the retriever; hiding it behind a threshold that happens to pass
would defeat the point of building this.
"""
from __future__ import annotations

import json
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from rag import config, golden, retrieve, store
from rag.golden import Question


def _fold(text: str) -> str:
    """Lower-case and strip accents, so a hit does not hinge on a tilde."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


@dataclass
class QuestionResult:
    id: str
    topic: str
    collection: str
    #: 1-based rank of the first passage from an expected document; 0 = missed.
    rank: int
    n_passages: int
    #: Which expected terms were found in the retrieved text.
    terms_found: tuple[str, ...] = ()
    terms_missed: tuple[str, ...] = ()
    #: A forbidden document that surfaced anyway, with its rank.
    trap_hit: str | None = None
    titles: tuple[str, ...] = ()
    top_score: float = 0.0

    @property
    def hit(self) -> bool:
        return self.rank > 0

    @property
    def rr(self) -> float:
        """Reciprocal rank: 1 at the top, 1/2 second, 0 if never found."""
        return 1.0 / self.rank if self.rank else 0.0

    @property
    def term_recall(self) -> float:
        total = len(self.terms_found) + len(self.terms_missed)
        return len(self.terms_found) / total if total else 1.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "topic": self.topic, "collection": self.collection,
            "rank": self.rank, "hit": self.hit, "rr": self.rr,
            "n_passages": self.n_passages, "term_recall": self.term_recall,
            "terms_missed": list(self.terms_missed), "trap_hit": self.trap_hit,
            "titles": list(self.titles), "top_score": self.top_score,
        }


def score_question(q: Question, top_k: int,
                   con: sqlite3.Connection | None = None) -> QuestionResult:
    passages = retrieve.search(q.question, q.collection, top_k, con=con)
    titles = tuple(p.title for p in passages)

    rank = 0
    for i, p in enumerate(passages, start=1):
        if any(_fold(d) in _fold(p.title) for d in q.expect_docs):
            rank = i
            break

    trap = None
    for p in passages:
        if any(_fold(d) in _fold(p.title) for d in q.forbidden_docs):
            trap = p.title
            break

    # A concept counts as present if any of its accepted surface forms appears;
    # it is named by its first form when reported as missing.
    blob = _fold(" ".join(p.text for p in passages))
    found = tuple(forms[0] for forms in q.expect_terms
                  if any(_fold(f) in blob for f in forms))
    missed = tuple(forms[0] for forms in q.expect_terms
                   if not any(_fold(f) in blob for f in forms))

    return QuestionResult(
        id=q.id, topic=q.topic, collection=q.collection, rank=rank,
        n_passages=len(passages), terms_found=found, terms_missed=missed,
        trap_hit=trap, titles=titles,
        top_score=passages[0].score if passages else 0.0,
    )


@dataclass
class RetrievalReport:
    results: list[QuestionResult] = field(default_factory=list)
    top_k: int = config.TOP_K

    def _subset(self, results: list[QuestionResult]) -> dict:
        n = len(results)
        if not n:
            return {"n": 0}
        return {
            "n": n,
            "hit_rate": sum(r.hit for r in results) / n,
            "mrr": sum(r.rr for r in results) / n,
            "top1": sum(r.rank == 1 for r in results) / n,
            "term_recall": sum(r.term_recall for r in results) / n,
        }

    def summary(self) -> dict:
        by_topic: dict[str, dict] = {}
        for r in self.results:
            by_topic.setdefault(r.topic, [])  # type: ignore[arg-type]
        for topic in by_topic:
            by_topic[topic] = self._subset([r for r in self.results if r.topic == topic])
        return {
            "top_k": self.top_k,
            "overall": self._subset(self.results),
            "by_topic": by_topic,
            "misses": [r.id for r in self.results if not r.hit],
            "traps_hit": [{"id": r.id, "document": r.trap_hit}
                          for r in self.results if r.trap_hit],
        }


def evaluate_retrieval(top_k: int | None = None,
                       questions: tuple[Question, ...] | None = None) -> RetrievalReport:
    """Score every answerable golden question. Unanswerable ones are excluded:
    they have no expected document, so a hit rate over them would be a
    category error — they are scored separately, by what the chat says."""
    k = top_k or config.TOP_K
    qs = questions if questions is not None else golden.ANSWERABLE
    con = store.connect()
    try:
        return RetrievalReport([score_question(q, k, con) for q in qs], top_k=k)
    finally:
        con.close()


def evaluate_isolation() -> dict:
    """Every collection boundary, checked on every golden question.

    A textbook and a YouTube transcript answering the same question is the
    failure this corpus was split to prevent. Cheap to check and easy to break
    silently in a refactor of the ranking code.
    """
    con = store.connect()
    leaks: list[dict] = []
    checked = 0
    try:
        for q in golden.GOLDEN:
            for name in config.COLLECTIONS:
                passages = retrieve.search(q.question, name, 4, con=con)
                checked += 1
                strays = {p.collection for p in passages} - {name}
                if strays:
                    leaks.append({"question": q.id, "asked": name,
                                  "returned": sorted(strays)})
    finally:
        con.close()
    return {"searches": checked, "leaks": leaks, "clean": not leaks}


def evaluate_guardrail() -> dict:
    """The advice guardrail, scored in both directions.

    Refusing everything would score perfectly on the probes alone, so the
    questions that must get through are scored in the same pass and reported
    with equal weight.
    """
    from rag import chat

    refused = [q for q in golden.ADVICE_PROBES if chat.refusal_for(q)]
    leaked = [q for q in golden.ADVICE_PROBES if not chat.refusal_for(q)]
    false_positives = [q for q in golden.ADVICE_ALLOWED if chat.refusal_for(q)]
    return {
        "probes": len(golden.ADVICE_PROBES),
        "refused": len(refused),
        "leaked": leaked,
        "allowed": len(golden.ADVICE_ALLOWED),
        "false_positives": false_positives,
        "clean": not leaked and not false_positives,
    }


def audit_corpus(db_path: Path | None = None) -> dict:
    """The corpus checked against itself, independently of any query.

    A document ingested with zero chunks is invisible to every search while
    still being counted in "43 documents" — the kind of gap that survives
    exactly because nothing ever looks for it.
    """
    con = store.connect(db_path)
    try:
        empty = [
            {"collection": c, "title": t}
            for c, t in con.execute(
                """SELECT d.collection, d.title FROM documents d
                   LEFT JOIN chunks c ON c.doc_id = d.id
                   GROUP BY d.id HAVING COUNT(c.id) = 0
                   ORDER BY d.collection, d.title""")
        ]
        n_docs = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        n_chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        n_vec = con.execute("SELECT COUNT(*) FROM chunks_vec").fetchone()[0]
        n_fts = con.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
        tiny = con.execute(
            "SELECT COUNT(*) FROM chunks WHERE length(text) < ?",
            (config.MIN_CHUNK_CHARS,)).fetchone()[0]
        per_collection = {
            c: {"documents": d, "chunks": n}
            for c, d, n in con.execute(
                """SELECT d.collection, COUNT(DISTINCT d.id), COUNT(c.id)
                   FROM documents d LEFT JOIN chunks c ON c.doc_id = d.id
                   GROUP BY d.collection ORDER BY d.collection""")
        }
    finally:
        con.close()

    return {
        "documents": n_docs, "chunks": n_chunks,
        "embeddings": n_vec, "fts_rows": n_fts,
        # Every chunk must be reachable by both retrievers. A shortfall here
        # means one half of the hybrid is silently searching less than it says.
        "embeddings_complete": n_vec == n_chunks,
        "fts_complete": n_fts == n_chunks,
        "empty_documents": empty,
        "chunks_below_minimum": tiny,
        "per_collection": per_collection,
        "clean": not empty and n_vec == n_chunks and n_fts == n_chunks,
    }


def run_all(top_k: int | None = None) -> dict:
    ret = evaluate_retrieval(top_k)
    return {
        "model": config.MODEL_NAME,
        "weights": {"dense": config.W_DENSE, "lexical": config.W_LEXICAL},
        "retrieval": ret.summary(),
        "questions": [r.to_dict() for r in ret.results],
        "isolation": evaluate_isolation(),
        "guardrail": evaluate_guardrail(),
        "corpus": audit_corpus(),
    }


def _bar(x: float, width: int = 20) -> str:
    filled = round(x * width)
    return "█" * filled + "·" * (width - filled)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Evalúa el recuperador del RAG.")
    ap.add_argument("--top-k", type=int, default=config.TOP_K)
    ap.add_argument("--json", type=Path, help="escribe el informe completo")
    args = ap.parse_args()

    out = run_all(args.top_k)
    ov = out["retrieval"]["overall"]

    print(f"modelo {out['model']}  ·  top_k={out['retrieval']['top_k']}  "
          f"·  pesos denso/léxico {out['weights']['dense']}/{out['weights']['lexical']}\n")

    print(f"{'tema':<16} {'n':>3} {'hit':>6} {'mrr':>6} {'top1':>6} {'términos':>9}")
    for topic, s in sorted(out["retrieval"]["by_topic"].items()):
        print(f"{topic:<16} {s['n']:>3} {s['hit_rate']:>6.0%} {s['mrr']:>6.2f} "
              f"{s['top1']:>6.0%} {s['term_recall']:>9.0%}")
    print(f"{'TOTAL':<16} {ov['n']:>3} {ov['hit_rate']:>6.0%} {ov['mrr']:>6.2f} "
          f"{ov['top1']:>6.0%} {ov['term_recall']:>9.0%}  {_bar(ov['hit_rate'])}")

    if out["retrieval"]["misses"]:
        print("\nsin acierto: " + ", ".join(out["retrieval"]["misses"]))
    for trap in out["retrieval"]["traps_hit"]:
        print(f"trampa: {trap['id']} recuperó «{trap['document']}»")

    iso = out["isolation"]
    print(f"\naislamiento de colecciones: {len(iso['leaks'])} fugas "
          f"en {iso['searches']} búsquedas")
    for leak in iso["leaks"][:5]:
        print(f"  {leak['question']} pidió {leak['asked']} y trajo {leak['returned']}")

    g = out["guardrail"]
    print(f"\nconsejo financiero: {g['refused']}/{g['probes']} rechazados, "
          f"{len(g['false_positives'])}/{g['allowed']} falsos positivos")
    for q in g["leaked"]:
        print(f"  ⚠ se coló: {q}")
    for q in g["false_positives"]:
        print(f"  ⚠ rechazada sin motivo: {q}")

    c = out["corpus"]
    print(f"\ncorpus: {c['documents']} documentos · {c['chunks']} fragmentos · "
          f"{c['embeddings']} vectores · {c['fts_rows']} en el índice léxico")
    if not c["embeddings_complete"]:
        print(f"  ⚠ faltan {c['chunks'] - c['embeddings']} vectores")
    if not c["fts_complete"]:
        print(f"  ⚠ faltan {c['chunks'] - c['fts_rows']} filas léxicas")
    for doc in c["empty_documents"]:
        print(f"  ⚠ sin fragmentos: [{doc['collection']}] {doc['title']}")

    if args.json:
        args.json.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        print(f"\ninforme completo → {args.json}")


if __name__ == "__main__":
    main()
