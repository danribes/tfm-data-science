# Indicadores de bienestar y pobreza infantil (marco MPI/MODA) — 2026-07-19

Incorpora el marco bienestar ↔ pobreza ↔ pobreza infantil (UN/WB/UNICEF) y lo
conecta con la pregunta central: cuánto bienestar OBJETIVO compra el ingreso
público. Conectores: `connectors/bienestar.py`; frontera:
`analysis/bienestar_a1.py`; gold: `gold_bienestar_pais.csv`.

## 1. Mapeo de los 7 bloques del marco a series implementadas

| Bloque del marco | Serie(s) implementadas | Fuente | Cobertura |
|---|---|---|---|
| 1. Renta/consumo del hogar | Pobreza $3,00/día 2021 PPP (`SI.POV.DDAY`), umbral nacional (`SI.POV.NAHC`), MPI UNDP&OPHI (`SI.POV.MPUN` — `SI.POV.MDIM` está archivada) | WB/UNDP | ~166/107 países |
| 2. Mortalidad <5 | `SH.DYN.MORT` (‰ nacidos vivos) | WB/UN-IGME | 189 países, 2000– |
| 3. Privación material infantil | AROPE <18 (`ilc_peps01n`, edad Y_LT18) | Eurostat | UE, 2015– |
| 4. Malnutrición | Stunting (`SH.STA.STNT.ZS`), wasting (`SH.STA.WAST.ZS`) | WB/JME | 157 países (ricos sin encuesta: ESP NaN, esperado) |
| 5. Educación en dos capas | Adultos 25+ con ≥secundaria baja (`SE.SEC.CUAT.LO.ZS`) + niños de primaria fuera de la escuela (`SE.PRM.UNER.ZS`) | WB/UIS | 186 países |
| 6. Piso de protección social | Cobertura de cualquier programa (`per_allsp.cov_pop_tot`, ASPIRE) | WB | 128 países |
| 7. Piso de servicios | Agua gestionada segura, saneamiento seguro, electricidad, combustibles limpios | WB/JMP | 137–193 países |

Declarado NO implementado (micro o gated): microdatos MPI (OPHI, descarga por
país), MODA de UNICEF (microdatos DHS/MICS), privación infantil específica
UE-SILC (ítem por ítem; el AROPE <18 es el agregado disponible), detalle de
transferencias child-sensitive de ASPIRE.

## 2. La frontera ingreso público → bienestar (protocolo A1 intacto)

Diseño: resultado ~ ingresos públicos % PIB (WoRLD, media 2010–18) + log PIB
pc + urbanización; LOOCV; regla flexible ≤0,90×OLS; conformal 90 % por cuartil
de renta. MLP omitido y declarado (mismo régimen n≈100–185 donde perdió dos
veces bajo reglas idénticas).

| Frontera | n | mediana | OLS | GBM | Publicado |
|---|---|---|---|---|---|
| log mortalidad <5 | 185 | 0,471 | **0,438** | 0,494 (no cumple) | OLS |
| stunting (pp) | 124 | 7,08 | **6,41** | 6,94 (no cumple) | OLS |

- **España**: mortalidad <5 mejor que lo que su renta+ingresos predicen
  (residual −0,51 ± 0,93, dentro de banda — funnel, no ranking).
- Extremos que validan el método: **Guinea Ecuatorial** +2,14 en log (≈8,5×
  la mortalidad esperada para su renta — PIB petrolero sin conversión en
  bienestar) y **Guatemala** +29 pp de stunting sobre lo esperado (la anomalía
  crónica documentada); mejor que lo esperado: Macedonia del Norte y Tonga.
- Cuarta y quinta victoria consecutiva del OLS sobre el flexible en fronteras
  transversales: con n≈100–200 países, la estructura lineal captura la señal.

## 3. El marco completo contra el dinero (Spearman, descriptivo)

| Indicador | rho vs ingresos públicos % PIB |
|---|---|
| Mortalidad <5 | **−0,60** |
| Agua segura | +0,56 |
| Pobreza $3/día | −0,52 |
| Electricidad | +0,51 |
| Stunting / MPI | −0,48 |
| Cobertura protección social | +0,40 |
| Niños sin escolarizar | −0,30 |

Todas las direcciones correctas y fuertes: más capacidad fiscal, menos
privación en todas las dimensiones del marco. La frontera responde la pregunta
fina — QUIÉN convierte mejor su capacidad fiscal en bienestar a renta
comparable — sin caer en la trampa del ranking (bandas conformal siempre).

## 4. Conexión con el resto del proyecto

- Cierra el triángulo: gasto por función (COFOG 89 países) + ingresos por tipo
  (WoRLD 195) + resultados de bienestar (13 series) — "dinero público →
  resultados" medido de punta a punta.
- El RAG y el stress test ganan la dimensión social: la pregunta "¿qué pasa
  con un Estado del 10 %?" ahora tiene contrapartida empírica en el marco
  (los países hoy en ~10 % de ingresos concentran los peores valores de las
  7 dimensiones).
- Réplica del patrón A1 en un tercer dominio con el MISMO protocolo y
  veredicto honesto — evidencia de método, no cherry-picking.
