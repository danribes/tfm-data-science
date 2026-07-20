# ¿Es predecible la renta en paridad de poder adquisitivo (PPA)?

Misma disección que el resto del proyecto (nivel vs evolución; predicción solo
condicional o con vara honesta), aplicada al PIB per cápita en PPA
(`analysis/ppp_predictibilidad.py`, WDI, 242 países 1995–2023). El hallazgo de
convergencia se sometió a **verificación adversarial** (workflow de 4 ataques
independientes que recomputaron sobre los datos reales).

## Respuesta en tres niveles

| Dimensión | ¿Predecible? | Detalle |
|---|---|---|
| **Nivel de PPA** (renta de un país el año que viene) | Sí, trivialmente | Persistencia extrema (correlación 0,92 entre 1995 y 2023) — pero a través de la COVID el naive (último valor) bate al drift (MAE 0,068 vs 0,080): extrapolar tendencia hace daño en un shock, la misma lección que la vivienda |
| **Crecimiento año a año** | Apenas | Autocorrelación AR(1) within-country = +0,11; el crecimiento es casi ruido alrededor de la media del país |
| **Convergencia (¿alcanzan los pobres?)** | Real pero CONDICIONAL | Pendiente −0,0044 (corr −0,31); verificado abajo |

## La convergencia, verificada adversarialmente (3 de 4 ataques superados)

Cuatro verificaciones independientes recomputaron el hallazgo sobre los datos:

1. **Falacia de Galton / reversión a la media** — ✅ SOBREVIVE. La pendiente no
   es un artefacto de error de medida: se mantiene con una ventana de medición
   independiente (2009→2023: −0,0032), hay sigma-convergencia genuina (la
   dispersión baja de 1,159 a 1,107) y la persistencia del nivel es alta (poca
   reversión). No es ruido disfrazado de convergencia.
2. **Selección muestral / outliers** — ✅ SOBREVIVE. Negativa y significativa en
   toda variante (rango jackknife [−0,0046, −0,0042]); NO la impulsan China
   (quitarla la debilita) ni los petroestados. Señal amplia, no de unos pocos.
3. **Ventana / endpoints** — ✅ SOBREVIVE. Estable 1995→2019 (−0,0051) y
   2000→2023 (−0,0044); no es un artefacto COVID (quitar 2023 la refuerza).
4. **Convergencia de club vs global** — ❌ NO SOBREVIVE. Y este es el matiz
   clave: la mitad POBRE de los países NO muestra convergencia significativa
   (p=0,37; los 50 más pobres p=0,69), mientras que se concentra en el club
   RICO (mitad rica −0,0082, p<0,0001). Condicionada por región, la pendiente
   se DUPLICA (−0,0088) — firma clásica de convergencia condicional.

## Veredicto honesto (para el tribunal)

**La convergencia de la PPA es un hallazgo estadísticamente real y robusto —
NO un artefacto — pero la lectura popular "los países pobres alcanzan a los
ricos" está sobredimensionada.** Es convergencia de **club/condicional**: los
países ricos y los de renta media convergen entre sí; los más pobres no dan
señal de alcanzar. Y es económicamente **glacial**: velocidad ~0,47 %/año,
media-vida ~147 años, R² 0,10. En términos de predicción: se puede proyectar
que un país de renta media-alta como España seguirá una senda de convergencia
lenta hacia la frontera, pero no que la desigualdad global entre países se
cierre.

España: log-renta 1995 = 10,42 → 2023 = 10,76; crecimiento medio 1,2 %/año —
una senda de convergencia de club coherente con el resto de la UE.

## Encaje con el proyecto

- Confirma la tesis central: **nivel trivialmente predecible (drift/persistencia),
  giros difíciles, y el uso honesto es el escenario condicional.** La PPA no es
  distinta de la vivienda o la deuda en esto.
- La convergencia de club, verificada, es un input legítimo para las cadenas
  condicionales de bienestar (la renta domina la mortalidad y la pobreza
  absoluta — `docs/bienestar_indicadores.md`): si la renta converge despacio,
  las mejoras de bienestar por la vía de la renta también.

## Límites declarados

- In-sample; verificación adversarial recomputada pero no validación
  out-of-sample formal (media-vida de 147 años excede cualquier ventana).
- 43 de los 230 "países" del cómputo bruto eran agregados WDI; quitarlos no
  cambia la pendiente (−0,0044 con 187 países reales), pero el recuento honesto
  es ~187 países.
