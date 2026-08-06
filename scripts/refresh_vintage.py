#!/usr/bin/env python3
"""Re-fetch the sources listed in data/gold/manifest.csv into a NEW dated
vintage directory data/vintages/<YYYY-MM-DD>/ (gitignored).

NEVER writes into data/gold/ — the committed vintage is immutable (spec §3.2);
promoting a new vintage into data/gold/ is a manual, reviewed act. Per-source
network failures are recorded in the new vintage's manifest, never fabricated.
"""
from __future__ import annotations

import csv
import datetime
from pathlib import Path

import requests

GOLD_MANIFEST = Path("data/gold/manifest.csv")
VINTAGES_ROOT = Path("data/vintages")


def refresh(manifest_path: Path = GOLD_MANIFEST, out_root: Path = VINTAGES_ROOT,
            fetch=requests.get, today: str | None = None) -> Path:
    today = today or datetime.date.today().isoformat()
    out_dir = out_root / today
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    new_rows = []
    with manifest_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            entry = {"source": row["source"], "url": row["url"],
                     "fetched": datetime.datetime.now().isoformat(timespec="seconds"),
                     "bytes": 0, "raw_file": "", "status": ""}
            try:
                resp = fetch(row["url"], timeout=30)
                resp.raise_for_status()
                name = Path(row["raw_file"]).name or f"{row['source']}.bin"
                (raw_dir / name).write_bytes(resp.content)
                entry.update(bytes=len(resp.content), raw_file=f"raw/{name}", status="ok")
            except Exception as exc:
                entry["status"] = f"error: {exc}"
            new_rows.append(entry)

    with (out_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "url", "fetched",
                                                "bytes", "raw_file", "status"])
        writer.writeheader()
        writer.writerows(new_rows)
    return out_dir


if __name__ == "__main__":
    print(f"vintage written to {refresh()}")
