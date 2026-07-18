"""Conector INE wstempus (núcleo España, Variante C / fallback vivienda).

Tablas renumeradas 2026 (descubierto en barrido): IPV trimestral = 80270
(76201/49300 MUERTAS). Estrategia limpia anti-sobredimensión (§7.12 E3):
SERIES_TABLA/{t} paginado → filtrar series por nombre → DATOS_SERIE/{COD}.
Así el IPC baja de 55,9MB (1.120 series) a las 20 de "Índice general".
"""
from __future__ import annotations

import re
import sys
import time

import pandas as pd

from base import PROCESSED, http_json, save_raw

WS = "https://servicios.ine.es/wstempus/js/ES"

TABLES = {
    # tabla, regex de series a conservar, nult, salida
    "ipv_trimestral": (80270, r"Índice", 80, "ine_ipv_q"),
    "ipc_general": (76136, r"Índice general\. Índice\.", 400, "ine_ipc"),
    "salarios": (28191, r".", 30, "ine_salarios"),
}


def list_series(table: int, max_pages: int = 12) -> list[dict]:
    """Paginación defensiva: corta en páginas vacías, repetidas o max_pages
    (el tamaño de página del INE no es fiable — un bucle abierto llegó a page=99 y 502)."""
    out, seen, page = [], set(), 1
    while page <= max_pages:
        js = http_json(f"{WS}/SERIES_TABLA/{table}", params=[("page", str(page))])
        if not isinstance(js, list) or not js:
            break
        cods = {s.get("COD") for s in js}
        if cods <= seen:  # página repetida → fin real
            break
        out.extend(s for s in js if s.get("COD") not in seen)
        seen |= cods
        page += 1
        time.sleep(0.4)
    return out


def fetch_table(key: str) -> pd.DataFrame:
    table, pattern, nult, name = TABLES[key]
    series = list_series(table)
    keep = [s for s in series if re.search(pattern, s.get("Nombre", ""))]
    print(f"  {key}: {len(series)} series en tabla {table}, {len(keep)} seleccionadas")
    assert keep, f"{key}: el filtro '{pattern}' no seleccionó nada — ¿tabla renumerada otra vez?"
    rows = []
    for s in keep:
        js = http_json(f"{WS}/DATOS_SERIE/{s['COD']}", params=[("nult", str(nult))])
        for d in js.get("Data", []):
            rows.append({
                "cod": s["COD"], "nombre": s["Nombre"],
                "anyo": d.get("Anyo"), "periodo": d.get("FK_Periodo"),
                "valor": d.get("Valor"),
            })
        time.sleep(0.15)
    df = pd.DataFrame(rows)
    save_raw(name + "_series_meta", {"table": table, "kept": [s["COD"] for s in keep]}, f"{WS}/SERIES_TABLA/{table}")
    dest = PROCESSED / f"{name}.csv"
    df.to_csv(dest, index=False)
    print(f"  {name}: {len(df)} filas → {dest.name}")
    return df


def smoke(dfs: dict[str, pd.DataFrame]) -> None:
    ipc = dfs.get("ipc_general")
    if ipc is not None and len(ipc):
        v = pd.to_numeric(ipc["valor"], errors="coerce").dropna()
        assert 40 < v.median() < 130, f"IPC mediana sospechosa (¿bug del promedio?): {v.median()}"
    ipv = dfs.get("ipv_trimestral")
    if ipv is not None and len(ipv):
        v = pd.to_numeric(ipv["valor"], errors="coerce").dropna()
        assert 30 < v.max() < 260, f"IPV rango: max={v.max()}"
    print("SMOKE INE OK")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    dfs = {}
    for key in TABLES:
        try:
            dfs[key] = fetch_table(key)
        except Exception as e:  # noqa: BLE001
            print(f"  {key}: FALLO {str(e)[:130]}")
    smoke(dfs)
