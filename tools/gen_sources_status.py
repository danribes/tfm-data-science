"""Freeze the state of the data sources into the «Estado de las fuentes» page.

The page is static on purpose: GitHub Pages has nothing to run, and the app
must not suggest that the data it computes with can change underneath it. So
this compares the frozen vintage (data/gold/manifest.csv) with the latest
download made by scripts/refresh_vintage.py and writes the result as a
committed snapshot the frontend imports.

What it may claim is limited by what was recorded. The frozen vintage kept no
sha256 for most sources, so for those the only comparison is the size, and
the snapshot says «same size» or «size changed», never «unchanged». A hash
decides only when both sides have one.

    PYTHONPATH=. python tools/gen_sources_status.py [data/vintages/<fecha>]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
VINTAGES = ROOT / "data" / "vintages"
OUT = ROOT / "frontend" / "src" / "data" / "fuentes.json"

#: raw file (or derived artifact name) -> series, in the reader's words.
#: Every source in the frozen manifest must be here; a test enforces it.
LABELS = {
    "eurostat_hicp_manr_es.json": "IPCA, tasa anual (España y UE-27)",
    "eurostat_une_rt_m_es.json": "Tasa de paro mensual, total y menores de 25",
    "eurostat_gdp_q_es.json": "PIB trimestral",
    "eurostat_gov_debt_es.json": "Deuda pública, % del PIB",
    "eurostat_gov_deficit_es.json": "Saldo público, % del PIB",
    "eurostat_hpi_q_es.json": "Índice de precios de vivienda (IPV)",
    "eurostat_overburden_es.json": "Sobrecarga por coste de la vivienda",
    "eurostat_arop_child_es.json": "Riesgo de pobreza infantil",
    "eurostat_pensions_pcgdp_es.json": "Gasto en pensiones, % del PIB",
    "eurostat_gov_edu_es.json": "Gasto público por funciones (educación)",
    "eurostat_temp_share_es.json": "Temporalidad del empleo",
    "ecb_bono10y_es.csv": "Bono a 10 años, España",
    "ecb_bono10y_de.csv": "Bono a 10 años, Alemania",
    "ecb_euribor12m.csv": "Euríbor a 12 meses",
    "ine_ipc_general.json": "IPC general",
    "wb_self_employment.json": "Autoempleo, % del empleo",
    "analog_panel": "Panel de análogos históricos",
    "analog_stats": "Estadísticos del panel de análogos",
}

#: Signals that ask a human to look before anything is promoted.
ATTENTION = {"changed", "size_changed", "error", "new", "missing"}


def _key(r: dict) -> str:
    return Path(r["raw_file"]).name if r.get("raw_file") else r["source"]


def _signal(old: dict | None, new: dict | None) -> str:
    either = new or old
    assert either is not None  # a key comes from one side or the other
    if either["kind"] == "derived":
        return "derived"
    if new is None:
        return "missing"
    if new.get("status", "").startswith("error"):
        return "error"
    if old is None:
        return "new"
    if old.get("sha256") and new.get("sha256"):
        return "unchanged" if old["sha256"] == new["sha256"] else "changed"
    return "same_size" if old["bytes"] == new["bytes"] else "size_changed"


def build_status(frozen: list[dict], fresh: list[dict], vintage: str, checked: str) -> dict:
    old_by = {_key(r): r for r in frozen}
    new_by = {_key(r): r for r in fresh}
    sources = []
    for key in list(old_by) + [k for k in new_by if k not in old_by]:
        old, new = old_by.get(key), new_by.get(key)
        either = new or old
        assert either is not None
        sources.append({
            "file": key,
            "agency": either["source"] if either["kind"] != "derived" else "Derivado",
            "series": LABELS.get(key, key),
            "kind": either["kind"],
            "status": (new or {}).get("status", "") or "ausente",
            "bytes_before": int(old["bytes"]) if old and old["bytes"] else None,
            # Skipped or failed downloads have no size; «0 B» would read as emptied.
            "bytes_after": int(new["bytes"]) if new and new.get("status") == "ok" else None,
            "signal": _signal(old, new),
        })
    real = [s for s in sources if s["kind"] != "derived"]
    return {
        "vintage": vintage,
        "checked": checked,
        "sources": sources,
        "counts": {
            "sources": len(real),
            "ok": sum(s["status"] == "ok" for s in real),
            "error": sum(s["signal"] == "error" for s in real),
            "attention": sum(s["signal"] in ATTENTION for s in real),
            "derived": len(sources) - len(real),
        },
    }


def _read(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main(argv: list[str]) -> None:
    latest = Path(argv[0]) if argv else max(p for p in VINTAGES.iterdir() if p.is_dir())
    status = build_status(
        _read(GOLD / "manifest.csv"), _read(latest / "manifest.csv"),
        vintage=(GOLD / "VINTAGE").read_text().strip(), checked=latest.name,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(f"{OUT.relative_to(ROOT)}: {status['counts']}")


if __name__ == "__main__":
    main(sys.argv[1:])
