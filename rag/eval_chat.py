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

This development evaluation uses live remote providers and incurs API calls:
`python -m rag.eval_chat`. It is separate from the offline unit-test suite.
"""
from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from rag import chat, golden
from rag.evaluate import evaluation_metadata
from rag.validation import is_refusal, citation_references

OUT = Path(__file__).resolve().parents[1] / "docs" / "eval"

#: Sentences worth checking carry a citation. The split is deliberately crude —
#: abbreviations barely occur in the librarian's register.
_SENT = re.compile(r"[^.!?\n]+[.!?]")

def citation_report(answer: str, n_passages: int) -> dict:
    """Deterministic citation integrity for one answer."""
    sentences = [s.strip() for s in _SENT.findall(answer) if len(s.strip()) > 25]
    cited = [s for s in sentences if citation_references(s)]
    refs = citation_references(answer)
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
        graded = [a for a in self.answers if a.get("provider") and not a.get("error")
                  and not a.get("refused", False)]
        f_known = [f for f in self.fidelity if f["supported"] is not None]
        return {
            "unanswerable_total": len(self.refusals),
            "unanswerable_refused": sum(r["refused"] for r in self.refusals),
            "answered": len(graded),
            "answerable_attempted": len(self.answers),
            "generation_failures": sum(bool(a.get("error")) for a in self.answers),
            "answerable_refused": sum(a.get("refused", False) for a in self.answers),
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
            "refused": not ans.error and is_refusal(ans.text),
            "error": ans.error, "model": ans.model, "answer": ans.text,
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
            "error": ans.error, "model": ans.model, "citations": rep,
            "refused": is_refusal(ans.text), "answer": ans.text,
            # Keep source identities/hashes in the shareable result; archive
            # the source database locally for full human audit of the excerpts.
            "passages": [{"chunk_id": p["chunk_id"], "title": p["title"],
                          "page": p.get("page"),
                          "text_sha256": hashlib.sha256(p["text"].encode()).hexdigest()}
                         for p in ans.passages],
        })
        if not ans.provider or ans.error or is_refusal(ans.text) or not ans.passages:
            continue

        # Fidelity, on the first cited sentence of each answer.
        checked = 0
        for s in _SENT.findall(ans.text):
            refs = citation_references(s)
            if not refs or checked >= fidelity_per_answer:
                continue
            idx = refs[0]
            if not (1 <= idx <= len(ans.passages)):
                continue
            verdict = _judge(s.strip(), ans.passages[idx - 1]["text"],
                             avoid_provider=ans.provider)
            ev.fidelity.append({"id": q.id, "sentence": s.strip(),
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
    payload = {"evaluation": evaluation_metadata(),
               "generation": {"providers": [{"name": p["name"], "model": p["model"]}
                                             for p in chat.PROVIDERS],
                              "system_prompt_sha256": hashlib.sha256(chat.SYSTEM.encode()).hexdigest(),
                              "temperature": 0.2, "max_tokens": 2600},
               "sampling": {"answerable": "every second development question, first 12",
                            "fidelity": "first cited sentence, first cited passage (max 2000 chars)",
                            "human_verified": False},
               "summary": s, "refusals": ev.refusals,
               "answers": ev.answers, "fidelity": ev.fidelity}
    (OUT / "rag-chat-eval.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ninforme → {OUT / 'rag-chat-eval.json'}")


if __name__ == "__main__":
    main()
