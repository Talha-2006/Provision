"""Run simple rule-based evaluations against Provision's RAG pipeline."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVALS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVALS_DIR.parent
SRC_DIR = BACKEND_DIR / "src"
QUESTIONS_PATH = EVALS_DIR / "questions.json"
RESULTS_PATH = EVALS_DIR / "results" / "latest_results.json"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
load_dotenv()

from generator import ProvisionResponse, generate_answer  # noqa: E402
from retriever import RetrievalResult, retrieve_documents  # noqa: E402

DEFAULT_K = 5
ANSWER_PREVIEW_LENGTH = 300
SEPARATOR = "=" * 80


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict[str, Any]]:
    """Load and minimally validate the evaluation dataset."""
    with path.open(encoding="utf-8") as questions_file:
        questions = json.load(questions_file)

    if not isinstance(questions, list):
        raise ValueError(f"{path} must contain a JSON array.")

    required_fields = {
        "id",
        "question",
        "expected_topic",
        "must_cite",
        "expected_risk_level",
        "professional_help_recommended",
    }
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            raise ValueError(f"Question at index {index} must be a JSON object.")

        missing_fields = required_fields - question.keys()
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Question at index {index} is missing: {missing}.")

    return questions


def _retrieved_topics(results: list[RetrievalResult]) -> list[str]:
    """Return unique retrieved topics while preserving retrieval order."""
    topics: list[str] = []

    for document, _score in results:
        topic = str(document.metadata.get("topic") or "Not available")
        if topic not in topics:
            topics.append(topic)

    return topics


def _topic_matches(expected_topic: str, retrieved_topics: list[str]) -> bool:
    expected = expected_topic.strip().casefold()
    return any(topic.strip().casefold() == expected for topic in retrieved_topics)


def _answer_preview(answer: str, limit: int = ANSWER_PREVIEW_LENGTH) -> str:
    cleaned = re.sub(r"\s+", " ", answer).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _evaluate_question(
    eval_question: dict[str, Any],
    *,
    k: int = DEFAULT_K,
) -> dict[str, Any]:
    """Run retrieval and generation, then calculate rule-based checks."""
    question = str(eval_question["question"])

    # Run the complete RAG pipeline through its traced entry point. The
    # additional retrieval below is only for rule-based retrieval metrics.
    response: ProvisionResponse = generate_answer(question, k=k)
    retrieval_results = retrieve_documents(question, k=k)

    topics = _retrieved_topics(retrieval_results)
    expected_topic = str(eval_question["expected_topic"])
    must_cite = bool(eval_question["must_cite"])
    expected_risk = str(eval_question["expected_risk_level"]).casefold()
    expected_help = bool(eval_question["professional_help_recommended"])
    expected_insufficient = eval_question.get("expected_insufficient_context")

    citation_requirement_pass = None
    if must_cite:
        citation_requirement_pass = bool(response.citations)

    insufficient_context_match = None
    if expected_insufficient is not None:
        insufficient_context_match = (
            response.insufficient_context is bool(expected_insufficient)
        )

    return {
        "id": str(eval_question["id"]),
        "question": question,
        "expected_topic": expected_topic,
        "retrieved_topics": topics,
        "retrieval_topic_match": _topic_matches(expected_topic, topics),
        "must_cite": must_cite,
        "citation_count": len(response.citations),
        "citation_requirement_pass": citation_requirement_pass,
        "expected_risk_level": expected_risk,
        "actual_risk_level": response.risk_level,
        "risk_level_match": response.risk_level.casefold() == expected_risk,
        "expected_professional_help_recommended": expected_help,
        "actual_professional_help_recommended": (
            response.professional_help_recommended
        ),
        "professional_help_recommendation_match": (
            response.professional_help_recommended is expected_help
        ),
        "expected_insufficient_context": expected_insufficient,
        "actual_insufficient_context": response.insufficient_context,
        "insufficient_context_match": insufficient_context_match,
        "answer": response.answer,
        "answer_preview": _answer_preview(response.answer),
        "citations": [citation.model_dump() for citation in response.citations],
        "error": None,
    }


def _failed_question_result(
    eval_question: dict[str, Any],
    error: Exception,
) -> dict[str, Any]:
    """Record an evaluation error without stopping the remaining questions."""
    return {
        "id": str(eval_question.get("id", "unknown")),
        "question": str(eval_question.get("question", "")),
        "expected_topic": eval_question.get("expected_topic"),
        "retrieved_topics": [],
        "retrieval_topic_match": False,
        "must_cite": bool(eval_question.get("must_cite", False)),
        "citation_count": 0,
        "citation_requirement_pass": False
        if eval_question.get("must_cite")
        else None,
        "expected_risk_level": eval_question.get("expected_risk_level"),
        "actual_risk_level": None,
        "risk_level_match": False,
        "expected_professional_help_recommended": eval_question.get(
            "professional_help_recommended"
        ),
        "actual_professional_help_recommended": None,
        "professional_help_recommendation_match": False,
        "expected_insufficient_context": eval_question.get(
            "expected_insufficient_context"
        ),
        "actual_insufficient_context": None,
        "insufficient_context_match": False
        if "expected_insufficient_context" in eval_question
        else None,
        "answer": "",
        "answer_preview": "",
        "citations": [],
        "error": f"{type(error).__name__}: {error}",
    }


def _metric_summary(
    results: list[dict[str, Any]],
    field: str,
) -> dict[str, int | float | None]:
    """Summarize a boolean metric, excluding non-applicable null values."""
    evaluated_values = [result[field] for result in results if result[field] is not None]
    passed = sum(value is True for value in evaluated_values)
    evaluated = len(evaluated_values)
    percentage = round((passed / evaluated) * 100, 1) if evaluated else None

    return {
        "passed": passed,
        "evaluated": evaluated,
        "percentage": percentage,
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate percentages for all requested metrics."""
    return {
        "questions_total": len(results),
        "questions_with_errors": sum(bool(result["error"]) for result in results),
        "retrieval_topic_match": _metric_summary(
            results, "retrieval_topic_match"
        ),
        "citation_requirement": _metric_summary(
            results, "citation_requirement_pass"
        ),
        "risk_level_match": _metric_summary(results, "risk_level_match"),
        "professional_help_recommendation_match": _metric_summary(
            results, "professional_help_recommendation_match"
        ),
        "insufficient_context_match": _metric_summary(
            results, "insufficient_context_match"
        ),
    }


