#!/usr/bin/env python3
"""
fetch_data.py — Descarga datos INE para el proyecto de asequibilidad de vivienda.

Tablas descargadas:
    49300 — IPV por CCAA: general, nueva, segunda mano (anual)
    76201 — IPV por CCAA: general, nueva, segunda mano (trimestral)
    76136 — IPC por CCAA: índice general y grupos ECOICOP
    28191 — Salario bruto anual: medias y percentiles por CCAA

Uso:
    python fetch_data.py            # todas las series disponibles
    python fetch_data.py --nult 10  # ultimos 10 periodos por tabla
    python fetch_data.py --cache    # solo reprocesa JSON ya descargado

Salidas:
    data/raw/         JSON crudo por tabla
    data/processed/   CSV limpios + asequibilidad_ccaa.csv
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from src.client import fetch_and_save, load_cached
from src.cleaning import (
    build_asequibilidad,
    parse_ipc_ccaa,
    parse_ipv_anual,
    parse_ipv_trimestral,
    parse_salario_ccaa,
)
from src.config import DATA_PROCESSED, RAW_FILES, TABLES


def main(nult: int | None, cache: bool) -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Fetch / load raw JSON
    # ------------------------------------------------------------------
    print("=== Descarga de tablas INE ===\n")

    raw = {}
    for key, table_id in TABLES.items():
        path = RAW_FILES[key]
        if cache and path.exists():
            print(f"  [cache] {key} <- {path.name}")
            raw[key] = load_cached(path)
        else:
            print(f"  [fetch] {key} (tabla {table_id}) ...", end=" ", flush=True)
            raw[key] = fetch_and_save(table_id, path, nult=nult)
            print(f"{len(raw[key])} series")

    # ------------------------------------------------------------------
    # 2. Parse + clean
    # ------------------------------------------------------------------
    print("\n=== Limpieza y transformación ===\n")

    ipv_anual = parse_ipv_anual(raw["ipv_ccaa_anual"])
    ipv_trimestral = parse_ipv_trimestral(raw["ipv_ccaa_trimestral"])
    ipc = parse_ipc_ccaa(raw["ipc_ccaa"])
    salario = parse_salario_ccaa(raw["salario_ccaa"])

    print(f"  IPV anual:      {len(ipv_anual):>6} filas")
    print(f"  IPV trimestral: {len(ipv_trimestral):>6} filas")
    print(f"  IPC CCAA:       {len(ipc):>6} filas")
    print(f"  Salarios CCAA:  {len(salario):>6} filas")

    # ------------------------------------------------------------------
    # 3. Build affordability index
    # ------------------------------------------------------------------
    asequibilidad = build_asequibilidad(ipv_anual, salario)
    print(f"  Asequibilidad:  {len(asequibilidad):>6} filas  "
          f"({asequibilidad['ccaa'].nunique()} CCAA, "
          f"{asequibilidad['anyo'].min()}-{asequibilidad['anyo'].max()})")

    # ------------------------------------------------------------------
    # 4. Save processed CSVs
    # ------------------------------------------------------------------
    print("\n=== Guardando CSV procesados ===\n")

    saves = {
        "ipv": ipv_anual,
        "ipc": ipc,
        "salario": salario,
        "asequibilidad": asequibilidad,
    }

    from src.config import PROCESSED_FILES
    for name, df in saves.items():
        path = PROCESSED_FILES[name]
        df.to_csv(path, index=False, encoding="utf-8")
        print(f"  -> {path.relative_to(Path.cwd())}  ({len(df)} filas)")

    print("\nFin.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descarga y limpia datos INE de vivienda.")
    parser.add_argument("--nult", type=int, default=None,
                        help="Ultimos N periodos por tabla (por defecto: todos)")
    parser.add_argument("--cache", action="store_true",
                        help="Reutiliza JSON ya descargado en data/raw/")
    args = parser.parse_args()
    main(nult=args.nult, cache=args.cache)
