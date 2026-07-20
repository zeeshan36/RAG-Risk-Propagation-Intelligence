"""Tests for document chunking."""
from rag_pipeline.chunking.simple_chunker import SimpleDocumentChunker


def test_chunker_preserves_metadata():
    chunker = SimpleDocumentChunker(max_chunk_size=200)
    docs = [
        {
            "id": "doc1",
            "text": "Contract SLA\n\nDetails here.",
            "metadata": {
                "source_type": "contract",
                "entity_ids": ["C1"],
                "effective_date": "2026-01-01",
            },
        }
    ]
    chunks = chunker.chunk(docs)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["source_type"] == "contract"
        assert chunk["metadata"]["entity_ids"] == ["C1"]
        assert chunk["metadata"]["effective_date"] == "2026-01-01"
        assert chunk["metadata"]["source_id"] == "doc1"


def test_chunker_respects_max_size():
    chunker = SimpleDocumentChunker(max_chunk_size=50)
    docs = [{"id": "doc2", "text": "a" * 200, "metadata": {}}]
    chunks = chunker.chunk(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]) <= 50


def test_chunker_preserves_table():
    chunker = SimpleDocumentChunker(max_chunk_size=100, preserve_tables=True)
    docs = [
        {
            "id": "doc3",
            "text": "Table\n| a | b |\n| 1 | 2 |\nSome extra text that is long enough to be split if needed.",
            "metadata": {},
        }
    ]
    chunks = chunker.chunk(docs)
    table_chunks = [c for c in chunks if "|" in c["text"]]
    assert len(table_chunks) >= 1


def test_chunker_split_by_heading():
    chunker = SimpleDocumentChunker(max_chunk_size=1000)
    docs = [
        {
            "id": "doc4",
            "text": "# Heading 1\nBody one.\n## Heading 2\nBody two.",
            "metadata": {},
        }
    ]
    chunks = chunker.chunk(docs)
    assert len(chunks) >= 2
