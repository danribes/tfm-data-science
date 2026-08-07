import { http, HttpResponse } from "msw";
import { BASE_LEVERS } from "../../engine/vintage";
import { SERIES_KEYS, YEARS, baseline, runScenario, type Scenario } from "../../engine/spain";
import { evaluateRedlines } from "../../engine/redlines";
import { seriesOf, type AnySeriesKey } from "../../engine/derived";
import { CONSTANTS_META } from "../../engine/constants";
import type { MonteCarloRequest, PersonaDependentsOut, ScenarioRequest } from "../../api/types";
import {
  MOCK_VINTAGE,
  mockKpis,
  mockPercentiles,
  mockPersonaCards,
  mockPresets,
  mockRedlines,
  mockSeries,
} from "./fixtures";

const META = { vintage: MOCK_VINTAGE, computed_not_advice: true };
const BASE = "http://localhost:8000";

/** Build the per-persona dependent series (outs + reds keys, deduped) from the honest scenario run. */
function personaDependents(scn: Scenario): Record<string, PersonaDependentsOut> {
  return Object.fromEntries(
    mockPersonaCards.map((card) => {
      const keys = new Set<AnySeriesKey>([
        card.headline as AnySeriesKey,
        ...card.outs.map((o) => o.k as AnySeriesKey),
        ...card.reds.flatMap((r) => (r.k ? [r.k as AnySeriesKey] : [])),
      ]);
      const series = Object.fromEntries([...keys].map((k) => [k, seriesOf(scn, k)]));
      return [card.id, { pill: card.pill, headline: card.headline, series }];
    }),
  );
}

export const handlers = [
  http.get(`${BASE}/health`, () => HttpResponse.json({ ...META, status: "ok", engine_version: "1.0.0" })),

  http.get(`${BASE}/vintage`, () =>
    HttpResponse.json({
      ...META,
      n_files: 141,
      files: [
        {
          name: "gov_10a_exp_TE",
          url: "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10a_exp?na_item=TE",
          fetched_at: "2026-07-18T08:31:29",
          bytes: 366460,
        },
      ],
    }),
  ),

  http.get(`${BASE}/constants`, () => HttpResponse.json({ ...META, constants: CONSTANTS_META })),

  http.get(`${BASE}/personas`, () =>
    HttpResponse.json({ ...META, kpis: mockKpis, series: mockSeries, personas: mockPersonaCards }),
  ),

  http.get(`${BASE}/presets`, () => HttpResponse.json({ ...META, presets: mockPresets })),

  http.get(`${BASE}/redlines`, () => HttpResponse.json({ ...META, redlines: mockRedlines })),

  // Real TS engine, not canned arrays — keeps the load-time cross-check (Task 11) meaningful.
  http.post(`${BASE}/scenario`, async ({ request }) => {
    const body = (await request.json()) as ScenarioRequest;
    const levers = { ...BASE_LEVERS, ...(body.levers ?? {}) };
    const horizon = body.horizon ?? 2050;
    const bas = baseline();
    const scn = runScenario(levers);
    const deltas = Object.fromEntries(
      SERIES_KEYS.map((k) => [k, scn[k].map((v, i) => v - bas[k][i])]),
    );
    const k = YEARS.indexOf(horizon);
    return HttpResponse.json({
      ...META,
      horizon,
      years: YEARS,
      baseline: bas,
      scenario: scn,
      deltas,
      personas: personaDependents(scn),
      redlines: evaluateRedlines(mockRedlines, scn, k >= 0 ? k : YEARS.length - 1),
    });
  }),

  http.post(`${BASE}/scenario/montecarlo`, async ({ request }) => {
    const body = (await request.json()) as MonteCarloRequest;
    const horizon = body.horizon ?? 2070;
    const years = Array.from({ length: horizon - 2026 + 1 }, (_, i) => 2026 + i);
    return HttpResponse.json({
      ...META,
      years,
      percentiles: mockPercentiles(years),
      n_paths: body.n_paths ?? 4000,
      seed: body.seed ?? 42,
    });
  }),
];
