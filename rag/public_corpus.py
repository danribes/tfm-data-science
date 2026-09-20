"""Build the public project-documentation FTS index using only the standard library.

    python -m rag.public_corpus --source-root ORIGINAL_REPO --out DEST/public.db

This never reads the private corpus or its manifest. Only the six explicit
project-authored Markdown paths below are eligible; no recursive source scan,
symlink traversal, embedding, or network request occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile

from rag import extract


MANIFEST = Path(__file__).with_name("public_sources.json")
ALLOWED_SOURCES = {
    "README.md": "metodo",
    "docs/MEMORIA_TFM.md": "metodo",
    "docs/RESULTS.md": "metodo",
    "docs/METHODOLOGY_CHANGES.md": "metodo",
    "docs/REPRODUCIBILITY.md": "metodo",
    "docs/DEFENSA_TFM.md": "defensa_tfm",
}


def source_manifest() -> list[dict]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = payload["sources"]
    if (payload.get("schema_version") != 1
            or payload.get("corpus_scope") != "public_project_docs"
            or len(sources) != len(ALLOWED_SOURCES)
            or {s["path"]: s["collection"] for s in sources} != ALLOWED_SOURCES):
        raise ValueError("El manifiesto debe contener exactamente las fuentes públicas aprobadas")
    return sources


def _source_path(root: Path, relative: str) -> Path:
    rel = PurePosixPath(relative)
    if (relative not in ALLOWED_SOURCES or rel.is_absolute()
            or ".." in rel.parts or "\\" in relative):
        raise ValueError(f"Fuente fuera de la lista pública: {relative}")
    path = root
    for part in rel.parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"No se admiten enlaces simbólicos: {relative}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"Fuente fuera de la raíz del proyecto: {relative}")
    return resolved


def build(source_root: Path, out: Path) -> dict:
    """Build to a temporary file, then atomically publish a complete public DB."""
    original_root = Path(source_root).absolute()
    # Reject symlinks in the root itself and in its parents, too.
    if any(p.is_symlink() for p in (original_root, *original_root.parents)):
        raise ValueError("La raíz de fuentes no puede atravesar enlaces simbólicos")
    root = original_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("La raíz de fuentes debe ser un directorio")
    sources = source_manifest()
    prepared = []
    for source in sources:
        path = _source_path(root, source["path"])
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        # One synthetic page drives the chunker; it is not stored as a real
        # page number. Markdown citations use section headings as locators.
        chunks = list(extract.chunk_pages(iter([(1, text)])))
        if not chunks:
            raise ValueError(f"La fuente no contiene texto indexable: {source['path']}")
        prepared.append((source, hashlib.sha256(raw).hexdigest(), chunks))

    target = Path(out).absolute()
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("El destino no puede atravesar enlaces simbólicos")
    if target.resolve() in {_source_path(root, s["path"]) for s in sources}:
        raise ValueError("El destino no puede reemplazar una fuente")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    temporary = Path(temp_name)
    con = None
    try:
        con = sqlite3.connect(temporary)
        con.executescript("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY, collection TEXT NOT NULL,
                title TEXT NOT NULL, source_path TEXT NOT NULL,
                sha256 TEXT NOT NULL UNIQUE, pages INTEGER, meta TEXT,
                ingested_at TEXT
            );
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY,
                doc_id INTEGER NOT NULL REFERENCES documents(id),
                ordinal INTEGER NOT NULL, page INTEGER, section TEXT,
                text TEXT NOT NULL
            );
            CREATE INDEX idx_chunks_doc ON chunks(doc_id);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                text, content='chunks', content_rowid='id', tokenize='unicode61'
            );
            CREATE TABLE public_corpus_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        total_chunks = 0
        summary_sources = []
        for source, digest, chunks in prepared:
            meta = {"authority": "propio", "document_status": "current",
                    "corpus_scope": "public_project_docs"}
            cursor = con.execute(
                "INSERT INTO documents(collection,title,source_path,sha256,pages,meta) VALUES(?,?,?,?,?,?)",
                (source["collection"], source["title"], source["path"], digest, None,
                 json.dumps(meta, sort_keys=True, ensure_ascii=False)),
            )
            doc_id = cursor.lastrowid
            for chunk in chunks:
                cursor = con.execute(
                    "INSERT INTO chunks(doc_id,ordinal,page,section,text) VALUES(?,?,?,?,?)",
                    (doc_id, chunk["ordinal"], None, chunk["section"], chunk["text"]),
                )
                con.execute("INSERT INTO chunks_fts(rowid,text) VALUES(?,?)",
                            (cursor.lastrowid, chunk["text"]))
            total_chunks += len(chunks)
            summary_sources.append({**source, "sha256": digest, "chunks": len(chunks)})
        metadata = {"schema_version": "1", "corpus_scope": "public_project_docs",
                    "retrieval_mode": "lexical",
                    "sources": json.dumps(summary_sources, sort_keys=True, ensure_ascii=False)}
        con.executemany("INSERT INTO public_corpus_meta(key,value) VALUES(?,?)", sorted(metadata.items()))
        con.commit()
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("El índice público no supera la comprobación de integridad")
        con.close()
        con = None
        os.replace(temporary, target)
    finally:
        if con is not None:
            con.close()
        temporary.unlink(missing_ok=True)
    return {"corpus_scope": "public_project_docs", "retrieval_mode": "lexical",
            "documents": len(prepared), "chunks": total_chunks,
            "sources": summary_sources}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source_root, args.out), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
