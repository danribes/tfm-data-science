#!/usr/bin/env bash
# Assemble the Hugging Face Space's content into a staging directory.
#
# The Space is a curated subset of the repo, not a mirror: the API code, the
# frozen data, the committed evaluation artifacts, and the Space's own README
# (whose YAML frontmatter is how HF knows this is a Docker app on port 7860).
# The repo's real README stays on GitHub — the two files serve different
# readers.
set -euo pipefail

STAGE="${1:?uso: assemble.sh <dir-destino>}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Reusing a populated stage could publish stale files removed from the
# allowlist (including earlier private RAG reports). Fail without deleting
# anything; callers must supply a new directory or an existing empty one.
if [[ -e "$STAGE" || -L "$STAGE" ]]; then
  if [[ ! -d "$STAGE" || -L "$STAGE" || -n "$(find "$STAGE" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    echo "error: el destino debe ser un directorio nuevo o vacío: $STAGE" >&2
    exit 1
  fi
fi
mkdir -p "$STAGE"

# Runtime code, including the lightweight public lexical RAG. The private
# corpus and embedding models are never inputs to this assembly.
for d in api engine explain research rag data tools; do
  mkdir -p "$STAGE/$d"
  find "$ROOT/$d" -name "*.py" -not -path "*/__pycache__/*" | while read -r f; do
    rel="${f#"$ROOT"/}"
    mkdir -p "$STAGE/$(dirname "$rel")"
    cp "$f" "$STAGE/$rel"
  done
done

# The frozen vintage and the external panels the endpoints read.
cp -r "$ROOT/data/gold" "$STAGE/data/gold"
cp -r "$ROOT/data/external" "$STAGE/data/external"
cp "$ROOT/data/live/indicator_catalog.yaml" "$STAGE/data/live/"

# Only the research artifacts read by the public endpoints. Do not glob this
# directory: private RAG acquisition/probe reports may contain book passages.
#
# Los dos informes del RAG se añadieron tras comprobar uno por uno que no los
# llevan: el de recuperación guarda títulos y métricas, y el de generación
# guarda frases de las respuestas del modelo y sus rechazos. Sin ellos,
# /rag/eval respondía «faltan artefactos de evaluación» en el despliegue
# mientras los ficheros estaban en el repositorio desde el principio.
mkdir -p "$STAGE/docs/eval"
for report in t1-dl-global distress state_dependence regimes \
              rag-eval-2026-08-09 rag-chat-eval; do
  cp "$ROOT/docs/eval/$report.json" "$STAGE/docs/eval/"
done

# Build from the original project README, before installing the Space README.
# The builder reads a fixed allowlist of six project-authored Markdown files;
# it needs only Python's standard library, never the local books/index.
cp "$ROOT/rag/public_sources.json" "$STAGE/rag/"
PYTHONPATH="$ROOT" python -m rag.public_corpus \
  --source-root "$ROOT" --out "$STAGE/data/rag/public.db"

cp "$ROOT/requirements-deploy.txt" "$STAGE/"
cp "$ROOT/requirements-lock.txt" "$STAGE/"
cp "$ROOT/deploy/hf/Dockerfile" "$STAGE/Dockerfile"
cp "$ROOT/deploy/hf/README-space.md" "$STAGE/README.md"

echo "staging listo en $STAGE:"
du -sh "$STAGE"
