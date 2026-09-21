"""Ninguna versión interna del motor debe llegar a lo que publica la API.

«v16» es un prototipo anterior de este repositorio. Al lector no le dice nada,
y llegó a ser engañoso: la ficha afirmaba «la calibración v16 usaba 3,00» para
un parámetro que el motor ya no toma de ahí —usa la estimación del panel—, y
la tabla de «Datos y método» publicaba «phase 3 contests may replace, AC-V6»,
que son referencias de planificación interna.

La cadena equivalente del frontend tiene su propio guardián
(frontend/src/__tests__/noVersionLeaks.test.ts). Éste cubre lo que no ve
aquél: las cadenas que viajan por la API en tiempo de ejecución.

Los comentarios del código sí pueden nombrarla. Ahí documenta de dónde se
portó cada constante y es útil para quien mantiene esto.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

#: Sin delimitadores de palabra a propósito: `\bv16\b` no casa con
#: "build_v16.py" —el guion bajo es carácter de palabra— y esa cadena siguió
#: publicándose en «Datos y método» con el guardián del frontend en verde.
VERSION = re.compile(r"v16|AC-V\d|phase \d contests", re.I)


def test_la_procedencia_publicada_no_nombra_versiones():
    from engine.constants import CONSTANTS_TABLE

    culpables = [(c["name"], c["provenance"]) for c in CONSTANTS_TABLE
                 if VERSION.search(str(c["provenance"]))]
    assert culpables == [], culpables


def test_la_procedencia_publicada_dice_algo_util():
    """Quitar la versión no puede dejar la celda vacía: la procedencia tiene
    que seguir diciendo de dónde sale el número."""
    from engine.constants import CONSTANTS_TABLE

    for c in CONSTANTS_TABLE:
        assert len(str(c["provenance"])) > 25, c["name"]


def test_las_fuentes_de_las_comparaciones_no_nombran_versiones():
    """Las cadenas `source=` de research/validate.py se publican tal cual en
    la capa «En qué se apoya esta cifra»."""
    texto = (RAIZ / "research/validate.py").read_text(encoding="utf-8")
    fuentes = re.findall(r"source=\((.*?)\),", texto, re.S)
    assert fuentes, "no se han encontrado cadenas source= que revisar"
    culpables = [f for f in fuentes if VERSION.search(f)]
    assert culpables == [], culpables
