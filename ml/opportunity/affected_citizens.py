"""
CuraTera AI - Step 10.3 Affected Citizen Detector

Responsibility:
    Identify citizens whose profiles could be affected by a
    meaningful government-scheme eligibility change.

Important:
    This component does NOT decide final eligibility.

    It only answers:

        "Could this citizen be affected by the change?"

    The existing Eligibility Engine performs the final check.
"""

from __future__ import annotations

from typing import Any


# -------------------------------------------------
# Helper: normalize values
# -------------------------------------------------

def normalize_value(value: Any) -> Any:

    if value is None:
        return None

    if isinstance(value, str):

        value = value.strip().lower()

        replacements = {
            "female": "female",
            "girl": "female",
            "girls": "female",

            "male": "male",
            "boy": "male",
            "boys": "male",

            "general category": "general",
        }

        return replacements.get(
            value,
            value
        )

    return value


# -------------------------------------------------
# Helper: numeric value
# -------------------------------------------------

def to_number(value: Any):

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# -------------------------------------------------
# Helper: parse ranges
# -------------------------------------------------

def parse_range(value: Any):

    if value is None:
        return None

    text = (
        str(value)
        .replace("years", "")
        .replace("year", "")
        .replace("class", "")
        .strip()
    )

    parts = text.split("-")

    if len(parts) != 2:
        return None

    try:
        lower = float(parts[0].strip())
        upper = float(parts[1].strip())

        return lower, upper

    except ValueError:
        return None


# -------------------------------------------------
# Check whether citizen value matches a changed value
# -------------------------------------------------

def value_matches(
    citizen_value: Any,
    changed_value: Any
) -> bool:

    citizen_value = normalize_value(
        citizen_value
    )

    changed_value = normalize_value(
        changed_value
    )

    if citizen_value is None or changed_value is None:
        return False

    # ---------------------------------------------
    # Range
    # ---------------------------------------------

    range_value = parse_range(
        changed_value
    )

    if range_value is not None:

        number = to_number(
            citizen_value
        )

        if number is None:
            return False

        lower, upper = range_value

        return lower <= number <= upper

    # ---------------------------------------------
    # Comma-separated values
    # ---------------------------------------------

    if isinstance(changed_value, str):

        values = [
            normalize_value(item)
            for item in changed_value.split(",")
            if item.strip()
        ]

        if len(values) > 1:

            return citizen_value in values

    # ---------------------------------------------
    # Normal equality
    # ---------------------------------------------

    return citizen_value == changed_value


# -------------------------------------------------
# Check one eligibility-related change
# -------------------------------------------------

def citizen_may_be_affected(
    profile: dict[str, Any],
    change: dict[str, Any]
) -> bool:

    field = change.get("field")

    old_value = change.get("old_value")

    new_value = change.get("new_value")

    if not field:
        return False

    # ---------------------------------------------
    # Map scheme field -> citizen profile field
    # ---------------------------------------------

    field_mapping = {

        "age": "age",
        "age_range": "age",

        "school_class": "school_class",
        "class": "school_class",

        "gender": "gender",

        "category": "social_category",
        "social_category": "social_category",

        "state": "state",
        "state_residency": "state",

        "education_level": "education_level",

        "income": "annual_family_income",
        "income_limit": "annual_family_income",

        "land_holding": "land_holding",

        "farmer_status": "farmer_status",

        "student_status": "student_status",

        "disability_status": "disability_status",

        "minority_status": "minority_status",

        "occupation": "occupation",

        "employment_status": "employment_status",

        "business_status": "business_status",
    }

    profile_field = field_mapping.get(field)

    if not profile_field:
        return False

    citizen_value = profile.get(profile_field)

    # ---------------------------------------------
    # Missing profile information
    #
    # We cannot safely determine the impact,
    # so the citizen should be re-checked.
    # ---------------------------------------------

    if citizen_value is None:
        return True

    # ---------------------------------------------
    # Numeric threshold change
    #
    # Example:
    #
    # old limit = 250000
    # new limit = 300000
    #
    # A citizen with income = 280000
    # lies inside the changed range and
    # should therefore be re-checked.
    # ---------------------------------------------

    old_number = to_number(old_value)
    new_number = to_number(new_value)
    citizen_number = to_number(citizen_value)

    if (
        old_number is not None
        and new_number is not None
        and citizen_number is not None
    ):

        lower = min(old_number, new_number)
        upper = max(old_number, new_number)

        # Citizen is inside the interval between
        # the old and new threshold.
        if lower < citizen_number <= upper:
            return True

        return False

    # ---------------------------------------------
    # Categorical / exact-value change
    # ---------------------------------------------

    matches_old = value_matches(
        citizen_value,
        old_value
    )

    matches_new = value_matches(
        citizen_value,
        new_value
    )

    return matches_old or matches_new


# -------------------------------------------------
# Find potentially affected citizens
# -------------------------------------------------

def find_affected_citizens(
    citizens: list[dict[str, Any]],
    classified_change: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Find citizens who could be affected by a scheme change.

    Only eligibility-related changes are considered.

    Returns citizen IDs and the fields that triggered the
    potential impact.
    """

    affected = []

    # ---------------------------------------------
    # Only eligibility changes trigger citizen
    # re-checks.
    # ---------------------------------------------

    if classified_change.get(
        "overall_action"
    ) != "recheck_eligibility":

        return affected

    scheme_id = classified_change.get(
        "scheme_id"
    )

    changes = classified_change.get(
        "changes",
        []
    )

    eligibility_changes = [
        change
        for change in changes
        if change.get(
            "change_type"
        ) == "eligibility_change"
    ]

    for citizen in citizens:

        citizen_id = citizen.get(
            "citizen_id",
            "unknown"
        )

        profile = citizen.get(
            "profile",
            {}
        )

        affected_fields = []

        for change in eligibility_changes:

            if citizen_may_be_affected(
                profile=profile,
                change=change
            ):

                affected_fields.append(
                    change.get("field")
                )

        if affected_fields:

            affected.append(
                {
                    "citizen_id": citizen_id,
                    "scheme_id": scheme_id,
                    "affected_fields": affected_fields,
                    "action": "recheck_eligibility",
                }
            )

    return affected