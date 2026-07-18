"""INE API client — fetch and cache raw JSON tables."""

import json
import random
import time
from pathlib import Path

import requests

from evo_final_work._old.src.config import INE_BASE_URL

_SESSION = requests.Session()
_SESSION.headers.update({"Accept": "application/json", "User-Agent": "ine-vivienda/1.0"})


def fetch_table(table_id: int, nult: int | None = None) -> list[dict]:
    """Download a single INE table, return list of series dicts."""
    url = f"{INE_BASE_URL}/{table_id}"
    params = {}
    if nult is not None:
        params["nult"] = nult

    resp = _SESSION.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_and_save(table_id: int, out_path: Path, nult: int | None = None, delay: float = 1.0) -> list[dict]:
    """Fetch table, save raw JSON, return data."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = fetch_table(table_id, nult=nult)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    jitter = random.uniform(0.5, 1.5)
    time.sleep(delay * jitter)
    return data


def load_cached(out_path: Path) -> list[dict]:
    """Load previously saved raw JSON."""
    return json.loads(out_path.read_text(encoding="utf-8"))
