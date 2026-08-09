"""Policy Brief HTML Report Generator for Spain Macro Scenarios.

Generates a standalone, publication-grade, 1-page printable HTML policy brief.
Calculates scenario projections, red lines, lever deltas, and persona impacts dynamically.
"""
from __future__ import annotations

import html
from engine import constants as c
from engine.levers import LEVER_SPECS, Levers
from engine.redlines import evaluate_redlines
from engine.spain import Y0, Y1, persona_dependents, run_scenario


def generate_policy_brief_html(levers: Levers, horizon: int = 2050) -> str:
    """Generate a clean, standalone, printable HTML policy brief document."""
    scenario = run_scenario(levers)
    k_horizon = min(max(0, horizon - Y0), len(scenario["b"]) - 1)
    redlines = evaluate_redlines(scenario, k_horizon)
    personas_out = persona_dependents(scenario)

    # 1. Levers Table Data
    lever_rows = []
    for spec in LEVER_SPECS:
        lid = spec["id"]
        val = getattr(levers, lid)
        base = c.BASE_LEVERS[lid]
        delta = val - base
        delta_str = f"{delta:+.2f}" if abs(delta) > 1e-4 else "0.00"
        lever_rows.append({
            "name": spec["nm"],
            "unit": spec["unit"],
            "base": f"{base:.2f}",
            "scenario": f"{val:.2f}",
            "delta": delta_str,
            "modified": abs(delta) > 1e-4,
        })

    # 2. Key Projections Table Data (2026, 2030, 2040, 2050)
    target_years = [2026, 2030, 2040, 2050]
    year_indices = [y - Y0 for y in target_years]

    macro_indicators = [
        {"key": "b", "label": "Deuda Pública", "unit": "% PIB", "dec": 1},
        {"key": "saldo", "label": "Saldo Público", "unit": "% PIB", "dec": 2},
        {"key": "u", "label": "Tasa de Paro", "unit": "%", "dec": 1},
        {"key": "pi", "label": "Inflación IPCA", "unit": "%", "dec": 1},
        {"key": "g", "label": "PIB Real", "unit": "% a/a", "dec": 1},
        {"key": "esf", "label": "Esfuerzo Vivienda", "unit": "% renta", "dec": 1},
        {"key": "pens", "label": "Gasto Pensiones", "unit": "% PIB", "dec": 1},
        {"key": "arop", "label": "Pobreza Infantil AROP", "unit": "%", "dec": 1},
    ]

    # HTML rendering
    lever_tr_html = []
    for r in lever_rows:
        highlight_cls = ' class="mod"' if r["modified"] else ""
        lever_tr_html.append(
            f"<tr{highlight_cls}>"
            f"<td><strong>{html.escape(r['name'])}</strong></td>"
            f"<td>{html.escape(r['unit'])}</td>"
            f"<td>{r['base']}</td>"
            f"<td><strong>{r['scenario']}</strong></td>"
            f"<td>{r['delta']}</td>"
            f"</tr>"
        )

    macro_tr_html = []
    for ind in macro_indicators:
        k_str = ind["key"]
        dec = ind["dec"]
        vals = [f"{scenario[k_str][idx]:.{dec}f}" for idx in year_indices]
        macro_tr_html.append(
            f"<tr>"
            f"<td><strong>{html.escape(ind['label'])}</strong></td>"
            f"<td>{html.escape(ind['unit'])}</td>"
            + "".join([f"<td>{v}</td>" for v in vals])
            + f"</tr>"
        )

    redline_cards_html = []
    for rl in redlines:
        st = rl["status"]
        st_label = "CROSSED" if st == "crossed" else ("NEAR" if st == "near" else "SAFE")
        st_cls = f"badge-{st}"
        redline_cards_html.append(
            f'<div className="red-card" class="red-card {st_cls}">'
            f'<div class="red-hdr"><span class="badge {st_cls}">{st_label}</span>'
            f'<strong>{html.escape(rl["label"])}</strong></div>'
            f'<div class="red-val">Valor: <strong>{rl["value"]:.1f}</strong> (Umbral: {rl["threshold"]:.1f})</div>'
            f'<div class="red-src">{html.escape(rl["source"])}</div>'
            f'</div>'
        )

    # Shipped Personas Narrative Cards
    persona_cards_html = []
    shipped_ids = ["01", "02", "03", "06", "08", "09", "10", "12"]
    for pid in shipped_ids:
        if pid in personas_out:
            p = personas_out[pid]
            pill = p.get("pill", f"Perfil {pid}")
            headline_k = p.get("headline", "b")
            headline_v = scenario[headline_k][k_horizon]
            persona_cards_html.append(
                f'<div class="persona-card">'
                f'<h4>{html.escape(pill)} <span class="h-val">{headline_k.upper()}: {headline_v:.1f}</span></h4>'
                f'</div>'
            )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>España en Escenarios — Informe de Política Pública ({horizon})</title>
  <style>
    @page {{ size: A4 portrait; margin: 12mm; }}
    * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{ background: #f8fafc; color: #0f172a; margin: 0; padding: 20px; font-size: 13px; line-height: 1.4; }}
    .container {{ max-width: 960px; margin: 0 auto; background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
    
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 16px; }}
    .header h1 {{ margin: 0; font-size: 22px; color: #0f172a; font-weight: 700; }}
    .header .subtitle {{ font-size: 12px; color: #64748b; margin-top: 2px; }}
    .header .meta-box {{ text-align: right; font-size: 11px; color: #475569; background: #f1f5f9; padding: 6px 10px; border-radius: 6px; }}
    
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
    
    section {{ margin-bottom: 18px; }}
    h3 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #0369a1; margin: 0 0 8px 0; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }}
    
    table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; margin-top: 4px; }}
    th, td {{ padding: 5px 8px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
    th {{ background: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 10px; }}
    td {{ color: #1e293b; }}
    tr.mod {{ background: #eff6ff; }}
    
    .red-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
    .red-card {{ padding: 8px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 11px; }}
    .red-card.badge-crossed {{ border-color: #fca5a5; background: #fef2f2; }}
    .red-card.badge-near {{ border-color: #fde047; background: #fefce8; }}
    .red-card.badge-safe {{ border-color: #86efac; background: #f0fdf4; }}
    
    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 9px; margin-right: 6px; }}
    .badge-crossed {{ background: #ef4444; color: #ffffff; }}
    .badge-near {{ background: #eab308; color: #ffffff; }}
    .badge-safe {{ background: #22c55e; color: #ffffff; }}
    
    .red-hdr {{ font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; }}
    .red-val {{ color: #334155; font-size: 10.5px; }}
    .red-src {{ color: #64748b; font-size: 9.5px; margin-top: 2px; }}
    
    .personas-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
    .persona-card {{ background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; }}
    .persona-card h4 {{ margin: 0; font-size: 11.5px; color: #0f172a; display: flex; justify-content: space-between; }}
    .persona-card .h-val {{ font-weight: 700; color: #0284c7; }}
    
    .footer {{ border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 10px; color: #64748b; text-align: justify; margin-top: 16px; }}
    
    @media print {{
      body {{ background: #ffffff; padding: 0; }}
      .container {{ border: none; shadow: none; padding: 0; width: 100%; max-width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>España en Escenarios</h1>
        <div class="subtitle">Informe de Política Pública · Evaluación de Sostenibilidad y Stress Test Macro ({Y0}–{Y1})</div>
      </div>
      <div class="meta-box">
        <div><strong>Vintage Oficial:</strong> {c.VINTAGE}</div>
        <div><strong>Motor Macro:</strong> v{c.ENGINE_VERSION}</div>
        <div><strong>Horizonte Evaluado:</strong> {horizon}</div>
      </div>
    </div>

    <div class="grid-2">
      <section>
        <h3>1. Configuración de Palancas Macro</h3>
        <table>
          <thead>
            <tr>
              <th>Palanca</th>
              <th>Unidad</th>
              <th>Base</th>
              <th>Escenario</th>
              <th>Δ</th>
            </tr>
          </thead>
          <tbody>
            {"".join(lever_tr_html)}
          </tbody>
        </table>
      </section>

      <section>
        <h3>2. Proyecciones Macro Clave ({Y0}–{Y1})</h3>
        <table>
          <thead>
            <tr>
              <th>Indicador</th>
              <th>Unidad</th>
              {"".join([f"<th>{y}</th>" for y in target_years])}
            </tr>
          </thead>
          <tbody>
            {"".join(macro_tr_html)}
          </tbody>
        </table>
      </section>
    </div>

    <section>
      <h3>3. Evaluación de Líneas Rojas y Umbrales Críticos ({horizon})</h3>
      <div class="red-grid">
        {"".join(redline_cards_html)}
      </div>
    </section>

    <section>
      <h3>4. Resumen de Impacto por Perfil</h3>
      <div class="personas-grid">
        {"".join(persona_cards_html)}
      </div>
    </section>

    <div class="footer">
      <strong>Nota Metodológica y Exención de Asesoramiento:</strong>
      Este informe ha sido generado de forma 100 % determinista mediante el motor semiestructural <em>España en escenarios</em> v{c.ENGINE_VERSION},
      anclado en la muestra de datos oficiales sellada en el vintage {c.VINTAGE} (INE, Eurostat, Banco de España, BCE, World Bank).
      Los cálculos evalúan desviaciones respecto al escenario central oficial y no constituyen predicciones incondicionales ni asesoramiento de inversión.
    </div>
  </div>
</body>
</html>"""
