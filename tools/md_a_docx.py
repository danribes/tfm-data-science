#!/usr/bin/env python3
"""Convierte un Markdown del proyecto a Word con la tipografía de la casa.

    PYTHONPATH=. python tools/md_a_docx.py docs/ACTUALIZAR_DATOS.md
    PYTHONPATH=. python tools/md_a_docx.py docs/PRESENTACION_10MIN.md --perfil guion

Ningún .docx se versiona: el Markdown es la fuente, es el que se revisa y es el
que tiene sus cifras comprobadas contra el motor. Versionar los dos invita a
que dos documentos digan cosas distintas.

Dos perfiles, porque no se leen igual:

  · `guion` — se lee de pie, a distancia y mientras se habla. Cuerpo a 12,5
    puntos, interlineado amplio, y las acotaciones escénicas en cursiva gris
    para no confundirlas con lo que se dice en voz alta.

  · `documento` — se lee sentado, con el teclado delante. Cuerpo algo menor y
    los bloques de código en monoespaciada sobre fondo claro, que es la mitad
    de un procedimiento que se copia y se pega.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Inches, Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]

PERFILES = {
    "guion": {
        "cuerpo": 12.5, "interlineado": 1.3, "h1": 19, "h2": 15.5,
        "cita_italica": True, "toc": True,
    },
    "documento": {
        "cuerpo": 11.5, "interlineado": 1.22, "h1": 18, "h2": 14.5,
        "cita_italica": True, "toc": True,
    },
}

NAVY, TEAL, GRIS = "0F2B46", "087F8C", "5A6B7A"


def _estilo(style, *, size=None, color=None, bold=None, italic=None, fuente=None,
            antes=None, despues=None, interlineado=None, sangria=None):
    f = style.font
    if size is not None:
        f.size = Pt(size)
    if color is not None:
        f.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if fuente is not None:
        f.name = fuente
    # Los estilos de carácter —«Verbatim Char» es uno— no tienen formato de
    # párrafo, y pedírselo revienta.
    pf = getattr(style, "paragraph_format", None)
    if pf is None:
        return
    if antes is not None:
        pf.space_before = Pt(antes)
    if despues is not None:
        pf.space_after = Pt(despues)
    if sangria is not None:
        pf.left_indent = Inches(sangria)
    if interlineado is not None:
        pf.line_spacing = interlineado
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE


def build(origen: Path, destino: Path | None = None, perfil: str = "documento") -> Path:
    cfg = PERFILES[perfil]
    destino = destino or origen.with_suffix(".docx")
    cmd = ["pandoc", str(origen), "-o", str(destino), "--from", "gfm"]
    if cfg["toc"]:
        cmd += ["--toc", "--toc-depth=2", "--metadata", "toc-title=Índice"]
    subprocess.run(cmd, check=True)

    d = Document(str(destino))
    S = d.styles
    nombres = {s.name for s in S}
    _estilo(S["Normal"], size=cfg["cuerpo"], interlineado=cfg["interlineado"],
            despues=9, fuente="Calibri")
    _estilo(S["Title"], size=24, bold=True, color=NAVY, despues=14)
    _estilo(S["Heading 1"], size=cfg["h1"], bold=True, color=NAVY, antes=22, despues=8)
    _estilo(S["Heading 2"], size=cfg["h2"], bold=True, color=TEAL, antes=20, despues=7)
    if "Heading 3" in nombres:
        _estilo(S["Heading 3"], size=cfg["h2"] - 2, bold=True, color=NAVY, antes=14, despues=5)
    for nombre in ("Block Text", "Quote", "Block Quote"):
        if nombre in nombres:
            _estilo(S[nombre], size=cfg["cuerpo"] - 1, italic=cfg["cita_italica"],
                    color=GRIS, antes=6, despues=10, sangria=0.28)
    # Los bloques de codigo son la mitad de un procedimiento que se copia.
    for nombre in ("Source Code", "Verbatim Char", "SourceCode"):
        if nombre in nombres:
            _estilo(S[nombre], size=cfg["cuerpo"] - 1.5, fuente="Consolas",
                    color="1A1A1A")
    for sec in d.sections:
        sec.left_margin = sec.right_margin = Inches(0.95)
        sec.top_margin = sec.bottom_margin = Inches(0.85)
    d.save(str(destino))
    return destino


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origen", type=Path)
    ap.add_argument("--destino", type=Path, default=None)
    ap.add_argument("--perfil", choices=sorted(PERFILES), default="documento")
    args = ap.parse_args()
    if not args.origen.exists():
        print(f"no existe: {args.origen}")
        return 1
    out = build(args.origen, args.destino, args.perfil)
    doc = Document(str(out))
    print(f"{out}  {out.stat().st_size / 1000:.1f} kB  · perfil {args.perfil}")
    print(f"  {len(doc.paragraphs)} párrafos · {len(doc.tables)} tablas · "
          f"{sum(1 for p in doc.paragraphs if p.style.name.startswith('Heading'))} encabezados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
