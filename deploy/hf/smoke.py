"""Check an assembled Space in an environment containing only deploy requirements.

    /path/to/slim-venv/bin/python deploy/hf/smoke.py /path/to/fresh-stage

No provider keys, private corpus, embedding models or network calls are needed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    stage = parser.parse_args().stage.resolve(strict=True)
    assert (stage / "data/rag/public.db").is_file(), "Missing assembled public index"
    assert not (stage / ".env").exists(), "A deployment must not include local secrets"
    # sqlite_vec is deliberately absent from this list: 0,2 MB of C extension
    # that reads vectors is what lets the deployment answer by dense retrieval
    # under remote_hybrid. What must stay out is everything that *creates*
    # them — that is the weight, and the private corpus with it.
    for package in ("torch", "sentence_transformers", "pymupdf"):
        assert importlib.util.find_spec(package) is None, f"Use a slim environment: {package} is installed"

    os.environ.update({
        "EVO_RAG_MODE": "public_lexical",
        "EVO_RAG_DB": str(stage / "data/rag/public.db"),
        "EVO_RAG_DATA": str(stage / "absent-private-corpus"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    })
    for key in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GLM_API_KEY", "KIMI_API_KEY", "OPENAI_API_KEY"):
        os.environ.pop(key, None)
    sys.path.insert(0, str(stage))
    from api import main as api_main
    from fastapi.testclient import TestClient

    assert Path(api_main.__file__).resolve().is_relative_to(stage), "Imported the working tree instead of the stage"
    checked = []
    with TestClient(api_main.app) as client:
        def check(method: str, path: str, body: dict | None = None, expected: int = 200):
            kwargs = {"json": body} if body is not None else {}
            response = client.request(method, path, **kwargs)
            assert response.status_code == expected, f"{method} {path}: {response.status_code} {response.text[:500]}"
            checked.append({"method": method, "path": path, "status": response.status_code})
            return response

        for path in ("/health", "/vintage", "/constants", "/personas", "/presets", "/redlines",
                     "/evidence", "/prediction", "/distress", "/state-dependence", "/regimes",
                     "/demography", "/scenario/sensitivity", "/scenario/report"):
            response = check("GET", path)
            if path in {"/prediction", "/distress", "/state-dependence", "/regimes"}:
                assert response.json()["available"], f"Missing packaged report: {path}"

        collections = check("GET", "/rag/collections").json()
        assert collections["corpus_scope"] == "public_project_docs"
        assert collections["retrieval_mode"] == "lexical"
        assert collections["default_collection"] == "metodo"
        assert collections["total_documents"] == 6
        assert {c["id"] for c in collections["collections"]} == {"metodo", "defensa_tfm"}
        assert check("GET", "/rag/eval").json()["available"] is False

        check("POST", "/scenario", {"levers": {}, "horizon": 2036})
        check("POST", "/scenario/montecarlo", {"levers": {}, "horizon": 2036, "n_paths": 100})
        check("POST", "/scenario/analog", {"levers": {}, "horizon": 2036})
        check("POST", "/explain", {"levers": {}, "horizon": 2036, "narrate": False})
        search = check("POST", "/rag/search", {"query": "deuda nominal"}).json()
        assert search["collection"] == "metodo" and search["passages"]
        assert all(p["authority"] == "propio" for p in search["passages"])
        defence = check("POST", "/rag/search", {"query": "defensa", "collection": "defensa_tfm"}).json()
        assert defence["passages"]
        assert all(p["collection"] == "defensa_tfm" for p in defence["passages"])
        answer = check("POST", "/rag/chat", {"question": "deuda nominal"}).json()
        assert answer["passages"] and answer["provider"] is None and answer["model"] is None
        stream = check("POST", "/rag/chat/stream", {"question": "deuda nominal"})
        assert "event: passages" in stream.text and "event: done" in stream.text
        for path, field in (("/rag/search", "query"), ("/rag/chat", "question"), ("/rag/chat/stream", "question")):
            check("POST", path, {field: "deuda", "collection": "libros"}, expected=422)
        cors = client.options("/rag/search", headers={
            "Origin": "https://danribes.github.io", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert cors.headers.get("access-control-allow-origin") == "https://danribes.github.io"

    assert not {"rag.embed", "torch", "sentence_transformers", "sqlite_vec"} & sys.modules.keys()
    assert not (stage / "absent-private-corpus").exists()
    print(json.dumps({"checks": checked, "documents": collections["total_documents"],
                      "chunks": collections["total_chunks"], "mode": "public_lexical"}, indent=2))


if __name__ == "__main__":
    main()
