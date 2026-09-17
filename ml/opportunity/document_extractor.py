"""
CuraTera AI - Step 10.6.3 Document Extractor

Responsibility:
    Extract readable text from government PDF documents.

This component does NOT:
    - decide eligibility
    - detect policy changes
    - classify changes
    - identify affected citizens
    - send notifications
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def extract_pdf_text(
    pdf_path: str
) -> str:
    """
    Extract text from all pages of a PDF.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    reader = PdfReader(
        str(path)
    )

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def clean_text(
    text: str
) -> str:
    """
    Clean common PDF extraction artifacts.
    """

    # Normalize line endings
    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Remove excessive spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def extract_scheme_document(
    pdf_path: str,
    scheme_id: str
) -> dict[str, Any]:
    """
    Extract and clean a scheme document.
    """

    raw_text = extract_pdf_text(
        pdf_path
    )

    cleaned_text = clean_text(
        raw_text
    )

    return {
        "scheme_id": scheme_id,
        "source_file": str(pdf_path),
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "character_count": len(cleaned_text),
    }