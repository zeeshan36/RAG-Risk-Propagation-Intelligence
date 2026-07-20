"""Simple heading-aware document chunker."""
import re
import uuid
from typing import Any, Dict, List

from rag_pipeline.chunking.base import DocumentChunker


class SimpleDocumentChunker(DocumentChunker):
    """Chunks documents by Markdown-style headings or by max token length.

    Tables (lines containing ``|``) are kept together as a single chunk when
    ``preserve_tables`` is enabled.
    """

    def __init__(
        self,
        max_chunk_size: int = 512,
        preserve_tables: bool = True,
        heading_regex: str = r"^#{1,3}\s+",
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.preserve_tables = preserve_tables
        self.heading_pattern = re.compile(heading_regex, re.MULTILINE)

    def chunk(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        for doc in documents:
            text = doc.get("text", "")
            base_meta = dict(doc.get("metadata", {}) or {})
            base_meta.setdefault("source_type", base_meta.get("source_type", "document"))
            base_meta.setdefault("source_id", doc.get("id"))

            sections = self._split_into_sections(text)
            for idx, section in enumerate(sections):
                section_chunks = self._chunk_section(section, base_meta)
                for sidx, chunk_text in enumerate(section_chunks):
                    chunk_id = f"{doc.get('id', uuid.uuid4().hex)}_c{idx}_{sidx}"
                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "metadata": dict(base_meta),
                        }
                    )
        return chunks

    def _split_into_sections(self, text: str) -> List[str]:
        if not self.heading_pattern:
            return [text]
        # Split while keeping the heading with the following body.
        parts = self.heading_pattern.split(text)
        headings = self.heading_pattern.findall(text)
        sections: List[str] = []
        if parts[0].strip():
            sections.append(parts[0].strip())
        for heading, body in zip(headings, parts[1:]):
            sections.append(f"{heading}{body.strip()}")
        return [s for s in sections if s.strip()]

    def _chunk_section(self, section: str, metadata: Dict[str, Any]) -> List[str]:
        if self.preserve_tables:
            table_block, remainder = self._extract_table_block(section)
            chunks = []
            if table_block:
                chunks.append(table_block)
            if remainder:
                chunks.extend(self._split_by_size(remainder))
            return chunks or [section]
        return self._split_by_size(section)

    def _extract_table_block(self, text: str) -> tuple:
        lines = text.splitlines()
        table_lines: List[str] = []
        other_lines: List[str] = []
        in_table = False
        for line in lines:
            if "|" in line:
                table_lines.append(line)
                in_table = True
            else:
                if in_table and line.strip() == "":
                    # End of table
                    in_table = False
                other_lines.append(line)
        table_block = "\n".join(table_lines).strip()
        remainder = "\n".join(other_lines).strip()
        return table_block, remainder

    def _split_by_size(self, text: str) -> List[str]:
        """Split text into chunks no longer than ``max_chunk_size`` characters."""
        if len(text) <= self.max_chunk_size:
            return [text]
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = start + self.max_chunk_size
            if end < len(text):
                # Try to break at a newline or sentence boundary.
                break_point = text.rfind("\n", start, end)
                if break_point == -1:
                    break_point = text.rfind(". ", start, end)
                if break_point != -1:
                    end = break_point + 1
            chunks.append(text[start:end].strip())
            start = end
        return chunks
