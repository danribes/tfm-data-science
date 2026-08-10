# The public API, slimmed: engine + committed research artifacts + reports.
# No torch, no vector index — the RAG corpus is copyrighted and never leaves
# the local machine; its routes answer 503 with that explanation.
FROM python:3.12-slim

# HF Spaces runs containers as uid 1000 and serves on port 7860.
RUN useradd -m -u 1000 user
WORKDIR /app

COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

COPY --chown=user . .
USER user

EXPOSE 7860
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
