"""Command-line interface for asking Provision compliance questions."""

from __future__ import annotations

import argparse

if __package__:
    from .generator import ProvisionResponse, generate_answer
else:
    from generator import ProvisionResponse, generate_answer

SEPARATOR = "=" * 80


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask Provision a source-grounded compliance question."
    )
    parser.add_argument("question", help="Compliance question to answer.")
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of chunks to retrieve (default: 5).",
    )
    return parser.parse_args()


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _print_response(question: str, response: ProvisionResponse) -> None:
    """Print a structured Provision response for terminal use."""
    print(SEPARATOR)
    print("PROVISION")
    print(SEPARATOR)
    print(f"Question: {question}")

    print("\nANSWER")
    print(response.answer)

    print("\nCHECKLIST")
    if response.checklist:
        for item in response.checklist:
            print(f"- {item}")
    else:
        print("- No source-supported checklist items were generated.")

    print(f"\nRISK LEVEL: {response.risk_level.upper()}")
    print(
        "PROFESSIONAL HELP RECOMMENDED: "
        f"{_yes_no(response.professional_help_recommended)}"
    )
    print(f"INSUFFICIENT CONTEXT: {_yes_no(response.insufficient_context)}")

    print("\nCITATIONS")
    if not response.citations:
        print("No citations available.")
        return

    for index, citation in enumerate(response.citations, start=1):
        print(f"\n[{index}] {citation.title}")
        print(f"URL:          {citation.url}")
        print(f"Chunk ID:     {citation.chunk_id}")
        print(f"Topic:        {citation.topic}")
        print(f"Jurisdiction: {citation.jurisdiction}")
        print(f"Province:     {citation.province}")


def main() -> None:
    """Parse CLI arguments, generate an answer, and print it."""
    args = _parse_args()
    response = generate_answer(args.question, k=args.k)
    _print_response(args.question, response)


if __name__ == "__main__":
    main()
