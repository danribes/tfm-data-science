"""Portada, índice y diagrama de la idea central de la memoria.

    PYTHONPATH=. python tools/build_frontmatter.py

Genera tres artefactos y reescribe una sección de la memoria:

  docs/figures/arquitectura.svg  — las cuatro capas y la regla que las gobierna
  docs/figures/portada.svg       — la cubierta, con ese mismo diagrama
  docs/MEMORIA_TFM.md            — el índice, entre marcadores

El índice se deriva de los encabezados reales del documento. Escribirlo a mano
es garantizar que quede desfasado en la siguiente edición, que es exactamente
el fallo que este repositorio ha corregido ya en el deck: si un número o una
lista puede derivarse del artefacto que la respalda, se deriva.

Los iconos son los del deck (`docs/deck/icons`), 24x24 y `currentColor`, para
que la memoria y la presentación compartan lenguaje visual.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "docs/deck/icons"
FIGURES = ROOT / "docs/figures"
MEMORIA = ROOT / "docs/MEMORIA_TFM.md"

NAVY, TEAL, CLAY, SLATE = "#0b2545", "#087f8c", "#b85622", "#476a9f"
PAPER, INK, GREY = "#f4f7fa", "#1b2430", "#536475"

#: Las cuatro capas, en el orden en que se ejecutan. `check` es lo que la capa
#: siguiente puede comprobar de esta — la regla que da sentido al diagrama.
LAYERS = [
    {"icon": "gauge", "name": "Motor determinista",
     "what": "Identidad de deuda y reglas calibradas,\nen Python y TypeScript",
     "check": "anclas numéricas: 40 series, todos los años"},
    {"icon": "beaker", "name": "Capa empírica",
     "what": "Estimación en panel, modelos predictivos\ny descriptivos",
     "check": "artefactos JSON con muestra, banda y protocolo"},
    {"icon": "doc", "name": "Capa de explicación",
     "what": "Calcula los hechos primero,\nredacta después",
     "check": "inventario numérico: sólo cifras de los hechos"},
    {"icon": "book", "name": "Capa de recuperación",
     "what": "Índice híbrido denso + léxico,\nseparado por colecciones",
     "check": "cita con documento y página verificables"},
]


def icon_paths(name: str) -> str:
    """Los <path> de un icono, sin su <svg> envolvente."""
    svg = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
    return "".join(re.findall(r"<path\b[^>]*/>", svg))


def icon(name: str, x: float, y: float, size: float, color: str) -> str:
    s = size / 24.0
    return (f'<g transform="translate({x},{y}) scale({s})" fill="{color}" '
            f'color="{color}">{icon_paths(name)}</g>')


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chevron(cx: float, y: float, colour: str, w: float = 9, h: float = 6,
            up: bool = False) -> str:
    """Una punta de flecha dibujada explícitamente.

    Los marcadores SVG con `orient="auto"` se rotaban respecto a la dirección
    del trazo y salían apuntando de lado; un trazo explícito no puede girarse
    solo, que es justo lo que se quiere aquí.
    """
    tip = y - h if up else y + h
    return (f'<path d="M {cx - w / 2} {y} L {cx} {tip} L {cx + w / 2} {y}" '
            f'fill="none" stroke="{colour}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def architecture_svg() -> str:
    """Las cuatro capas, el flujo que baja y la comprobación que sube."""
    W, H = 920, 694
    top, band_h, gap = 104, 100, 26
    left = 56
    box_w = 540

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" font-family="Arial, Helvetica, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
           f'<text x="{left}" y="40" font-size="23" font-weight="bold" fill="{NAVY}">'
           'Cada capa sólo puede hacer aquello que la siguiente puede comprobar</text>',
           f'<text x="{left}" y="64" font-size="14" fill="{GREY}">'
           'La regla que ordena el sistema: separar cálculo, evidencia y redacción, '
           'y dejar una comprobación entre cada par.</text>']

    for i, layer in enumerate(LAYERS):
        y = top + i * (band_h + gap)
        out.append(f'<rect x="{left}" y="{y}" width="{box_w}" height="{band_h}" rx="8" '
                   f'fill="white" stroke="{NAVY}" stroke-width="1.5"/>')
        out.append(f'<rect x="{left}" y="{y}" width="6" height="{band_h}" rx="3" fill="{TEAL}"/>')
        out.append(icon(layer["icon"], left + 26, y + 26, 44, NAVY))
        out.append(f'<text x="{left + 90}" y="{y + 34}" font-size="18" font-weight="bold" '
                   f'fill="{NAVY}">{esc(layer["name"])}</text>')
        for k, line in enumerate(layer["what"].split("\n")):
            out.append(f'<text x="{left + 90}" y="{y + 56 + k * 17}" font-size="13.5" '
                       f'fill="{INK}">{esc(line)}</text>')

        # La comprobación, a la derecha, con la flecha que sube hacia la capa previa.
        cx = left + box_w + 30
        out.append(icon("check", cx, y + 20, 20, TEAL))
        out.append(f'<text x="{cx + 27}" y="{y + 28}" font-size="12" font-weight="bold" '
                   f'fill="{TEAL}">COMPROBABLE</text>')
        for k, line in enumerate(_wrap(layer["check"], 34)):
            out.append(f'<text x="{cx}" y="{y + 52 + k * 15}" font-size="12" '
                       f'fill="{GREY}">{esc(line)}</text>')

    # La espina de ejecución, a la izquierda: baja atravesando las cuatro capas.
    spine_x = left - 18
    spine_top, spine_bot = top + 18, top + 3 * (band_h + gap) + band_h - 18
    out.insert(4, f'<path d="M {spine_x} {spine_top} L {spine_x} {spine_bot}" '
                  f'stroke="{NAVY}" stroke-width="2"/>')
    for i in range(len(LAYERS) - 1):
        ay = top + i * (band_h + gap) + band_h + gap / 2 - 3
        out.append(chevron(spine_x, ay, NAVY))

    # La comprobación, a la derecha: sube desde cada capa hacia la anterior.
    ver_x = W - 42
    out.append(f'<path d="M {ver_x} {spine_top} L {ver_x} {spine_bot}" '
               f'stroke="{TEAL}" stroke-width="2" stroke-dasharray="5 4"/>')
    for i in range(len(LAYERS) - 1):
        ay = top + i * (band_h + gap) + band_h + gap / 2 + 3
        out.append(chevron(ver_x, ay, TEAL, up=True))

    foot = H - 40
    out.append(f'<line x1="{left - 30}" y1="{foot - 30}" x2="{W - 30}" y2="{foot - 30}" '
               f'stroke="#d5dee6" stroke-width="1"/>')
    out.append(chevron(left - 18, foot - 12, NAVY))
    out.append(f'<text x="{left - 2}" y="{foot - 3}" font-size="13" fill="{INK}">'
               f'<tspan font-weight="bold" fill="{NAVY}">Ejecución</tspan>'
               '  los hechos se calculan antes de narrarse</text>')
    out.append(chevron(W - 330, foot - 6, TEAL, up=True))
    out.append(f'<text x="{W - 314}" y="{foot - 3}" font-size="13" fill="{GREY}">'
               f'<tspan font-weight="bold" fill="{TEAL}">Comprobación</tspan>'
               '  cada capa deja una traza verificable</text>')
    out.append("</svg>")
    return "\n".join(out)


def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


#: Lo que el motor separa y que la portada resume en cuatro sellos.
CLAIMS = [
    ("check", "Coherencia computacional", "verificada", TEAL),
    ("history", "Descripción histórica", "publicada con su muestra", SLATE),
    ("target", "Capacidad predictiva", "medida y no alcanzada", CLAY),
    ("dismiss", "Identificación causal", "no reclamada", GREY),
]


def portada_svg(title: str, subtitle: str, author: str, programme: str,
                defence: str, vintage: str, engine: str) -> str:
    """Cubierta A4. El campo de la universidad queda a completar a propósito."""
    W, H = 595, 842
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W}" height="{H}" font-family="Arial, Helvetica, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<rect x="0" y="0" width="{W}" height="196" fill="{NAVY}"/>',
           f'<rect x="0" y="196" width="{W}" height="5" fill="{TEAL}"/>']

    # Marca de agua: la identidad de deuda, que es el núcleo del motor.
    out.append(f'<text x="44" y="52" font-size="12.5" fill="#9fd9d3" '
               f'font-family="Georgia, serif" font-style="italic">'
               'b(t) = b(t−1)·(1+i)/(1+g) − sp</text>')

    for k, line in enumerate(_wrap(title, 26)):
        out.append(f'<text x="44" y="{104 + k * 38}" font-size="33" font-weight="bold" '
                   f'fill="white">{esc(line)}</text>')
    for k, line in enumerate(_wrap(subtitle, 58)):
        out.append(f'<text x="44" y="{166 + k * 19}" font-size="14.5" '
                   f'fill="#9fd9d3">{esc(line)}</text>')

    # El diagrama de la idea central, reducido a cuatro bandas.
    y0 = 240
    out.append(f'<text x="44" y="{y0 - 14}" font-size="12" font-weight="bold" '
               f'letter-spacing="1.2" fill="{GREY}">LA IDEA CENTRAL</text>')
    for i, layer in enumerate(LAYERS):
        y = y0 + i * 52
        out.append(f'<rect x="44" y="{y}" width="{W - 88}" height="42" rx="6" '
                   f'fill="{PAPER}" stroke="{NAVY}" stroke-width="1"/>')
        out.append(f'<rect x="44" y="{y}" width="5" height="42" rx="2.5" fill="{TEAL}"/>')
        out.append(icon(layer["icon"], 64, y + 11, 21, NAVY))
        out.append(f'<text x="97" y="{y + 20}" font-size="13.5" font-weight="bold" '
                   f'fill="{NAVY}">{esc(layer["name"])}</text>')
        out.append(f'<text x="97" y="{y + 34}" font-size="10.5" fill="{GREY}">'
                   f'{esc(layer["check"])}</text>')
        if i < len(LAYERS) - 1:
            out.append(chevron(68, y + 44, NAVY, w=8, h=5))
        out.append(icon("check", W - 74, y + 12, 18, TEAL))

    # Los cuatro sellos: qué se acredita y qué no.
    ys = y0 + 4 * 52 + 22
    out.append(f'<text x="44" y="{ys}" font-size="12" font-weight="bold" '
               f'letter-spacing="1.2" fill="{GREY}">QUÉ SE ACREDITA Y QUÉ NO</text>')
    for i, (ic, label, verdict, colour) in enumerate(CLAIMS):
        cx, cy = 44 + (i % 2) * 254, ys + 16 + (i // 2) * 46
        out.append(f'<rect x="{cx}" y="{cy}" width="240" height="38" rx="5" '
                   f'fill="white" stroke="{colour}" stroke-width="1.2"/>')
        out.append(icon(ic, cx + 12, cy + 11, 17, colour))
        out.append(f'<text x="{cx + 38}" y="{cy + 17}" font-size="11.5" '
                   f'font-weight="bold" fill="{NAVY}">{esc(label)}</text>')
        out.append(f'<text x="{cx + 38}" y="{cy + 30}" font-size="10.5" '
                   f'fill="{colour}">{esc(verdict)}</text>')

    # El hallazgo que sostiene la memoria, en el hueco entre los sellos y el pie.
    hy = ys + 16 + 2 * 46 + 12
    out.append(f'<rect x="44" y="{hy}" width="{W - 88}" height="58" rx="6" '
               f'fill="{PAPER}" stroke="{TEAL}" stroke-width="1.2"/>')
    out.append(f'<rect x="44" y="{hy}" width="5" height="58" rx="2.5" fill="{CLAY}"/>')
    out.append(icon("bulb", 62, hy + 13, 19, CLAY))
    out.append(f'<text x="90" y="{hy + 21}" font-size="11.5" font-weight="bold" '
               f'letter-spacing="0.8" fill="{CLAY}">HALLAZGO METODOLÓGICO PRINCIPAL</text>')
    finding = ("Preservar los movimientos nacionales comunes al remuestrear ensancha la banda "
               "regional hasta que el 3 % heredado deja de rechazarse.")
    for k, line in enumerate(_wrap(finding, 82)):
        out.append(f'<text x="90" y="{hy + 38 + k * 14}" font-size="11" '
                   f'fill="{INK}">{esc(line)}</text>')

    # Pie: autoría y sello del corte. La universidad y el tutor van vacíos.
    fy = H - 176
    out.append(f'<line x1="44" y1="{fy}" x2="{W - 44}" y2="{fy}" stroke="#d5dee6" stroke-width="1"/>')
    out.append(f'<text x="44" y="{fy + 26}" font-size="16" font-weight="bold" '
               f'fill="{NAVY}">{esc(author)}</text>')
    out.append(f'<text x="44" y="{fy + 46}" font-size="12.5" fill="{INK}">{esc(programme)}</text>')
    out.append(f'<text x="44" y="{fy + 70}" font-size="12.5" fill="{GREY}">'
               '<tspan font-weight="bold">Universidad:</tspan> '
               '<tspan fill="#b0bcc7">_______________________________________</tspan></text>')
    out.append(f'<text x="44" y="{fy + 90}" font-size="12.5" fill="{GREY}">'
               '<tspan font-weight="bold">Tutor/a:</tspan> '
               '<tspan fill="#b0bcc7">___________________________________________</tspan></text>')
    out.append(f'<text x="44" y="{fy + 116}" font-size="12.5" fill="{INK}">'
               f'<tspan font-weight="bold">Defensa:</tspan> {esc(defence)}</text>')

    out.append(f'<rect x="0" y="{H - 52}" width="{W}" height="52" fill="{PAPER}"/>')
    out.append(f'<rect x="0" y="{H - 52}" width="{W}" height="3" fill="{TEAL}"/>')
    out.append(icon("calendar", 44, H - 38, 17, GREY))
    out.append(f'<text x="70" y="{H - 25}" font-size="11" fill="{GREY}">'
               f'Corte de datos {esc(vintage)} · motor {esc(engine)} · '
               'proyección condicional, no previsión</text>')

    out.append("</svg>")
    return "\n".join(out)


BEGIN, END = "<!-- INDICE:INICIO -->", "<!-- INDICE:FIN -->"


def build_index(text: str) -> str:
    """Índice numerado a partir de los encabezados ## y ### reales."""
    body = text.split(END, 1)[1] if END in text else text
    rows, skip = [], {"Referencias", "Anexos"}
    for line in body.splitlines():
        m = re.match(r"^(#{2,3}) (.+)$", line)
        if not m:
            continue
        level, title = len(m.group(1)), m.group(2).strip()
        # El rótulo del índice no lleva LaTeX: «$r-g$» se lee mal en una lista.
        label = title.replace("$", "")
        anchor = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
        indent = "  " * (level - 2)
        rows.append(f"{indent}- [{label}](#{anchor})")
    return "\n".join(rows)


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    (FIGURES / "arquitectura.svg").write_text(architecture_svg(), encoding="utf-8")

    text = MEMORIA.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    main_title, _, subtitle = title.partition(":")
    (FIGURES / "portada.svg").write_text(
        portada_svg(main_title.strip(), subtitle.strip(),
                    "Daniel Ribes", "Máster en Inteligencia Artificial y Data Science",
                    "28 de septiembre de 2026", "2026-07-31", "1.1.0"),
        encoding="utf-8")

    if BEGIN in text and END in text:
        idx = build_index(text)
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        MEMORIA.write_text(f"{head}{BEGIN}\n\n{idx}\n\n{END}{tail}", encoding="utf-8")
        print(f"índice: {len(idx.splitlines())} entradas")
    else:
        print("índice: marcadores ausentes en la memoria, no se ha tocado")

    for f in ("arquitectura.svg", "portada.svg"):
        print(f"{FIGURES / f}  {(FIGURES / f).stat().st_size / 1000:.1f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
