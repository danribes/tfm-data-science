# frontend — España en escenarios (fase 2)

Panel editorial sobre la API de fase 1: 10 palancas, presets S0–S7, líneas rojas,
Monte Carlo y 4 perfiles (01 Bonista, 02 Banca, 03 Comprador, 06 Político).
El escenario se calcula EN el navegador con un port TypeScript del motor v16,
verificado contra el mismo fixture de anclas que el motor Python
(`tests/fixtures/engine_anchors.json`, vintage 2026-07-31).

## Requisitos

- Node 20+ (desarrollado con Node 22) y npm.
- Para usar la app: la API de fase 1 en marcha —
  `uvicorn api.main:app --reload --port 8000` desde la raíz del repo.
  `VITE_API_BASE` cambia la URL (por defecto `http://localhost:8000`).
- Para los tests: nada — todo corre offline con MSW.

## Comandos

| Comando | Qué hace |
|---|---|
| `npm install` | dependencias |
| `npm run dev` | Vite dev server en http://localhost:5173 (necesita la API) |
| `npm test` | Vitest: paridad de motores, store/URL, componentes, rutas (offline) |
| `npm run e2e` | Playwright smoke contra un preview con API simulada (offline) |
| `npm run build` | build de producción en `dist/` |
| `npm run build:mock` | build con `VITE_MOCK_API=1` (ver `.env.mock`) — el que usa `npm run e2e` |
| `npm run gen:constants` | regenera `src/engine/constants.ts` + `vintage.ts` desde la API y `data/gold/` (solo al cambiar de vintage; el resultado se commitea) |

### Playwright smoke (`npm run e2e`)

`playwright.config.ts` levanta `npm run build:mock && npm run preview` en
`http://localhost:4173` y ejecuta `e2e/smoke.spec.ts` contra ese preview. El
build `:mock` activa el worker de MSW (`public/mockServiceWorker.js`, generado
en la Tarea 6) vía `.env.mock` → `VITE_MOCK_API=1`, que intercepta toda
llamada a `http://localhost:8000/*` en el propio navegador — el preview nunca
toca la red y la API real de fase 1 no necesita estar arrancada para correr
el smoke. Primera vez en una máquina nueva: `npx playwright install chromium`.

El smoke (spec §9, fila 6) cubre: arranque, mover una palanca (el gauge y la
curva del gráfico cambian), cambiar de perfil (el escenario persiste), alternar
tema, cero errores de consola.

## El contrato de doble motor

`src/engine/` es un port línea a línea de `engine/spain.py`. El test
`src/engine/__tests__/anchors.test.ts` es el contrato: carga
`tests/fixtures/engine_anchors.json` (vía el alias `@fixtures`, ver
`vite.config.ts`) y comprueba que el motor TS reproduce, dentro de tolerancia,
los mismos valores que el motor Python fijó en ese fixture — línea base,
los 8 presets S0–S7 y una sonda con las 10 palancas movidas a la vez.

Para regenerar el fixture de anclas (tras un cambio de vintage o de motor),
desde la raíz del repo:

```
.venv/bin/python scripts/generate_anchor_fixture.py
```

Esto reescribe `tests/fixtures/engine_anchors.json`, que ambos motores leen
(`tests/test_anchors.py` en Python, `anchors.test.ts` en TS) — cámbialo y
re-commítealo junto con cualquier cambio de vintage; no hace falta tocar
ningún otro archivo generado del lado TS salvo `npm run gen:constants` si
también cambió `/constants`.

Monte Carlo nunca se calcula en JS (PCG64 no es reproducible en el navegador);
el abanico llega siempre de `POST /scenario/montecarlo` y su regla de
aceptación en el lado TS es la envolvente dorada ±2 pp.

## Contratos que no se negocian

- Copy de personas y presets: verbatim de la API. Números: siempre `es-ES` vía
  `src/lib/fmt.ts` (`nf`/`sg`/`eur`) — excepto años e identificadores opacos
  (p. ej. la semilla del Monte Carlo).
- Sin API no hay app: pantalla de bloqueo con la URL y el comando de arranque,
  jamás datos inventados.

## Gaps conocidos

- **Nota de fórmula del KPI (`o-note`) omitida.** El texto de v16 no viene en
  el payload de la API; la tile muestra la línea de delta calculado en su
  lugar.
- **Gráfico histórico del perfil reutiliza `ProjectionChart`** (serie
  observada única) en vez de un componente retro dedicado con línea `--retro`
  morada. El eje X y el tooltip **sí** imprimen el periodo real
  (`2021-07`, `2020-Q2`) vía la prop `labels`; lo que queda es cosmético —
  la leyenda dice «escenario / base» para una serie observada, y el color de
  línea no es el morado retro. Pendiente de un pase de pulido rápido.
- **Tarjeta de atribución por palanca no implementada** — v16 la recalculaba
  por palanca; fuera del alcance de la especificación fase 2 (§10). El
  semáforo + cadena + narrativa del perfil cubren el mismo argumento.
- **Slot de aviso `defaults_used` es genérico y no se activa.** Los endpoints
  de España nunca emiten `defaults_used` (pertenece a `GenericScenarioResponse`,
  fuera de alcance §10), pero `Warnings.addWarning()` ya existe para el día
  que llegue una UI genérica.
- **Umbral de vintage obsoleto: 90 días** (`STALE_LIMIT_DAYS` en
  `src/state/appHealth.ts`). La especificación exige el aviso pero no fija un
  número; 90 días ≈ un trimestre de deriva en un dataset de refresco
  trimestral. Trivial de cambiar si se decide otro valor.
- **Banda "near" del semáforo/gauge es 10 % en todo el front**, igual que
  `engine/redlines.py` (spec §4.5); el extracto de v16 usaba 12 %. Una sola
  tolerancia, una sola regla de honestidad.


## Despliegue público

| Pieza | Dónde | Cómo |
|---|---|---|
| Frontend | GitHub Pages — <https://danribes.github.io/tfm-data-science/> | `.github/workflows/deploy-pages.yml`, se publica en cada push a `main` |
| API | Render (capa gratuita) | `render.yaml` — en el panel de Render: *New → Blueprint* sobre este repo |
| RAG | **Sólo local, a propósito** | el corpus contiene libros con derechos de autor y nunca sale de la máquina; el despliegue responde 503 con esa explicación |

La instancia gratuita de Render se duerme tras 15 min sin uso y tarda ~1 min
en despertar; el frontend lo sabe — la sonda de salud reintenta durante dos
minutos y muestra «Despertando el servidor…» mientras tanto.

Si Render asigna otra URL distinta de `https://evo-espana-api.onrender.com`,
define la variable de repositorio `API_BASE` con la URL asignada y relanza el
workflow `deploy-pages`.

El despliegue de la API es adelgazado (`requirements-deploy.txt`): motor,
artefactos de investigación y informes, sin torch ni el índice vectorial.
