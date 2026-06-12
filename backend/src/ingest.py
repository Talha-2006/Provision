"""Build Provision's persistent Chroma vector store."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

if __package__:
    from .loaders import load_documents
    from .splitter import split_documents
else:
    from loaders import load_documents
    from splitter import split_documents

COLLECTION_NAME = "provision_compliance"
EMBEDDING_MODEL = "text-embedding-3-small"

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
ENV_PATH = BACKEND_DIR / ".env"
SOURCES_PATH = REPO_ROOT / "data" / "sources.json"
VECTOR_STORE_PATH = BACKEND_DIR / "vectorstore" / "chroma"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Provision Chroma vector store."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing vector store before rebuilding it.",
    )
    return parser.parse_args()


def _load_environment() -> None:
    """Load backend environment variables and require an OpenAI API key."""
    load_dotenv(dotenv_path=ENV_PATH)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            f"OPENAI_API_KEY is missing. Add it to {ENV_PATH} before ingestion."
        )


def _prepare_vector_store_path(*, reset: bool) -> None:
    """Prevent duplicate ingestion or remove the store for an explicit rebuild."""
    if VECTOR_STORE_PATH.exists():
        if not reset:
            raise FileExistsError(
                f"Vector store already exists at {VECTOR_STORE_PATH}. "
                "Run with --reset to rebuild it."
            )
        shutil.rmtree(VECTOR_STORE_PATH)

    VECTOR_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _chunk_ids(chunks: Sequence[Document]) -> list[str]:
    """Return validated Chroma IDs from chunk metadata."""
    ids: list[str] = []

    for chunk in chunks:
        chunk_id = chunk.metadata.get("chunk_id")
        if not chunk_id:
            raise ValueError("Every chunk must include metadata['chunk_id'].")
        ids.append(str(chunk_id))

    if len(ids) != len(set(ids)):
        raise ValueError("Chunk IDs must be unique before ingestion.")

    return ids


def ingest(*, reset: bool = False) -> int:
    """Load, split, embed, and persist all configured source documents."""
    _load_environment()
    _prepare_vector_store_path(reset=reset)

    print(f"Loading sources from: {SOURCES_PATH}")
    documents = load_documents(SOURCES_PATH)
    print(f"Loaded documents: {len(documents)}")

    chunks = split_documents(documents)
    print(f"Created chunks: {len(chunks)}")

    if not chunks:
        raise ValueError("No chunks were created; vector store was not built.")

    ids = _chunk_ids(chunks)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_PATH),
    )
    vector_store.add_documents(documents=chunks, ids=ids)

    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Vector store path: {VECTOR_STORE_PATH}")
    print(f"Stored chunks: {len(ids)}")
    return len(ids)


def main() -> None:
    """Run ingestion from the command line."""
    args = _parse_args()
    ingest(reset=args.reset)


if __name__ == "__main__":
    main()
