"""RAG configuration — every knob that affects memory sits here.

Defaults are chosen for a 6 GB laptop GPU inside a 12 GB WSL VM, not for a
workstation. The ingest is streaming and resumable by design: nothing here ever
holds a whole book, let alone the whole corpus, in RAM.
"""
from __future__ import annotations

import os
from pathlib import Path

# The public deployment is a deliberately smaller corpus and uses lexical
# retrieval. Never infer this mode from missing dependencies or model errors.
MODE = os.environ.get("EVO_RAG_MODE", "hybrid")
if MODE not in {"hybrid", "public_lexical"}:
    raise ValueError(f"EVO_RAG_MODE desconocido: {MODE!r}")
PUBLIC_MODE = MODE == "public_lexical"
RETRIEVAL_MODE = "lexical" if PUBLIC_MODE else "hybrid"
CORPUS_SCOPE = "public_project_docs" if PUBLIC_MODE else "private_local"
DEFAULT_COLLECTION = "metodo" if PUBLIC_MODE else "libros"

# ---- corpora ----------------------------------------------------------------

DATA_ROOT = Path(os.environ.get(
    "EVO_RAG_DATA", Path(__file__).resolve().parents[1].with_name("evo_final_work_data")))

BOOKS_DIR = DATA_ROOT / "econ_pdfs"
BOOKS_MANIFEST = BOOKS_DIR / "CORPUS_MANIFEST.csv"
CRACK_DIR = DATA_ROOT / "crack23"

#: Collections are kept strictly apart at retrieval time. A textbook passage and
#: a YouTube transcript must never compete in the same ranked list — citing a
#: channel with the same authority as Mankiw would discredit the whole answer.
COLLECTIONS = {
    "libros": {
        "label": "Economía y métodos",
        "authority": "academico",
        "note": "Documentos e índice almacenados localmente; los pasajes recuperados se envían al proveedor de IA configurado para redactar respuestas.",
    },
    "metodo": {
        "label": "Método y diseño del propio modelo",
        "authority": "propio",
        "note": "Specs, Metodología y Cómo funciona de esta app.",
    },
    "defensa_tfm": {
        "label": "Defensa del TFM (Pregúntale al TFM)",
        "authority": "defensa",
        "note": "Defensa metodológica: derivaciones de las 10 palancas, Okun, Phillips, Monte Carlo y calibración.",
    },
    "crack23": {
        "label": "Canal crack23",
        "authority": "opinion",
        "note": "Transcripciones y resúmenes. Es opinión, no fuente académica.",
    },
}

if PUBLIC_MODE:
    COLLECTIONS = {
        "metodo": {
            "label": "Método y resultados del proyecto",
            "authority": "propio",
            "note": "Documentación pública de este proyecto. Búsqueda por palabras (BM25), sin embeddings; los pasajes pueden enviarse al proveedor de IA para redactar la respuesta.",
        },
        "defensa_tfm": {
            "label": "Defensa del TFM",
            "authority": "propio",
            "note": "Guía de defensa escrita para este proyecto; no es una fuente académica independiente. Búsqueda por palabras (BM25).",
        },
    }

# ---- store ------------------------------------------------------------------

_DEFAULT_DB = (Path(__file__).resolve().parents[1] / "data/rag/public.db"
               if PUBLIC_MODE else DATA_ROOT / "rag" / "corpus.db")
DB_PATH = Path(os.environ.get("EVO_RAG_DB", _DEFAULT_DB))

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
#: Historical development observation: the initial bilingual corpus was
#: dominated by Mises among Spanish sources and textbooks among English ones.
#: In that snapshot the `-base` variant ranked passages strongly by language:
#: "qué es el multiplicador fiscal" reached Mises on taxation, whereas the
#: English query reached Mankiw ch. 34. This motivated the `-large` model.
#: The corpus has since gained Spanish institutional sources and methods
#: references; these comments are not current language shares or held-out
#: evidence. Re-evaluate against a frozen corpus before changing the model.
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

