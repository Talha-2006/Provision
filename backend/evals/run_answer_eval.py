"""
Run LangSmith LLM-as-judge evaluation for Provision.

Place this file at:
    backend/evals/run_answer_eval.py

Run from the backend folder:
    python -m evals.run_answer_eval

Required .env values:
    OPENAI_API_KEY=...
    LANGSMITH_API_KEY=...
    LANGSMITH_TRACING=true
    LANGSMITH_PROJECT=provision-evals

Optional .env values:
    LANGSMITH_ANSWER_DATASET=provision_answer_eval_dataset
    JUDGE_MODEL=gpt-4.1-mini
    EVAL_K=5
"""

from __future__ import annotations

import inspect
import json
import os
from typing import Any, cast

from dotenv import load_dotenv
from langsmith import evaluate, traceable
from openai import OpenAI


load_dotenv()

DATASET_NAME = os.getenv("LANGSMITH_ANSWER_DATASET", "provision_answer_eval_dataset")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4.1-mini")
K = int(os.getenv("EVAL_K", "5"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))

openai_client = OpenAI()


# -----------------------------------------------------------------------------
# Provision app adapters
# -----------------------------------------------------------------------------

def _load_ask_function():
    """
    Tries to find the function in src/ask.py that runs the full RAG pipeline.

    If your function has a different name, either:
      1. Rename it to ask_question(question: str, k: int = 5), or
      2. Add its name to candidate_names below.
    """
    try:
        import src.ask as ask_module
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "Could not import src.ask. Make sure you run this from the backend "
            "folder and that src/ask.py exists."
        ) from exc

    candidate_names = [
        "ask_question",
        "answer_question",
        "run_ask",
        "run_pipeline",
        "generate_answer",
        "ask",
    ]

    for name in candidate_names:
        fn = getattr(ask_module, name, None)
        if callable(fn):
            return fn, name

    raise AttributeError(
        "Could not find a callable RAG function in src.ask. Expected one of: "
        f"{candidate_names}. Add your function name to _load_ask_function()."
    )


def _call_with_supported_args(fn: Any, *, question: str, k: int) -> Any:
    """Calls the app function while handling common signatures."""
    signature = inspect.signature(fn)
    params = signature.parameters

    if "question" in params and "k" in params:
        return fn(question=question, k=k)

    if "query" in params and "k" in params:
        return fn(query=question, k=k)

    if "question" in params:
        return fn(question=question)

    if "query" in params:
        return fn(query=question)

    # Common simple signature: ask_question(question, k=5) or ask_question(question)
    try:
        return fn(question, k=k)
    except TypeError:
        return fn(question)


def _extract_answer(result: Any) -> str:
    """Extract answer text from common result shapes."""
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in ["answer", "response", "result", "final_answer", "output"]:
            value = result.get(key)
            if value is not None:
                return str(value)
        return json.dumps(result, ensure_ascii=False)

    for attr in ["answer", "response", "result", "final_answer", "output"]:
        value = getattr(result, attr, None)
        if value is not None:
            return str(value)

    return str(result)


def _extract_sources_from_answer_result(result: Any) -> list[dict]:
    """Extract citation/source list from common result shapes."""
    if isinstance(result, dict):
        for key in ["sources", "citations", "source_documents", "retrieved_sources"]:
            value = result.get(key)
            if isinstance(value, list):
                return [_normalize_source_item(item) for item in value]

    for attr in ["sources", "citations", "source_documents", "retrieved_sources"]:
        value = getattr(result, attr, None)
        if isinstance(value, list):
            return [_normalize_source_item(item) for item in value]

    return []


def _normalize_source_item(item: Any) -> dict:
    """Normalize source/citation/document-like objects to a plain dict."""

    if isinstance(item, dict):
        metadata_raw = item.get("metadata")
        metadata = cast(
            dict[str, Any],
            metadata_raw if isinstance(metadata_raw, dict) else item,
        )

        return {
            "source_id": _get_source_id(metadata),
            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "topic": metadata.get("topic"),
            "jurisdiction": metadata.get("jurisdiction"),
        }

    metadata_raw = getattr(item, "metadata", None)

    if isinstance(metadata_raw, dict):
        metadata = cast(dict[str, Any], metadata_raw)

        return {
            "source_id": _get_source_id(metadata),
            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "topic": metadata.get("topic"),
            "jurisdiction": metadata.get("jurisdiction"),
        }

    return {
        "source_id": None,
        "title": str(item),
        "url": None,
        "topic": None,
        "jurisdiction": None,
    }


# -----------------------------------------------------------------------------
# Retrieval helpers
# -----------------------------------------------------------------------------

def _extract_document_and_score(result: Any) -> tuple[Any, Any | None]:
    """
    Handles common retrieval result shapes:
    - (Document, score)
    - object with .document and .score
    - plain Document
    """
    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], None

    document = getattr(result, "document", None)
    if document is not None:
        return document, getattr(result, "score", None)

    return result, None


def _get_source_id(metadata: dict | None) -> str | None:
    if not metadata:
        return None
    return metadata.get("source_id") or metadata.get("id") or metadata.get("source")


