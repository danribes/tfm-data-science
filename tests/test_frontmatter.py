"""La portada, el índice y el diagrama, comprobados como se comprueba el resto.

Un índice escrito a mano se desfasa en la primera reedición y nadie se entera
hasta que un lector pincha un enlace muerto. Como se genera, puede comprobarse
que está generado: si alguien añade una sección y no regenera, esto falla.
"""
from __future__ import annotations

import hashlib
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


def test_no_credential_reaches_the_tracked_tree():
    """El repositorio es público: un token en su historial queda quemado.

    La hoja de acceso del tribunal lleva EVO_RAG_TOKEN y vive fuera del
    control de versiones. Esta prueba existe porque `git add -A` es cómodo y
    no pregunta, y porque un `.gitignore` sólo protege mientras nadie fuerce
    la ruta.
    """
    import subprocess

    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root,
                             capture_output=True, text=True, check=True)
    patterns = (
        re.compile(r"hf_[A-Za-z0-9]{30,}"),              # token de Hugging Face
        re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),       # clave de proveedor
        re.compile(r"EVO_RAG_TOKEN\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    )
    #: El token de revisión, pegado tal cual, no encaja en ningún patrón de
    #: arriba: es una cadena alfanumérica sin prefijo. Se busca por huella, de
    #: modo que la prueba reconoce el secreto sin contenerlo.
    known_secret = "c6040958408df2241c3fdb20ae64959d09e171bca03ac2660da4a2f90134e416"
    candidate = re.compile(r"[A-Za-z0-9_\-]{24,64}")

    offenders = []
    for rel in filter(None, tracked.stdout.split("\0")):
        path = root / rel
        if not path.is_file() or path.suffix in {".png", ".pdf", ".pptx", ".db", ".svg"}:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in patterns:
            if pat.search(body):
                offenders.append(f"{rel}: {pat.pattern}")
        for tok in candidate.findall(body):
            if hashlib.sha256(tok.encode()).hexdigest() == known_secret:
                offenders.append(f"{rel}: el token de revisión, literal")
    assert not offenders, offenders


def test_the_leak_guard_would_actually_catch_a_leak(tmp_path):
    """Una prueba de fugas que no puede fallar no protege de nada.

    Se ejercita con un secreto sintético. El de verdad no aparece aquí: partir
    la cadena en dos trozos concatenados no la oculta de quien lee el fichero
    ni de quien lo rastrea, y este fichero sí está en el repositorio público.
    """
    fake = "ZzQ7wKpLmN4rT8vB2xY6hJ3sD5fG9aCe"
    fake_digest = hashlib.sha256(fake.encode()).hexdigest()

    candidate = re.compile(r"[A-Za-z0-9_\-]{24,64}")
    doc = tmp_path / "filtrado.md"
    doc.write_text(f"token de acceso: {fake}\n", encoding="utf-8")
    found = [t for t in candidate.findall(doc.read_text(encoding="utf-8"))
             if hashlib.sha256(t.encode()).hexdigest() == fake_digest]
    assert found, "el detector por huella no encontró un secreto plantado"

    assert re.compile(r"hf_[A-Za-z0-9]{30,}").search("hf_" + "A" * 34)
    assert not candidate.findall("una línea corriente, sin credenciales")


def test_the_evaluator_sheet_is_ignored_if_it_exists():
    """Si alguien la crea, git no debe poder verla."""
    import subprocess

    root = Path(__file__).resolve().parents[1]
    r = subprocess.run(["git", "check-ignore", "docs/ACCESO_EVALUADORES.md"],
                       cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, "docs/ACCESO_EVALUADORES.md debe estar en .gitignore"
