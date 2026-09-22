#!/usr/bin/env python3
"""Genera la presentación PowerPoint del front-end.

    SHOT=<dir-de-capturas> PYTHONPATH=. python tools/build_deck_frontend.py

Diapositivas 16:9 con una captura de la aplicación desplegada y un texto que
dice qué se está mirando y qué NO puede afirmarse de ello. Se construye con
python-pptx, así que las formas son editables: no es un PDF metido en una
diapositiva ni una imagen de un diseño.

Reglas de la casa que se aplican aquí: ninguna plantilla vacía de «Haga clic
para agregar…» —se parte de un diseño en blanco y se añade sólo lo que se
usa—, y el texto de los bloques va alineado a la izquierda, nunca centrado.
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
CAPTURAS = Path(os.environ.get("SHOT", RAIZ / "docs/deck/capturas"))
DESTINO = RAIZ / "docs/Presentacion_frontend.pptx"

NAVY = RGBColor(0x0F, 0x2B, 0x46)
TEAL = RGBColor(0x08, 0x7F, 0x8C)
GRIS = RGBColor(0x5A, 0x6B, 0x7A)
TINTA = RGBColor(0x1A, 0x1A, 0x1A)

W, H = Inches(13.333), Inches(7.5)

#: (imagen, título, frase que dice qué se mira, límite declarado)
SLIDES: list[tuple[str | None, str, str, str]] = [
    (None, "España en escenarios",
     "Análisis macrofiscal condicional para España, con evaluación empírica y "
     "explicaciones trazables.", ""),
    ("01-portada.png", "La aplicación se presenta antes de usarse",
     "Qué hace, las cuatro capas y qué se acredita de cada una.",
     "Capacidad predictiva: medida y no alcanzada. Identificación causal: no reclamada."),
    ("02-tabla.png", "El futuro, en números",
     "Ocho series a 2026, 2030, 2040 y 2050, con el valor del escenario y su "
     "diferencia frente a la base.",
     "Paro e IPCA van marcados «sin senda propia»: el motor no les da trayectoria."),
    ("06-pensiones.png", "Ejemplo 1 · indexar las pensiones un punto más",
     "Las pensiones pasan de 22,3 a 28,2 %PIB en 2050 y la deuda de 223,8 a 286,6.",
     "Aritmética bajo un supuesto contable: sin respuesta de política ni efectos de segunda ronda."),
    ("07-euribor.png", "Ejemplo 2 · el Euríbor dos puntos arriba",
     "La cuota sube de 1.213 a 1.409 € y el esfuerzo hipotecario de 49,1 % a 59,0 %, "
     "aunque el precio baje.",
     "El coeficiente del tipo sobre la vivienda no está identificado por este corte de datos."),
    ("11-comprador.png", "El mismo ejemplo, preguntado por quien lo vive",
     "El comprador pulsa «¿Y si el Euríbor sube al 4,8 %?» y la pregunta aplica "
     "su propio supuesto: 59,0 % de esfuerzo en 2035 frente al 49,1 % de la base.",
     "Misma aritmética que la diapositiva anterior. Quien pregunta no tiene que "
     "saber qué palanca mover."),
    ("12-jubilado.png", "Y una pregunta que no supone nada",
     "«¿Cuánto costará pagar las pensiones?» — 16,49 %PIB en 2035 y 22,3 en 2050, "
     "con la dependencia 65+ subiendo de 32,6 a 59,0 por cada cien.",
     "Sin ninguna palanca movida la base y el escenario coinciden, así que sólo se "
     "ve una línea: esto es demografía, no una decisión de política."),
    ("03-banda.png", "La única serie con banda de incertidumbre",
     "Mide cuánto se mueve la proyección si los dos parámetros estimados no se dan "
     "por exactos: un 17 % del nivel en 2050.",
     "No es un intervalo de predicción: excluye error de modelo, cambios estructurales y las palancas."),
    ("10-presupuesto.png", "A dónde va el gasto",
     "Siete partidas identificadas del presupuesto, de pensiones a inversión pública.",
     "El gasto total no evoluciona, así que desde 2035 las partidas suman más que él. La tarjeta lo dice."),
    ("05-analogos.png", "España entre los demás",
     "Episodios históricos parecidos al escenario, y qué le pasó después a cada país.",
     "Descriptivo. España está excluida del conjunto de referencia por construcción."),
    ("08-consulta.png", "Las respuestas citan documento y página",
     "Corpus de 58 obras académicas; búsqueda híbrida, densa y por palabras.",
     "La cita acredita procedencia, no que el pasaje respalde cada frase."),
    ("09c-horizonte.png", "El error, horizonte a horizonte",
     "MASE del modelo frente a la deriva. Gana en 2 trimestres y pierde en los "
     "otros tres; contra las referencias ingenuas gana en todos.",
     "MASE escala el error por el de un pronóstico ingenuo, para poder promediar series de distinto tamaño."),
    ("09b-resultado.png", "El resultado negativo se publica",
     "La red neuronal no batió a una extrapolación de tendencia: 5 comunidades de 17 "
     "cuando la regla exigía 12.",
     "La regla se fijó antes de ver el resultado. Por eso la pantalla no enseña una predicción puntual."),
]


def _fondo(slide, prs):
    fondo = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    fondo.fill.solid(); fondo.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    fondo.line.fill.background(); fondo.shadow.inherit = False
    return fondo


def _texto(slide, x, y, cx, cy, texto, *, size, color, bold=False, italic=False):
    caja = slide.shapes.add_textbox(x, y, cx, cy)
    tf = caja.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT          # nunca centrado: regla de la casa
    r = p.add_run(); r.text = texto
    r.font.size = Pt(size); r.font.color.rgb = color
    r.font.bold = bold; r.font.italic = italic
    r.font.name = "Calibri"
    return caja


def build(capturas: Path = CAPTURAS, destino: Path = DESTINO) -> Path:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blanco = prs.slide_layouts[6]        # diseño en blanco: sin placeholders vacíos

    for imagen, titulo, que, limite in SLIDES:
        s = prs.slides.add_slide(blanco)
        _fondo(s, prs)
        if imagen is None:
            s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(2.6)).fill.solid()
            s.shapes[-1].fill.fore_color.rgb = NAVY
            s.shapes[-1].line.fill.background(); s.shapes[-1].shadow.inherit = False
            _texto(s, Inches(0.9), Inches(0.85), Inches(11.5), Inches(1.2), titulo,
                   size=40, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True)
            _texto(s, Inches(0.9), Inches(3.1), Inches(11.0), Inches(1.4), que,
                   size=18, color=TINTA)
            _texto(s, Inches(0.9), Inches(4.4), Inches(11.0), Inches(2.0),
                   "Daniel Ribes · Máster en Inteligencia Artificial y Data Science\n"
                   "Evolve Academy · tutor: Julio Valero\n"
                   "Corte de datos 2026-07-31 · motor 1.1.0\n"
                   "danribes.github.io/tfm-data-science",
                   size=14, color=GRIS)
            continue

        _texto(s, Inches(0.6), Inches(0.34), Inches(12.2), Inches(0.6), titulo,
               size=26, color=NAVY, bold=True)
        _texto(s, Inches(0.6), Inches(0.95), Inches(12.2), Inches(0.55), que,
               size=14.5, color=TINTA)

        ruta = capturas / imagen
        iw, ih = Image.open(ruta).size
        disp_w, disp_h = Inches(12.1), Inches(4.72)
        escala = min(disp_w / iw, disp_h / ih)
        w, h = Emu(int(iw * escala)), Emu(int(ih * escala))
        # Centrada tambien en vertical: las capturas anchas y bajas dejaban un
        # hueco al pie de la diapositiva.
        banda_y, banda_alto = Inches(1.62), Inches(4.72)
        s.shapes.add_picture(str(ruta), Emu(int((prs.slide_width - w) / 2)),
                             Emu(int(banda_y + (banda_alto - h) / 2)), w, h)

        if limite:
            barra = s.shapes.add_shape(1, Inches(0.6), Inches(6.5), Inches(12.1), Inches(0.62))
            barra.fill.solid(); barra.fill.fore_color.rgb = RGBColor(0xFD, 0xF3, 0xE2)
            barra.line.color.rgb = RGBColor(0xE0, 0xA3, 0x4A)
            barra.shadow.inherit = False
            # el texto va en su propia caja, separado del borde del chip
            _texto(s, Inches(0.82), Inches(6.62), Inches(11.7), Inches(0.42),
                   limite, size=12.5, color=RGBColor(0xA8, 0x6A, 0x00))

    destino.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(destino))
    return destino


if __name__ == "__main__":
    out = build()
    p = Presentation(str(out))
    vacios = sum(1 for s in p.slides for sh in s.shapes
                 if sh.has_text_frame and not sh.text_frame.text.strip())
    print(f"{out}  {out.stat().st_size / 1000:.0f} kB")
    print(f"  {len(p.slides.__iter__.__self__._sldIdLst)} diapositivas · "
          f"marcadores vacíos: {vacios}")
