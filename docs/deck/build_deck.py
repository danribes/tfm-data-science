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
from engine.constants import ENGINE_VERSION, VINTAGE, IPV_LR, IPV_REV
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
    ax.axvline(3, color='#b85622', ls='--', label='Calibración v16: 3 %')
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


def main():
    housing, mc = read('housing-robustness.json'), read('montecarlo-sensitivity.json')
    dl, distress = read('t1-dl-global.json'), read('distress.json')
    state, rag = read('state_dependence.json'), read('rag-eval-2026-08-09.json')
    analog = read('analog-metric.json')
    figures(housing, mc)
    verdict = dl['verdict']
    slides = [
'''<!-- _class: cover -->
# España en escenarios
## Simulación transparente, evaluación empírica y explicaciones trazables

Daniel Ribes · Máster en Inteligencia Artificial y Data Science

Defensa académica · borrador para revisión del autor y tutor''',
'''# Preguntas y contribuciones

1. **Coherencia:** ¿pueden servidor y navegador reproducir un escenario macrofiscal trazable?
2. **Evidencia:** ¿qué apoyan los datos sobre la vivienda y qué añade la transferencia neuronal frente a baselines?
3. **Explicaciones:** ¿qué calidad demuestra el sistema RAG y qué evaluación falta?

Aportaciones: sistema integrado, contrastes reproducibles y comunicación explícita de límites. La comparación independiente final del RAG sigue pendiente.''',
'''# Arquitectura que permite auditar

**Fuentes y tablas congeladas → motor Python → API → aplicación React**

- El navegador ejecuta el mismo modelo con anclas compartidas.
- La investigación publica parámetros, métricas y resultados negativos.
- Las explicaciones separan hechos calculados y texto generado.
- Los documentos y el índice RAG son locales; la generación remota envía pasajes seleccionados al proveedor.

La paridad numérica demuestra coherencia de implementación; la evaluación empírica responde otras preguntas.''',
'''# Datos: referencia, muestra y fechas

- Referencia del escenario: **2026-07-31**; adquisición y construcción se documentan por separado.
- Vivienda: **17 CCAA + Ceuta y Melilla**; Nacional excluido.
- Red global: series extranjeras; objetivos de entrenamiento hasta **2019Q3**.
- Distress: **3.874 observaciones, 377 eventos, 154 países** en la muestra evaluada.
- Tablas y resultados sellados con SHA-256; parte del pipeline original todavía no está reconstruida.

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
- El .60 de v16 era persistencia, equivalente a reversión .40.
- La comparación LP acumula log-precios, excluye crecimiento realizado y muestra puntos anuales; su amplitud se normaliza en el primer año.

Media histórica estimada: **{IPV_LR:.4f}%**. No identifica por sí sola una tendencia estructural.''',
'''# La incertidumbre depende de la inferencia

![w:990](figures/housing-uncertainty.svg)

El 3% queda fuera de la banda regional, pero dentro de las bandas que conservan choques nacionales comunes. **Su rechazo no es robusto.** 500 réplicas, semilla 42; sensibilidad condicional a ventana y bloques.''',
f'''# Transferencia neuronal: resultado negativo

| Contraste principal conservado | Resultado |
|---|---:|
| Regiones donde vence al baseline | {verdict['beaten_ccaa']}/{verdict['total_ccaa']} |
| Regiones requeridas por el criterio | {verdict['required']} |
| MASE candidato (horizontes hasta 4 trimestres) | {verdict['mase_candidate']:.3f} |
| MASE drift | {verdict['mase_drift']:.3f} |

**Esta configuración no supera drift.** El protocolo usa orígenes móviles y escalado con entrenamiento. El holdout final y la sensibilidad a semillas siguen pendientes. No se reentrenó la red en esta revisión.''',
f'''# Distress: discriminación, no riesgo calibrado

- AUC por grupos de países: **{distress['auc']:.3f}**.
- Average precision: **{distress['pr_auc']:.3f}**.
- El score se muestra en escala 0–1; no como probabilidad para España.
- Muestra seleccionada por disponibilidad de etiquetas; tasa base no representativa del mundo.
- Separar países no equivale a evaluar el futuro con entrenamiento pasado.

Pendiente: negativos representativos, baseline logístico, validación temporal y calibración. Métricas históricas conservadas, sin nueva estimación.''',
f'''# SHAP y regímenes: lectura descriptiva

**Gemelo empírico:** R² fuera de país **{state['r2_grouped']:.3f}**.

- La falta de poder predictivo limita la interpretación de las pendientes SHAP.
- Un intervalo que incluye cero no demuestra que la constante del motor sea correcta.
- SHAP describe asociaciones del predictor; no identifica intervenciones causales.
- Los regímenes HMM describen retrospectivamente la serie y dependen de la especificación.

Estas capas ayudan a explorar hipótesis; su utilidad no convierte sus resultados en pronósticos validados.''',
'''# RAG: qué se midió realmente

| Evidencia histórica de desarrollo | Lectura correcta |
|---|---|
| 34/35 documentos esperados en top-8 | Recuperación de libro, no corrección de respuesta |
| 10/12 afirmaciones muestreadas respaldadas | Primera afirmación citada, juicio de otro LLM |
| Pesos/glosario ajustados sobre preguntas doradas | Conjunto de desarrollo, no test independiente |

Las métricas no se han vuelto a medir después de esta revisión. No justifican afirmar ausencia de alucinaciones.''',
'''# RAG revisado y test independiente pendiente

- Comprobación formal de citas y referencias; salida interrumpida → fallback.
- Narración: inventario de magnitudes numéricas; no valida completamente signos, unidades o asociación cifra–concepto.
- `grounded` conserva compatibilidad: significa contexto recuperado.
- Protocolo ejecutable: corpus y etiquetas congelados, BM25/dense/híbrido/bilingüe, relevancia de pasajes y revisión humana de afirmaciones.

La plantilla está intencionadamente incompleta: no se presenta como anotación independiente realizada.''',
f'''# Análogos: comparación descriptiva corregida

**{analog['n_complete']:,} observaciones completas · {analog['n_countries']} países · {analog['years'][0]}–{analog['years'][1]}**

- Consulta en el año seleccionado: deuda, saldo total, crecimiento real, paro e inflación.
- Mahalanobis: covarianza y diferencias en las mismas coordenadas.
- Sin bonus por palanca ni imputación de huecos como valores observados.
- Tipo bancario de préstamo excluido del matching y de cualquier r−g soberano.
- Sin veredicto de sostenibilidad; información estructural no medida se declara ausente.

La semejanza histórica no predice la trayectoria española.''',
'''# Monte Carlo: sensibilidad, no cobertura predictiva

![w:940](figures/montecarlo-sensitivity.svg)

4.000 trayectorias, semilla común 42. La amplitud cambia con los supuestos. La banda contiene el 90% central de simulaciones; su cobertura en datos reales no está validada.''',
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

Limitaciones: no se ha probado aquí una instalación limpia; faltan algunas transformaciones originales. La CI añadida no se presenta como una ejecución remota ya realizada.''',
'''# Demostración breve

1. Abrir S0 y separar dato, supuesto y resultado.
2. Aplicar S1: refinanciación → crecimiento → deuda.
3. Mostrar vivienda: persistencia y bandas alternativas.
4. Buscar un análogo en el año elegido; comprobar qué datos faltan.
5. Contrastar explicaciones deterministas con el alcance de la evidencia RAG.

Usar esta versión regenerada. Las capturas antiguas de producción no prueban el comportamiento del motor revisado.''',
'''# Conclusiones y trabajo pendiente

**Aportación demostrable:** sistema integrado, trazable y evaluable; correcciones científicas reproducibles y resultados negativos publicados.

- La red no supera el baseline principal en el experimento conservado.
- La conclusión sobre crecimiento de vivienda cambia al tratar choques comunes.
- Distress, HMM, SHAP y análogos mantienen alcance exploratorio.
- Pendientes: test RAG humano independiente, holdout final de vivienda, evaluación temporal/calibración de distress y reconstrucción completa de fuentes.

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
