"""Generate citation-grounded Provision answers from retrieved chunks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable
from pydantic import BaseModel, Field

if __package__:
    from .prompts import PROVISION_SYSTEM_PROMPT, format_retrieved_documents
    from .retriever import RetrievalResult, retrieve_documents
else:
    from prompts import PROVISION_SYSTEM_PROMPT, format_retrieved_documents
    from retriever import RetrievalResult, retrieve_documents

MODEL_NAME = "gpt-4.1-mini"

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"


class Citation(BaseModel):
    """Metadata for a retrieved chunk used in the answer."""

    title: str = Field(description="Exact source title from the retrieved context.")
    url: str = Field(description="Exact source URL from the retrieved context.")
    chunk_id: str = Field(description="Exact chunk ID cited in the answer.")
    topic: str = Field(description="Source topic from the retrieved context.")
    jurisdiction: str = Field(
        description="Source jurisdiction from the retrieved context."
    )
    province: str = Field(description="Source province from the retrieved context.")


class ProvisionResponse(BaseModel):
    """Structured answer returned by the Provision generation pipeline."""

    answer: str = Field(
        description="Source-grounded answer with inline chunk ID citations."
    )
    checklist: list[str] = Field(
        description="Supported practical next steps, or an empty list."
    )
    citations: list[Citation] = Field(
        description="Retrieved chunks actually cited in the answer."
    )
    risk_level: Literal["low", "medium", "high"]
    professional_help_recommended: bool
    insufficient_context: bool


def _load_environment() -> None:
    """Load backend environment variables and require an OpenAI API key."""
    load_dotenv(dotenv_path=ENV_PATH)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            f"OPENAI_API_KEY is missing. Add it to {ENV_PATH} before asking questions."
        )


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    """Return a citation-safe metadata value."""
    value = metadata.get(key)
    return str(value) if value not in (None, "") else "Not available"


def _citation_from_result(result: RetrievalResult) -> Citation:
    """Build a citation from trusted retrieved-document metadata."""
    metadata = result[0].metadata
    return Citation(
        title=_metadata_value(metadata, "title"),
        url=_metadata_value(metadata, "url"),
        chunk_id=_metadata_value(metadata, "chunk_id"),
        topic=_metadata_value(metadata, "topic"),
        jurisdiction=_metadata_value(metadata, "jurisdiction"),
        province=_metadata_value(metadata, "province"),
    )


def _normalize_citations(
    response: ProvisionResponse,
    results: list[RetrievalResult],
) -> ProvisionResponse:
    """Replace model citation metadata with trusted retrieved metadata."""
    citations_by_chunk_id = {
        _metadata_value(document.metadata, "chunk_id"): _citation_from_result(result)
        for result in results
        for document in [result[0]]
    }
    normalized: list[Citation] = []
    seen_chunk_ids: set[str] = set()

    for citation in response.citations:
        trusted_citation = citations_by_chunk_id.get(citation.chunk_id.strip())
        if trusted_citation and trusted_citation.chunk_id not in seen_chunk_ids:
            normalized.append(trusted_citation)
            seen_chunk_ids.add(trusted_citation.chunk_id)

    for chunk_id, trusted_citation in citations_by_chunk_id.items():
        if f"[{chunk_id}]" in response.answer and chunk_id not in seen_chunk_ids:
            normalized.append(trusted_citation)
            seen_chunk_ids.add(chunk_id)

    return response.model_copy(update={"citations": normalized})


def _empty_retrieval_response() -> ProvisionResponse:
    """Return a grounded response when retrieval produces no context."""
    return ProvisionResponse(
        answer=(
            "The retrieved sources are insufficient to answer this question. "
            "No relevant source chunks were available."
        ),
        checklist=[],
        citations=[],
        risk_level="medium",
        professional_help_recommended=True,
        insufficient_context=True,
    )

@traceable(name="Generate Provision Answer")
def generate_answer(question: str, k: int = 5) -> ProvisionResponse:
    """Retrieve relevant chunks and generate a structured, cited answer."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question must not be empty.")
    if k < 1:
        raise ValueError("k must be at least 1.")

    _load_environment()
    results = retrieve_documents(cleaned_question, k=k)
    if not results:
        return _empty_retrieval_response()

    context = format_retrieved_documents(results)
    user_prompt = (
        f"Question:\n{cleaned_question}\n\n"
        f"Retrieved source context:\n{context}\n\n"
        "Answer using only this context and return the required structured fields."
    )

    model = ChatOpenAI(model=MODEL_NAME, temperature=0)
    structured_model = model.with_structured_output(
        ProvisionResponse,
        method="json_schema",
    )
    raw_response = structured_model.invoke(
        [
            SystemMessage(content=PROVISION_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )
    response = (
        raw_response
        if isinstance(raw_response, ProvisionResponse)
        else ProvisionResponse.model_validate(raw_response)
    )
    return _normalize_citations(response, results)
