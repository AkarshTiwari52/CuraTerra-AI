"""
CuraTera AI - Step 10.6.4 Structured Policy Extractor

Purpose:
    Convert extracted government scheme text into a structured
    policy snapshot while preserving source evidence.

Important:
    This component does NOT decide eligibility.
    It only extracts information explicitly present in the source.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------
# Actual headings used in the tested government PDF
# ---------------------------------------------------------

SECTION_PATTERNS = {
    "introduction": r"^\s*1\.\s*Introduction\s*$",

    "objectives": r"^\s*2\.\s*(?:Objective|Objectives)\s*$",

    "salient_features":
        r"^\s*3\.\s*Salient features of the Scheme\s*$",

    "scope":
        r"^\s*3\.1\.?\s*Scope\s*$",

    "conditions_of_eligibility":
        r"^\s*3\.2\.?\s*Conditions of eligibility\s*$",

    "income_criteria":
        r"^\s*3\.3\.?\s*Income Criteria\s*$",

    "value_of_scholarship":
        r"^\s*3\.4\.?\s*Value of scholarship\s*$",

    "fee_component":
        r"^\s*3\.4\.1\.?\s*Fee component:\s*$",

    "stipend":
        r"^\s*3\.4\.2\.?\s*Stipend:\s*$",

    "documents_required":
        r"^\s*6\.?\s*Documents required:\s*$",

    "duration_and_renewal":
        r"^\s*7\.?\s*Duration and renewal of scholarship\s*$",

    "announcement_and_timeline":
        r"^\s*8\.?\s*Announcement and timeline of the scheme\s*$",

    "publicity_and_application":
        r"^\s*9\.?\s*Publicity\s*&?\s*Inviting Application\s*$",

    "change_in_provisions":
        r"^\s*15\.?\s*Change in the provisions of the scheme\s*$",
}


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Clean PDF extraction artifacts while preserving lines.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\xa0", " ")

    # Fix soft hyphen artifacts such as:
    # post￾secondary -> post-secondary
    text = text.replace("\u00ad", "-")
    text = text.replace("￾", "-")

    # Remove trailing spaces
    text = re.sub(
        r"[ \t]+$",
        "",
        text,
        flags=re.MULTILINE,
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ---------------------------------------------------------
# Find actual body
# ---------------------------------------------------------

def find_body_start(text: str) -> int:
    """
    Find the actual document body.

    The PDF has a contents page containing the same headings,
    so we use the LAST occurrence of '1. Introduction'.
    """

    pattern = r"(?im)^\s*1\.\s*Introduction\s*$"

    matches = list(
        re.finditer(
            pattern,
            text,
        )
    )

    if not matches:
        return 0

    return matches[-1].start()


# ---------------------------------------------------------
# Locate sections in actual body
# ---------------------------------------------------------

def locate_sections(
    text: str,
) -> dict[str, tuple[int, int]]:
    """
    Locate actual section headings after the document body begins.
    """

    body_start = find_body_start(text)

    body_text = text[body_start:]

    matches = []

    for section_name, pattern in SECTION_PATTERNS.items():

        found = list(
            re.finditer(
                pattern,
                body_text,
                flags=re.IGNORECASE
                | re.MULTILINE,
            )
        )

        if not found:
            continue

        # Use first occurrence AFTER the body starts.
        match = found[0]

        absolute_start = (
            body_start + match.start()
        )

        matches.append(
            (
                absolute_start,
                section_name,
            )
        )

    matches.sort(
        key=lambda item: item[0]
    )

    sections = {}

    for index, (start, section_name) in enumerate(matches):

        if index + 1 < len(matches):
            end = matches[index + 1][0]
        else:
            end = len(text)

        sections[section_name] = (
            start,
            end,
        )

    return sections


# ---------------------------------------------------------
# Extract a section
# ---------------------------------------------------------

def extract_section(
    text: str,
    section_name: str,
    sections: dict[str, tuple[int, int]],
) -> str | None:

    location = sections.get(
        section_name
    )

    if location is None:
        return None

    start, end = location

    section_text = text[
        start:end
    ].strip()

    if not section_text:
        return None

    return section_text


# ---------------------------------------------------------
# Extract income limit
# ---------------------------------------------------------

def extract_income_limit(
    text: str,
) -> dict[str, Any] | None:
    """
    Extract annual family-income limit.
    """

    patterns = [
        (
            r"family\s+income.*?"
            r"(?:Rs\.?|₹)\s*"
            r"(\d+(?:\.\d+)?)\s*lakh"
            r".{0,40}?"
            r"(?:per\s+annum|annum|year)"
        ),

        (
            r"(?:Rs\.?|₹)\s*"
            r"(\d+(?:\.\d+)?)\s*lakh"
            r".{0,40}?"
            r"(?:per\s+annum|annum|year)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
            | re.DOTALL,
        )

        if not match:
            continue

        lakh_value = float(
            match.group(1)
        )

        annual_amount = int(
            lakh_value * 100000
        )

        return {
            "value": annual_amount,
            "display_value":
                f"Rs.{lakh_value:g} lakh per annum",
            "evidence":
                match.group(0).strip(),
        }

    return None


# ---------------------------------------------------------
# Extract education scope
# ---------------------------------------------------------

def extract_education_scope(
    text: str,
) -> dict[str, str] | None:
    """
    Extract the educational scope explicitly stated in the document.

    The tested PDF says:
        class XI to Post Graduation courses
    """

    patterns = [
        r"starting\s+from\s+class\s+"
        r"(XI|XII)"
        r"\s+to\s+"
        r"(Post\s+Graduation)"
        r"\s+courses",

        r"class\s+"
        r"(XI|XII)"
        r"\s+to\s+"
        r"(Post\s+Graduation)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:

            return {
                "value": (
                    f"Class {match.group(1)} "
                    f"to {match.group(2)}"
                ),
                "evidence":
                    match.group(0).strip(),
            }

    return None


# ---------------------------------------------------------
# Extract social category
# ---------------------------------------------------------

def extract_social_category(
    text: str,
) -> dict[str, str] | None:

    pattern = (
        r"student\s+should\s+belong\s+to\s+"
        r"Scheduled Tribe"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return {
        "value": "ST",
        "evidence": match.group(0).strip(),
    }


# ---------------------------------------------------------
# Main extraction
# ---------------------------------------------------------

def extract_structured_policy(
    text: str,
    scheme_id: str,
) -> dict[str, Any]:

    cleaned_text = normalize_text(
        text
    )

    sections = locate_sections(
        cleaned_text
    )

    extracted_sections = {}

    for section_name in SECTION_PATTERNS:

        section_text = extract_section(
            cleaned_text,
            section_name,
            sections,
        )

        if section_text:
            extracted_sections[
                section_name
            ] = section_text

    # -----------------------------------------------------
    # Eligibility source text
    # -----------------------------------------------------

    eligibility_text = "\n".join(
        [
            extracted_sections.get(
                "introduction",
                "",
            ),

            extracted_sections.get(
                "conditions_of_eligibility",
                "",
            ),

            extracted_sections.get(
                "income_criteria",
                "",
            ),
        ]
    )

    income_limit = extract_income_limit(
        eligibility_text
    )

    education_scope = extract_education_scope(
        eligibility_text
    )

    social_category = extract_social_category(
        eligibility_text
    )

    # -----------------------------------------------------
    # Final structured snapshot
    # -----------------------------------------------------

    return {

        "scheme_id": scheme_id,

        "policy": {

            "eligibility": {

                "social_category": (
                    social_category["value"]
                    if social_category
                    else None
                ),

                "income_limit": (
                    income_limit["value"]
                    if income_limit
                    else None
                ),

                "education_scope": (
                    education_scope["value"]
                    if education_scope
                    else None
                ),
            },

            "benefits": {

                "value_of_scholarship":
                    extracted_sections.get(
                        "value_of_scholarship"
                    ),

                "fee_component":
                    extracted_sections.get(
                        "fee_component"
                    ),

                "stipend":
                    extracted_sections.get(
                        "stipend"
                    ),
            },

            "documents":
                extracted_sections.get(
                    "documents_required"
                ),

            "duration_and_renewal":
                extracted_sections.get(
                    "duration_and_renewal"
                ),

            "announcement_and_timeline":
                extracted_sections.get(
                    "announcement_and_timeline"
                ),

            "application_information":
                extracted_sections.get(
                    "publicity_and_application"
                ),

            "change_in_provisions":
                extracted_sections.get(
                    "change_in_provisions"
                ),
        },

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        "evidence": {

            "social_category": (
                social_category["evidence"]
                if social_category
                else None
            ),

            "income_limit": (
                income_limit["evidence"]
                if income_limit
                else None
            ),

            "education_scope": (
                education_scope["evidence"]
                if education_scope
                else None
            ),

            "conditions_of_eligibility":
                extracted_sections.get(
                    "conditions_of_eligibility"
                ),

            "income_criteria":
                extracted_sections.get(
                    "income_criteria"
                ),

            "value_of_scholarship":
                extracted_sections.get(
                    "value_of_scholarship"
                ),

            "documents_required":
                extracted_sections.get(
                    "documents_required"
                ),
        },

        "sections_found":
            list(
                extracted_sections.keys()
            ),
    }