"""Generate the academic defence from local evidence, with no remote API calls.

python docs/deck/build_deck.py             # Markdown and two scientific figures
python docs/deck/build_deck.py --render    # also HTML/PDF/PPTX via installed Marp

Old production screenshots are not evidence for the revised engine. Tables,
figures and illustrative scenarios are derived from committed artifacts/current
code. Historical model metrics are explicitly labelled as not rerun here.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', '/tmp/evo-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from engine.constants import ENGINE_VERSION, VINTAGE, IPV_LR, IPV_REV, IPV_REV_V16
from engine.levers import Levers, PRESETS, preset_levers
from engine.spain import run_scenario


def read(name):
    return json.loads((ROOT / 'docs/eval' / name).read_text())


def figures(housing, mc):
    output = HERE / 'figures'
    output.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 12, 'axes.spines.top': False, 'axes.spines.right': False})
    primary = housing['windows'][0]['primary_region_clustered']
    rows = [primary] + housing['windows'][0]['synchronized_time_blocks']
    labels = ['Agrupación por región', 'Bloques comunes: 4 trimestres', 'Bloques comunes: 8 trimestres', 'Bloques comunes: 12 trimestres']
    fig, ax = plt.subplots(figsize=(10, 3.6), layout='constrained')
    for i, row in enumerate(rows):
        mean = row.get('mean', row.get('coef'))
        ax.errorbar(mean, 3-i, xerr=[[mean-row['ci_low']], [row['ci_high']-mean]], fmt='o', capsize=5, color='#087f8c')
    ax.axvline(3, color='#b85622', ls='--', label='Valor calibrado: 3 %')
    ax.set_yticks(range(4), labels[::-1]); ax.set_xlabel('Media histórica del crecimiento anual (%) · intervalos 90 %')
    ax.grid(axis='x', alpha=.2); ax.legend(loc='lower right', fontsize=10)
    fig.savefig(output / 'housing-uncertainty.svg'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 3.7), layout='constrained')
    for rho, color in zip((.5, .8, .96), ('#476a9f', '#087f8c', '#b85622')):
        rows = [r for r in mc['assumption_sensitivity'] if r['rho'] == rho]
        ax.plot([r['shock_scale'] for r in rows], [r['years']['2050']['width_p5_p95'] for r in rows], 'o-', color=color, label=f'Persistencia {rho}')
    ax.set_xlabel('Escala de las innovaciones (1 = calibración actual)')
    ax.set_ylabel('Anchura p5–p95 en 2050 (pp PIB)'); ax.grid(alpha=.2); ax.legend()
    fig.savefig(output / 'montecarlo-sensitivity.svg'); plt.close(fig)

    # La curva entera y no dos puntos. La pendiente sube de 48 a 65 pp de
    # deuda por punto de indexación de un extremo al otro, así que el coste de
    # indexar se acelera; interpolar entre los extremos se equivoca en hasta
    # 6,8 pp. Poco para un titular, bastante para una cifra que se cita.
    pens = read('pension-indexation-sensitivity.json')
    fig, ax = plt.subplots(figsize=(9, 3.7), layout='constrained')
    xs = [r['idx'] for r in pens['rows']]
    ys = [r['debt_2050'] for r in pens['rows']]
    ax.plot(xs, ys, '-', color='#087f8c', lw=2.2)
    base = pens['lever']['base']
    y0 = next(r['debt_2050'] for r in pens['rows'] if abs(r['idx'] - base) < 1e-9)
    ax.plot([base], [y0], 'o', color='#b85622', zorder=3)
    ax.annotate(f'referencia: {y0:.0f} % PIB', (base, y0), textcoords='offset points',
                xytext=(8, -14), fontsize=10, color='#b85622')
    ax.set_xlabel('Indexación de pensiones y nóminas sobre la inflación (puntos/año)')
    ax.set_ylabel('Deuda en 2050 (% PIB)')
    ax.grid(alpha=.2)
    fig.savefig(output / 'pension-indexation.svg'); plt.close(fig)


def main():
    housing, mc = read('housing-robustness.json'), read('montecarlo-sensitivity.json')
    dl, distress = read('t1-dl-global.json'), read('distress.json')
    state, rag = read('state_dependence.json'), read('rag-eval-2026-08-09.json')
    analog = read('analog-metric.json')
    chat = read('rag-chat-eval.json')
    figures(housing, mc)
    verdict = dl['verdict']

    # Figures that used to be typed into the slide text. Every one of them was
    # correct when checked against docs/RESULTS.md, which is exactly the
    # problem: nothing made them stay correct. They are read from the same
    # artefacts RESULTS.md cites, so a re-run moves the deck with the evidence
    # instead of leaving the two to drift apart silently.
    # Python's ',' grouping is anglo: 3,874 where a Spanish deck needs 3.874.
    def es(n):
        return f"{n:,}".replace(",", ".")

    regions_head, _, regions_tail = housing['regions'].partition(';')
    boot = housing['windows'][0]['synchronized_time_blocks'][0]
    mc_central = max(mc['assumption_sensitivity'], key=lambda r: r['n_paths'])
    rag_hit = sum(1 for q in rag['questions'] if q['hit'])
    rag_n = len(rag['questions'])
    fidelity = chat['summary']
    slides = [
'''<!-- _class: cover -->
# España en escenarios
## Simulación transparente, evaluación empírica y explicaciones trazables

Daniel Ribes · Máster en Inteligencia Artificial y Data Science

Defensa del Trabajo Fin de Máster · 28 de septiembre de 2026''',
'''# Preguntas y contribuciones

1. **Coherencia:** ¿pueden servidor y navegador reproducir un escenario macrofiscal trazable?
2. **Evidencia:** ¿qué apoyan los datos sobre la vivienda y qué añade la transferencia neuronal frente a baselines?
3. **Explicaciones:** ¿qué calidad demuestra el sistema RAG y qué garantías permite afirmar?

Aportaciones: sistema integrado, contrastes reproducibles y comunicación explícita de límites.''',
'''# Arquitectura que permite auditar

**Fuentes y tablas congeladas → motor Python → API → aplicación React**

- El navegador ejecuta el mismo modelo con anclas compartidas.
- La investigación publica parámetros, métricas y resultados negativos.
- Las explicaciones separan hechos calculados y texto generado.
- Los documentos y el índice RAG son locales; la generación remota envía pasajes seleccionados al proveedor.

La paridad numérica demuestra coherencia de implementación; la evaluación empírica responde otras preguntas.''',
f'''# Datos: referencia, muestra y fechas

- Referencia del escenario: **{VINTAGE}**; adquisición y construcción se documentan por separado.
- Vivienda: **{regions_head}**;{regions_tail}.
- Red global: {es(dl['n_series'])} series extranjeras; objetivos de entrenamiento hasta **{dl['cutoff']}**.
- Distress: **{es(distress['n'])} observaciones, {distress['n_positive']} eventos, {distress['n_countries']} países** en la muestra evaluada.
- Tablas y resultados sellados con SHA-256; la reconstrucción completa del pipeline original queda fuera del alcance.

Congelar un archivo permite repetir cálculos, sin certificar su autenticidad o eliminar revisiones históricas.''',
r'''# Identidad de deuda y alcance del escenario

$$b_t=b_{t-1}\frac{1+i_t/100}{1+g^{nom}_t/100}-pb_t$$

- Coste efectivo y crecimiento nominal en unidades compatibles.
- Saldo primario en puntos de PIB.
- Diez palancas generan desviaciones condicionales sobre la referencia.
- Las elasticidades de comportamiento son principalmente calibraciones.

**Un diferencial negativo ayuda a diluir la deuda heredada. Un déficit primario puede hacer subir la ratio total.**''',
fr'''# Vivienda: una corrección que cambia la dinámica

Tasa anual de reversión: **{IPV_REV:.4f}**. Persistencia: **{1-IPV_REV:.4f}**.

$$h_k=\mu+(h_0-\mu)(1-\kappa)^k+\text{{canales de tipos y crecimiento}}$$

- Antes se utilizaba la tasa de reversión como factor de persistencia.
- Python y TypeScript ahora aplican la misma definición.
- El .{int(IPV_REV_V16*100)} de v16 era persistencia, equivalente a reversión .{int((1-IPV_REV_V16)*100)}.
- La comparación LP acumula log-precios, excluye crecimiento realizado y muestra puntos anuales; su amplitud se normaliza en el primer año.

Media histórica estimada: **{IPV_LR:.4f}%**. No identifica por sí sola una tendencia estructural.''',
f'''# La incertidumbre depende de la inferencia

![w:990](figures/housing-uncertainty.svg)

El 3% queda fuera de la banda regional, pero dentro de las bandas que conservan choques nacionales comunes. **Su rechazo no es robusto.** {boot['n_boot']} réplicas, semilla {boot['seed']}; sensibilidad condicional a ventana y bloques.''',
f'''# Transferencia neuronal: resultado negativo

| Contraste principal conservado | Resultado |
|---|---:|
| Regiones donde vence al baseline | {verdict['beaten_ccaa']}/{verdict['total_ccaa']} |
| Regiones requeridas por el criterio | {verdict['required']} |
| MASE candidato (horizontes hasta 4 trimestres) | {verdict['mase_candidate']:.3f} |
| MASE drift | {verdict['mase_drift']:.3f} |

**Esta configuración no supera al baseline de deriva.** El protocolo usa orígenes móviles y escalado ajustado solo con datos de entrenamiento. El holdout final y la sensibilidad a semillas quedan como trabajo futuro.''',
f'''# Distress: discriminación, no riesgo calibrado

- AUC por grupos de países: **{distress['auc']:.3f}**.
- Average precision: **{distress['pr_auc']:.3f}**.
- El score se muestra en escala 0–1; no como probabilidad para España.
- Muestra seleccionada por disponibilidad de etiquetas; tasa base no representativa del mundo.
- Separar países no equivale a evaluar el futuro con entrenamiento pasado.

Trabajo futuro: negativos representativos, baseline logístico, validación temporal y calibración.''',
f'''# SHAP y regímenes: lectura descriptiva

**Gemelo empírico:** R² fuera de país **{state['r2_grouped']:.3f}**.

- La falta de poder predictivo limita la interpretación de las pendientes SHAP.
- Un intervalo que incluye cero no demuestra que la constante del motor sea correcta.
- SHAP describe asociaciones del predictor; no identifica intervenciones causales.
- Los regímenes HMM describen retrospectivamente la serie y dependen de la especificación.

Estas capas ayudan a explorar hipótesis; su utilidad no convierte sus resultados en pronósticos validados.''',
f'''# RAG: qué se midió realmente

| Evidencia histórica de desarrollo | Lectura correcta |
|---|---|
| {rag_hit}/{rag_n} documentos esperados en top-8 | Recuperación de libro, no corrección de respuesta |
| {fidelity['fidelity_supported']}/{fidelity['fidelity_checked']} primeras frases citadas con respaldo | Una frase por respuesta, juicio de otro LLM |
| Pesos/glosario ajustados sobre preguntas doradas | Conjunto de desarrollo, no test independiente |

Estas métricas no justifican afirmar ausencia de alucinaciones.''',
'''# RAG: alcance medido y protocolo de validación

- Comprobación formal de citas y referencias, con fallback ante salida incompleta del modelo.
- Narración: inventario de magnitudes numéricas; no valida completamente signos, unidades o asociación cifra–concepto.
- `grounded` conserva compatibilidad: significa contexto recuperado.
- Protocolo ejecutable: corpus y etiquetas congelados, BM25/dense/híbrido/bilingüe, relevancia de pasajes y revisión humana de afirmaciones.

El protocolo queda especificado y ejecutable; la anotación independiente es trabajo futuro, no un resultado que se presente aquí.''',
f'''# Análogos: comparación descriptiva corregida

**{es(analog['n_complete'])} observaciones completas · {analog['n_countries']} países · {analog['years'][0]}–{analog['years'][1]}**

- Consulta en el año seleccionado: deuda, saldo total, crecimiento real, paro e inflación.
- Mahalanobis: covarianza y diferencias en las mismas coordenadas.
- Sin bonus por palanca ni imputación de huecos como valores observados.
- Tipo bancario de préstamo excluido del matching y de cualquier r−g soberano.
- Sin veredicto de sostenibilidad; información estructural no medida se declara ausente.

La semejanza histórica no predice la trayectoria española.''',
f'''# Monte Carlo: sensibilidad, no cobertura predictiva

![w:940](figures/montecarlo-sensitivity.svg)

{es(mc_central['n_paths'])} trayectorias, semilla común {mc_central['seed']}. La amplitud cambia con los supuestos. La banda contiene el 90% central de simulaciones; su cobertura en datos reales no está validada.''',
]
    rows=[]
    for preset in PRESETS:
        run=run_scenario(preset_levers(preset['id']))
        rows.append(f"| {preset['id']} | {run['b'][-1]:.1f} | {run['u'][-1]:.1f} | {run['esf'][-1]:.1f} |")
    slides.append('''# Escenarios ilustrativos actuales · 2050

| Preset | Deuda (% PIB) | Paro (%) | Cuota/salario (%) |
|---|---:|---:|---:|
'''+ '\n'.join(rows)+f'''\n\nCálculos locales del motor **{ENGINE_VERSION}**. Son implicaciones de supuestos mantenidos; no resultados observados ni previsiones.''')
    slides += [
'''# Reproducción y pruebas

- Dependencias Python restringidas y lock npm; entorno de desarrollo registrado.
- Contratos Python/TypeScript regenerados desde los defaults actuales.
- Crosswalk de países congelado; errores de cobertura visibles.
- Tests ordinarios sin inferencia remota ni corpus privado.
- Checksum de tablas e informes, CI y comandos documentados.

Limitaciones: la instalación limpia no está verificada y algunas transformaciones originales no se han reconstruido. La CI está definida, no ejecutada en remoto.''',
'''# Demostración breve

1. Abrir S0 y separar dato, supuesto y resultado.
2. Aplicar S1: refinanciación → crecimiento → deuda.
3. Mostrar vivienda: persistencia y bandas alternativas.
4. Buscar un análogo en el año elegido; comprobar qué datos faltan.
5. Contrastar explicaciones deterministas con el alcance de la evidencia RAG.

La demostración se ejecuta sobre el motor regenerado, no sobre capturas anteriores.''',
'''# Conclusiones y líneas futuras

**Aportación demostrable:** sistema integrado, trazable y evaluable; correcciones científicas reproducibles y resultados negativos publicados.

- La red no supera el baseline principal en el experimento conservado.
- La conclusión sobre crecimiento de vivienda cambia al tratar choques comunes.
- Distress, HMM, SHAP y análogos mantienen alcance exploratorio.
- Líneas futuras: test RAG humano independiente, holdout final de vivienda, evaluación temporal/calibración de distress y reconstrucción completa de fuentes.

La memoria distingue resultados medidos, comprobaciones de software y trabajo futuro.''',
'''# Referencias y artefactos

- Jordà (2005), *Estimation and Inference of Impulse Responses by Local Projections*.
- Hyndman y Koehler (2006), *Another look at measures of forecast accuracy*.
- Cameron y Miller (2015), *A Practitioner's Guide to Cluster-Robust Inference*.
- Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*.
- FMI: marco de riesgo soberano y sostenibilidad de deuda.

Referencias primarias completas: **docs/MEMORIA_TFM.md**.
Métodos y límites: **docs/RESULTS.md**, **docs/REPRODUCIBILITY.md**.
Artefactos y nuevas sensibilidades: **docs/eval/**.''',
    ]
    header=f'''---
marp: true
theme: default
paginate: true
size: 16:9
footer: 'Daniel Ribes · TFM · motor {ENGINE_VERSION} · escenario condicional'
style: |
  section {{ background: #f4f7fa; color: #1b2430; font-family: Arial, sans-serif; font-size: 24px; padding: 46px 58px; }}
  h1 {{ color: #0b2545; font-size: 36px; border-bottom: 3px solid #087f8c; padding-bottom: 12px; }}
  h2 {{ color: #087f8c; font-size: 27px; }}
  strong {{ color: #0b2545; }}
  table {{ font-size: 22px; width: 100%; }}
  th {{ background: #0b2545; color: white; }}
  td {{ background: white; }}
  li {{ margin: 10px 0; }}
  footer {{ font-size: 14px; color: #536475; }}
  section.cover {{ background: #0b2545; color: white; }}
  section.cover h1 {{ color: white; font-size: 54px; }}
  section.cover h2 {{ color: #a8deda; }}
---
'''
    output=HERE/'deck.marp.md'
    output.write_text(header+'\n\n---\n\n'.join(slides)+'\n')
    print(f'Wrote {len(slides)} slides and 2 figures')
    if '--render' in sys.argv:
        marp=shutil.which('marp')
        if not marp:
            raise SystemExit('Marp CLI is required for rendering; Markdown and figures generated.')
        for extension, extra in [('html',[]),('pdf',['--pdf']),('pptx',['--pptx'])]:
            subprocess.run([marp,str(output),'--html','--allow-local-files',*extra,'-o',str(HERE/f'deck.{extension}')],check=True)


if __name__=='__main__':
    main()
