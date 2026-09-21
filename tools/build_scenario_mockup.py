"""Maqueta de la «ficha del escenario»: propuesta de portada del panel.

    PYTHONPATH=. python tools/build_scenario_mockup.py
    PYTHONPATH=. python tools/build_scenario_mockup.py --lever r=4.8 --lever prima=150

Escribe `docs/mockups/ficha-escenario.html`, una página estática que propone
cómo debería abrir la aplicación: qué has cambiado, qué implica, la
trayectoria, **el futuro en una tabla** y qué lo mueve.

Es una maqueta, no la aplicación: no hay estado, los botones no hacen nada y
nada de esto está conectado al panel. Lo que sí es real son las cifras, que
salen del motor en cada ejecución. Una maqueta con números inventados invita a
decidir sobre un diseño que luego no cuadra con los datos, y este repositorio
ya ha pagado ese precio en el deck.

Tres decisiones de diseño que conviene no perder si la propuesta se acepta:

  · El color del delta no puede ser «sube = rojo». Un salario que sube no es
    mala noticia. Se usa `up_is_bad` de explain.facts, y las series cuyo signo
    depende de quién pregunta —las de SIDES— van en azul y sin veredicto, igual
    que hace ya la narración.

  · Las series sin senda propia se marcan. `u` y `pi` son constantes en toda la
    proyección de la línea base: el motor no les da trayectoria, sólo un
    desplazamiento en bloque cuando una palanca las empuja. Dibujar esa recta
    sin decirlo es lo que hace pensar que la herramienta está rota.

  · El año de lectura por defecto no es Y0. En el primer año no ha pasado nada
    todavía y todos los deltas salen 0,0, que es exactamente la primera
    impresión que hay que evitar.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.levers import BASE_LEVERS, LEVER_SPECS, Levers
from engine.spain import Y0, baseline, run_scenario
from explain.facts import HEADLINES, SERIES_META, SIDES, decompose

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/mockups/ficha-escenario.html"

#: Las filas de la tabla. Ocho: más deja de poder leerse de un vistazo.
ROWS = [("b", "Deuda pública"), ("u", "Paro"), ("pi", "IPCA"),
        ("saldo", "Saldo público"), ("precio", "Precio vivienda"),
        ("cuota", "Cuota hipotecaria"), ("salario", "Salario medio"),
        ("esf", "Esfuerzo vivienda")]

#: De dónde sale cada cifra. No es decoración: es la pregunta que más veces se
#: hace sobre un trabajo con «IA» en el título, y la respuesta honesta para
#: casi todas estas filas es «de una identidad contable», no de un modelo
#: aprendido. Comprobado, no supuesto: las seis series marcadas PANEL son las
#: que cambian al sustituir IPV_LR e IPV_REV por sus valores heredados.
PANEL_DEPENDENT = {"ipv", "precio", "cuota", "esf", "hip", "sobre"}

LAYERS = [
    ("motor", "MOTOR",
     "Identidad contable de la deuda más reglas calibradas. Determinista: "
     "las mismas palancas dan siempre el mismo número, y se reproduce en "
     "Python y en el navegador con anclas compartidas."),
    ("panel", "PANEL",
     "Dos constantes de la cadena de vivienda estimadas con econometría de "
     "panel sobre 19 unidades: media de largo plazo 1,2151 % "
     "[0,9008; 1,5295] y reversión anual 0,2039 [0,1811; 0,2268]. Son los "
     "únicos parámetros del motor que vienen de los datos."),
    ("dl", "APRENDIZAJE PROFUNDO",
     "No interviene en estas cifras. La red se entrenó con 1.760 series "
     "extranjeras y no superó a una extrapolación de tendencia —MASE 0,4000 "
     "frente a 0,3953, gana en 5 de 17 comunidades cuando la regla exigía "
     "12—. El resultado negativo se conserva; el modelo no se usa."),
    ("ml", "CLASIFICADOR",
     "Gradient boosting sobre 3.874 país-año de 154 países. Produce una "
     "puntuación exploratoria de tensión soberana, no una probabilidad "
     "calibrada, y no entra en la senda de deuda de esta tabla."),
    ("knn", "ANÁLOGOS",
     "Vecinos históricos por distancia de Mahalanobis sobre 4.091 "
     "observaciones de 173 países, con España excluida del conjunto de "
     "referencia. Descriptivo: la semejanza histórica no predice."),
    ("llm", "RAG Y LENGUAJE",
     "Cero cifras. La recuperación documental cita pasajes con documento y "
     "página; el modelo de lenguaje redacta sobre hechos ya calculados y una "
     "comprobación posterior rechaza cualquier magnitud que no esté en ellos."),
]
COLUMNS = (2026, 2030, 2040, 2050)
READING_YEAR = 2035          # el año de lectura propuesto; los stocks van a Y1


def meta_for(key: str) -> dict:
    by_key = {h["key"]: h for h in HEADLINES}
    return by_key.get(key) or SERIES_META.get(key, {})


def nf(value: float, dec: int) -> str:
    """Formato español: millares con punto, decimales con coma."""
    return f"{value:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def signed(value: float, dec: int) -> str:
    if abs(value) < 5e-3:
        return "0,0" if dec else "0"
    return ("+" if value > 0 else "−") + nf(abs(value), dec)


def tone(delta: float, row: dict) -> str:
    """Verde/rojo sólo cuando el signo del bienestar es de la serie, no del lector."""
    if abs(delta) < 5e-3:
        return "zero"
    if row["reader_relative"]:
        return "rel"
    return "up" if (delta > 0) == row["up_is_bad"] else "dn"


def collect(levers: Levers) -> dict:
    base, scn = baseline(), run_scenario(levers)
    moved = []
    for spec in LEVER_SPECS:
        now = getattr(levers, spec["id"])
        if abs(now - BASE_LEVERS[spec["id"]]) > 1e-12:
            moved.append({"name": spec["nm"], "unit": spec["unit"],
                          "base": BASE_LEVERS[spec["id"]], "value": now,
                          "dec": spec["dec"]})
    rows = []
    for key, label in ROWS:
        m = meta_for(key)
        b, s = base[key], scn[key]
        rows.append({
            "key": key, "label": label, "unit": m.get("unit", ""),
            "dec": m.get("dec", 1), "up_is_bad": bool(m.get("up_is_bad", True)),
            "reader_relative": key in SIDES,
            # Sin senda propia: la línea base no se mueve en 25 años.
            "pinned": max(b) - min(b) < 1e-9,
            "panel": key in PANEL_DEPENDENT,
            "cells": [{"year": y, "scn": s[y - Y0], "delta": s[y - Y0] - b[y - Y0]}
                      for y in COLUMNS],
        })
    contribs, _interaction, joint = decompose(levers, "b", 2050 - Y0) if moved else ([], 0.0, 0.0)
    return {"moved": moved, "rows": rows, "joint": joint,
            "world": world(levers),
            "contrib": [{"name": c.lever_name, "delta": c.delta, "share": c.share}
                        for c in contribs],
            "path": {"years": list(range(Y0, 2051)), "base": base["b"], "scn": scn["b"]}}


def world(levers: Levers) -> dict:
    """España situada entre los demás países, por dos vías distintas.

    Ninguna de las dos predice. Los análogos son descriptivos y excluyen a
    España del conjunto de referencia por construcción; la puntuación de
    tensión es la salida bruta de un clasificador entrenado en otros países,
    sin calibrar, y España queda fuera del conjunto etiquetado. Decirlo aquí
    importa más que la cifra: es la lectura que se presta a sobreinterpretar.
    """
    out: dict = {"analogs": [], "distress": None}
    try:
        from engine.analog import find_analogs
        for a in find_analogs(levers, horizon=10):
            snap = a.get("match_snapshot", {})
            tail = a.get("outcome") or []
            out["analogs"].append({
                "iso3": a["iso3"], "name": a["country_name"], "year": a["match_year"],
                "distance": a["distance"], "debt": snap.get("debt_gdp"),
                "balance": snap.get("overall_balance_gdp"),
                "unemployment": snap.get("unemployment"),
                "after": (tail[-1].get("debt_gdp") if tail else None),
                "after_years": (tail[-1].get("year_offset") if tail else None)})
    except Exception as exc:                                   # noqa: BLE001
        out["analogs_error"] = f"{type(exc).__name__}: {exc}"
    try:
        d = json.loads((ROOT / "docs/eval/distress.json").read_text(encoding="utf-8"))
        sp = d.get("spain") or {}
        out["distress"] = {
            "score": sp.get("probability"), "year": sp.get("year"),
            "base_rate": d.get("base_rate"), "n_countries": d.get("n_countries"),
            "n_rows": d.get("n"), "auc": d.get("auc"),
            "coverage": sp.get("coverage"), "in_label_set": sp.get("in_label_set")}
    except Exception as exc:                                   # noqa: BLE001
        out["distress_error"] = f"{type(exc).__name__}: {exc}"
    return out


def chart(path: dict, width: int = 720, height: int = 230, pad: int = 34) -> str:
    ys, bs, sc = path["years"], path["base"], path["scn"]
    lo, hi = min(min(bs), min(sc)) - 6, max(max(bs), max(sc)) + 6
    x = lambda i: pad + i * (width - pad - 12) / (len(ys) - 1)          # noqa: E731
    y = lambda v: height - pad - (v - lo) / (hi - lo) * (height - 2 * pad)  # noqa: E731
    line = lambda vs: " ".join(("M" if i == 0 else "L") + f"{x(i):.1f} {y(v):.1f}"  # noqa: E731
                               for i, v in enumerate(vs))
    ticks = [t for t in (120, 160, 200, 240, 280) if lo < t < hi]
    grid = "".join(
        f'<line x1="{pad}" y1="{y(t):.1f}" x2="{width-12}" y2="{y(t):.1f}" stroke="var(--grid)"/>'
        f'<text x="{pad-6}" y="{y(t)+4:.1f}" text-anchor="end" font-size="10" '
        f'fill="var(--muted)">{nf(t,0)}</text>' for t in ticks)
    xlab = "".join(
        f'<text x="{x(i):.1f}" y="{height-12}" text-anchor="middle" font-size="10" '
        f'fill="var(--muted)">{yr}</text>'
        for i, yr in enumerate(ys) if yr in COLUMNS)
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}">{grid}'
            f'<line x1="{x(0):.1f}" y1="{pad-12}" x2="{x(0):.1f}" y2="{height-pad}" '
            f'stroke="var(--muted)" stroke-dasharray="3 3"/>'
            f'<text x="{x(0)+6:.1f}" y="{pad-15}" font-size="10.5" fill="var(--muted)">'
            'dato observado · proyección →</text>'
            f'<path d="{line(bs)}" fill="none" stroke="var(--muted)" stroke-width="1.6" '
            'stroke-dasharray="5 4"/>'
            f'<path d="{line(sc)}" fill="none" stroke="var(--lab)" stroke-width="2.4"/>'
            f'{xlab}</svg>')


STYLE = """
:root{--page:#f7f5f0;--surface:#fcfcfb;--card:#f9f9f7;--ink:#1a1a1a;--ink-2:#52514e;
--muted:#898781;--grid:#e1e0d9;--accent:#2a78d6;--lab:#b0399a;--good:#006300;
--div-neg:#e34948;--warn:#a86a00;--chip:#eef3fa;--chip-lab:#fbecf7;--chip-warn:#fdf3e2;
color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--page:#060606;
--surface:#1a1a19;--card:#141413;--ink:#f4f4f1;--ink-2:#b9b8b2;--grid:#2a2a28;
--chip:#16212e;--chip-lab:#2a1526;--chip-warn:#2e2415;--accent:#6aa9ec;--lab:#e082cd;
--good:#5fbf72;--div-neg:#ff6b6a;--warn:#e0a34a;color-scheme:dark}}
:root[data-theme=dark]{--page:#060606;--surface:#1a1a19;--card:#141413;--ink:#f4f4f1;
--ink-2:#b9b8b2;--grid:#2a2a28;--chip:#16212e;--chip-lab:#2a1526;--chip-warn:#2e2415;
--accent:#6aa9ec;--lab:#e082cd;--good:#5fbf72;--div-neg:#ff6b6a;--warn:#e0a34a;
color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;padding:26px;background:var(--page);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:980px;margin:0 auto;display:flex;flex-direction:column;gap:18px}
h1{font-size:23px;margin:0}
h2{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
margin:0 0 10px;font-weight:700}
.card{background:var(--surface);border:1px solid var(--grid);border-radius:8px;padding:18px}
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.stamp{font-size:12px;color:var(--muted);border:1px solid var(--grid);border-radius:999px;
padding:4px 11px;background:var(--card)}
.pill{background:var(--chip-lab);color:var(--lab);border-radius:999px;padding:5px 12px;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{background:var(--card);border:1px solid var(--grid);border-radius:8px;padding:12px 14px}
.kpi .lab{font-size:12px;color:var(--muted)}
.kpi .val{font-size:25px;font-weight:700;margin:3px 0}
.kpi .u{font-size:13px;font-weight:400;color:var(--muted)}
.kpi .dlt{font-size:12.5px;font-weight:600}
.up{color:var(--div-neg)}.dn{color:var(--good)}.zero{color:var(--muted)}.rel{color:var(--accent)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{padding:7px 9px;border-bottom:1px solid var(--grid);text-align:left}
thead th{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
border-bottom:2px solid var(--grid)}
tbody th{font-weight:600}
tbody th small{display:block;font-weight:400;color:var(--muted);font-size:11.5px}
.num{text-align:right;font-variant-numeric:tabular-nums}
td.d{font-size:12.5px;font-weight:600;padding-left:2px}
.tag{display:inline-block;font-size:10.5px;border-radius:4px;padding:1px 6px;
margin-left:6px;font-weight:600}
.tag.warn{background:var(--chip-warn);color:var(--warn)}
.tag.rel{background:var(--chip);color:var(--accent)}
.bar{width:120px}.bar span{display:block;height:8px;border-radius:4px;background:var(--lab)}
.acts{display:flex;gap:8px;margin-top:12px}
button{font:inherit;font-size:12.5px;padding:6px 13px;border:1px solid var(--grid);
border-radius:6px;background:var(--card);color:var(--ink);cursor:pointer}
.foot{font-size:12px;color:var(--muted)}
.key{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--muted);margin-top:10px}
.tag.prov{background:var(--chip);color:var(--accent);font-weight:700;letter-spacing:.03em}
.tag.prov.motor{background:var(--code);color:var(--ink-2)}
.tag.prov.dl,.tag.prov.ml{background:var(--chip-warn);color:var(--warn)}
.tag.prov.knn{background:var(--chip-lab);color:var(--lab)}
.tag.prov.llm{background:var(--code);color:var(--ink-2)}
table.layers th{width:190px;vertical-align:top}
table.layers td.lay{font-size:12.5px;color:var(--ink-2)}
h3{color:var(--ink)}
.scale{position:relative;height:10px;border-radius:5px;margin:14px 0 6px;
background:linear-gradient(90deg,var(--good),var(--warn),var(--div-neg))}
.scale .mark{position:absolute;top:-5px;width:3px;height:20px;background:var(--ink);border-radius:2px}
.scale .tick{position:absolute;top:-3px;width:2px;height:16px;background:var(--surface);opacity:.9}
.scalelab{display:flex;justify-content:space-between;font-size:11.5px;color:var(--muted)}
.note{background:var(--chip-warn);border-left:3px solid var(--warn);border-radius:0 6px 6px 0;
padding:10px 14px;font-size:12.5px;color:var(--ink-2)}
"""


def render_world(w: dict) -> str:
    """España situada entre los demás, con la advertencia pegada a la cifra."""
    if w.get("analogs_error") or w.get("distress_error"):
        return ('<div class="note">No se han podido construir las comparaciones '
                f'internacionales: {w.get("analogs_error") or w.get("distress_error")}</div>')
    def who(a: dict) -> str:
        """El panel no trae nombre para todos los países; entonces queda el ISO."""
        return a["name"] if a["name"] == a["iso3"] else f'{a["name"]} ({a["iso3"]})'

    rows = "".join(
        f'<tr><th scope="row">{who(a)} · {a["year"]}</th>'
        f'<td class="num">{nf(a["debt"], 1)}</td>'
        f'<td class="num">{nf(a["balance"], 1) if a["balance"] is not None else "—"}</td>'
        f'<td class="num">{nf(a["unemployment"], 1) if a["unemployment"] is not None else "—"}</td>'
        f'<td class="num"><strong>{nf(a["after"], 1) if a["after"] is not None else "—"}</strong></td>'
        f'<td class="num">{a["distance"]:.3f}</td></tr>' for a in w["analogs"])
    d = w["distress"] or {}
    score, base = d.get("score"), d.get("base_rate")
    pos = max(2.0, min(98.0, (score / (base * 3)) * 100)) if (score and base) else 50.0
    return f"""
<h3 style="font-size:14px;margin:0 0 8px">Vecinos históricos más parecidos al escenario</h3>
<table><thead><tr><th>País · año</th><th class="num">Deuda</th>
<th class="num">Saldo</th><th class="num">Paro</th>
<th class="num">Deuda 10 años después</th><th class="num">Distancia</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="foot" style="margin-top:8px">Distancia de Mahalanobis sobre cinco
variables normalizadas. <strong>España está excluida del conjunto de
referencia</strong> por construcción, y la semejanza histórica no predice: dos
de estos tres países redujeron deuda después y el tercero la duplicó.</div>

<h3 style="font-size:14px;margin:18px 0 8px">Puntuación de tensión soberana</h3>
<div class="scale"><span class="mark" style="left:{pos:.1f}%"></span>
  <span class="tick" style="left:{min(98.0, 33.3):.1f}%"></span></div>
<div class="scalelab"><span>España {nf(score * 100, 2) if score else "—"} %
  (puntuación bruta)</span>
  <span>| frecuencia de eventos del panel {nf(base * 100, 2) if base else "—"} %</span></div>
<div class="note" style="margin-top:10px">Sobre {d.get("n_rows", "—")} país-año de
{d.get("n_countries", "—")} países, AUC {nf(d.get("auc", 0), 4)} con particiones por
país. <strong>No es una probabilidad de impago.</strong> Es la salida bruta de un
clasificador sin calibrar; España queda fuera del conjunto etiquetado y sólo
{d.get("coverage", "—")} de sus características están disponibles. No debe leerse
como un {nf(score * 100, 2) if score else "—"} % de probabilidad de impago, ni
compararse con la frecuencia del panel para decir que España está «tantas veces»
mejor o peor: son magnitudes distintas y la transferencia entre países no está
validada.</div>"""


def render(data: dict) -> str:
    moved = "".join(
        f'<span class="pill">{m["name"]} {nf(m["base"], m["dec"])} → '
        f'{nf(m["value"], m["dec"])} {m["unit"]}</span>' for m in data["moved"])
    if not moved:
        moved = '<span class="foot">Nada movido: esto es la línea base del vintage.</span>'

    kpis = ""
    for row in data["rows"][:4]:
        cell = row["cells"][-1] if row["key"] == "b" else row["cells"][1]
        kpis += (f'<div class="kpi"><div class="lab">{row["label"]} · {cell["year"]}</div>'
                 f'<div class="val">{nf(cell["scn"], row["dec"])}'
                 f'<span class="u"> {row["unit"]}</span></div>'
                 f'<div class="dlt {tone(cell["delta"], row)}">'
                 f'{signed(cell["delta"], row["dec"])} vs base</div></div>')

    body = ""
    for row in data["rows"]:
        tags = ""
        if row["pinned"]:
            tags += ('<span class="tag warn" title="El motor no le da senda propia: se queda '
                     'en su valor observado y sólo se desplaza en bloque">sin senda propia · '
                     'plana por construcción</span>')
        if row["reader_relative"]:
            tags += ('<span class="tag rel" title="Subir es buena noticia para unos y mala '
                     'para otros">signo según quién pregunte</span>')
        prov = ('<span class="tag prov" title="Dos constantes estimadas con '
                'econometría de panel entran en esta cadena">motor + panel</span>'
                if row["panel"] else
                '<span class="tag prov motor" title="Identidad contable y reglas '
                'calibradas: ningún modelo aprendido interviene">motor</span>')
        cells = "".join(
            f'<td class="num">{nf(c["scn"], row["dec"])}</td>'
            f'<td class="num d {tone(c["delta"], row)}">{signed(c["delta"], row["dec"])}</td>'
            for c in row["cells"])
        body += (f'<tr><th scope="row">{row["label"]}{tags}'
                 f'<small>{row["unit"]} · {prov}</small></th>{cells}</tr>')

    heads = "".join(f'<th class="num" colspan="2">{y}{" · hoy" if y == Y0 else ""}</th>'
                    for y in COLUMNS)
    layers = "".join(
        f'<tr><th scope="row"><span class="tag prov {cid}">{name}</span></th>'
        f'<td class="lay">{text}</td></tr>' for cid, name, text in LAYERS)
    world = render_world(data["world"])
    contrib = "".join(
        f'<tr><th scope="row">{c["name"]}</th>'
        f'<td class="num">{signed(c["delta"], 1)}</td>'
        f'<td class="bar"><span style="width:{abs(c["share"])*100:.0f}%"></span></td>'
        f'<td class="num">{c["share"]*100:.0f} %</td></tr>' for c in data["contrib"])

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ficha del escenario · maqueta</title><style>{STYLE}</style></head>
<body><div class="wrap">

<div class="head">
  <div><h1>España en escenarios</h1>
  <div class="foot">Proyección condicional sobre el vintage 2026-07-31 · motor 1.1.0</div></div>
  <span class="stamp">año de lectura · <strong>{READING_YEAR}</strong> · stocks a 2050</span>
</div>

<div class="note"><strong>Maqueta, no la aplicación.</strong> Propone cómo debería
abrir el panel. Los botones no hacen nada y nada está conectado; las cifras, en
cambio, salen del motor cada vez que se genera este archivo
(<code>tools/build_scenario_mockup.py</code>).</div>

<section class="card"><h2>1 · Qué has cambiado</h2>
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">{moved}
  <span class="foot">todo lo demás, en su valor observado</span></div></section>

<section class="card"><h2>2 · Qué implica, de un vistazo</h2>
  <div class="kpis">{kpis}</div></section>

<section class="card"><h2>3 · La trayectoria</h2>
  {chart(data["path"])}
  <div class="foot">— — base congelada · <span style="color:var(--lab)">——</span>
  escenario · Deuda %PIB</div></section>

<section class="card"><h2>4 · El futuro, en números</h2>
  <table><thead><tr><th>Serie</th>{heads}</tr></thead><tbody>{body}</tbody></table>
  <div class="acts"><button>Copiar tabla</button><button>Descargar CSV</button></div>
  <div class="key">
    <span>Cada par: valor del escenario y Δ frente a la base.</span>
    <span><b class="dn">verde</b> mejora · <b class="up">rojo</b> empeora ·
    <b class="rel">azul</b> depende de quién pregunte</span></div></section>

<section class="card"><h2>5 · Qué mueve la deuda en 2050</h2>
  <table><tbody>{contrib}</tbody></table>
  <div class="foot" style="margin-top:8px">El motor vuelto a correr con una sola
  palanca cada vez. Total conjunto: {signed(data["joint"], 1)} pp.</div></section>

<section class="card"><h2>6 · Cómo se ha calculado cada cifra</h2>
  <table class="layers"><tbody>{layers}</tbody></table>
  <div class="note" style="margin-top:12px"><strong>La respuesta corta:</strong>
  las cifras de la tabla salen de una identidad contable con reglas calibradas,
  no de un modelo aprendido. De los parámetros del motor sólo dos vienen de los
  datos, y afectan a la cadena de vivienda. La red neuronal no se usa porque no
  superó a su referencia, el clasificador vive aparte y el modelo de lenguaje no
  calcula: redacta sobre hechos ya calculados.</div></section>

<section class="card"><h2>7 · España entre los demás</h2>
  {world}</section>

<div class="foot">Proyección condicional, no recomendación de compra, venta o voto.</div>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lever", action="append", default=[], metavar="id=valor",
                    help="palanca a mover, repetible (por defecto lam=1.4)")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--json", action="store_true", help="volcar los datos en vez del HTML")
    args = ap.parse_args()

    pairs = args.lever or ["lam=1.4"]
    known = {s["id"] for s in LEVER_SPECS}
    kwargs = {}
    for pair in pairs:
        lid, _, raw = pair.partition("=")
        if lid not in known:
            print(f"palanca desconocida: {lid!r} (conocidas: {', '.join(sorted(known))})")
            return 1
        kwargs[lid] = float(raw)

    data = collect(Levers(**kwargs))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(data), encoding="utf-8")
    print(f"{args.out}  {args.out.stat().st_size / 1000:.1f} kB")
    print(f"  palancas: {', '.join(f'{k}={v}' for k, v in kwargs.items())}")
    print(f"  filas: {len(data['rows'])} · columnas: {', '.join(map(str, COLUMNS))}")
    flat = [r["label"] for r in data["rows"] if r["pinned"]]
    if flat:
        print(f"  sin senda propia (planas por construcción): {', '.join(flat)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
