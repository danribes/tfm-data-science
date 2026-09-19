/**
 * Cloudflare Worker serving the corpus that used to require a tunnel to Dan's laptop.
 *
 * Retrieval is the same shape as rag/retrieve.py: a dense ranking from Vectorize
 * and a BM25 ranking from D1's FTS5, fused with reciprocal rank. Dense-only
 * retrieval measurably loses the questions whose wording matches a heading, so
 * the lexical half is not optional.
 *
 * Queries are embedded through HF Inference with intfloat/multilingual-e5-large.
 * That is not a preference: the stored vectors came from that model, and a query
 * embedded by a Workers AI model would be scored against an incompatible space.
 */

const RRF_K = 60;
const W_DENSE = 6.0;
const W_LEXICAL = 1.0;
const EMBED_MODEL = "intfloat/multilingual-e5-large";

const COLLECTIONS = {
  libros: { label: "Manuales de economía", authority: "academico" },
  metodo: { label: "Método y diseño del propio modelo", authority: "propio" },
  defensa_tfm: { label: "Defensa del TFM", authority: "defensa" },
  crack23: { label: "Canal crack23", authority: "opinion" },
};

const CORS = {
  "Access-Control-Allow-Origin": "https://danribes.github.io",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization",
};

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });

/** The corpus is copyrighted, so every read is gated. Without this the endpoint
 *  is a public extraction API for 43 textbooks rather than a citation tool. */
function authorised(request, env) {
  if (!env.RAG_TOKEN) return false; // fail closed when unconfigured
  const h = request.headers.get("Authorization") || "";
  const token = h.startsWith("Bearer ") ? h.slice(7) : "";
  if (token.length !== env.RAG_TOKEN.length) return false;
  let diff = 0;
  for (let i = 0; i < token.length; i++) diff |= token.charCodeAt(i) ^ env.RAG_TOKEN.charCodeAt(i);
  return diff === 0;
}

async function embedQuery(text, env) {
  const r = await fetch(
    `https://api-inference.huggingface.co/pipeline/feature-extraction/${EMBED_MODEL}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.HF_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        inputs: `query: ${text}`,
        options: { wait_for_model: true },
      }),
    },
  );
  if (!r.ok) throw new Error(`HF embed ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const v = await r.json();
  return Array.isArray(v[0]) ? v[0] : v;
}

/** FTS5 rejects bare punctuation and unbalanced quotes; quote each term. */
function ftsQuery(text) {
  const terms = text
    .toLowerCase()
    .replace(/["'()]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 2)
    .slice(0, 24)
    .map((t) => `"${t}"`);
  return terms.length ? terms.join(" OR ") : null;
}

function rrf(rankings) {
  const score = new Map();
  for (const [ids, weight] of rankings) {
    ids.forEach((id, i) => {
      score.set(id, (score.get(id) || 0) + weight / (RRF_K + i + 1));
    });
  }
  return [...score.entries()].sort((a, b) => b[1] - a[1]).map(([id]) => id);
}

async function retrieve(question, collection, topK, env) {
  const vector = await embedQuery(question, env);

  const dense = await env.VECTORIZE.query(vector, {
    topK: Math.max(topK * 4, 32),
    filter: { collection },
    returnMetadata: "none",
  });
  const denseIds = dense.matches.map((m) => Number(m.id));

  let lexIds = [];
  const expr = ftsQuery(question);
  if (expr) {
    try {
      const res = await env.DB.prepare(
        `SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid
         WHERE chunks_fts MATCH ? AND c.collection = ?
         ORDER BY bm25(chunks_fts) LIMIT ?`,
      )
        .bind(expr, collection, Math.max(topK * 4, 32))
        .all();
      lexIds = res.results.map((r) => Number(r.id));
    } catch {
      lexIds = []; // a malformed FTS expression must not sink the dense half
    }
  }

  const ids = rrf([
    [denseIds, W_DENSE],
    [lexIds, W_LEXICAL],
  ]).slice(0, topK);
  if (!ids.length) return [];

  const rows = await env.DB.prepare(
    `SELECT id, collection, title, page, section, text FROM chunks
     WHERE id IN (${ids.map(() => "?").join(",")})`,
  )
    .bind(...ids)
    .all();

  const byId = new Map(rows.results.map((r) => [Number(r.id), r]));
  return ids
    .map((id) => byId.get(id))
    .filter(Boolean)
    .map((r) => ({
      text: r.text,
      cita: [r.title, r.section, r.page ? `p. ${r.page}` : null]
        .filter(Boolean)
        .join(" · "),
      authority: (COLLECTIONS[r.collection] || {}).authority || "propio",
      collection: r.collection,
    }));
}

const SYSTEM = `Responde SÓLO con lo que digan los pasajes numerados. Cita como [1], [2].
Si los pasajes no cubren la pregunta, dilo explícitamente en vez de rellenar el hueco.
No inventes cifras ni fuentes. Responde en español.`;

async function generate(question, passages, env) {
  const ctx = passages
    .map((p, i) => `[${i + 1}] ${p.cita}\n${p.text}`)
    .join("\n\n");
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${env.GEMINI_API_KEY}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM }] },
        contents: [{ parts: [{ text: `Pasajes:\n\n${ctx}\n\nPregunta: ${question}` }] }],
        generationConfig: { temperature: 0.2, maxOutputTokens: 1024 },
      }),
    },
  );
  if (!r.ok) throw new Error(`Gemini ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const d = await r.json();
  return d.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (url.pathname === "/health") {
      return json({ status: "ok", vintage: "2026-07-31", computed_not_advice: true });
    }

    if (!authorised(request, env)) {
      return json({ detail: "Falta el token de acceso al corpus." }, 401);
    }

    if (url.pathname === "/rag/collections") {
      const rows = await env.DB.prepare(
        "SELECT collection, COUNT(*) n FROM chunks GROUP BY collection",
      ).all();
      return json({
        vintage: "2026-07-31",
        computed_not_advice: true,
        collections: rows.results.map((r) => ({
          id: r.collection,
          label: (COLLECTIONS[r.collection] || {}).label || r.collection,
          authority: (COLLECTIONS[r.collection] || {}).authority || "propio",
          note: "",
          documents: 0,
          chunks: r.n,
        })),
        total_documents: 0,
        total_chunks: rows.results.reduce((a, r) => a + r.n, 0),
      });
    }

    if (url.pathname === "/rag/chat" && request.method === "POST") {
      const body = await request.json();
      const collection = body.collection || "libros";
      if (!COLLECTIONS[collection]) {
        return json({ detail: `colección desconocida: ${collection}` }, 422);
      }
      try {
        const passages = await retrieve(body.question, collection, body.top_k || 8, env);
        const answer = passages.length
          ? await generate(body.question, passages, env)
          : "El corpus no contiene pasajes que cubran esta pregunta.";
        return json({
          vintage: "2026-07-31",
          computed_not_advice: true,
          question: body.question,
          collection,
          answer,
          passages,
          grounded: passages.length > 0,
          provider: "gemini",
          model: "gemini-2.0-flash",
          error: null,
        });
      } catch (e) {
        return json({ detail: `corpus no disponible: ${e.message}` }, 503);
      }
    }

    return json({ detail: "not found" }, 404);
  },
};
