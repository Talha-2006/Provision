"""FastAPI application exposing Provision's existing RAG pipeline."""

from __future__ import annotations

import re
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.generator import ProvisionResponse, generate_answer
from src.retriever import retrieve_documents

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_DIR / ".env"
TEXT_PREVIEW_LENGTH = 500

load_dotenv(dotenv_path=ENV_PATH)

APP_ENV = os.getenv("APP_ENV", "development")
ENABLE_DEBUG_ENDPOINTS = os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"
ASK_RATE_LIMIT = os.getenv("ASK_RATE_LIMIT", "5/minute")
DEBUG_RATE_LIMIT = os.getenv("DEBUG_RATE_LIMIT", "3/minute")
MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "2000"))

app = FastAPI(
    title="Provision API",
    description=(
        "Citation-grounded Canadian startup compliance research. "
        "Provision provides general information, not legal or accounting advice."
    ),
    version="0.1.0",
)

# In-memory rate limiting is fine for local/single-instance deployments.
# Production multi-instance deployments should use Redis-backed SlowAPI
# storage, cloud rate limiting, or Cloudflare-level protection.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str


class QuestionRequest(BaseModel):
    """Validated request shared by generation and retrieval endpoints."""

    question: str
    k: int = Field(default=5, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject empty questions and remove surrounding whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Question must not be empty.")
        return cleaned


class RetrievedChunk(BaseModel):
    """One retrieved chunk returned by the debug endpoint."""

    title: str
    url: str
    topic: str
    jurisdiction: str
    province: str
    chunk_id: str
    similarity_score: float | None
    text_preview: str


class RetrieveDebugResponse(BaseModel):
    """Retrieved chunks and metadata for debugging search quality."""

    question: str
    k: int
    chunks: list[RetrievedChunk]


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    return str(value) if value not in (None, "") else "Not available"


def _text_preview(text: str, limit: int = TEXT_PREVIEW_LENGTH) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _service_unavailable(error: FileNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(error),
    )


def _validate_question_length(question: str) -> None:
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Question is too long. "
                f"Maximum length is {MAX_QUESTION_LENGTH} characters."
            ),
        )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return a simple API health status without calling external services."""
    return HealthResponse(status="ok")


@app.post("/ask", response_model=ProvisionResponse)
@limiter.limit(ASK_RATE_LIMIT)
def ask(request: Request, payload: QuestionRequest) -> ProvisionResponse:
    """Generate a structured, citation-grounded answer."""
    _validate_question_length(payload.question)
    try:
        return generate_answer(payload.question, payload.k)
    except FileNotFoundError as error:
        raise _service_unavailable(error) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Answer generation failed.",
        ) from error


if ENABLE_DEBUG_ENDPOINTS:

    @app.post("/retrieve-debug", response_model=RetrieveDebugResponse)
    @limiter.limit(DEBUG_RATE_LIMIT)
    def retrieve_debug(
        request: Request,
        payload: QuestionRequest,
    ) -> RetrieveDebugResponse:
        """Return retrieved chunks without generating an answer."""
        _validate_question_length(payload.question)
        try:
            results = retrieve_documents(payload.question, payload.k)
        except FileNotFoundError as error:
            raise _service_unavailable(error) from error
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document retrieval failed.",
            ) from error

        chunks = [
            RetrievedChunk(
                title=_metadata_value(document.metadata, "title"),
                url=_metadata_value(document.metadata, "url"),
                topic=_metadata_value(document.metadata, "topic"),
                jurisdiction=_metadata_value(document.metadata, "jurisdiction"),
                province=_metadata_value(document.metadata, "province"),
                chunk_id=_metadata_value(document.metadata, "chunk_id"),
                similarity_score=float(score) if score is not None else None,
                text_preview=_text_preview(document.page_content),
            )
            for document, score in results
        ]

        return RetrieveDebugResponse(
            question=payload.question,
            k=payload.k,
            chunks=chunks,
        )

else:

    @app.post("/retrieve-debug", include_in_schema=False)
    def retrieve_debug_disabled() -> None:
        """Hide retrieved source chunks unless debug endpoints are enabled."""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
