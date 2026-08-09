"""Embedding with explicit memory discipline.

The failure mode this guards against is real: a 6 GB laptop GPU shared with the
desktop compositor, inside a 12 GB WSL VM. A CUDA OOM here does not just fail
the batch — it can take the whole session down.

So: the model loads once and is reused; batches are small; an OOM halves the
batch and retries rather than propagating; and if the GPU refuses entirely the
encoder falls back to CPU and keeps going. Slower is always better than dead.
"""
from __future__ import annotations

import gc
import threading
from typing import Sequence

from rag import config

_model = None
_lock = threading.Lock()


def _free_cuda() -> None:
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def get_model():
    """Load once, reuse. Thread-safe because the API may call it concurrently."""
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer

        device = config.resolve_device()
        model = SentenceTransformer(config.MODEL_NAME, device=device)
        if device == "cuda" and config.USE_FP16:
            model = model.half()   # halves weights and activations
        model.max_seq_length = min(model.max_seq_length, 512)
        _model = model
        return _model


def unload() -> None:
    """Drop the model and reclaim VRAM — call between heavy phases."""
    global _model
    _model = None
    _free_cuda()


def _encode(texts: Sequence[str], batch_size: int) -> list[list[float]]:
    model = get_model()
    out = model.encode(
        list(texts),
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,   # cosine == dot product downstream
        show_progress_bar=False,
    )
    return [row.tolist() for row in out]


def embed_passages(texts: Sequence[str],
                   batch_size: int | None = None) -> list[list[float]]:
    """Embed chunk text, halving the batch on OOM instead of crashing."""
    if not texts:
        return []
    prefixed = [config.PASSAGE_PREFIX + t for t in texts]
    bs = batch_size or config.BATCH_SIZE

    while bs >= 1:
        try:
            return _encode(prefixed, bs)
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower():
                raise
            _free_cuda()
            if bs == 1:
                break
            bs = max(1, bs // 2)
            print(f"    [embed] CUDA OOM → reintentando con batch={bs}")

    # Last resort: the GPU cannot hold even one sequence. Finish on CPU rather
    # than lose the ingest.
    print("    [embed] GPU agotada → cayendo a CPU para este lote")
    unload()
    prev, config.DEVICE = config.DEVICE, "cpu"
    try:
        return _encode(prefixed, 4)
    finally:
        config.DEVICE = prev
        unload()


def embed_query(text: str) -> list[float]:
    return _encode([config.QUERY_PREFIX + text], 1)[0]
