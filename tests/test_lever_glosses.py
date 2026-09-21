"""Cada palanca y cada indicador se explican en castellano llano.

«Saldo primario · Δ vs central» no significa nada para quien no es economista,
y es justo la palanca que más mueve la deuda. Sin una línea que diga qué es,
el panel pide al lector que decida sobre algo que no puede leer.

Las cadenas viven en engine/levers.py y se copian a mano al motor de
TypeScript, que es de donde las pinta el panel. La copia a mano es lo que esta
prueba vigila: dos ficheros con el mismo texto divergen en cuanto alguien
corrige una coma en uno solo.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.levers import LEVER_SPECS

RAIZ = Path(__file__).resolve().parents[1]
TS_LEVERS = RAIZ / "frontend/src/engine/levers.ts"
TS_SERIES = RAIZ / "frontend/src/lib/seriesMeta.ts"


def test_todas_las_palancas_tienen_explicacion():
    for spec in LEVER_SPECS:
        assert spec.get("plain"), spec["id"]


def test_la_explicacion_no_es_el_nombre_otra_vez():
    """Repetir el nombre con otras palabras no explica nada."""
    for spec in LEVER_SPECS:
        assert spec["plain"] != spec["nm"], spec["id"]
        assert len(spec["plain"]) > 40, spec["id"]


def test_la_explicacion_evita_la_jerga_que_pretende_traducir():
    """Una explicación que usa el término que explica no explica.

    `sp` no puede definirse como «el saldo primario»; `prima` no puede
    apoyarse en «spread». Se comprueba sobre el término propio de cada
    palanca, no sobre una lista general: «inflación» es jerga en la
    definición de IPCA y es la palabra correcta en la de la indexación.
    """
    prohibido = {
        "sp": ["saldo primario"],
        "prima": ["spread", "prima de riesgo"],
        "tau": ["cuña"],
        "lam": ["productividad total"],
        "dem": ["tasa de dependencia"],
        "idx": ["revalorización"],
    }
    for spec in LEVER_SPECS:
        for termino in prohibido.get(spec["id"], []):
            assert termino not in spec["plain"].lower(), (spec["id"], termino)


def _ts_plains(ruta: Path) -> dict[str, str]:
    """Los pares id -> plain tal y como los lee el navegador."""
    texto = ruta.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in re.finditer(r'\{\s*k?i?d?:?\s*"([a-z]+)".*?plain:\s*("(?:[^"\\]|\\.)*")', texto, re.S):
        out[m.group(1)] = json.loads(m.group(2))
    return out


def test_el_motor_de_typescript_dice_exactamente_lo_mismo():
    ts = _ts_plains(TS_LEVERS)
    assert len(ts) == len(LEVER_SPECS), f"encontradas {len(ts)} de {len(LEVER_SPECS)}"
    for spec in LEVER_SPECS:
        assert ts[spec["id"]] == spec["plain"], spec["id"]


@pytest.mark.parametrize("serie", ["b", "u", "pi", "saldo", "precio", "cuota",
                                   "salario", "esf"])
def test_los_ocho_indicadores_de_la_tabla_tambien_se_explican(serie):
    texto = TS_SERIES.read_text(encoding="utf-8")
    m = re.search(r'\{\s*k:\s*"' + serie + r'".*?plain:\s*"([^"]+)"', texto, re.S)
    assert m, serie
    assert len(m.group(1)) > 30, serie
