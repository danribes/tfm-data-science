"""Text extraction and chunking. Streams page by page — never loads a book.

A 600-page textbook held whole in memory alongside a GPU model is how a 12 GB
WSL VM dies. Everything here is a generator: pages come out one at a time,
chunks are yielded as they close, and the caller writes them to SQLite before
asking for more.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterator

from rag import config


def sha256_file(path: Path, buf: int = 1 << 20) -> str:
    """Streaming hash — used as the resume key, so it must not read the file whole."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(buf):
            h.update(chunk)
    return h.hexdigest()


# ---- page text --------------------------------------------------------------

#: Running heads, page numbers and other furniture that repeats on every page
#: and would otherwise dominate the lexical index.
_NOISE = re.compile(
    r"^\s*(?:\d{1,4}|[ivxlcdm]{1,7}|Part\s+\w+|Chapter\s+\d+|CHAPTER\s+\d+)\s*$",
    re.IGNORECASE,
)
_WS = re.compile(r"[ \t ]+")
_MULTINL = re.compile(r"\n{3,}")


def clean_page(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        ln = _WS.sub(" ", ln).strip()
        if not ln or _NOISE.match(ln):
            continue
        lines.append(ln)
    return _MULTINL.sub("\n\n", "\n".join(lines)).strip()


def pdf_pages(path: Path) -> Iterator[tuple[int, str]]:
    """Yield (page_number, cleaned_text). Closes the document on exit."""
    import pymupdf

    doc = pymupdf.open(path)
    try:
        for i in range(doc.page_count):
            try:
                raw = doc.load_page(i).get_text("text")
            except Exception:
                continue  # a single unreadable page must not kill a 600-page book
            cleaned = clean_page(raw)
            if cleaned:
                yield i + 1, cleaned
    finally:
        doc.close()


def markdown_pages(path: Path) -> Iterator[tuple[int, str]]:
    """Markdown/text files: one synthetic 'page', already clean."""
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _MULTINL.sub("\n\n", text).strip()
    if text:
        yield 1, text


# ---- chunking ---------------------------------------------------------------

_HEADING = re.compile(
    r"^(?:#{1,6}\s+.+"                       # markdown heading
    r"|(?:CAP[IÍ]TULO|CHAPTER|PARTE|PART|SECCI[OÓ]N|SECTION)\s+[\dIVXLC]+.*"
    r"|\d{1,2}\.\d{1,2}\s+\S.*)$",           # 12.3 Numbered section
    re.IGNORECASE | re.MULTILINE,
)


def _heading_in(text: str) -> str | None:
    m = _HEADING.search(text)
    return m.group(0).strip()[:120] if m else None


def chunk_pages(pages: Iterator[tuple[int, str]]) -> Iterator[dict]:
    """Accumulate page text into overlapping chunks, tracking the last heading.

    Chunks are sized in characters (a cheap proxy for tokens) and closed on a
    paragraph boundary where possible, so a citation lands on readable prose
    rather than mid-sentence.
    """
    target = config.CHUNK_TOKENS * config.CHARS_PER_TOKEN
    overlap = config.CHUNK_OVERLAP * config.CHARS_PER_TOKEN

    buf: list[str] = []
    buf_len = 0
    first_page = None
    section: str | None = None
    ordinal = 0

    def emit(text: str, page: int | None, sec: str | None, ordn: int) -> dict | None:
        t = text.strip()
        if len(t) < config.MIN_CHUNK_CHARS:
            return None
        return {"ordinal": ordn, "page": page, "section": sec,
                "text": t[: config.MAX_CHUNK_CHARS]}

    for page_no, text in pages:
        if first_page is None:
            first_page = page_no
        head = _heading_in(text)
        if head:
            section = head

        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            buf.append(para)
            buf_len += len(para) + 2

            while buf_len >= target:
                joined = "\n\n".join(buf)
                cut = joined[:target]
                # prefer to break on a paragraph, else a sentence
                brk = cut.rfind("\n\n")
                if brk < target * 0.5:
                    brk = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
                    brk = brk + 1 if brk > target * 0.5 else target
                piece, rest = joined[:brk], joined[max(0, brk - overlap):]
                ch = emit(piece, first_page, section, ordinal)
                if ch:
                    ordinal += 1
                    yield ch
                buf = [rest] if rest.strip() else []
                buf_len = len(rest)
                first_page = page_no

    if buf:
        ch = emit("\n\n".join(buf), first_page, section, ordinal)
        if ch:
            yield ch
