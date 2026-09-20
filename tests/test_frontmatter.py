"""La portada, el índice y el diagrama, comprobados como se comprueba el resto.

Un índice escrito a mano se desfasa en la primera reedición y nadie se entera
hasta que un lector pincha un enlace muerto. Como se genera, puede comprobarse
que está generado: si alguien añade una sección y no regenera, esto falla.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tools import build_frontmatter as fm

MEMORIA = Path(__file__).resolve().parents[1] / "docs/MEMORIA_TFM.md"
TEXT = MEMORIA.read_text(encoding="utf-8")


def anchor(heading: str) -> str:
    return re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")


def test_the_index_matches_the_headings_it_claims_to_list():
    """Regenerar no debe cambiar nada: si cambia, el índice está desfasado."""
    current = TEXT.split(fm.BEGIN, 1)[1].split(fm.END, 1)[0].strip()
    assert current == fm.build_index(TEXT).strip(), (
        "el índice no coincide con los encabezados; "
        "ejecuta PYTHONPATH=. python tools/build_frontmatter.py")


def test_every_index_anchor_points_at_a_real_heading():
    heads = {anchor(h) for h in re.findall(r"^#{2,3} (.+)$", TEXT, re.M)}
    index = TEXT.split(fm.BEGIN, 1)[1].split(fm.END, 1)[0]
    targets = re.findall(r"\]\(#([^)]+)\)", index)
    assert targets, "el índice está vacío"
    assert not [t for t in targets if t not in heads]


def test_the_figures_the_memoria_references_exist():
    for target in re.findall(r"^!\[[^\]]*\]\(([^)]+)\)", TEXT, re.M):
        assert (MEMORIA.parent / target).is_file(), target


def test_the_cover_leaves_the_institution_blank():
    """No inventar la universidad ni el tutor.

    Son datos de un registro oficial. Rellenarlos con algo plausible sería
    falsificarlos, así que la portada deja el hueco y la memoria dice que el
    autor debe completarlo.
    """
    svg = (MEMORIA.parent / "figures/portada.svg").read_text(encoding="utf-8")
    assert "Universidad:" in svg and "Tutor/a:" in svg
    assert "____" in svg, "los campos deben quedar visiblemente vacíos"
    assert "Daniel Ribes" in svg


def test_the_cover_carries_the_vintage_and_engine_version():
    """Una portada sin corte de datos invita a leer el trabajo como actual."""
    from engine.constants import ENGINE_VERSION, VINTAGE

    svg = (MEMORIA.parent / "figures/portada.svg").read_text(encoding="utf-8")
    assert VINTAGE in svg
    assert ENGINE_VERSION in svg


@pytest.mark.parametrize("name", ["portada.svg", "arquitectura.svg"])
def test_the_generated_svgs_are_well_formed(name):
    import xml.etree.ElementTree as ET

    path = MEMORIA.parent / "figures" / name
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    assert root.tag.endswith("svg")
    assert root.get("viewBox")


def test_the_declaration_names_what_the_tools_were_used_for():
    """Una declaración vaga sería incoherente con la tesis del trabajo."""
    section = TEXT.split("## Declaración de uso", 1)[1].split("\n## ", 1)[0]
    for topic in ("Implementación", "Redacción", "Bibliografía", "Depuración"):
        assert topic in section, topic
    assert "no ha generado datos ni resultados" in section.lower()
    assert "responsabilidad" in section.lower()
