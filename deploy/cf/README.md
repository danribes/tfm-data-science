# Corpus on Cloudflare

Serves the RAG corpus from Vectorize + D1 so the published app no longer depends
on a tunnel to a laptop.

The corpus is copyrighted. Every endpoint except `/health` requires a bearer
token, and `RAG_TOKEN` fails closed when unset — an unauthenticated deployment
would be a public extraction API for 43 textbooks, not a citation tool.

## Why queries are embedded at Hugging Face and not on Workers AI

The stored vectors come from `intfloat/multilingual-e5-large`. Vectors from two
different models are not comparable, so a query embedded by a Workers AI model
would score as noise against this index. Re-embedding all 17,946 chunks with a
Workers AI model is the alternative; using HF Inference keeps the existing
vectors valid and costs one extra hop per query.

## Sizes worth knowing before starting

| | |
|---|---|
| Chunks | 17,946 (`libros` 13,994 · `crack23` 3,684 · `metodo` 267 · `defensa_tfm` 1) |
| Stored dimensions | 18.4 M — above the 5 M free allowance, so Workers Paid is required |
| Export size | ≈370 MB of NDJSON across 18 shards |

## Steps

```bash
npm install -g wrangler
wrangler login

# 1. Resources. Cosine because the vectors are L2-normalised.
wrangler vectorize create evo-corpus --dimensions=1024 --metric=cosine
wrangler vectorize create-metadata-index evo-corpus --property-name=collection --type=string
wrangler d1 create evo-corpus          # put the printed id into wrangler.toml

# 2. Export locally.
cd "$(git rev-parse --show-toplevel)"
PYTHONPATH=. python deploy/cf/export_corpus.py --out /tmp/cf-export

# 3. Load D1, then the vectors.
wrangler d1 execute evo-corpus --remote --file=/tmp/cf-export/schema.sql
wrangler d1 execute evo-corpus --remote --file=/tmp/cf-export/chunks.sql
for f in /tmp/cf-export/vectors/*.ndjson; do
  wrangler vectorize insert evo-corpus --file="$f"
done

# 4. Secrets, then deploy.
cd deploy/cf/worker
wrangler secret put HF_TOKEN
wrangler secret put GEMINI_API_KEY
wrangler secret put RAG_TOKEN        # openssl rand -hex 24
wrangler deploy
```

## Check

```bash
curl -s "$WORKER/health"
curl -s -X POST "$WORKER/rag/chat" \
  -H "Authorization: Bearer $RAG_TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"¿Qué es la curva de Phillips?","collection":"libros","top_k":5}'
```

Retrieval must be compared against the local engine before trusting it: the
Worker reimplements `rag/retrieve.py`'s RRF fusion, and a silent regression here
looks like a plausible answer citing the wrong passage.
