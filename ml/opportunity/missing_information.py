"""
CuraTera AI - Missing Information Handler

Responsibility:
    Convert eligibility results with missing information into
    clear follow-up requests.

This component does NOT:
    - decide eligibility
    - create eligibility rules
    - calculate scores
    - send notifications
"""

from typing import Any


def extract_missing_information(
    eligibility_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Extract the exact missing profile attributes from one
    eligibility result.

    Expected eligibility result format:

    {
        "scheme_id": "S016",
        "status": "missing_information",
        "missing_information": [
            "annual_family_income",
            "land_holding"
        ]
    }
    """

    scheme_id = eligibility_result.get("scheme_id")

    if eligibility_result.get("status") != "missing_information":
        return []

    missing_fields = eligibility_result.get(
        "missing_information",
        []
    )

    return [
        {
            "scheme_id": scheme_id,
            "field": field,
        }
        for field in missing_fields
    ]


def build_follow_up_requests(
    eligibility_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Build citizen follow-up requests from all eligibility results.
    """

    follow_ups = []

    for result in eligibility_results:

        missing_items = extract_missing_information(
            result
        )

        for item in missing_items:

            follow_ups.append(
                {
                    "scheme_id": item["scheme_id"],
                    "field": item["field"],
                    "action": "collect_information",
                }
            )

    return follow_ups


def format_field_name(field: str) -> str:
    """
    Convert internal profile field names into
    citizen-friendly labels.
    """

    labels = {
        "annual_family_income": "annual family income",
        "land_holding": "land holding",
        "age": "age",
        "gender": "gender",
        "state": "state",
        "district": "district",
        "social_category": "social category",
        "occupation": "occupation",
        "school_class": "school class",
        "student_status": "student status",
        "farmer_status": "farmer status",
        "education_level": "education level",
        "disability_status": "disability status",
        "minority_status": "minority status",
        "business_status": "business status",
        "employment_status": "employment status",
    }

    return labels.get(
        field,
        field.replace("_", " ")
    )


def build_citizen_follow_up_message(
    scheme_id: str,
    field: str
) -> str:
    """
    Create a simple citizen-facing request for
    the missing information.
    """

    friendly_field = format_field_name(field)

    return (
        f"To check your eligibility for {scheme_id}, "
        f"please provide your {friendly_field}."
    )