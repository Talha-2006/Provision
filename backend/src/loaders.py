"""Load Provision source URLs into LangChain documents."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import fitz
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

LOGGER = logging.getLogger(__name__)

DEFAULT_SOURCES_PATH = Path(__file__).resolve().parents[2] / "data" / "sources.json"
DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = "Provision/0.1 (Canadian compliance research)"
REQUIRED_SOURCE_FIELDS = {
    "id",
    "title",
    "url",
    "jurisdiction",
    "topic",
    "source_type",
    "enabled",
}


def read_sources(sources_path: str | Path = DEFAULT_SOURCES_PATH) -> list[dict[str, Any]]:
    """Read and validate source definitions from a JSON file."""
    path = Path(sources_path)

    with path.open(encoding="utf-8") as source_file:
        sources = json.load(source_file)

    if not isinstance(sources, list):
        raise ValueError(f"{path} must contain a JSON array of sources.")

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source at index {index} must be a JSON object.")

        missing_fields = REQUIRED_SOURCE_FIELDS - source.keys()
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Source at index {index} is missing fields: {missing}.")

        if not isinstance(source["enabled"], bool):
            raise ValueError(
                f"Source at index {index} field 'enabled' must be a boolean."
            )

    return sources


def load_documents(
    sources_path: str | Path = DEFAULT_SOURCES_PATH,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    continue_on_error: bool = False,
) -> list[Document]:
    """Download all configured sources and return one Document per source."""
    sources = read_sources(sources_path)
    documents: list[Document] = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        count = 0
        for source in sources:
            if not source["enabled"]:
                continue
            count += 1
            print(f"{count}")
            print(f"Fetching: {source['title']}")
            print(f"URL: {source['url']}")
            try:
                documents.append(load_source(source, session=session, timeout=timeout))
            except (requests.RequestException, ValueError, RuntimeError):
                if not continue_on_error:
                    raise
                LOGGER.exception(
                    "Could not load source %s from %s.",
                    source["id"],
                    source["url"],
                )

    return documents


def load_source(
    source: dict[str, Any],
    *,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Document:
    """Download one source and convert it to a LangChain Document."""
    client = session or requests.Session()
    owns_session = session is None

    if owns_session:
        client.headers.update({"User-Agent": USER_AGENT})

    try:
        response = client.get(source["url"], timeout=timeout)
        response.raise_for_status()
        text = _extract_response_text(response)
    finally:
        if owns_session:
            client.close()

    if not text:
        raise ValueError(f"No text could be extracted from {source['url']}.")

    return Document(page_content=text, metadata=_build_metadata(source))


def _extract_response_text(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type", "").lower()
    is_pdf = "application/pdf" in content_type or response.url.lower().endswith(
        ".pdf"
    )

    if is_pdf:
        return _extract_pdf_text(response.content)

    if "html" in content_type or not content_type:
        return _extract_html_text(response.text)

    raise ValueError(
        f"Unsupported content type {content_type!r} returned by {response.url}."
    )


def _extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "svg", "form", "nav", "footer", "header", "aside"]
    ):
        element.decompose()

    content = soup.find("main") or soup.find("article") or soup.body or soup
    return _clean_text(content.get_text(separator="\n"))


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
            pages = [page.get_text("text") for page in pdf]
    except (fitz.FileDataError, RuntimeError) as exc:
        raise ValueError("The downloaded PDF could not be read.") from exc

    return _clean_text("\n\n".join(pages))


def _clean_text(text: str) -> str:
    cleaned_lines: list[str] = []

    for raw_line in text.replace("\xa0", " ").splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line and (not cleaned_lines or line != cleaned_lines[-1]):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _build_metadata(source: dict[str, Any]) -> dict[str, str]:
    jurisdiction = str(source["jurisdiction"])
    is_federal = jurisdiction.casefold() == "federal"

    return {
        "source_id": str(source["id"]),
        "title": str(source["title"]),
        "url": str(source["url"]),
        "jurisdiction": "Canada Federal" if is_federal else jurisdiction,
        "province": str(source.get("province") or ("All" if is_federal else jurisdiction)),
        "topic": str(source["topic"]),
        "source_type": str(source["source_type"]),
    }
