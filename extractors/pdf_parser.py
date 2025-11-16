"""Utilities for extracting text from PDF sources."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import List

from pdfminer.high_level import extract_text_to_fp  # type: ignore[import]
from pdfminer.layout import LAParams  # type: ignore[import]

from utils.logger import get_logger

logger = get_logger(__name__)

PAGE_HEADER_TEMPLATE = "--- PAGE {page_number} ---"


def parse_pdf_file(file_path: str) -> str:
    """Return normalized text content extracted from a PDF file.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Unicode text extracted from the PDF with page delimiters inserted.

    Raises:
        ValueError: If the PDF cannot be parsed or contains no textual data.
    """

    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"PDF file not found: {file_path}")

    laparams = LAParams()
    buffer = StringIO()

    with path.open("rb") as pdf_file:
        extract_text_to_fp(
            pdf_file,
            buffer,
            laparams=laparams,
            output_type="text",
            codec="utf-8",
        )

    raw_text = buffer.getvalue()
    normalized_pages = _normalize_pdf_text(raw_text)
    if not normalized_pages.strip():
        raise ValueError(
            "PDF appears to contain no selectable text. Image-based PDFs "
            "require OCR, which is not yet supported."
        )

    page_count = _count_pages(normalized_pages)
    logger.info("Parsed %d PDF page(s) from '%s'", page_count, path.name)

    return normalized_pages


def _normalize_pdf_text(text: str) -> str:
    """Split text into pages, clean artifacts, and join with delimiters."""

    if not text:
        return ""

    pages = _split_pages(text)
    cleaned_pages: List[str] = []

    for index, page in enumerate(pages, start=1):
        cleaned = _clean_page_text(page)
        if cleaned:
            page_header = PAGE_HEADER_TEMPLATE.format(page_number=index)
            cleaned_pages.append(f"{page_header}\n\n{cleaned.strip()}")

    return "\n\n".join(cleaned_pages)


def _split_pages(text: str) -> List[str]:
    """Split raw PDF text on form-feed characters."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [segment for segment in normalized.split("\x0c")]


def _clean_page_text(page_text: str) -> str:
    """Clean up PDF text artifacts (soft hyphens, repeated whitespace, NBSP)."""

    if not page_text:
        return ""

    normalized = page_text.replace("\xa0", " ")
    normalized = re.sub(r"-\n(?=[A-Za-z])", "", normalized)
    normalized = re.sub(r"[\u00ad]", "", normalized)  # remove soft hyphen characters
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _count_pages(text: str) -> int:
    """Return the number of page headers in the normalized text."""

    if not text:
        return 0

    return text.count("--- PAGE ") or 1
