"""Manually inspect retrieval results from Provision's Chroma vector store."""

from __future__ import annotations

import argparse
import re
from typing import Any

if __package__:
    from .retriever import retrieve_documents
else:
    from retriever import retrieve_documents

PREVIEW_LENGTH = 600
SEPARATOR = "=" * 80


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test semantic retrieval from the Provision vector store."
    )
    parser.add_argument("question", help="Question to search for.")
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of chunks to retrieve (default: 5).",
    )
    return parser.parse_args()


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    return str(value) if value not in (None, "") else "Not available"


def _preview(text: str, limit: int = PREVIEW_LENGTH) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def main() -> None:
    """Retrieve and print chunks for a command-line question."""
    args = _parse_args()
    results = retrieve_documents(args.question, k=args.k)

    print(SEPARATOR)
    print(f"Question: {args.question}")
    print(f"Results requested: {args.k}")
    print(f"Results returned: {len(results)}")
    print("Score: Chroma distance (lower means a closer semantic match)")
    print(SEPARATOR)

    if not results:
        print("No matching chunks were found.")
        return

    for result_number, (document, score) in enumerate(results, start=1):
        metadata = document.metadata

        print(f"\nResult {result_number}")
        print("-" * 80)
        print(f"Title:        {_metadata_value(metadata, 'title')}")
        print(f"URL:          {_metadata_value(metadata, 'url')}")
        print(f"Topic:        {_metadata_value(metadata, 'topic')}")
        print(f"Jurisdiction: {_metadata_value(metadata, 'jurisdiction')}")
        print(f"Province:     {_metadata_value(metadata, 'province')}")
        print(f"Chunk ID:     {_metadata_value(metadata, 'chunk_id')}")
        print(f"Score:        {score:.6f}")
        print("Preview:")
        print(_preview(document.page_content))


if __name__ == "__main__":
    main()
