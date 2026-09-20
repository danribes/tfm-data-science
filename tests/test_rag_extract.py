"""Extraction provenance and conservative PDF-noise handling; no model or corpus."""

import pytest

from rag import config, extract


@pytest.fixture
def compact_chunks(monkeypatch):
    def configure(target=40, overlap=8):
        for name, value in {
            "CHUNK_TOKENS": target,
            "CHARS_PER_TOKEN": 1,
            "CHUNK_OVERLAP": overlap,
            "MIN_CHUNK_CHARS": 1,
            "MAX_CHUNK_CHARS": 2 * target,
        }.items():
            monkeypatch.setattr(config, name, value)

    configure()
    return configure


def test_overlap_retains_the_page_where_its_text_begins(compact_chunks):
    chunks = list(extract.chunk_pages(iter([(7, "a" * 26), (12, "b" * 70)])))

    assert chunks[0]["page"] == 7
    assert chunks[1]["text"].startswith("a" * 8 + "\n\n")
    assert chunks[1]["page"] == 7
    assert all(chunk["page"] == 12 for chunk in chunks if chunk["text"].startswith("b"))


def test_three_short_pages_keep_provenance_after_a_later_page_emits(compact_chunks):
    compact_chunks(target=48, overlap=16)
    pages = [(11, "A" * 10), (19, "B" * 10), (23, "C" * 10), (31, "D" * 60)]
    chunks = list(extract.chunk_pages(iter(pages)))

    assert chunks[0]["text"] == "A" * 10 + "\n\n" + "B" * 10 + "\n\n" + "C" * 10
    assert chunks[1]["text"].startswith("B" * 4 + "\n\n" + "C" * 10)
    expected_page = {"A": 11, "B": 19, "C": 23, "D": 31}
    assert [chunk["page"] for chunk in chunks] == [
        expected_page[chunk["text"][0]] for chunk in chunks
    ]


def test_empty_pages_do_not_supply_a_chunk_start_page(compact_chunks):
    chunks = list(extract.chunk_pages(iter([(2, ""), (4, "\n\n"), (9, "z" * 60)])))

    assert chunks
    assert all(chunk["page"] == 9 for chunk in chunks)


def test_later_page_heading_does_not_relabel_earlier_text(compact_chunks):
    pages = [(3, "# Old\n" + "a" * 20), (4, "# New\n" + "b" * 60)]
    chunks = list(extract.chunk_pages(iter(pages)))

    assert chunks[0]["section"] == "# Old"
    assert chunks[1]["text"].startswith("a" * 8 + "\n\n# New")
    assert chunks[1]["section"] == "# Old"
    later = [chunk for chunk in chunks if chunk["text"].startswith("b")]
    assert later and all(chunk["section"] == "# New" for chunk in later)


def test_multiple_headings_on_one_page_follow_the_chunk_start(compact_chunks):
    text = "# Old\n" + "a" * 80 + "\n# New\n" + "b" * 80
    chunks = list(extract.chunk_pages(iter([(5, text)])))

    assert [chunk["section"] for chunk in chunks] == [
        "# Old", "# Old", "# Old", "# New", "# New", "# New"
    ]
    assert "# New" in chunks[2]["text"]
    assert chunks[2]["section"] == "# Old"


def test_heading_later_on_page_does_not_label_unsectioned_prefix(compact_chunks):
    text = "a" * 70 + "\n# New\n" + "b" * 70
    chunks = list(extract.chunk_pages(iter([(8, text)])))

    assert [chunk["section"] for chunk in chunks] == [None, None, None, "# New", "# New"]


def test_exact_character_sizes_and_overlap_are_preserved(compact_chunks):
    compact_chunks(target=24, overlap=6)
    text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    chunks = list(extract.chunk_pages(iter([(17, text)])))

    assert [chunk["text"] for chunk in chunks] == [
        text[:24], text[18:42], text[36:60], text[54:]
    ]
    assert [chunk["ordinal"] for chunk in chunks] == [0, 1, 2, 3]
    assert all(chunk["page"] == 17 for chunk in chunks)
    assert all(left["text"][-6:] == right["text"][:6] for left, right in zip(chunks, chunks[1:]))


@pytest.mark.parametrize("count", [8, 12, 80])
def test_clean_page_removes_long_consecutive_pipe_only_runs(count):
    rug = [" | ", "| |", "\t||\t", "||| "] * ((count + 3) // 4)
    raw = "\n".join(["Before the plot", *rug[:count], "After the plot"])

    assert extract.clean_page(raw) == "Before the plot\nAfter the plot"


def test_clean_page_keeps_short_runs_and_meaningful_pipe_expressions():
    lines = ["Body text", *(["|"] * 7), "|x|", "||x||", "a | b", "|", "More prose"]

    assert extract.clean_page("\n".join(lines)) == "\n".join(lines)


def test_clean_page_does_not_join_runs_across_meaningful_content():
    lines = [*(["|"] * 7), "x | y", *(["|"] * 7)]

    assert extract.clean_page("\n".join(lines)) == "\n".join(lines)


def test_clean_page_filter_is_limited_to_ascii_pipe_noise():
    lines = ["Body text", *(["│"] * 8), "More prose"]

    assert extract.clean_page("\n".join(lines)) == "\n".join(lines)


@pytest.mark.parametrize("axes", ["1.0\n0.08", "0.8\n1.0", "1.0 0.08"])
def test_numeric_plot_coordinates_are_not_section_headings(axes, compact_chunks):
    compact_chunks(target=200)
    assert extract._heading_in(axes) is None
    chunks = list(extract.chunk_pages(iter([(196, axes + "\nBody after the plot.")])))
    assert chunks[0]["section"] is None


@pytest.mark.parametrize("heading", [
    "8.8\nReferences and further reading",
    "2.1\nMétodos de evaluación",
    "3.2 Δοκιμή",
])
def test_numbered_headings_allow_letters_and_split_lines(heading, compact_chunks):
    compact_chunks(target=200)
    assert extract._heading_in(heading) == heading
    chunks = list(extract.chunk_pages(iter([(10, heading + "\nBody of the section.")])))
    assert chunks[0]["section"] == heading
