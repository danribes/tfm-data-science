"""Check frozen data and research outputs against their committed SHA-256s.

Run ``python scripts/check_data_integrity.py`` to verify. After intentionally
regenerating and reviewing artifacts, ``--update`` records the new checksums.
This proves file identity, not source authenticity or validity of a model.
"""
from __future__ import annotations

import argparse
from fnmatch import fnmatch
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "artifact_checksums.json"
PRIVATE_REPORT_PATTERNS = (
    "rag-book-additions-*.json",
    "rag-staged-book-probes-*.json",
    "rag-staged-books-*.json",
)


def snapshot() -> dict[str, dict]:
    files = [ROOT / "data" / "ARTIFACT_METADATA.json"]
    for directory in ("data/gold", "data/external", "docs/eval"):
        files.extend(p for p in (ROOT / directory).iterdir()
                     if p.is_file() and not (
                         directory == "docs/eval"
                         and any(fnmatch(p.name, pattern) for pattern in PRIVATE_REPORT_PATTERNS)))
    return {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(files)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    actual = snapshot()
    if args.update:
        MANIFEST.write_text(json.dumps({"algorithm": "sha256", "files": actual}, indent=2) + "\n")
        print(f"Recorded {len(actual)} artifact checksums. Review the diff before committing.")
        return
    expected = json.loads(MANIFEST.read_text())["files"]
    changes = [name for name in sorted(expected.keys() | actual.keys())
               if expected.get(name) != actual.get(name)]
    if changes:
        raise SystemExit("Artifact checksum mismatch (missing, changed or added):\n" + "\n".join(changes))
    print(f"Verified {len(actual)} artifacts.")


if __name__ == "__main__":
    main()
