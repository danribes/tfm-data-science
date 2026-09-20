"""Check that the deployed Space answers, not merely that it responds.

    python deploy/hf/live_check.py [--base URL]

`smoke.py` checks an assembled stage before it ships. This checks the running
service afterwards, and it exists because of a specific failure: the app went
on returning 200 everywhere, rendering every page and reporting itself healthy,
while `/rag/chat` generated nothing for want of a provider key. A verification
log recorded "browser checks passed" for that build. The page looked right; the
answer was missing.

So every assertion here is about content. A 200 proves the route is wired; it
proves nothing about whether a reader gets an answer.

Exit code 1 on the first failure, with the endpoint and the reason.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "https://danribes-evo-espana-api.hf.space"
TIMEOUT = 180


def call(base: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"detail": raw[:200]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=DEFAULT_BASE)
    base = ap.parse_args().base.rstrip("/")
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}{'' if ok else f'  — {detail}'}")
        if not ok:
            failures.append(name)

    print(f"live check: {base}")

    status, health = call(base, "/health")
    check("/health responds", status == 200, str(status))
    check("/health carries a vintage", bool(health.get("vintage")), str(health))

    # The engine: a scenario has to move, or the levers are not reaching it.
    status, scn = call(base, "/scenario", {"levers": {"r": 4.8}, "horizon": 2040})
    moved = (status == 200
             and scn.get("scenario", {}).get("b", [0])[-1]
             != scn.get("baseline", {}).get("b", [0])[-1])
    check("/scenario responds to a lever", moved, f"status {status}")

    # The explanation: all four blocks, whichever path wrote them. An empty
    # block is the failure this cannot see from a status code.
    status, exp = call(base, "/explain",
                       {"levers": {"r": 4.8}, "horizon": 2040, "headline": "esf"})
    blocks = ("resumen", "mecanismo", "advertencia", "coloquial")
    check("/explain returns every block", status == 200
          and all(str(exp.get(b, "")).strip() for b in blocks),
          f"status {status}, missing {[b for b in blocks if not str(exp.get(b, '')).strip()]}")
    check("/explain names who wrote it", exp.get("source") in {"llm", "deterministic"},
          str(exp.get("source")))

    # The resolver: a question carrying a year and a lever must yield all three.
    status, ask = call(base, "/ask",
                       {"question": "¿Qué pasa con mi hipoteca si el Euríbor sube al 5 % en 2040?"})
    check("/ask resolves a series", status == 200 and bool(ask.get("series")),
          f"status {status}: {str(ask)[:120]}")
    check("/ask extracts the year", ask.get("year") == 2040, str(ask.get("year")))
    check("/ask extracts the lever", bool(ask.get("levers")), str(ask.get("levers")))

    # The corpus: retrieval AND generation. `grounded` was true with six
    # passages and no answer at all, which is the case that started this file.
    status, coll = call(base, "/rag/collections")
    check("/rag/collections lists something", status == 200
          and bool(coll.get("collections")), f"status {status}")
    default = coll.get("default_collection") or "metodo"

    status, chat = call(base, "/rag/chat",
                        {"question": "¿qué límites reconoce el modelo?",
                         "collection": default, "top_k": 4})
    check("/rag/chat generated an answer", status == 200 and bool(chat.get("provider")),
          f"provider {chat.get('provider')}, error {chat.get('error')}")
    check("/rag/chat answer is not the fallback notice",
          "no se ha obtenido una respuesta" not in str(chat.get("answer", "")).lower(),
          str(chat.get("answer", ""))[:110])

    # Containment: the copyrighted collections must not be reachable without a
    # token. Which refusal arrives depends on what is deployed — 422 when the
    # index does not hold them at all, 401 when it does and they are gated —
    # and this check ran with only 422/503 allowed, so the deploy that put the
    # reviewer index up failed on the collection being *correctly* protected.
    #
    # The status is the weaker half of the assertion anyway. What actually
    # matters is that no book text comes back, so that is asserted directly:
    # a future 200 with passages fails here whatever the status line says.
    for private in ("libros", "crack23"):
        status, body = call(base, "/rag/search",
                            {"query": "curva de Phillips", "collection": private, "top_k": 2})
        passages = body.get("passages") or body.get("hits") or []
        check(f"/rag/search refuses «{private}»",
              status in (401, 403, 422, 503) and not passages,
              f"status {status}, {len(passages)} pasajes")

    print()
    if failures:
        print(f"FAILED: {len(failures)} — {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