def _retrieve_context(question: str, k: int) -> dict:
    """
    Runs your retriever so the evaluator can see source IDs and context.
    This assumes your retriever lives at src/retriever.py.
    """
    try:
        from src.retriever import retrieve_documents
    except Exception:
        return {
            "retrieved_source_ids": [],
            "retrieved_sources": [],
            "retrieved_context": "",
            "retrieval_error": "Could not import src.retriever.retrieve_documents",
        }

    try:
        results = retrieve_documents(question, k=k)
    except Exception as exc:
        return {
            "retrieved_source_ids": [],
            "retrieved_sources": [],
            "retrieved_context": "",
            "retrieval_error": repr(exc),
        }

    retrieved_sources: list[dict] = []
    retrieved_source_ids: list[str] = []
    context_parts: list[str] = []

    for rank, result in enumerate(results, start=1):
        doc, distance = _extract_document_and_score(result)
        metadata = getattr(doc, "metadata", {}) or {}
        page_content = getattr(doc, "page_content", "") or ""
        source_id = _get_source_id(metadata)

        if source_id:
            retrieved_source_ids.append(source_id)

        retrieved_sources.append(
            {
                "rank": rank,
                "source_id": source_id,
                "title": metadata.get("title"),
                "url": metadata.get("url"),
                "topic": metadata.get("topic"),
                "jurisdiction": metadata.get("jurisdiction"),
                "distance": distance,
            }
        )

        context_parts.append(
            f"[Rank {rank}]\n"
            f"source_id: {source_id}\n"
            f"title: {metadata.get('title')}\n"
            f"url: {metadata.get('url')}\n"
            f"content:\n{page_content}"
        )

    retrieved_context = "\n\n---\n\n".join(context_parts)
    retrieved_context = retrieved_context[:MAX_CONTEXT_CHARS]

    return {
        "retrieved_source_ids": retrieved_source_ids,
        "retrieved_sources": retrieved_sources,
        "retrieved_context": retrieved_context,
        "retrieval_error": None,
    }


# -----------------------------------------------------------------------------
# Target function evaluated by LangSmith
# -----------------------------------------------------------------------------

@traceable(name="Provision Answer Eval Target")
def answer_target(inputs: dict) -> dict:
    question = inputs["question"]

    ask_fn, ask_fn_name = _load_ask_function()
    answer_result = _call_with_supported_args(ask_fn, question=question, k=K)

    answer = _extract_answer(answer_result)
    answer_sources = _extract_sources_from_answer_result(answer_result)
    retrieval = _retrieve_context(question, k=K)

    # Prefer explicit answer sources when your ask pipeline returns them;
    # otherwise use the retrieved sources collected above.
    sources = answer_sources or retrieval["retrieved_sources"]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_source_ids": retrieval["retrieved_source_ids"],
        "retrieved_sources": retrieval["retrieved_sources"],
        "retrieved_context": retrieval["retrieved_context"],
        "retrieval_error": retrieval["retrieval_error"],
        "ask_function": ask_fn_name,
        "k": K,
    }


# -----------------------------------------------------------------------------
# Deterministic source evaluators
# -----------------------------------------------------------------------------

def strict_source_match(outputs: dict, reference_outputs: dict) -> dict:
    expected = set(reference_outputs.get("expected_source_ids", []))
    retrieved = outputs.get("retrieved_source_ids", [])
    retrieved_set = set(retrieved)

    first_match_rank = None
    for i, source_id in enumerate(retrieved, start=1):
        if source_id in expected:
            first_match_rank = i
            break

    return {
        "key": "strict_source_match",
        "score": 1 if first_match_rank is not None else 0,
        "comment": (
            f"Expected: {sorted(expected)}. "
            f"First match rank: {first_match_rank}. "
            f"Retrieved: {retrieved}."
        ),
    }


def acceptable_source_match(outputs: dict, reference_outputs: dict) -> list[dict]:
    acceptable = set(
        reference_outputs.get("acceptable_source_ids")
        or reference_outputs.get("expected_source_ids", [])
    )
    retrieved = outputs.get("retrieved_source_ids", [])

    first_match_rank = None
    for i, source_id in enumerate(retrieved, start=1):
        if source_id in acceptable:
            first_match_rank = i
            break

    top_1 = first_match_rank == 1
    top_3 = first_match_rank is not None and first_match_rank <= 3
    top_5 = first_match_rank is not None and first_match_rank <= 5

    return [
        {
            "key": "acceptable_source_match",
            "score": 1 if first_match_rank is not None else 0,
            "comment": (
                f"Acceptable: {sorted(acceptable)}. "
                f"First match rank: {first_match_rank}. "
                f"Retrieved: {retrieved}."
            ),
        },
        {
            "key": "acceptable_source_top_1",
            "score": 1 if top_1 else 0,
            "comment": f"First acceptable source rank: {first_match_rank}",
        },
        {
            "key": "acceptable_source_top_3",
            "score": 1 if top_3 else 0,
            "comment": f"First acceptable source rank: {first_match_rank}",
        },
        {
            "key": "acceptable_source_top_5",
            "score": 1 if top_5 else 0,
            "comment": f"First acceptable source rank: {first_match_rank}",
        },
    ]


