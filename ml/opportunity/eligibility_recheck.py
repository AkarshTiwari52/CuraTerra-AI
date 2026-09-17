"""
CuraTera AI - Step 10.4 Eligibility Re-check

Responsibility:
    Re-check potentially affected citizens using the
    existing Eligibility Engine after a government
    scheme change.

This component does NOT:
    - create eligibility rules
    - decide eligibility independently
    - modify citizen profiles
    - send notifications
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ml.eligibility.engine import evaluate_all_schemes


# -------------------------------------------------
# Find one scheme's result
# -------------------------------------------------

def get_scheme_result(
    eligibility_results: list[dict[str, Any]],
    scheme_id: str,
) -> dict[str, Any] | None:

    for result in eligibility_results:

        if result.get("scheme_id") == scheme_id:
            return result

    return None


# -------------------------------------------------
# Compare old and new eligibility status
# -------------------------------------------------

def classify_eligibility_impact(
    old_status: str | None,
    new_status: str | None,
) -> str:

    # ---------------------------------------------
    # Not eligible → eligible
    # ---------------------------------------------

    if (
        old_status == "not_eligible"
        and new_status == "eligible"
    ):
        return "newly_eligible"

    # ---------------------------------------------
    # Eligible → not eligible
    # ---------------------------------------------

    if (
        old_status == "eligible"
        and new_status == "not_eligible"
    ):
        return "no_longer_eligible"

    # ---------------------------------------------
    # Eligible → eligible
    # ---------------------------------------------

    if (
        old_status == "eligible"
        and new_status == "eligible"
    ):
        return "still_eligible"

    # ---------------------------------------------
    # Not eligible → not eligible
    # ---------------------------------------------

    if (
        old_status == "not_eligible"
        and new_status == "not_eligible"
    ):
        return "still_not_eligible"

    # ---------------------------------------------
    # Anything involving missing information
    # ---------------------------------------------

    if (
        old_status == "missing_information"
        or new_status == "missing_information"
    ):
        return "missing_information"

    # ---------------------------------------------
    # Fallback
    # ---------------------------------------------

    return "status_changed"


# -------------------------------------------------
# Re-check one citizen for one scheme
# -------------------------------------------------

def recheck_citizen_scheme(
    citizen_id: str,
    profile: dict[str, Any],
    scheme_id: str,
    old_status: str | None,
    rules_df: pd.DataFrame,
) -> dict[str, Any]:

    # ---------------------------------------------
    # Run existing Eligibility Engine
    # ---------------------------------------------

    all_results = evaluate_all_schemes(
        profile=profile,
        rules_df=rules_df,
    )

    # ---------------------------------------------
    # Get new status for target scheme
    # ---------------------------------------------

    scheme_result = get_scheme_result(
        eligibility_results=all_results,
        scheme_id=scheme_id,
    )

    if scheme_result is None:

        new_status = None

    else:

        new_status = scheme_result.get(
            "status"
        )

    # ---------------------------------------------
    # Determine impact
    # ---------------------------------------------

    impact = classify_eligibility_impact(
        old_status=old_status,
        new_status=new_status,
    )

    return {
        "citizen_id": citizen_id,
        "scheme_id": scheme_id,
        "old_status": old_status,
        "new_status": new_status,
        "impact": impact,
    }


# -------------------------------------------------
# Re-check multiple affected citizens
# -------------------------------------------------

def recheck_affected_citizens(
    affected_citizens: list[dict[str, Any]],
    citizens: list[dict[str, Any]],
    rules_df: pd.DataFrame,
    previous_statuses: dict[tuple[str, str], str | None],
) -> list[dict[str, Any]]:

    results = []

    # ---------------------------------------------
    # Create quick citizen lookup
    # ---------------------------------------------

    citizen_lookup = {
        citizen.get("citizen_id"): citizen
        for citizen in citizens
    }

    # ---------------------------------------------
    # Re-check affected citizens
    # ---------------------------------------------

    for affected in affected_citizens:

        citizen_id = affected.get(
            "citizen_id"
        )

        scheme_id = affected.get(
            "scheme_id"
        )

        citizen = citizen_lookup.get(
            citizen_id
        )

        if citizen is None:
            continue

        profile = citizen.get(
            "profile",
            {}
        )

        old_status = previous_statuses.get(
            (citizen_id, scheme_id)
        )

        result = recheck_citizen_scheme(
            citizen_id=citizen_id,
            profile=profile,
            scheme_id=scheme_id,
            old_status=old_status,
            rules_df=rules_df,
        )

        results.append(result)

    return results