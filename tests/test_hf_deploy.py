"""The Space assembly must not carry private or stale artifacts into uploads."""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from rag.public_corpus import ALLOWED_SOURCES


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLE = ROOT / "deploy/hf/assemble.sh"


def assemble(destination: Path) -> subprocess.CompletedProcess:
    # The script invokes `python`; use the test environment's interpreter.
    env = {**os.environ, "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]}
    return subprocess.run(
        ["bash", str(ASSEMBLE), str(destination)], cwd=ROOT, env=env,
        text=True, capture_output=True, timeout=60,
    )


def test_assembly_rejects_populated_stage_without_deleting_private_report(tmp_path):
    stage = tmp_path / "stage"
    report = stage / "docs/eval/private-report.json"
    report.parent.mkdir(parents=True)
    before = b'{"passage":"PRIVATE-CANARY"}'
    report.write_bytes(before)

    result = assemble(stage)

    assert result.returncode != 0
    assert "nuevo o vacío" in result.stderr
    assert report.read_bytes() == before
    assert {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()} == {
        "docs/eval/private-report.json",
    }


@pytest.mark.parametrize("existing_empty", [False, True])
def test_fresh_assembly_contains_only_public_corpus_and_allowlisted_reports(tmp_path, existing_empty):
    stage = tmp_path / "stage"
    if existing_empty:
        stage.mkdir()

    result = assemble(stage)

    assert result.returncode == 0, result.stderr
    # Igualdad exacta a propósito: es la red que atraparía a quien recorra
    # docs/eval con glob y acabe publicando pasajes de los libros. Los dos
    # informes del RAG se añadieron tras comprobar que sólo llevan títulos,
    # métricas y frases de las respuestas del propio modelo.
    assert {p.name for p in (stage / "docs/eval").iterdir()} == {
        "t1-dl-global.json", "distress.json", "state_dependence.json", "regimes.json",
        "rag-eval-2026-08-09.json", "rag-chat-eval.json",
    }
    assert {p.name for p in (stage / "data/rag").iterdir()} == {"public.db"}
    with sqlite3.connect(stage / "data/rag/public.db") as con:
        sources = dict(con.execute("SELECT source_path, collection FROM documents"))
        assert sources == ALLOWED_SOURCES
        assert con.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 6
        assert con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] > 0
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert con.execute("SELECT name FROM sqlite_master WHERE name='chunks_vec'").fetchone() is None
    assert not list(stage.rglob("*.pdf"))
    assert not (stage / "econ_pdfs").exists()
    assert (stage / "data/gold/VINTAGE").is_file()
    assert not (stage / "data/gold/gold").exists()
    assert not (stage / "data/external/external").exists()


def test_space_user_owns_the_working_directory():
    # El Space corre como uid 1000 y la API crea data_cache/ bajo el directorio
    # de trabajo. `COPY --chown` cambia el dueño de lo copiado, no el de /app,
    # que WORKDIR crea como root: sin un chown explícito, /countries devolvía
    # una lista vacía y /panel y /scenario/generic, un 500 por PermissionError.
    lines = [l.strip() for l in (ROOT / "deploy/hf/Dockerfile").read_text().splitlines()]
    workdir = next(l.split()[1] for l in lines if l.startswith("WORKDIR "))
    user_at = next(i for i, l in enumerate(lines) if l.startswith("USER "))
    user = lines[user_at].split()[1]
    assert any(
        l.startswith("RUN ") and "chown" in l and user in l and workdir in l.split()
        for l in lines[:user_at]
    ), f"falta un `RUN chown {user} {workdir}` antes de `USER {user}`"
