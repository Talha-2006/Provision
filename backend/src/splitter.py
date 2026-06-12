"""Split loaded source documents into retrieval-sized chunks."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


def split_documents(
    documents: Sequence[Document],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Split documents while preserving source metadata and adding chunk IDs."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(list(documents))
    source_chunk_counts: defaultdict[str, int] = defaultdict(int)

    for chunk in chunks:
        source_id = chunk.metadata.get("source_id")
        if not source_id:
            raise ValueError("Every document must include metadata['source_id'].")

        chunk_index = source_chunk_counts[str(source_id)]
        chunk.metadata["chunk_id"] = f"{source_id}_{chunk_index}"
        source_chunk_counts[str(source_id)] += 1

    return chunks
