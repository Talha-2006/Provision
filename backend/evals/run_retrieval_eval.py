from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from langsmith import evaluate, traceable

from src.retriever import retrieve_documents  # adjust only if your file name is different


load_dotenv()

DATASET_NAME = "provision_retrieval_eval_dataset"
K = 5

def _extract_document_and_score(result: Any) -> tuple[Any, Any | None]:
    """
    Handles common retrieval result shapes:
    - (Document, score)
    - object with .document and .score
    - plain Document
    """

    # LangChain Chroma similarity_search_with_score returns:
    # (Document, score)
    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], None

    # Handles custom RetrievalResult objects without upsetting Pylance
    document = getattr(result, "document", None)
    if document is not None:
        score = getattr(result, "score", None)
        return document, score

    # Handles plain Document objects
    return result, None


def _get_source_id(metadata: dict) -> str | None:
    """
    Your ingestion should store source id in document metadata.
    This checks a few likely field names so the eval does not break
    if you used 'id' instead of 'source_id'.
    """
    return (
        metadata.get("source_id")
        or metadata.get("id")
        or metadata.get("source")
    )


@traceable(name="Provision Retrieval Eval Target", run_type="retriever")
def retrieval_target(inputs: dict) -> dict:
    question = inputs["question"]

    results = retrieve_documents(question, k=K)

    retrieved_sources = []
    retrieved_source_ids = []

    for rank, result in enumerate(results, start=1):
        doc, score = _extract_document_and_score(result)
        metadata = getattr(doc, "metadata", {}) or {}

        source_id = _get_source_id(metadata)

        item = {
            "rank": rank,
            "source_id": source_id,
            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "topic": metadata.get("topic"),
            "jurisdiction": metadata.get("jurisdiction"),
            "score": score,
        }

        retrieved_sources.append(item)

        if source_id:
            retrieved_source_ids.append(source_id)

    return {
        "question": question,
        "retrieved_source_ids": retrieved_source_ids,
        "retrieved_sources": retrieved_sources,
    }


def source_match(outputs: dict, reference_outputs: dict) -> dict:
    expected = set(reference_outputs.get("expected_source_ids", []))
    retrieved = set(outputs.get("retrieved_source_ids", []))

    matched = sorted(expected & retrieved)
    missed = sorted(expected - retrieved)

    score = 1 if matched else 0

    return {
        "key": "source_match",
        "score": score,
        "comment": (
            f"Matched: {matched}. "
            f"Missed: {missed}. "
            f"Retrieved: {sorted(retrieved)}."
        ),
    }


def source_recall(outputs: dict, reference_outputs: dict) -> dict:
    expected = set(reference_outputs.get("expected_source_ids", []))
    retrieved = set(outputs.get("retrieved_source_ids", []))

    if not expected:
        return {
            "key": "source_recall",
            "score": 0,
            "comment": "No expected_source_ids found on example.",
        }

    matched = expected & retrieved
    recall = len(matched) / len(expected)

    return {
        "key": "source_recall",
        "score": recall,
        "comment": f"Found {len(matched)} of {len(expected)} expected sources.",
    }


if __name__ == "__main__":
    results = evaluate(
        retrieval_target,
        data=DATASET_NAME,
        evaluators=[
            source_match,
            source_recall,
        ],
        experiment_prefix=f"provision-retrieval-k{K}",
        max_concurrency=1,
        metadata={
            "pipeline": "Provision RAG",
            "eval_type": "retrieval_source_match",
            "k": K,
        },
    )

    print(results)