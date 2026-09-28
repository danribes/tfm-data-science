"""The «Estado de las fuentes» snapshot: what it may and may not claim."""
from __future__ import annotations

import csv
from pathlib import Path

from tools.gen_sources_status import AGENCIES, LABELS, build_catalog, build_status

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


def dl(name, url, bytes_, at):
    return {"name": name, "url": url, "bytes": str(bytes_), "fetched_at": at}


def test_the_catalog_counts_sources_not_downloads():
    # El registro de julio repite descargas: una fuente descargada tres veces
    # es una fuente, con tres descargas.
    log = [dl("x.xls", "https://apps.fomento.gob.es/x.XLS", 10, "2026-07-19T10:00"),
           dl("x.xls", "https://apps.fomento.gob.es/x.XLS", 12, "2026-07-19T10:05"),
           dl("x.xls", "https://apps.fomento.gob.es/x.XLS", 12, "2026-07-19T10:01"),
           dl("weo", "https://www.imf.org/weo", 5, "2026-07-18T09:00")]
    manifest = [row("euribor.csv", "https://data-api.ecb.europa.eu/e", 7, source="ECB SDW"),
                row("", "", 900, kind="derived", source="analog_panel")]
    cat = build_catalog(log, manifest)
    assert cat["downloads"] == 4
    by_url = {s["url"]: s for s in cat["sources"]}
    assert len(by_url) == 3  # el derivado no es una fuente: no tiene URL
    x = by_url["https://apps.fomento.gob.es/x.XLS"]
    # La última descarga manda, no la última fila del registro.
    assert (x["downloads"], x["bytes"], x["inventory"]) == (3, 12, "original")
    assert x["agency"] == AGENCIES["apps.fomento.gob.es"]
    assert by_url["https://data-api.ecb.europa.eu/e"]["inventory"] == "manifest"
    assert cat["by_agency"] == {AGENCIES["apps.fomento.gob.es"]: 1, "FMI": 1, "BCE": 1}


def test_one_url_with_different_names_is_several_series_not_repeats():
    # Eurostat gov_10a_main aparece 11 veces en el registro con 11 nombres y
    # 11 tamaños: son 11 series del mismo conjunto cuyos parámetros no se
    # anotaron en la URL, no una descarga repetida 11 veces.
    base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10a_main"
    log = [dl("interest_paid", base, 17491, "2026-07-18T13:29"),
           dl("rev_TR", base, 18549, "2026-07-19T18:45"),
           dl("rev_TR", base, 18549, "2026-07-19T18:50")]
    cat = build_catalog(log, [])
    got = sorted((s["name"], s["downloads"]) for s in cat["sources"])
    assert got == [("interest_paid", 1), ("rev_TR", 2)]


def test_every_host_in_both_inventories_has_an_agency_name():
    from urllib.parse import urlparse
    hosts = set()
    for name in ("manifest.csv", "provenance_vintage_manifest.csv"):
        with open(ROOT / "data/gold" / name) as f:
            hosts |= {urlparse(r["url"]).netloc for r in csv.DictReader(f) if r["url"]}
    assert hosts <= set(AGENCIES), sorted(hosts - set(AGENCIES))


def test_every_source_in_the_frozen_manifest_has_a_spanish_label():
    with open(ROOT / "data/gold/manifest.csv") as f:
        files = {r["raw_file"] or r["source"] for r in csv.DictReader(f)}
    assert files <= set(LABELS), sorted(files - set(LABELS))
