"""Retrieve relevant chunks from Provision's existing Chroma vector store."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langsmith import traceable

COLLECTION_NAME = "provision_compliance"
EMBEDDING_MODEL = "text-embedding-3-small"

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"
VECTOR_STORE_PATH = BACKEND_DIR / "vectorstore" / "chroma"

RetrievalResult = tuple[Document, float]


def _load_environment() -> None:
    """Load backend environment variables and require an OpenAI API key."""
    load_dotenv(dotenv_path=ENV_PATH)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            f"OPENAI_API_KEY is missing. Add it to {ENV_PATH} before retrieval."
        )


def get_vectorstore() -> Chroma:
    """Connect to and return Provision's existing Chroma vector store."""
    _load_environment()

    if not VECTOR_STORE_PATH.is_dir():
        raise FileNotFoundError(
            f"Vector store was not found at {VECTOR_STORE_PATH}. "
            "Run ingestion before testing retrieval."
        )

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_PATH),
    )

@traceable(name="Chroma Retrieval", run_type="retriever")
def retrieve_documents(query: str, k: int = 5) -> list[RetrievalResult]:
    """Return the top matching chunks and their Chroma distance scores."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query must not be empty.")
    if k < 1:
        raise ValueError("k must be at least 1.")

    vector_store = get_vectorstore()
    return vector_store.similarity_search_with_score(cleaned_query, k=k)
