# Public API and a lexical index of explicitly approved project documents.
# The private book corpus, torch, and embedding models are not shipped.
FROM python:3.12-slim

# HF Spaces runs containers as uid 1000 and serves on port 7860.
RUN useradd -m -u 1000 user
WORKDIR /app
# Defaults are the public deployment. A reviewer deployment overrides both in
# the Space settings — EVO_RAG_MODE=remote_hybrid with EVO_RAG_DB pointing at
# the uploaded index — and adds HF_TOKEN and EVO_RAG_TOKEN. Defaulting the
# other way round would mean a misconfiguration serves the books.
ENV EVO_RAG_MODE=public_lexical \
    EVO_RAG_DB=/app/data/rag/public.db

COPY requirements-deploy.txt requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY --chown=user . .
USER user

EXPOSE 7860
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
