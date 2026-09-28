"""The «Estado de las fuentes» snapshot: what it may and may not claim."""
from __future__ import annotations

import csv
from pathlib import Path

from tools.gen_sources_status import LABELS, build_status

ROOT = Path(__file__).resolve().parents[1]


def row(raw_file, url, bytes_, sha="", kind="source", status="", source="Eurostat"):
    return {"source": source, "url": url, "raw_file": raw_file, "bytes": str(bytes_),
            "sha256": sha, "kind": kind, "status": status}


def signals(frozen, fresh):
    out = build_status(frozen, fresh, vintage="2026-07-31", checked="2026-09-22")
    return {s["file"]: s["signal"] for s in out["sources"]}, out


def test_without_fingerprints_the_size_is_a_clue_not_a_verdict():
    # El vintage congelado no guardó sha256: sólo se puede comparar el tamaño,
    # y la señal tiene que decir eso y no «sin cambios».
    frozen = [row("a.json", "u/a", 100), row("b.json", "u/b", 100)]
    fresh = [row("raw/a.json", "u/a", 100, sha="x", status="ok"),
             row("raw/b.json", "u/b", 120, sha="y", status="ok")]
    got, _ = signals(frozen, fresh)
    assert got == {"a.json": "same_size", "b.json": "size_changed"}


def test_with_fingerprints_on_both_sides_the_hash_decides():
    frozen = [row("a.json", "u/a", 100, sha="h1"), row("b.json", "u/b", 100, sha="h1")]
    fresh = [row("raw/a.json", "u/a", 100, sha="h1", status="ok"),
             row("raw/b.json", "u/b", 100, sha="h2", status="ok")]
    got, _ = signals(frozen, fresh)
    # Mismo tamaño y huella distinta: ha cambiado, aunque el tamaño no lo diga.
    assert got == {"a.json": "unchanged", "b.json": "changed"}


def test_errors_derived_new_and_missing_are_named_not_hidden():
    frozen = [row("a.json", "u/a", 100), row("gone.json", "u/gone", 50),
              row("", "", 900, kind="derived", source="analog_panel")]
    fresh = [row("raw/a.json", "u/a", 0, status="error: HTTP 503"),
             row("raw/new.json", "u/new", 10, sha="z", status="ok"),
             row("", "", 0, kind="derived", status="skipped: derived artifact", source="analog_panel")]
    got, out = signals(frozen, fresh)
    assert got == {"a.json": "error", "new.json": "new", "gone.json": "missing",
                   "analog_panel": "derived"}
    assert out["counts"] == {"sources": 3, "ok": 1, "error": 1, "attention": 3, "derived": 1}
    # Lo que no se descargó no pesa 0 bytes: no tiene tamaño que comparar.
    after = {s["file"]: s["bytes_after"] for s in out["sources"]}
    assert after == {"a.json": None, "new.json": 10, "gone.json": None, "analog_panel": None}


def test_every_source_in_the_frozen_manifest_has_a_spanish_label():
    with open(ROOT / "data/gold/manifest.csv") as f:
        files = {r["raw_file"] or r["source"] for r in csv.DictReader(f)}
    assert files <= set(LABELS), sorted(files - set(LABELS))