#: Fusion weights retain the historical development configuration. On the
#: initial bilingual snapshot, unweighted fusion over-ranked Spanish Mises
#: passages for Spanish queries; dense retrieval received greater weight to
#: improve cross-language retrieval. Later corpus additions change the mix.
#: These observations do not establish present-day performance; lexical search
#: still contributes exact terminology ("Okun", "prima de riesgo").
W_DENSE = float(os.environ.get("EVO_RAG_W_DENSE", "6.0"))
W_LEXICAL = float(os.environ.get("EVO_RAG_W_LEXICAL", "1.0"))

#: Weight of the English-only dense probe (see rag/glossary.py), set by sweep
#: on the development/golden set. Its reported scores are NOT held-out results.
#:
#: 0 is the old behaviour: hit@8 94 %, MRR 0,69. It climbs to 97 % / 0,76 at 4
#: and then flattens, so 4 is the first value on the plateau rather than the
#: largest that scores well. The choice between 3 (MRR 0,77, top1 69 %) and 4
#: (0,76 / 66 %) is a real trade — 3 ranks better, 4 finds more. Recall wins:
#: a passage that never surfaces cannot be cited, while one at rank 3 still
#: reaches the answer.
W_DENSE_EN = float(os.environ.get("EVO_RAG_W_DENSE_EN", "4.0"))
USE_GLOSSARY = os.environ.get("EVO_RAG_GLOSSARY", "1") == "1"

#: No single book may take more than this many of the returned passages. Without
#: it one 1.100-chunk volume can fill the whole answer and the citation list
#: looks like a single-source essay.
#:
#: Tightened from 3 to 2 on measurement: it is worth 3 points of hit@8 (91 % to
#: 94 %) on its own. The reason is the same hub effect the model shows
#: elsewhere — a handful of documents sit close to every query, and at a cap of
#: 3 two of them can take six of the eight slots before an on-topic passage is
#: reached. This is a retrieval fix that happens to also be a citation-quality
#: fix, which is unusual enough to be worth stating.
MAX_PER_DOCUMENT = int(os.environ.get("EVO_RAG_MAX_PER_DOC", "2"))

#: Centring the dense vectors on the collection mean was tried and rejected.
#:
#: The hypothesis was good: the chunk embeddings are unit vectors whose mean has
#: norm 0,90, so nearly the whole space points one way, and cosine scores that
#: shared direction as much as the topic. Subtracting the mean is the standard
#: correction. Measured on the golden set it made dense retrieval *worse* —
#: MRR 0,63 to 0,55 — and left the fused result unchanged. Written down so the
#: next person reads the result instead of re-deriving the idea.


def resolve_device() -> str:
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

# ---- who may read which collection -------------------------------------------

#: Collections holding third-party copyrighted text. Reachable only with the
#: reviewer token, never by default.
RESTRICTED_COLLECTIONS = frozenset({"libros", "crack23"})

#: Shared secret that unlocks them, from EVO_RAG_TOKEN. Empty means locked:
#: an unset token can never accidentally publish the books, which is the
#: failure mode worth designing against.
REVIEWER_TOKEN = os.environ.get("EVO_RAG_TOKEN", "").strip()


def is_restricted(collection: str) -> bool:
    return collection in RESTRICTED_COLLECTIONS


def token_ok(supplied: str | None) -> bool:
    """Constant-time-ish comparison; a wrong length is already a mismatch."""
    if not REVIEWER_TOKEN or not supplied:
        return False
    supplied = supplied.strip()
    if len(supplied) != len(REVIEWER_TOKEN):
        return False
    diff = 0
    for a, b in zip(supplied, REVIEWER_TOKEN):
        diff |= ord(a) ^ ord(b)
    return diff == 0


def readable(collection: str, token: str | None) -> bool:
    """A collection is readable when it is not restricted, or the token matches."""
    return not is_restricted(collection) or token_ok(token)
