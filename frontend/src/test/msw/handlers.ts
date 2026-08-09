import { HttpResponse, delay, http } from "msw";
import { BASE_LEVERS } from "../../engine/vintage";
import { LEVER_SPECS } from "../../engine/levers";
import type { SeriesKey } from "../../engine/spain";
import { SERIES_KEYS, YEARS, baseline, runScenario } from "../../engine/spain";
import { evaluateRedlines } from "../../engine/redlines";
import { CONSTANTS_META } from "../../engine/constants";
import type { ExplainRequest, MonteCarloRequest, ScenarioRequest } from "../../api/types";
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
      // Empty per the brief: the real backend derives each persona's series from
      // engine/spain.py's `extra` field, which api/schemas.py's PersonaCard does NOT
      // expose to the frontend — so no local mock can reproduce the real shape
      // faithfully (a prior attempt fabricated `ipvreal` and dropped `esf` for card 02).
      // The front never consumes this field: it computes persona series from its own
      // engine, and uses /scenario only for the load-time parity cross-check on `b`.
      personas: {},
      redlines: evaluateRedlines(mockRedlines, scn, k >= 0 ? k : YEARS.length - 1),
    });
  }),

  http.post(`${BASE}/scenario/montecarlo`, async ({ request }) => {
    const body = (await request.json()) as MonteCarloRequest;
    const horizon = body.horizon ?? 2070;
    const years = Array.from({ length: horizon - 2026 + 1 }, (_, i) => 2026 + i);
    const pct = mockPercentiles(years);
    const paths = Array.from({ length: Math.min(body.n_show ?? 80, 80) }, () =>
      years.map((_, i) => 106.32 + i * 0.4),
    );
    return HttpResponse.json({
      ...META,
      years,
      percentiles: pct,
      n_paths: body.n_paths ?? 4000,
      seed: body.seed ?? 42,
      paths,
    });
  }),

  http.get(`${BASE}/scenario/sensitivity`, () =>
    HttpResponse.json({
      ...META,
      horizons: [2030, 2050],
      target_series: [
        { key: "b", label: "Deuda pública", unit: "% PIB" },
        { key: "u", label: "Paro total", unit: "%" },
        { key: "pi", label: "Inflación IPCA", unit: "%" },
        { key: "g", label: "PIB real", unit: "%" },
        { key: "esf", label: "Esfuerzo de compra de vivienda", unit: "%" },
        { key: "saldo", label: "Saldo público", unit: "% PIB" },
      ],
      matrix: Object.fromEntries(
        LEVER_SPECS.map((s) => [
          s.id,
          {
            lever_id: s.id,
            lever_name: s.nm,
            unit: s.unit,
            sensitivities: {
              "2030": { b: 2.45, u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
              "2050": { b: 8.12, u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
            },
            lever_span: s.max - s.min,
            span_effects: {
              "2030": { b: 2.45 * (s.max - s.min), u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
              "2050": { b: 8.12 * (s.max - s.min), u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
            },
          },
        ]),
      ),
    }),
  ),

  http.post(`${BASE}/scenario/sensitivity`, () =>
    HttpResponse.json({
      ...META,
      horizons: [2030, 2050],
      target_series: [
        { key: "b", label: "Deuda pública", unit: "% PIB" },
        { key: "u", label: "Paro total", unit: "%" },
        { key: "pi", label: "Inflación IPCA", unit: "%" },
        { key: "g", label: "PIB real", unit: "%" },
        { key: "esf", label: "Esfuerzo de compra de vivienda", unit: "%" },
        { key: "saldo", label: "Saldo público", unit: "% PIB" },
      ],
      matrix: Object.fromEntries(
        LEVER_SPECS.map((s) => [
          s.id,
          {
            lever_id: s.id,
            lever_name: s.nm,
            unit: s.unit,
            sensitivities: {
              "2030": { b: 2.45, u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
              "2050": { b: 8.12, u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
            },
            lever_span: s.max - s.min,
            span_effects: {
              "2030": { b: 2.45 * (s.max - s.min), u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
              "2050": { b: 8.12 * (s.max - s.min), u: 0.31, pi: 0.12, g: 0.45, esf: 1.2, saldo: -0.5 },
            },
          },
        ]),
      ),
    }),
  ),

  http.get(`${BASE}/scenario/report`, () => HttpResponse.html("<!DOCTYPE html><html><body>Policy Brief</body></html>")),
  http.post(`${BASE}/scenario/report`, () => HttpResponse.html("<!DOCTYPE html><html><body>Policy Brief</body></html>")),

  // Evidencia, offline: shapes only. The real numbers come from the frozen
  // panels and belong to the Python suite; what the UI must get right is the
  // compatible / not-compatible rendering and the unidentifiable list.
  http.get(`${BASE}/evidence`, () =>
    HttpResponse.json({
      ...META,
      engine_version: "1.0.0",
      comparisons: [
        { constant: "IPV_LR", label: "Crecimiento a largo plazo del precio de la vivienda",
          calibrated: 3.0, source: "gold_ccaa_trimestral.csv · 20 CCAA",
          compatible: false, verdict: "fuera de la banda (por encima)",
          name: "crecimiento anual del IPV (% a/a)", coef: 1.23, se: 0.18,
          n: 1460, n_units: 20, ci_low: 0.93, ci_high: 1.53, significant: true,
          subperiods: [
            { label: "2007–2013 · ajuste", name: "2007–2013 · ajuste",
              coef: -6.48, se: 0.35, n: 480, n_units: 20,
              ci_low: -7.05, ci_high: -5.9, significant: true },
            { label: "2014–2026 · recuperación", name: "2014–2026 · recuperación",
              coef: 5.0, se: 0.25, n: 980, n_units: 20,
              ci_low: 4.59, ci_high: 5.41, significant: true },
          ] },
        { constant: "IPV_REV", label: "Reversión anual del IPV hacia su tendencia",
          calibrated: 0.6, source: "gold_ccaa_trimestral.csv · AR(1)",
          compatible: false, verdict: "fuera de la banda (por encima)",
          name: "reversión (1 - phi)", coef: 0.2, se: 0.012,
          n: 1380, n_units: 20, ci_low: 0.18, ci_high: 0.22, significant: true,
          subperiods: [] },
      ],
      irf: {
        anchor_h: 4,
        unit: "% de desviación del precio por punto de choque",
        note: "choque idiosincrásico regional",
        horizons: [
          { h: 0, years: 0, name: "h=0", coef: 0, se: 0, n: 1460, n_units: 20,
            ci_low: 0, ci_high: 0, significant: false },
          { h: 4, years: 1, name: "h=4", coef: 0.342, se: 0.052, n: 1380, n_units: 20,
            ci_low: 0.257, ci_high: 0.427, significant: true },
          { h: 8, years: 2, name: "h=8", coef: 0.479, se: 0.085, n: 1300, n_units: 20,
            ci_low: 0.34, ci_high: 0.619, significant: true },
          { h: 12, years: 3, name: "h=12", coef: 0.566, se: 0.124, n: 1220, n_units: 20,
            ci_low: 0.362, ci_high: 0.769, significant: true },
        ],
        engine_path: [
          { h: 0, years: 0, coef: null },
          { h: 4, years: 1, coef: 0.342 },
          { h: 8, years: 2, coef: 0.137 },
          { h: 12, years: 3, coef: 0.055 },
        ],
      },
      fiscal_persistence: {
        name: "persistencia del saldo (proxy)", coef: 0.87, se: 0.04,
        n: 931, n_units: 18, ci_low: 0.81, ci_high: 0.94, significant: true,
      },
      identifiable: {
        IPV_LR: "sí — crecimiento medio del IPV en el panel CCAA",
        MULT: "no — haría falta un shock fiscal identificado",
        OKUN: "no — el vintage no trae paro regional",
      },
    }),
  ),

  // Predicción, offline. The numbers are the real ones from
  // docs/eval/t1-dl-global.json: the page's whole job is to render a loss
  // correctly, so a fixture where the candidate wins would test the wrong path.
  http.get(`${BASE}/prediction`, () =>
    HttpResponse.json({
      ...META,
      available: true,
      protocol: {
        origins: "2019Q4–2023Q4", test_start: "2024Q1", horizons: 8,
        n_ccaa: 17, train_series: 1760, train_windows: 113649,
        train_cutoff: "2019Q3", seed: 42,
      },
      methods: ["dl_global", "drift", "naive", "snaive"],
      rows: [
        { h: 1, mase: { dl_global: 0.2435, drift: 0.2411, naive: 0.2953, snaive: 0.8424 } },
        { h: 2, mase: { dl_global: 0.3514, drift: 0.3579, naive: 0.4993, snaive: 0.8664 } },
        { h: 4, mase: { dl_global: 0.5651, drift: 0.5541, naive: 0.9424, snaive: 0.9424 } },
        { h: 8, mase: { dl_global: 1.0382, drift: 0.9792, naive: 2.1289, snaive: 2.1289 } },
      ],
      verdict: {
        candidate: "dl_global", beaten_ccaa: 5, total_ccaa: 17,
        required: 12, horizon: 4,
        mase_candidate: 0.4, mase_drift: 0.3953,
        mase_candidate_long: 0.8421, mase_drift_long: 0.796,
        wins: false, verdict: "no bate al drift",
      },
      note: "",
    }),
  ),

  // --- RAG, offline ---
  // The corpus itself cannot ship to the browser (copyrighted textbooks), so
  // the mock serves a small fixed set of passages with the real response shape.
  // What the tests exercise is the contract: authority tags, citations, and the
  // ungrounded path — not retrieval quality, which belongs in the Python suite.
  http.get(`${BASE}/rag/collections`, () =>
    HttpResponse.json({
      ...META,
      collections: [
        { id: "libros", label: "Manuales de economía", authority: "academico",
          note: "Textos con copyright — nunca salen de la máquina local.",
          documents: 43, chunks: 13316 },
        { id: "metodo", label: "Método y diseño del propio modelo", authority: "propio",
          note: "Specs, Metodología y Cómo funciona de esta app.",
          documents: 10, chunks: 267 },
        { id: "crack23", label: "Canal crack23", authority: "opinion",
          note: "Transcripciones y resúmenes. Es opinión, no fuente académica.",
          documents: 420, chunks: 3586 },
      ],
      total_documents: 473,
      total_chunks: 17169,
    }),
  ),

  http.post(`${BASE}/rag/search`, async ({ request }) => {
    const body = (await request.json()) as { query?: string; collection?: string };
    const collection = body.collection ?? "libros";
    const authority =
      collection === "crack23" ? "opinion" : collection === "metodo" ? "propio" : "academico";
    const grounded = !/fusi[oó]n fr[ií]a/i.test(body.query ?? "");
    return HttpResponse.json({
      ...META,
      query: body.query ?? "",
      collection,
      passages: grounded
        ? [{
            chunk_id: 1,
            text: "El diferencial entre el tipo de interés y el crecimiento nominal determina la senda de la deuda.",
            title: "Banco de Espana - Documento Ocasional 1803 (ES)",
            collection, authority, page: 12, section: "3.1", score: 0.0387,
            cita: "Banco de Espana - Documento Ocasional 1803 (ES) · 3.1 · p. 12",
          }]
        : [],
    });
  }),

  // SSE mock: one `passages` frame, then deltas, then `done` — the same order
  // the real endpoint emits, so the UI's streaming path is genuinely exercised.
  http.post(`${BASE}/rag/chat/stream`, async ({ request }) => {
    const body = (await request.json()) as { question?: string; collection?: string };
    const collection = body.collection ?? "libros";
    const authority =
      collection === "crack23" ? "opinion" : collection === "metodo" ? "propio" : "academico";
    const grounded = !/fusi[oó]n fr[ií]a/i.test(body.question ?? "");
    const passages = grounded
      ? [{
          chunk_id: 1,
          text: "El diferencial entre el tipo de interés y el crecimiento nominal determina la senda de la deuda.",
          title: "Banco de Espana - Documento Ocasional 1803 (ES)",
          collection, authority, page: 12, section: "3.1", score: 0.0387,
          cita: "Banco de Espana - Documento Ocasional 1803 (ES) · 3.1 · p. 12",
        }]
      : [];
    const answer = grounded
      ? "La deuda crece cuando el tipo efectivo supera al crecimiento nominal [1]."
      : "El corpus no cubre esta pregunta.";

    const frame = (event: string, data: unknown) =>
      `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;

    const stream = new ReadableStream({
      async start(controller) {
        const enc = new TextEncoder();
        controller.enqueue(enc.encode(frame("passages", { passages, grounded })));
        if (grounded) {
          for (const word of answer.split(" ")) {
            await delay(5);
            controller.enqueue(enc.encode(frame("delta", { text: word + " " })));
          }
        }
        controller.enqueue(enc.encode(frame("done", {
          answer, grounded,
          provider: grounded ? "gemini" : null,
          model: grounded ? "gemini-2.5-flash" : null,
          error: null,
        })));
        controller.close();
      },
    });
    return new HttpResponse(stream, {
      headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
    });
  }),

  http.post(`${BASE}/rag/chat`, async ({ request }) => {
    const body = (await request.json()) as { question?: string; collection?: string };
    const collection = body.collection ?? "libros";
    const authority =
      collection === "crack23" ? "opinion" : collection === "metodo" ? "propio" : "academico";
    // A question about something the corpus cannot cover exercises the
    // ungrounded branch, which must never fabricate an answer.
    const grounded = !/fusi[oó]n fr[ií]a/i.test(body.question ?? "");
    return HttpResponse.json({
      ...META,
      question: body.question ?? "",
      collection,
      answer: grounded
        ? "La deuda crece cuando el tipo efectivo supera al crecimiento nominal [1]."
        : "El corpus no cubre esta pregunta.",
      passages: grounded
        ? [{
            chunk_id: 1,
            text: "El diferencial entre el tipo de interés y el crecimiento nominal determina la senda de la deuda.",
            title: "Banco de Espana - Documento Ocasional 1803 (ES)",
            collection, authority, page: 12, section: "3.1", score: 0.0387,
            cita: "Banco de Espana - Documento Ocasional 1803 (ES) · 3.1 · p. 12",
          }]
        : [],
      grounded,
      provider: grounded ? "gemini" : null,
      model: grounded ? "gemini-2.5-flash" : null,
      error: null,
    });
  }),

  // The explanation, offline. The decomposition runs the real TS engine one
  // lever at a time — same method as the Python `explain.facts.decompose` — so
  // the mocked numbers are the engine's, not canned. Only the prose is a
  // shortened stand-in for the server's deterministic templates.
  http.post(`${BASE}/explain`, async ({ request }) => {
    const body = (await request.json()) as ExplainRequest;
    const levers = { ...BASE_LEVERS, ...(body.levers ?? {}) };
    const key = (body.headline ?? "b") as SeriesKey;
    const last = YEARS.length - 1;

    const bas = baseline();
    const scn = runScenario(levers);
    const jointDelta = scn[key][last] - bas[key][last];

    const moved = LEVER_SPECS.filter(
      (s) => Math.abs(levers[s.id] - BASE_LEVERS[s.id]) > 1e-9,
    );
    const contributions = moved
      .map((s) => {
        const solo = runScenario({ ...BASE_LEVERS, [s.id]: levers[s.id] });
        return { lever_id: s.id, lever_name: s.nm, delta: solo[key][last] - bas[key][last], share: 0 };
      })
      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
    const grossTotal = contributions.reduce((acc, c) => acc + Math.abs(c.delta), 0);
    for (const c of contributions) c.share = grossTotal > 1e-12 ? Math.abs(c.delta) / grossTotal : 0;
    const interaction = jointDelta - contributions.reduce((acc, c) => acc + c.delta, 0);

    const resumen = moved.length
      ? `Has movido ${moved.length} palanca${moved.length > 1 ? "s" : ""}: ` +
        `${moved.map((s) => s.nm).join("; ")}. La deuda pública queda en ` +
        `${scn[key][last].toFixed(1)} %PIB en ${YEARS[last]}.`
      : `Estás viendo la línea base del vintage ${MOCK_VINTAGE}: nada está proyectado todavía.`;

    return HttpResponse.json({
      ...META,
      resumen,
      mecanismo: moved.length
        ? "Cada palanca se propaga por la identidad de deuda b(t+1) = b(t)·(1+r−g) − sp."
        : "Sin palancas movidas no hay mecanismo que trazar.",
      advertencia:
        "Proyección condicional. No es una previsión ni una recomendación de compra, venta o voto.",
      source: "deterministic",
      model: null,
      fallback_reason: "offline mock",
      contributions,
      interaction,
      joint_delta: jointDelta,
      headline_key: key,
      headline_year: YEARS[last],
    });
  }),
];