# -----------------------------------------------------------------------------
# LLM-as-judge evaluator
# -----------------------------------------------------------------------------

def _safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Sometimes models wrap JSON in text/code fences. Try extracting the object.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

    return {
        "overall_score": 0,
        "correctness": 0,
        "completeness": 0,
        "groundedness": 0,
        "caution": 0,
        "reason": f"Judge returned invalid JSON: {text[:500]}",
    }


def _clip(text: Any, max_chars: int = 12000) -> str:
    value = str(text or "")
    return value[:max_chars]


def llm_answer_judge(inputs: dict, outputs: dict, reference_outputs: dict) -> list[dict]:
    question = inputs.get("question", "")
    reference_answer = reference_outputs.get("reference_answer", "")
    expected_source_ids = reference_outputs.get("expected_source_ids", [])
    acceptable_source_ids = reference_outputs.get("acceptable_source_ids", expected_source_ids)

    answer = outputs.get("answer", "")
    sources = outputs.get("sources", [])
    retrieved_context = outputs.get("retrieved_context", "")

    prompt = f"""
You are evaluating an answer from Provision, a Canadian startup compliance RAG assistant.

Grade the assistant answer using the reference answer and retrieved context.

Question:
{question}

Reference answer:
{reference_answer}

Assistant answer:
{answer}

Expected source IDs:
{expected_source_ids}

Acceptable source IDs:
{acceptable_source_ids}

Assistant sources:
{sources}

Retrieved context:
{_clip(retrieved_context, MAX_CONTEXT_CHARS)}

Scoring rules:
- Score each category from 1 to 5.
- correctness: factual/legal-compliance accuracy compared to the reference answer.
- completeness: covers the important points needed to answer the question.
- groundedness: answer is supported by the retrieved context and does not invent obligations, deadlines, penalties, exceptions, or legal tests.
- caution: avoids acting like a lawyer/accountant and clearly signals uncertainty or professional-help limits when appropriate.
- overall_score: your overall quality score from 1 to 5.

Rubric for overall_score:
5 = Fully correct, complete, grounded, and appropriately cautious.
4 = Mostly correct with only minor omissions or wording issues.
3 = Partially correct but missing important details or somewhat unclear.
2 = Mostly incorrect, materially incomplete, weakly supported, or overconfident.
1 = Incorrect, misleading, hallucinated, or gives professional legal/tax advice beyond the sources.

Important:
- Do not require exact wording from the reference answer.
- Penalize unsupported confident claims.
- Penalize invented deadlines, penalties, filing requirements, exceptions, or legal obligations.
- Reward concise answers that directly answer the question and cite/use the right sources.

Return JSON only with this exact schema:
{{
  "overall_score": 1,
  "correctness": 1,
  "completeness": 1,
  "groundedness": 1,
  "caution": 1,
  "reason": "brief explanation"
}}
"""

    response = openai_client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a strict but fair evaluator for RAG answer quality. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content or ""
    parsed = _safe_json_loads(content)

    def score_0_to_1(key: str) -> float:
        try:
            raw = float(parsed.get(key, 0))
        except (TypeError, ValueError):
            raw = 0
        raw = max(0, min(5, raw))
        return raw / 5

    reason = parsed.get("reason", "")

    return [
        {
            "key": "llm_overall_answer_quality",
            "score": score_0_to_1("overall_score"),
            "comment": f"Raw: {parsed.get('overall_score')}/5. {reason}",
        },
        {
            "key": "llm_correctness",
            "score": score_0_to_1("correctness"),
            "comment": f"Raw: {parsed.get('correctness')}/5. {reason}",
        },
        {
            "key": "llm_completeness",
            "score": score_0_to_1("completeness"),
            "comment": f"Raw: {parsed.get('completeness')}/5. {reason}",
        },
        {
            "key": "llm_groundedness",
            "score": score_0_to_1("groundedness"),
            "comment": f"Raw: {parsed.get('groundedness')}/5. {reason}",
        },
        {
            "key": "llm_caution",
            "score": score_0_to_1("caution"),
            "comment": f"Raw: {parsed.get('caution')}/5. {reason}",
        },
    ]


if __name__ == "__main__":
    print("Running Provision answer eval")
    print(f"Dataset: {DATASET_NAME}")
    print(f"k: {K}")
    print(f"Judge model: {JUDGE_MODEL}")

    evaluators: list[Any] = [
        strict_source_match,
        acceptable_source_match,
        llm_answer_judge,
    ]

    results = evaluate(  # pyright: ignore[reportCallIssue]
        answer_target,
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix=f"provision-answer-quality-k{K}",
        max_concurrency=1,
        metadata={
            "pipeline": "Provision RAG",
            "eval_type": "answer_quality_with_llm_judge",
            "k": K,
            "judge_model": JUDGE_MODEL,
            "dataset": DATASET_NAME,
        },
    )

    print(results)
