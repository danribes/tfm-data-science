import { http, HttpResponse } from "msw";
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
    const nShow = body.n_show ?? 60;
    // Spaghetti strands for the offline build: deterministic pseudo-paths
    // spread across the mocked p5–p95 envelope. No RNG — a fixed hash of
    // (strand, year) keeps the smoke test and the mock build reproducible.
    const paths = Array.from({ length: nShow }, (_, j) =>
      years.map((_, i) => {
        const wobble = Math.sin((j + 1) * 12.9898 + i * 78.233) * 0.5 + 0.5;
        return pct.p5[i] + (pct.p95[i] - pct.p5[i]) * wobble;
      }),
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
