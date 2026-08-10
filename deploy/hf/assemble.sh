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

mkdir -p "$STAGE"

# Code the API imports at runtime. rag/ ships as source so the guarded lazy
# imports resolve the module and fail on the missing heavy deps, which is what
# turns a would-be 500 into the clean 503.
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

# Committed research artifacts: prediction, distress, state-dependence,
# regimes, RAG report card. Without them the endpoints answer "not generated".
mkdir -p "$STAGE/docs/eval"
cp "$ROOT"/docs/eval/*.json "$STAGE/docs/eval/"

cp "$ROOT/requirements-deploy.txt" "$STAGE/"
cp "$ROOT/deploy/hf/Dockerfile" "$STAGE/Dockerfile"
cp "$ROOT/deploy/hf/README-space.md" "$STAGE/README.md"

echo "staging listo en $STAGE:"
du -sh "$STAGE"
