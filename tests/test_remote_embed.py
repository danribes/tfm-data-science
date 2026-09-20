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


def test_search_degrades_to_lexical_when_the_encoder_is_down(monkeypatch):
    """The whole point of the fallback: a timeout at the encoder must cost
    quality, not availability. A corpus that errors is worse than one that
    answers by BM25 and says so."""
    from rag import retrieve

    def boom(*a, **k):
        raise embed.RemoteEmbedUnavailable("simulado")

    monkeypatch.setattr("rag.embed.embed_query", boom)
    hits = retrieve.search("curva de Phillips", "libros", top_k=3)
    assert hits, "lexical retrieval must still answer"


def test_dense_runs_against_the_real_index_with_a_supplied_vector(monkeypatch):
    """Everything but the HTTP call, against the actual corpus.

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
