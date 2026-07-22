from pathlib import Path

from app.config.settings import settings


class KnowledgeChunk:

    def __init__(
        self,
        id: str,
        text: str,
        category: str,
        source: str,
        title: str
    ):
        self.id = id
        self.text = text
        self.category = category
        self.source = source
        self.title = title


class MarkdownChunker:
    """Splits markdown docs into retrievable chunks.

    Each chunk corresponds to one section (delimited by '## ' headings),
    keeping the document title and heading as context. This produces
    semantically coherent chunks that map cleanly onto a single standard.
    """

    def __init__(self):
        self.category_map = settings.get("category_folders", default={})
        self.section_heading = settings.get(
            "chunking", "section_heading", default="## "
        )

    def chunk_file(self, path: Path, base_dir: Path) -> list[KnowledgeChunk]:

        relative = path.relative_to(base_dir)

        # First path segment is the category folder.
        category_key = relative.parts[0]
        category = self.category_map.get(category_key, category_key)

        source = str(relative)

        text = path.read_text(encoding="utf-8")

        return self._chunk_text(text, category, source)

    def _chunk_text(
        self,
        text: str,
        category: str,
        source: str
    ) -> list[KnowledgeChunk]:

        lines = text.splitlines()

        doc_title = source
        for line in lines:
            if line.startswith("# "):
                doc_title = line[2:].strip()
                break

        chunks: list[KnowledgeChunk] = []

        current_heading = doc_title
        current_lines: list[str] = []
        index = 0

        def flush():
            nonlocal index, current_lines
            body = "\n".join(current_lines).strip()
            if not body:
                current_lines = []
                return
            title = f"{doc_title} — {current_heading}" if current_heading != doc_title else doc_title
            text_block = f"{title}\n\n{body}"
            chunks.append(
                KnowledgeChunk(
                    id=f"{source}::{index}",
                    text=text_block,
                    category=category,
                    source=source,
                    title=title
                )
            )
            index += 1
            current_lines = []

        heading = self.section_heading

        for line in lines:

            if line.startswith("# ") and not line.startswith(heading):
                # Document title line — skip, already captured.
                continue

            if line.startswith(heading):
                flush()
                current_heading = line[len(heading):].strip()
                continue

            current_lines.append(line)

        flush()

        return chunks
