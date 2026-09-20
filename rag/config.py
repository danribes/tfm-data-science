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
if MODE not in {"hybrid", "public_lexical", "remote_hybrid"}:
    raise ValueError(f"EVO_RAG_MODE desconocido: {MODE!r}")

#: remote_hybrid: the full index with dense retrieval, on a host without torch.
#:
#: Creating the vectors needs the model; querying them needs only a vector and
#: sqlite-vec, which is 0,2 MB. So the deployment carries the index and asks a
#: hosted copy of the same model to encode the question. Without this the
#: deployed corpus answers by BM25 alone, which is a different retrieval system
#: from the one the evaluation measured — the distinction matters more than the
#: megabytes it saves.
REMOTE_EMBED = MODE == "remote_hybrid"
PUBLIC_MODE = MODE == "public_lexical"
RETRIEVAL_MODE = "lexical" if PUBLIC_MODE else "hybrid"
CORPUS_SCOPE = "public_project_docs" if PUBLIC_MODE else "private_local"
DEFAULT_COLLECTION = "metodo" if PUBLIC_MODE else "mixto"

#: Where a query is encoded when the model cannot be loaded locally. The model
#: must be the one that produced the stored vectors: a query embedded by any
#: other is scored against an incompatible space and returns plausible noise.
REMOTE_EMBED_URL = os.environ.get(
    "EVO_RAG_EMBED_URL",
    "https://api-inference.huggingface.co/pipeline/feature-extraction/"
    + os.environ.get("EVO_RAG_MODEL", "intfloat/multilingual-e5-large"))
REMOTE_EMBED_TOKEN = os.environ.get("HF_TOKEN", "").strip()
REMOTE_EMBED_TIMEOUT = float(os.environ.get("EVO_RAG_EMBED_TIMEOUT", "20"))

# ---- corpora ----------------------------------------------------------------

DATA_ROOT = Path(os.environ.get(
    "EVO_RAG_DATA", Path(__file__).resolve().parents[1].with_name("evo_final_work_data")))

BOOKS_DIR = DATA_ROOT / "econ_pdfs"
BOOKS_MANIFEST = BOOKS_DIR / "CORPUS_MANIFEST.csv"
CRACK_DIR = DATA_ROOT / "crack23"

#: Collections are kept strictly apart at retrieval time. A textbook passage and
#: a YouTube transcript must never compete in the same ranked list — citing a
#: channel with the same authority as Mankiw would discredit the whole answer.
#: Colecciones que pueden fundirse en una misma respuesta.
#:
#: La regla del módulo de recuperación es que un manual y una transcripción de
#: YouTube no se ordenen nunca en la misma lista. Eso no prohíbe mezclar: lo
#: que prohíbe es mezclar autoridades distintas. `libros` (académico), `metodo`
#: y `defensa_tfm` (propios) se citan con peso comparable; `crack23` (opinión)
#: se queda fuera por ese mismo motivo, y sigue consultable por separado.
MIXED_ID = "mixto"
MIXED_MEMBERS: tuple[str, ...] = ("libros", "metodo", "defensa_tfm")

COLLECTIONS = {
    MIXED_ID: {
        "label": "Manuales y método, juntos",
        "authority": "mixto",
        "note": "Funde los manuales de economía con la documentación propia del "
                "proyecto. Cada pasaje conserva su colección y su autoridad, de "
                "modo que la cita sigue diciendo de dónde sale.",
    },
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

#: Collections holding third-party copyrighted text. This is a fact about the
#: material, not a policy: it stays true whether or not the collections are
#: gated, and it is what lets the deployment describe itself honestly.
THIRD_PARTY_COLLECTIONS = frozenset({"libros", "crack23"})

#: Collections reachable only with the reviewer token.
#:
#: Vacío por decisión explícita del autor (2026-09-20): el corpus completo,
#: manuales de terceros incluidos, se sirve abierto. La maquinaria de abajo se
#: conserva intacta y volver a cerrarlo es reponer los nombres aquí y fijar
#: EVO_RAG_TOKEN en el despliegue — una línea, sin cambios en la API.
#:
#: Mientras esté vacío, `/rag/search` devuelve texto literal de obras con
#: derechos de autor a cualquiera que lo pida, sin credencial.
RESTRICTED_COLLECTIONS: frozenset[str] = frozenset()

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


def effective_scope(has_third_party: bool) -> str:
    """What the deployment actually holds, not what it was configured for.

    A public build serving a reviewer index still answers project questions
    openly, but it is no longer only project documents, and saying otherwise in
    the listing would be the app misdescribing itself.

    The argument is about the *material* present, not about who may read it.
    An earlier version keyed it on RESTRICTED_COLLECTIONS, so emptying that set
    to open the corpus made the branch unreachable and the deployment reported
    itself as `private_local` while serving copyrighted books to anyone — the
    precise failure this function exists to prevent.
    """
    if not has_third_party:
        return CORPUS_SCOPE
    if not RESTRICTED_COLLECTIONS:
        return "full_open"
    return "reviewer_restricted" if REVIEWER_TOKEN else "restricted_locked"


def readable(collection: str, token: str | None) -> bool:
    """A collection is readable when it is not restricted, or the token matches.

    The mix is readable only when every member is: otherwise it would be a
    side door into a gated collection.
    """
    if collection == MIXED_ID:
        return all(readable(m, token) for m in MIXED_MEMBERS)
    return not is_restricted(collection) or token_ok(token)
