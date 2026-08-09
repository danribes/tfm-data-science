"""Regenerate the MSW persona fixture from the engine's own PERSONAS.

The fixture was hand-written and fell four personas behind the app, which left
`inicio.test.tsx` passing under the name "links to the four shipped personas"
long after twelve shipped. A mock that is derived cannot drift; one that is
transcribed always eventually does.

    python -m tools.gen_persona_fixture
"""
from __future__ import annotations

import json
import pathlib

from engine.spain import PERSONAS

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "frontend/src/test/msw/fixtures.ts"
FIELDS = ("id", "pill", "foot", "h1", "meta", "hot", "series_keys",
          "outs", "headline", "reds")


def _ts(v: object) -> str:
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k}: {_ts(x)}" for k, x in v.items()) + " }"
    if isinstance(v, list):
        return "[" + ", ".join(_ts(x) for x in v) + "]"
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return json.dumps(v, ensure_ascii=False)


def render() -> str:
    cards = ["  {\n    " + ",\n    ".join(f"{k}: {_ts(p[k])}" for k in FIELDS) + ",\n  }"
             for p in PERSONAS]
    return ("// Generated from engine/spain.py PERSONAS — the same twelve cards the server\n"
            "// serves. Hand-maintaining this list let the mock fall four personas behind the\n"
            "// app, which kept a test passing under a name that had stopped being true.\n"
            "// Regenerate with: python -m tools.gen_persona_fixture\n"
            "export const mockPersonaCards: PersonaCard[] = [\n"
            + ",\n".join(cards) + ",\n];")


def main() -> int:
    src = FIXTURE.read_text(encoding="utf-8")
    start = src.index("export const mockPersonaCards: PersonaCard[] = [")
    # Terminated by a line that is exactly "];". Counting brackets does not work
    # here: the red-line provenance strings contain "[hist]" and "[regla UE]",
    # and a depth counter that does not understand string literals silently
    # truncates the file mid-array.
    end = src.index("\n];\n", start) + len("\n];\n")
    FIXTURE.write_text(src[:start] + render() + "\n" + src[end:], encoding="utf-8")
    print(f"{FIXTURE.name}: {len(PERSONAS)} personas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
