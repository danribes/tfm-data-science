"""Chat-level evaluation: what the librarian actually says, scored.

`rag.evaluate` scores retrieval — whether the right passage surfaces. This
scores the layer above, which is where a RAG usually fails in public: an answer
that cites passages it was never given, a confident paragraph about a question
the corpus cannot answer, a citation bracket pointing at nothing.

Three measurements, in rising order of cost:

  refusal    — the four unanswerable golden questions must come back saying
               the corpus does not cover them, not with a fluent invention
  citations  — every [n] in an answer must point at a passage that was
               actually retrieved, and the answer must cite at all; both are
               deterministic string checks against the returned passages
  fidelity   — for a sample, a second model is shown one cited sentence and
               the passage it cites and asked only "does the passage support
               this?". Judged by a different provider than the one that wrote
               the answer whenever the cascade allows, because a model marking
               its own homework is the failure mode, not the method.

Runs against live providers and therefore offline, like every evaluation in
this project: `python -m rag.eval_chat`. Costs a few dozen calls.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from rag import chat, golden

OUT = Path(__file__).resolve().parents[1] / "docs" / "eval"

#: Sentences worth checking carry a citation. The split is deliberately crude —
#: abbreviations barely occur in the librarian's register.
_SENT = re.compile(r"[^.!?\n]+[.!?]")
_CITE = re.compile(r"\[(\d+)\]")

#: Phrases that count as declining to answer, accent-folded. The first run of
#: this evaluator flagged three correct refusals as inventions because the
#: model wrote "no contiene información" and the list only knew "no cubre" —
#: the evaluator was the broken part, which is why its own detector gets a test.
_REFUSALS = ("no cubre", "no cubro", "no aparece en el corpus",
             "no contiene informacion", "no contienen informacion",
             "no contienen la respuesta", "no hay informacion",
             "no dispongo de informacion")


def _fold(text: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def is_refusal(text: str) -> bool:
    t = _fold(text)
    return any(p in t for p in _REFUSALS)


def citation_report(answer: str, n_passages: int) -> dict:
    """Deterministic citation integrity for one answer."""
    sentences = [s.strip() for s in _SENT.findall(answer) if len(s.strip()) > 25]
    cited = [s for s in sentences if _CITE.search(s)]
    refs = [int(m) for m in _CITE.findall(answer)]
    dangling = sorted({r for r in refs if r < 1 or r > n_passages})
    return {
        "n_sentences": len(sentences),
        "n_cited": len(cited),
        "cited_share": (len(cited) / len(sentences)) if sentences else 0.0,
        "n_refs": len(refs),
        "dangling_refs": dangling,       # citations pointing at nothing
    }


def _judge(sentence: str, passage: str, avoid_provider: str | None) -> dict:
    """One fidelity verdict from a provider other than the author's."""
    providers = [p for p in chat.PROVIDERS if p["name"] != avoid_provider] or chat.PROVIDERS
    messages = [
        {"role": "system", "content":
         "Eres un verificador. Responde EXACTAMENTE una palabra: «si» si el "
         "pasaje respalda la afirmación, «no» si no la respalda. Nada más."},
        {"role": "user", "content":
         f"AFIRMACIÓN:\n{sentence}\n\nPASAJE:\n{passage[:2000]}"},
    ]
    for prov in providers:
        try:
            text = chat._call(prov, messages, max_tokens=8, timeout=45)
            if text:
                verdict = text.strip().lower()
                return {"provider": prov["name"],
                        "supported": verdict.startswith(("si", "sí", "yes"))}
        except Exception:
            continue
    return {"provider": None, "supported": None}


