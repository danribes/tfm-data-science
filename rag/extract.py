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
# Rug plots can extract as thousands of standalone vertical bars. Remove only
# long consecutive runs, preserving isolated bars, equations and bitwise code.
_RUG_LINE = re.compile(r"[| ]+")
_RUG_MIN_LINES = 8


def clean_page(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        ln = _WS.sub(" ", ln).strip()
        if not ln or _NOISE.match(ln):
            continue
        lines.append(ln)
    without_rugs: list[str] = []
    i = 0
    while i < len(lines):
        if _RUG_LINE.fullmatch(lines[i]):
            end = i + 1
            while end < len(lines) and _RUG_LINE.fullmatch(lines[end]):
                end += 1
            if end - i < _RUG_MIN_LINES:
                without_rugs.extend(lines[i:end])
            i = end
        else:
            without_rugs.append(lines[i])
            i += 1
    return _MULTINL.sub("\n\n", "\n".join(without_rugs)).strip()


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
    r"|\d{1,2}\.\d{1,2}\s+[^\W\d_].*)$",  # numbered title starts with a Unicode letter
    re.IGNORECASE | re.MULTILINE,
)


def _heading_in(text: str) -> str | None:
    m = _HEADING.search(text)
    return m.group(0).strip()[:120] if m else None


def chunk_pages(pages: Iterator[tuple[int, str]]) -> Iterator[dict]:
    """Yield overlapping chunks with the origin of their first non-space character.

    Character spans travel with the bounded text buffer, including retained
    overlap. A heading changes the section only at its actual position, so a
    heading encountered later cannot relabel an earlier passage.
    """
    target = config.CHUNK_TOKENS * config.CHARS_PER_TOKEN
    overlap = config.CHUNK_OVERLAP * config.CHARS_PER_TOKEN

    buf = ""
    buf_len = 0
    # Each span is (start, end, PDF page number, section at that position).
    spans: list[tuple[int, int, int, str | None]] = []
    section: str | None = None
    ordinal = 0

    def emit(text: str, ordn: int) -> dict | None:
        t = text.strip()
        if len(t) < config.MIN_CHUNK_CHARS:
            return None
        offset = len(text) - len(text.lstrip())
        _, _, page, sec = next(span for span in spans if span[0] <= offset < span[1])
        return {"ordinal": ordn, "page": page, "section": sec,
                "text": t[: config.MAX_CHUNK_CHARS]}

    for page_no, text in pages:
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            start = len(buf) + (2 if buf else 0)
            buf += ("\n\n" if buf else "") + para
            buf_len += len(para) + 2

            region = 0
            for head in _HEADING.finditer(para):
                if head.start() > region:
                    spans.append((start + region, start + head.start(), page_no, section))
                section = head.group(0).strip()[:120]
                region = head.start()
            spans.append((start + region, start + len(para), page_no, section))

            while buf_len >= target:
                cut = buf[:target]
                # Keep the existing paragraph/sentence breaks and overlap size.
                brk = cut.rfind("\n\n")
                if brk < target * 0.5:
                    brk = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
                    brk = brk + 1 if brk > target * 0.5 else target
                piece = buf[:brk]
                rest_start = max(0, brk - overlap)
                rest = buf[rest_start:]
                ch = emit(piece, ordinal)
                if ch:
                    ordinal += 1
                    yield ch
                spans = [(max(0, a - rest_start), b - rest_start, page, sec)
                         for a, b, page, sec in spans if b > rest_start]
                buf = rest if rest.strip() else ""
                buf_len = len(rest)
                if not buf:
                    spans = []

    if buf:
        ch = emit(buf, ordinal)
        if ch:
            yield ch
