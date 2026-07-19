"""Contrato común de conectores (plan T1.1.2).

fetch() -> DataFrame tidy; el JSON crudo cae SIEMPRE en storage/raw como
evidencia inmutable, con fila de vintage en storage/raw/vintage_manifest.csv.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "storage" / "raw"
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"
MANIFEST = RAW / "vintage_manifest.csv"

UA = {"User-Agent": "Mozilla/5.0 (TFM evo_final_work; contacto: danribes@gmail.com)"}


def http_json(url: str, params=None, timeout: int = 60) -> dict:
    r = requests.get(url, params=params, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.json()


def save_raw(name: str, payload: dict, source_url: str) -> pathlib.Path:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False))
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    line = f'"{name}","{source_url}","{stamp}",{path.stat().st_size}\n'
    if not MANIFEST.exists():
        MANIFEST.write_text('"name","url","fetched_at","bytes"\n')
    with MANIFEST.open("a") as fh:
        fh.write(line)
    return path


def save_raw_bytes(filename: str, content: bytes, source_url: str) -> pathlib.Path:
    """Como save_raw pero para binarios (XLS legado, etc.)."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / filename
    path.write_bytes(content)
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    if not MANIFEST.exists():
        MANIFEST.write_text('"name","url","fetched_at","bytes"\n')
    with MANIFEST.open("a") as fh:
        fh.write(f'"{filename}","{source_url}","{stamp}",{len(content)}\n')
    return path


def jsonstat_to_df(js: dict) -> pd.DataFrame:
    """JSON-stat 2.0 (API dissemination de Eurostat) -> DataFrame largo."""
    dims = js["id"]
    sizes = js["size"]
    cats = []
    for d in dims:
        idx = js["dimension"][d]["category"]["index"]
        if isinstance(idx, dict):
            ordered = [k for k, _ in sorted(idx.items(), key=lambda kv: kv[1])]
        else:  # lista
            ordered = list(idx)
        cats.append(ordered)
    values = js["value"]  # dict {posición_lineal: valor}
    rows = []
    for pos_str, val in values.items():
        pos = int(pos_str)
        coords = []
        for size in reversed(sizes):
            coords.append(pos % size)
            pos //= size
        coords.reverse()
        rows.append([cats[i][c] for i, c in enumerate(coords)] + [val])
    return pd.DataFrame(rows, columns=dims + ["value"])