@dataclass
class ChatEval:
    refusals: list[dict] = field(default_factory=list)
    answers: list[dict] = field(default_factory=list)
    fidelity: list[dict] = field(default_factory=list)

    def summary(self) -> dict:
        graded = [a for a in self.answers if a["grounded"]]
        f_known = [f for f in self.fidelity if f["supported"] is not None]
        return {
            "unanswerable_total": len(self.refusals),
            "unanswerable_refused": sum(r["refused"] for r in self.refusals),
            "answered": len(graded),
            "mean_cited_share": (sum(a["citations"]["cited_share"] for a in graded)
                                 / len(graded)) if graded else 0.0,
            "answers_with_dangling_refs": sum(
                1 for a in graded if a["citations"]["dangling_refs"]),
            "fidelity_checked": len(f_known),
            "fidelity_supported": sum(1 for f in f_known if f["supported"]),
        }


def run(sample_answerable: int = 12, fidelity_per_answer: int = 1) -> ChatEval:
    ev = ChatEval()

    # 1. The questions the corpus cannot answer. A fluent paragraph here is
    # the worst failure this layer has.
    for q in golden.UNANSWERABLE:
        ans = chat.ask(q.question, q.collection)
        ev.refusals.append({
            "id": q.id, "grounded": ans.grounded, "provider": ans.provider,
            "refused": (not ans.grounded) or is_refusal(ans.text),
            "text_head": ans.text[:160],
        })

    # 2. A spread of answerable questions: citation integrity plus fidelity.
    # Even ids, deterministic — a random sample would make two runs of the
    # evaluation disagree about what was evaluated.
    picked = list(golden.ANSWERABLE)[::2][:sample_answerable]
    for q in picked:
        ans = chat.ask(q.question, q.collection)
        rep = citation_report(ans.text, len(ans.passages))
        ev.answers.append({
            "id": q.id, "grounded": ans.grounded, "provider": ans.provider,
            "error": ans.error, "citations": rep,
        })
        if not ans.grounded or not ans.passages:
            continue

        # Fidelity, on the first cited sentence of each answer.
        checked = 0
        for s in _SENT.findall(ans.text):
            m = _CITE.search(s)
            if not m or checked >= fidelity_per_answer:
                continue
            idx = int(m.group(1))
            if not (1 <= idx <= len(ans.passages)):
                continue
            verdict = _judge(s.strip(), ans.passages[idx - 1]["text"],
                             avoid_provider=ans.provider)
            ev.fidelity.append({"id": q.id, "sentence": s.strip()[:200],
                                "cited": idx, **verdict})
            checked += 1

    return ev


def main() -> None:
    ev = run()
    s = ev.summary()

    print(f"incontestables rechazadas: {s['unanswerable_refused']}"
          f"/{s['unanswerable_total']}")
    for r in ev.refusals:
        mark = "✓" if r["refused"] else "✗ INVENTÓ"
        print(f"  {mark} {r['id']}: {r['text_head'][:90]}…")

    print(f"\nrespondidas: {s['answered']} · frases con cita: "
          f"{s['mean_cited_share']:.0%} · respuestas con citas colgantes: "
          f"{s['answers_with_dangling_refs']}")
    for a in ev.answers:
        c = a["citations"]
        flag = f"  ⚠ colgantes {c['dangling_refs']}" if c["dangling_refs"] else ""
        print(f"  {a['id']:28} [{a['provider'] or '—'}] "
              f"{c['n_cited']}/{c['n_sentences']} frases citadas{flag}")

    if s["fidelity_checked"]:
        print(f"\nfidelidad (juez cruzado): {s['fidelity_supported']}"
              f"/{s['fidelity_checked']} frases respaldadas por su pasaje")
        for f in ev.fidelity:
            if f["supported"] is False:
                print(f"  ✗ {f['id']}: «{f['sentence'][:100]}…» no respaldada")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"summary": s, "refusals": ev.refusals,
               "answers": ev.answers, "fidelity": ev.fidelity}
    (OUT / "rag-chat-eval.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ninforme → {OUT / 'rag-chat-eval.json'}")


if __name__ == "__main__":
    main()
