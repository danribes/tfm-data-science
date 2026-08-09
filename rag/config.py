"""RAG configuration — every knob that affects memory sits here.

Defaults are chosen for a 6 GB laptop GPU inside a 12 GB WSL VM, not for a
workstation. The ingest is streaming and resumable by design: nothing here ever
holds a whole book, let alone the whole corpus, in RAM.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---- corpora ----------------------------------------------------------------

DATA_ROOT = Path(os.environ.get(
    "EVO_RAG_DATA", "/home/dan/projects/evo_final_work_data"))

BOOKS_DIR = DATA_ROOT / "econ_pdfs"
BOOKS_MANIFEST = BOOKS_DIR / "CORPUS_MANIFEST.csv"
CRACK_DIR = DATA_ROOT / "crack23"

#: Collections are kept strictly apart at retrieval time. A textbook passage and
#: a YouTube transcript must never compete in the same ranked list — citing a
#: channel with the same authority as Mankiw would discredit the whole answer.
COLLECTIONS = {
    "libros": {
        "label": "Manuales de economía",
        "authority": "academico",
        "note": "Textos con copyright — nunca salen de la máquina local.",
    },
    "metodo": {
        "label": "Método y diseño del propio modelo",
        "authority": "propio",
        "note": "Specs, Metodología y Cómo funciona de esta app.",
    },
    "crack23": {
        "label": "Canal crack23",
        "authority": "opinion",
        "note": "Transcripciones y resúmenes. Es opinión, no fuente académica.",
    },
}

# ---- store ------------------------------------------------------------------

DB_PATH = Path(os.environ.get("EVO_RAG_DB", DATA_ROOT / "rag" / "corpus.db"))

# ---- chunking ---------------------------------------------------------------

CHUNK_TOKENS = int(os.environ.get("EVO_RAG_CHUNK", "800"))
CHUNK_OVERLAP = int(os.environ.get("EVO_RAG_OVERLAP", "120"))
#: Rough tokens-per-character for the ES/EN mix. Used only to size chunks; the
#: embedder truncates properly at its own limit.
CHARS_PER_TOKEN = 4
MIN_CHUNK_CHARS = 200      # below this a chunk is noise (page numbers, headers)
MAX_CHUNK_CHARS = CHUNK_TOKENS * CHARS_PER_TOKEN * 2  # hard ceiling, safety

# ---- embedding --------------------------------------------------------------

#: multilingual-e5-large: 560M params, 1024 dims, ~1,1 GB in fp16.
#:
#: The size is load-bearing, not a default nobody thought about. This corpus is
#: bilingual and lopsided — every Spanish-language book is Mises (39 % of
#: `libros`), the textbooks are English — so a question asked in Spanish only
#: reaches Mankiw if the embedder genuinely bridges ES↔EN. The `-base` variant
#: does not: measured on this corpus it ranked passages by language rather than
#: by topic, sending "qué es el multiplicador fiscal" to Mises on taxation while
#: the identical English query correctly returned Mankiw ch. 34. Pure-dense
#: retrieval showed the same failure, which ruled out the fusion weights and
#: indicted the model.
#:
#: bge-m3 would be the other natural choice and is NOT usable here: it ships its
#: pooling layers as `.pt` files, and transformers refuses torch.load on
#: torch < 2.6 (CVE-2025-32434). Switching to it means upgrading torch first.
MODEL_NAME = os.environ.get("EVO_RAG_MODEL", "intfloat/multilingual-e5-large")
EMBED_DIM = int(os.environ.get("EVO_RAG_DIM", "1024"))

#: Small on purpose. Each doubling roughly doubles peak VRAM; 8 leaves headroom
#: for the OS compositor and the browser on a 6 GB card.
BATCH_SIZE = int(os.environ.get("EVO_RAG_BATCH", "8"))
USE_FP16 = os.environ.get("EVO_RAG_FP16", "1") == "1"
DEVICE = os.environ.get("EVO_RAG_DEVICE", "auto")   # auto | cuda | cpu

#: e5 models require these prefixes; using the wrong one silently degrades
#: retrieval quality without any error.
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "

# ---- retrieval --------------------------------------------------------------

TOP_K = int(os.environ.get("EVO_RAG_TOPK", "8"))
CANDIDATES = int(os.environ.get("EVO_RAG_CANDIDATES", "40"))  # per retriever
RRF_K = 60          # reciprocal-rank-fusion constant, standard value
MIN_SCORE = float(os.environ.get("EVO_RAG_MIN_SCORE", "0.0"))

#: Fusion weights. Dense outranks lexical deliberately: this corpus is bilingual
#: and lopsided — the Spanish-language books are all Mises (39 % of `libros`),
#: while the textbooks are English. BM25 cannot cross languages, so an unweighted
#: fusion sends every Spanish question to Mises regardless of topic. The
#: embedder does bridge ES↔EN, so it gets the larger say; BM25 still earns its
#: place on exact terminology ("Okun", "prima de riesgo").
W_DENSE = float(os.environ.get("EVO_RAG_W_DENSE", "1.6"))
W_LEXICAL = float(os.environ.get("EVO_RAG_W_LEXICAL", "1.0"))

#: No single book may take more than this many of the returned passages. Without
#: it one 1.100-chunk volume can fill the whole answer and the citation list
#: looks like a single-source essay.
MAX_PER_DOCUMENT = int(os.environ.get("EVO_RAG_MAX_PER_DOC", "3"))


def resolve_device() -> str:
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"