def _status(value: bool | None, *, not_required: str = "N/A") -> str:
    if value is None:
        return not_required
    return "PASS" if value else "FAIL"


def print_question_report(result: dict[str, Any]) -> None:
    """Print one readable evaluation report."""
    print(SEPARATOR)
    print(f"Question ID: {result['id']}")
    print(f"Question: {result['question']}")
    print(f"Expected topic: {result['expected_topic']}")
    print(
        "Retrieved topics: "
        + (", ".join(result["retrieved_topics"]) or "None")
    )
    print(
        "Retrieval topic match: "
        f"{_status(result['retrieval_topic_match'])}"
    )

    citation_status = (
        _status(result["citation_requirement_pass"])
        if result["must_cite"]
        else "PASS"
    )
    citation_note = "" if result["must_cite"] else " (citation not required)"
    print(
        "Citation requirement: "
        f"{citation_status}{citation_note}"
    )
    print(
        "Risk level: "
        f"expected={result['expected_risk_level']}, "
        f"actual={result['actual_risk_level']} "
        f"[{_status(result['risk_level_match'])}]"
    )
    print(
        "Professional help recommended: "
        f"expected={result['expected_professional_help_recommended']}, "
        f"actual={result['actual_professional_help_recommended']} "
        f"[{_status(result['professional_help_recommendation_match'])}]"
    )

    if result["expected_insufficient_context"] is not None:
        print(
            "Insufficient context: "
            f"expected={result['expected_insufficient_context']}, "
            f"actual={result['actual_insufficient_context']} "
            f"[{_status(result['insufficient_context_match'])}]"
        )

    if result["error"]:
        print(f"Error: {result['error']}")
    print(f"Answer preview: {result['answer_preview'] or 'No answer generated.'}")


def _format_percentage(metric: dict[str, int | float | None]) -> str:
    percentage = metric["percentage"]
    if percentage is None:
        return "N/A (0 evaluated)"
    return (
        f"{percentage:.1f}% "
        f"({metric['passed']}/{metric['evaluated']})"
    )


def print_summary(summary: dict[str, Any]) -> None:
    """Print aggregate evaluation percentages."""
    print(f"\n{SEPARATOR}")
    print("EVALUATION SUMMARY")
    print(SEPARATOR)
    print(f"Questions: {summary['questions_total']}")
    print(f"Errors: {summary['questions_with_errors']}")
    print(
        "Retrieval topic match: "
        f"{_format_percentage(summary['retrieval_topic_match'])}"
    )
    print(
        "Citation requirement: "
        f"{_format_percentage(summary['citation_requirement'])}"
    )
    print(
        "Risk level match: "
        f"{_format_percentage(summary['risk_level_match'])}"
    )
    print(
        "Professional help recommendation match: "
        f"{_format_percentage(summary['professional_help_recommendation_match'])}"
    )
    print(
        "Insufficient context match: "
        f"{_format_percentage(summary['insufficient_context_match'])}"
    )
    print(f"Results saved to: {RESULTS_PATH}")


def save_results(
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    path: Path = RESULTS_PATH,
) -> None:
    """Save detailed and aggregate evaluation results as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "questions_path": str(QUESTIONS_PATH),
        "retrieval_k": DEFAULT_K,
        "summary": summary,
        "results": results,
    }

    with path.open("w", encoding="utf-8") as results_file:
        json.dump(payload, results_file, indent=2, ensure_ascii=True)
        results_file.write("\n")


def main() -> None:
    """Run all evaluation questions and report the results."""
    questions = load_questions()
    results: list[dict[str, Any]] = []

    print(f"Running {len(questions)} Provision evaluation questions...")
    print(f"Retrieving {DEFAULT_K} chunks per question.")

    for index, eval_question in enumerate(questions, start=1):
        print(f"\nEvaluating {index}/{len(questions)}...")
        try:
            result = _evaluate_question(eval_question)
        except Exception as error:
            result = _failed_question_result(eval_question, error)

        results.append(result)
        print_question_report(result)

    summary = build_summary(results)
    save_results(results, summary)
    print_summary(summary)


if __name__ == "__main__":
    main()
