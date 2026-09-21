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
            "cells": [{"year": y, "scn": s[y - Y0], "delta": s[y - Y0] - b[y - Y0]}
                      for y in COLUMNS],
        })
    contribs, _interaction, joint = decompose(levers, "b", 2050 - Y0) if moved else ([], 0.0, 0.0)
    return {"moved": moved, "rows": rows, "joint": joint,
            "contrib": [{"name": c.lever_name, "delta": c.delta, "share": c.share}
                        for c in contribs],
            "path": {"years": list(range(Y0, 2051)), "base": base["b"], "scn": scn["b"]}}


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
.note{background:var(--chip-warn);border-left:3px solid var(--warn);border-radius:0 6px 6px 0;
padding:10px 14px;font-size:12.5px;color:var(--ink-2)}
"""


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
        cells = "".join(
            f'<td class="num">{nf(c["scn"], row["dec"])}</td>'
            f'<td class="num d {tone(c["delta"], row)}">{signed(c["delta"], row["dec"])}</td>'
            for c in row["cells"])
        body += (f'<tr><th scope="row">{row["label"]}{tags}'
                 f'<small>{row["unit"]}</small></th>{cells}</tr>')

    heads = "".join(f'<th class="num" colspan="2">{y}{" · hoy" if y == Y0 else ""}</th>'
                    for y in COLUMNS)
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
