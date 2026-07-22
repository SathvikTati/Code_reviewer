from app.services.rag.chunker import MarkdownChunker


DOC = """\
# Doc Title

## Section One
body one line

## Section Two
body two line
"""


def test_chunks_by_section_with_category_and_titles(tmp_path):
    doc = tmp_path / "security" / "example.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(DOC)

    chunks = MarkdownChunker().chunk_file(doc, tmp_path)

    assert len(chunks) == 2

    first = chunks[0]
    assert first.category == "Security"                     # folder -> category
    assert first.source == "security/example.md"
    assert first.id == "security/example.md::0"
    assert first.title == "Doc Title — Section One"
    assert first.text.startswith("Doc Title — Section One")
    assert "body one line" in first.text

    assert chunks[1].title == "Doc Title — Section Two"
    assert "body two line" in chunks[1].text


def test_unknown_category_folder_falls_back_to_folder_name(tmp_path):
    doc = tmp_path / "misc" / "notes.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# T\n\n## S\nx\n")

    chunks = MarkdownChunker().chunk_file(doc, tmp_path)
    assert chunks[0].category == "misc"
