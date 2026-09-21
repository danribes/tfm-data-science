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


def test_the_cover_names_the_centre_and_tutor():
    """Antes la portada dejaba el hueco a propósito: no inventar datos de un
    registro oficial. Ya no hace falta, porque los ha dado el autor —Evolve
    Academy, Julio Valero— y están en un solo sitio del generador para que la
    cubierta y la declaración no puedan decir cosas distintas.
    """
    from tools.build_frontmatter import CENTRE, TUTOR

    svg = (MEMORIA.parent / "figures/portada.svg").read_text(encoding="utf-8")
    assert f"Centro:" in svg and CENTRE in svg
    assert f"Tutor:" in svg and TUTOR in svg
    assert "Daniel Ribes" in svg
    assert "____" not in svg, "ya no quedan huecos por rellenar"


def test_la_memoria_y_la_cubierta_no_se_contradicen():
    """El mismo tutor y el mismo centro en los dos sitios."""
    from tools.build_frontmatter import CENTRE, SIGNED_ON, TUTOR

    memoria = MEMORIA.read_text(encoding="utf-8")
    svg = (MEMORIA.parent / "figures/portada.svg").read_text(encoding="utf-8")
    for dato in (CENTRE, TUTOR, SIGNED_ON):
        assert dato in memoria, dato
        assert dato in svg, dato
    assert "Pendiente de firma" not in memoria


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
    """El repositorio es público: un secreto en su historial queda quemado.

    Ya no hay token de corpus que repartir —se sirve abierto—, pero siguen
    pasando por aquí claves de proveedor y de Hugging Face. La prueba existe
    porque `git add -A` es cómodo y no pregunta, y porque un `.gitignore`
    sólo protege mientras nadie fuerce la ruta.
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
    #: Huellas SHA-256 de secretos concretos que no deben aparecer nunca. La
    #: del token de revisión sigue aquí aunque el token esté retirado: si
    #: reaparece en un fichero versionado, es que alguien lo ha reintroducido.
    known_secrets = {"c6040958408df2241c3fdb20ae64959d09e171bca03ac2660da4a2f90134e416"}
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
            if hashlib.sha256(tok.encode()).hexdigest() in known_secrets:
                offenders.append(f"{rel}: un secreto conocido, literal")
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


# ---- los dos temas -----------------------------------------------------------

def _relative_luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    chan = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    chan = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in chan]
    return 0.2126 * chan[0] + 0.7152 * chan[1] + 0.0722 * chan[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_relative_luminance(a), _relative_luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_both_themes_are_generated_and_differ():
    """Un tema oscuro idéntico al claro es un fichero, no un tema."""
    figs = MEMORIA.parent / "figures"
    for name in ("portada", "arquitectura"):
        light = (figs / f"{name}.svg").read_text(encoding="utf-8")
        dark = (figs / f"{name}-dark.svg").read_text(encoding="utf-8")
        assert light and dark
        assert light != dark, name


def test_the_dark_theme_is_actually_dark():
    """Y el claro, claro: la comprobación que un intercambio de ficheros falla."""
    assert _relative_luminance(fm.DARK.paper) < 0.05
    assert _relative_luminance(fm.LIGHT.paper) > 0.85
    assert _relative_luminance(fm.DARK.ink) > 0.7
    assert _relative_luminance(fm.LIGHT.ink) < 0.1


def test_every_palette_field_is_set_in_both_themes():
    """Un campo olvidado en una paleta es un color del otro tema colándose."""
    assert set(fm.LIGHT._fields) == set(fm.DARK._fields)
    for field in fm.LIGHT._fields:
        for pal in (fm.LIGHT, fm.DARK):
            value = getattr(pal, field)
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), (pal, field, value)


@pytest.mark.parametrize("theme", ["LIGHT", "DARK"])
def test_text_clears_the_contrast_floor_in_both_themes(theme):
    """4,5:1 para texto corriente. El barro claro se quedaba en 4,45 y hubo
    que oscurecerlo: sin esta prueba, nadie lo habría vuelto a mirar."""
    pal = getattr(fm, theme)
    pairs = [("ink", "paper"), ("ink", "card"), ("grey", "paper"), ("grey", "card"),
             ("navy", "card"), ("teal", "card"), ("clay", "paper"), ("onnavy", "band")]
    for fg, bg in pairs:
        ratio = contrast(getattr(pal, fg), getattr(pal, bg))
        assert ratio >= 4.5, f"{theme}: {fg} sobre {bg} = {ratio:.2f}"
    assert contrast("#ffffff", pal.band) >= 4.5, f"{theme}: título sobre la banda"


def test_the_header_band_is_a_surface_not_an_ink():
    """En oscuro, `navy` es una tinta clara. Rellenar la banda con ella dejó una
    plancha azul pálido con texto blanco encima."""
    assert _relative_luminance(fm.DARK.band) < 0.1
    assert _relative_luminance(fm.LIGHT.band) < 0.1


def test_the_readme_serves_the_dark_cover_to_dark_readers():
    readme = (MEMORIA.parent.parent / "README.md").read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in readme
    assert "docs/figures/portada-dark.svg" in readme
    assert "docs/figures/portada.svg" in readme


# ---- cubierta: centro, tutor y declaración firmada --------------------------

def test_la_cubierta_lleva_el_centro_el_tutor_y_la_firma():
    from pathlib import Path

    svg = (Path(__file__).resolve().parents[1] / "docs/figures/portada.svg").read_text("utf-8")
    assert "Evolve Academy" in svg
    assert "Julio Valero" in svg
    assert "firmada el" in svg


def test_no_queda_ningun_marcador_sin_renderizar():
    """Dos líneas usaban `{p.blank}` dentro de una cadena que no era f-string,
    así que el SVG publicado llevaba fill="{p.blank}" —un color inválido— y el
    navegador pintaba negro. No falla nada: simplemente sale mal."""
    from pathlib import Path

    figuras = Path(__file__).resolve().parents[1] / "docs/figures"
    for svg in figuras.glob("*.svg"):
        texto = svg.read_text("utf-8")
        assert "{p." not in texto, f"{svg.name}: marcador sin renderizar"
        assert "{esc(" not in texto, svg.name


def test_la_marca_del_centro_es_un_trazo_y_no_un_mapa_de_bits():
    """Se copia el vector de evolve.es y no un PNG: la cubierta es un SVG, así
    que la marca escala con la página y puede teñirse para el tema oscuro."""
    from pathlib import Path

    from tools.build_frontmatter import EVOLVE_MARK, evolve_logo

    assert EVOLVE_MARK.startswith("M ") and EVOLVE_MARK.rstrip().endswith("Z")
    claro = (Path(__file__).resolve().parents[1] / "docs/figures/portada.svg").read_text("utf-8")
    assert EVOLVE_MARK in claro
    # y se tiñe, en vez de arrastrar el #1a1a1a de origen
    assert '#1a1a1a' not in evolve_logo(0, 0, 30, "#ffffff")


def test_el_texto_de_la_cubierta_cabe_en_la_pagina():
    """El ancho es 595 px. Una línea larga no desborda con error: se sale del
    papel y sólo se ve mirando la imagen, que es como se encontró."""
    import re
    from pathlib import Path

    svg = (Path(__file__).resolve().parents[1] / "docs/figures/portada.svg").read_text("utf-8")
    for m in re.finditer(r'<text x="(\d+)"[^>]*font-size="([\d.]+)"[^>]*>(.*?)</text>', svg, re.S):
        x, size = int(m.group(1)), float(m.group(2))
        texto = re.sub(r"<[^>]+>", "", m.group(3))
        # Arial ronda 0,52 em de ancho medio; se deja margen y se comprueba el
        # desbordamiento grosero, que es el que se ve.
        ancho = len(texto) * size * 0.52
        assert x + ancho < 595 + 40, f"se sale: {texto[:60]!r}"
