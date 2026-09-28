"""Every repository path the app shows to its reader has to exist.

The Banca profile sent readers to data/README.md for its declared gaps, a
file inherited by reference from the v16 prototype that this repository never
had. A citation that leads nowhere is worse than none: it is found by whoever
checks it, which is the reader the citation was written for.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"

# A repo-relative path in app text: «data/README.md», «engine/spain.py». The
# lookbehind skips module imports such as "../data/fuentes.json".
CITED = re.compile(
    r"(?<![./\w])(?:data|docs|tools|scripts|research|engine|tests|rag|explain|api)"
    r"/[\w./-]+\.(?:md|py|csv|json|gz)\b"
)


def app_sources():
    for path in SRC.rglob("*.ts*"):
        if "__tests__" in path.parts or "test" in path.parts or ".test." in path.name:
            continue
        yield path


def test_every_path_the_app_cites_exists():
    missing = {
        f"{p.relative_to(ROOT)}: {m}"
        for p in app_sources()
        for m in CITED.findall(p.read_text(encoding="utf-8"))
        if not (ROOT / m).exists()
    }
    assert not missing, sorted(missing)
