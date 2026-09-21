#!/usr/bin/env python3
"""Compara dos vintages descargados y dice qué ha cambiado en el origen.

`refresh_vintage.py` sabe traer los datos, pero nadie sabía responder a la
pregunta siguiente, que es la que importa: ¿ha cambiado algo desde la última
vez? Sin eso, actualizar consiste en sustituir ficheros y esperar.

Limitación heredada, y conviene decirla antes de que la encuentre otro: el
vintage congelado en `data/gold/` NO guarda el sha256 de las descargas
originales —16 de sus 18 filas lo tienen vacío— y los ficheros crudos de
entonces no se conservaron. Contra ese vintage no hay comparación posible, y
este script no la finge: exige dos directorios de `data/vintages/`. La
comparación queda disponible desde el primer refresco en adelante.

    python scripts/diff_vintage.py data/vintages/2026-09-22 data/vintages/2026-10-04
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Diff:
    changed: list[tuple[str, str, str]] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    unchanged: int = 0
    uncomparable: list[str] = field(default_factory=list)

    @property
    def moved(self) -> bool:
        """Si hay algo que obligue a revisar antes de promover."""
        return bool(self.changed or self.added or self.removed or self.failed)


def _rows(vintage: Path) -> dict[str, dict]:
    manifest = vintage / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(f"no hay manifest.csv en {vintage}")
    with manifest.open(encoding="utf-8") as fh:
        return {f"{r['source']}|{r['url']}": r for r in csv.DictReader(fh)}


def diff(antes: Path, despues: Path) -> Diff:
    a, b = _rows(antes), _rows(despues)
    out = Diff()
    for clave, nuevo in b.items():
        if nuevo.get("status", "").startswith("error"):
            out.failed.append((nuevo["source"], nuevo["status"]))
            continue
        if not nuevo.get("status", "").startswith("ok"):
            continue                                   # derivados y no descargables
        viejo = a.get(clave)
        if viejo is None:
            out.added.append(nuevo["source"])
        elif not viejo.get("sha256") or not nuevo.get("sha256"):
            # Sin huella en alguno de los dos no se puede afirmar nada. Decirlo
            # es el punto: un «sin cambios» falso es peor que un hueco.
            out.uncomparable.append(nuevo["source"])
        elif viejo["sha256"] != nuevo["sha256"]:
            out.changed.append((nuevo["source"], viejo["sha256"][:12], nuevo["sha256"][:12]))
        else:
            out.unchanged += 1
    for clave, viejo in a.items():
        if clave not in b and viejo.get("status", "").startswith("ok"):
            out.removed.append(viejo["source"])
    return out


def render(d: Diff, antes: Path, despues: Path) -> str:
    L = [f"{antes.name} -> {despues.name}", ""]
    L.append(f"  sin cambios      {d.unchanged}")
    L.append(f"  cambiados        {len(d.changed)}")
    L.append(f"  nuevos           {len(d.added)}")
    L.append(f"  desaparecidos    {len(d.removed)}")
    L.append(f"  fallos de red    {len(d.failed)}")
    if d.uncomparable:
        L.append(f"  no comparables   {len(d.uncomparable)}  (sin sha256 en alguno de los dos)")
    for nombre, va, vb in d.changed:
        L.append(f"\n  CAMBIADO  {nombre}\n            {va}… -> {vb}…")
    for nombre in d.added:
        L.append(f"\n  NUEVO     {nombre}")
    for nombre in d.removed:
        L.append(f"\n  YA NO ESTÁ {nombre}")
    for nombre, estado in d.failed:
        L.append(f"\n  FALLO     {nombre}: {estado}")
    L.append("")
    L.append("Nada que revisar: el origen no se ha movido." if not d.moved
             else "Hay cambios en el origen: revísalos antes de promover el vintage.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("antes", type=Path)
    ap.add_argument("despues", type=Path)
    args = ap.parse_args()
    d = diff(args.antes, args.despues)
    print(render(d, args.antes, args.despues))
    # 1 si algo se movió: encadenable en un script de actualización.
    return 1 if d.moved else 0


if __name__ == "__main__":
    raise SystemExit(main())
