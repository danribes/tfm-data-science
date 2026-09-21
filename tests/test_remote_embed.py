"""The hosted-encoder path, exercised without a network.

Creating embeddings needs the model; querying them needs a vector and
sqlite-vec. This is what lets a deployment without torch still answer by dense
retrieval, and it is the difference between evaluators querying the system the
evaluation measured and querying BM25 alone.

Everything here is tested against a stubbed transport. The HTTP call itself is
verified against the deployment, because no token exists in this environment —
so what is pinned here is every decision made around that call: the prefix, the
dimension check, and above all that a failure degrades instead of raising.
"""
from __future__ import annotations

import hashlib
import json
import io
import urllib.error

import pytest

from rag import config, embed


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _ok(vector):
    return lambda req, timeout=None: _Response(json.dumps(vector).encode())


@pytest.fixture
def remote(monkeypatch):
    monkeypatch.setattr(config, "REMOTE_EMBED", True)
    monkeypatch.setattr(config, "REMOTE_EMBED_TOKEN", "hf_test")


def _fake_vector(text: str, dim: int = config.EMBED_DIM) -> list[float]:
    """Deterministic unit-norm pseudo-embedding, as in test_rag."""
    h = hashlib.sha256(text.encode()).digest()
    raw = [(h[i % len(h)] - 128) / 128.0 for i in range(dim)]
    norm = sum(v * v for v in raw) ** 0.5 or 1.0
    return [v / norm for v in raw]


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A small real index — an FTS5 table and a vec0 table — built here.

    The first version of the two tests below read the corpus at config.DB_PATH.
    That passed on the machine that has the books and failed in CI, which is
    exactly backwards: the private corpus is data that exists in one place, not
    a fixture. What these tests are actually about is the plumbing — that a
    dead encoder still returns BM25 hits, and that a supplied vector reaches
    vec0 — and three sentences exercise that as well as twenty-one thousand.
    """
    from rag import store

    path = tmp_path / "corpus.db"
    monkeypatch.setattr(config, "DB_PATH", path)
    con = store.connect(path)
    store.init_schema(con)
    texts = [
        "La curva de Phillips relaciona la inflación con la brecha de desempleo.",
        "Las expectativas adaptativas forman la previsión a partir del error pasado.",
        "La deuda pública crece cuando el tipo de interés supera al crecimiento.",
    ]
    doc = store.add_document(con, collection="libros", title="Manual de prueba",
                             source_path="/x/sha-remote", sha256="sha-remote", pages=1)
    store.add_chunks(
        con, doc,
        [{"ordinal": i, "page": 1, "section": "Cap. 1", "text": t}
         for i, t in enumerate(texts)],
        [_fake_vector(t) for t in texts])
    con.commit()
    con.close()
    return path


def test_query_carries_the_asymmetric_prefix(remote, monkeypatch):
    """e5 stored passages with «passage: »; a query without «query: » is a
    different kind of vector and retrieves quietly worse."""
    seen = {}

    def capture(req, timeout=None):
        seen["body"] = json.loads(req.data)
        return _Response(json.dumps([[0.1] * config.EMBED_DIM]).encode())

    monkeypatch.setattr("urllib.request.urlopen", capture)
    embed.embed_query("¿qué es la curva de Phillips?")
    assert seen["body"]["inputs"].startswith(config.QUERY_PREFIX)


def test_accepts_both_shapes_the_endpoint_returns(remote, monkeypatch):
    """Feature extraction answers either a vector or a batch of one."""
    for payload in ([[0.2] * config.EMBED_DIM], [0.2] * config.EMBED_DIM):
        monkeypatch.setattr("urllib.request.urlopen", _ok(payload))
        assert len(embed.embed_query("hola")) == config.EMBED_DIM


def test_a_wrong_dimension_is_refused(remote, monkeypatch):
    """A different model would answer confidently with the wrong geometry, and
    its vectors would score as noise against the stored ones."""
    monkeypatch.setattr("urllib.request.urlopen", _ok([[0.1] * 384]))
    with pytest.raises(embed.RemoteEmbedUnavailable):
        embed.embed_query("hola")


def test_a_missing_token_is_refused_before_any_request(remote, monkeypatch):
    monkeypatch.setattr(config, "REMOTE_EMBED_TOKEN", "")
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **k: pytest.fail("must not call out"))
    with pytest.raises(embed.RemoteEmbedUnavailable):
        embed.embed_query("hola")


def test_network_failure_raises_the_typed_error(remote, monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.URLError("sin red")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(embed.RemoteEmbedUnavailable):
        embed.embed_query("hola")


def test_search_degrades_to_lexical_when_the_encoder_is_down(corpus, monkeypatch):
    """The whole point of the fallback: a timeout at the encoder must cost
    quality, not availability. A corpus that errors is worse than one that
    answers by BM25 and says so."""
    from rag import retrieve

    def boom(*a, **k):
        raise embed.RemoteEmbedUnavailable("simulado")

    monkeypatch.setattr("rag.embed.embed_query", boom)
    hits = retrieve.search("curva de Phillips", "libros", top_k=3)
    assert hits, "lexical retrieval must still answer"


def test_dense_runs_against_a_real_index_with_a_supplied_vector(corpus, monkeypatch):
    """Everything but the HTTP call, against a real index.

    A stub vector cannot retrieve meaningfully, so this asserts the plumbing —
    packing, the vec0 match and the collection filter — not the ranking.
    """
    from rag import retrieve, store

    monkeypatch.setattr("rag.embed.embed_query",
                        lambda _t: [0.01] * config.EMBED_DIM)
    con = store.connect()
    try:
        ids = retrieve._dense(con, "cualquier cosa", "libros", 5)
    finally:
        con.close()
    assert isinstance(ids, list)


def test_el_endpoint_por_defecto_no_es_el_host_retirado():
    """`api-inference.huggingface.co` dejó de resolver en DNS.

    Esto no falló como un error de API que alguien fuese a ver: la resolución
    del nombre moría, `urlopen` lanzaba URLError, el sondeo denso lo capturaba
    y la recuperación quedaba degradada a BM25 de forma permanente mientras la
    respuesta seguía anunciando `retrieval_mode: hybrid`. El despliegue estuvo
    así sin que ninguna prueba ni ninguna comprobación en vivo lo notara.

    Una prueba sin red no puede detectar que un nombre deje de resolver mañana,
    pero sí puede impedir que el valor por defecto vuelva al host retirado.
    """
    assert "api-inference.huggingface.co" not in config.REMOTE_EMBED_URL
    assert config.REMOTE_EMBED_URL.startswith("https://router.huggingface.co/hf-inference/models/")
    # El sufijo importa: sin él el router responde, pero la variante
    # /hf-inference/pipeline/feature-extraction/<modelo> devuelve 400
    # "Model not supported by provider hf-inference".
    assert config.REMOTE_EMBED_URL.endswith("/pipeline/feature-extraction")
    assert config.MODEL_NAME in config.REMOTE_EMBED_URL


# --- que la respuesta diga con qué recuperador se respondió ------------------
#
# El campo `retrieval_mode` era el valor estático de la configuración: decía
# "hybrid" mientras el codificador remoto estaba caído y todo salía por BM25.
# Estas pruebas fijan que ahora informa del hecho, no de la intención.

def test_reporta_hibrido_cuando_el_codificador_responde(corpus, monkeypatch):
    from rag import retrieve
    monkeypatch.setattr(retrieve, "_dense",
                        lambda con, q, c, n, text=None: [1])
    res = retrieve.search_reported("deuda", "libros", 3)
    assert res.degraded is False
    assert res.mode == "hybrid"


def test_reporta_degradado_cuando_el_codificador_cae(corpus, monkeypatch):
    from rag import retrieve

    def muerto(*a, **k):
        raise RuntimeError("sin codificador")

    monkeypatch.setattr(retrieve, "_dense", muerto)
    res = retrieve.search_reported("deuda", "libros", 3)
    assert res.degraded is True
    assert res.mode == "lexical_degraded"
    # Los pasajes siguen siendo válidos: degradado no es vacío.
    assert res.passages


def test_una_consulta_no_contagia_su_degradacion_a_la_siguiente(corpus, monkeypatch):
    """El aviso vive en una variable de contexto, no en un global. Con un
    booleano de módulo, la primera caída del codificador marcaría degradadas
    todas las consultas posteriores del proceso.

    Antes había además una prueba de que el aviso sobrevivía al abanico de la
    colección `mixto`, que anidaba una búsqueda por miembro. Esa vista se
    retiró al dejar de citarse los documentos propios, así que la prueba se
    quitó en vez de reescribirla contra algo que ya no existe. La propiedad que
    de verdad sostiene la elección —aislar consultas concurrentes— es la que
    comprueba ésta.
    """
    from rag import retrieve

    def muerto(*a, **k):
        raise RuntimeError("sin codificador")

    monkeypatch.setattr(retrieve, "_dense", muerto)
    assert retrieve.search_reported("deuda", "libros", 3).degraded is True

    monkeypatch.setattr(retrieve, "_dense",
                        lambda con, q, c, n, text=None: [1])
    assert retrieve.search_reported("deuda", "libros", 3).degraded is False


def test_search_sigue_devolviendo_una_lista(corpus, monkeypatch):
    """Una decena de sitios dependen de ello; el aviso viaja aparte."""
    from rag import retrieve
    monkeypatch.setattr(retrieve, "_dense",
                        lambda con, q, c, n, text=None: [1])
    hits = retrieve.search("deuda", "libros", 3)
    assert isinstance(hits, list)
