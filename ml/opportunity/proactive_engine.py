"""
CuraTera AI - Daily Proactive Engine

Responsibility:
    Run periodic eligibility checks for citizen profiles.

The Proactive Engine does NOT decide eligibility itself.
It delegates eligibility evaluation to the existing Eligibility Engine.

Flow:

Citizen Profiles
       ↓
Proactive Engine
       ↓
Eligibility Engine
       ↓
Eligibility Results
       ↓
Return structured daily check results

Notification sending, cooldowns, reminders, and change detection
will be added in later versions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from ml.eligibility.engine import evaluate_all_schemes


def is_valid_profile(profile: dict[str, Any]) -> bool:
    """
    Check whether the profile is usable for a proactive eligibility scan.

    A profile does not need every CitizenProfile field.
    We only reject completely empty profiles here.
    """

    if not isinstance(profile, dict):
        return False

    if not profile:
        return False

    return True


def get_eligible_schemes(
    eligibility_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Extract only currently eligible schemes.

    The Eligibility Engine remains responsible for determining
    whether a scheme is eligible.
    """

    return [
        result
        for result in eligibility_results
        if result.get("status") == "eligible"
    ]


def get_missing_information_schemes(
    eligibility_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Extract schemes for which additional citizen information is required.
    """

    return [
        result
        for result in eligibility_results
        if result.get("status") == "missing_information"
    ]


def check_citizen(
    citizen_id: str,
    profile: dict[str, Any],
    rules_df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Run one daily proactive eligibility check for one citizen.

    This function does NOT send notifications.

    Parameters
    ----------
    citizen_id:
        Unique citizen identifier.

    profile:
        Structured CitizenProfile dictionary.

    rules_df:
        DataFrame loaded from eligibility_rules.csv.

    Returns
    -------
    dict
        Structured proactive scan result.
    """

    checked_at = datetime.now(timezone.utc).isoformat()

    # ---------------------------------------------------------
    # Validate profile
    # ---------------------------------------------------------

    if not is_valid_profile(profile):
        return {
            "citizen_id": citizen_id,
            "checked_at": checked_at,
            "status": "invalid_profile",
            "eligible_schemes": [],
            "missing_information_schemes": [],
            "all_results": [],
        }

    # ---------------------------------------------------------
    # Delegate actual eligibility evaluation
    # ---------------------------------------------------------

    eligibility_results = evaluate_all_schemes(
        profile=profile,
        rules_df=rules_df,
    )

    # ---------------------------------------------------------
    # Extract results
    # ---------------------------------------------------------

    eligible_schemes = get_eligible_schemes(
        eligibility_results
    )

    missing_information_schemes = (
        get_missing_information_schemes(
            eligibility_results
        )
    )

    # ---------------------------------------------------------
    # Return structured result
    # ---------------------------------------------------------

    return {
        "citizen_id": citizen_id,
        "checked_at": checked_at,
        "status": "checked",
        "eligible_schemes": eligible_schemes,
        "missing_information_schemes": missing_information_schemes,
        "all_results": eligibility_results,
    }


def run_daily_check(
    citizens: list[dict[str, Any]],
    rules_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Run the proactive eligibility check for all active citizens.

    Expected citizen format:

    {
        "citizen_id": "C001",
        "profile": {
            ...
        }
    }

    The function only performs checks.
    It does not send messages.
    """

    daily_results: list[dict[str, Any]] = []

    for citizen in citizens:

        citizen_id = citizen.get(
            "citizen_id",
            "unknown",
        )

        profile = citizen.get(
            "profile",
            {},
        )

        result = check_citizen(
            citizen_id=citizen_id,
            profile=profile,
            rules_df=rules_df,
        )

        daily_results.append(result)

    return daily_results


def print_daily_summary(
    daily_results: list[dict[str, Any]],
) -> None:
    """
    Print a simple development-time summary.
    """

    total_citizens = len(daily_results)

    checked = sum(
        1
        for result in daily_results
        if result.get("status") == "checked"
    )

    invalid = sum(
        1
        for result in daily_results
        if result.get("status") == "invalid_profile"
    )

    total_eligible = sum(
        len(result.get("eligible_schemes", []))
        for result in daily_results
    )

    total_missing = sum(
        len(result.get("missing_information_schemes", []))
        for result in daily_results
    )

    print("\n" + "=" * 70)
    print("CURATERA DAILY PROACTIVE CHECK")
    print("=" * 70)

    print(f"Citizens scanned:              {total_citizens}")
    print(f"Profiles successfully checked: {checked}")
    print(f"Invalid profiles:              {invalid}")
    print(f"Eligible scheme matches:       {total_eligible}")
    print(f"Missing-information matches:   {total_missing}")

    print("=" * 70)


if __name__ == "__main__":

    # ---------------------------------------------------------
    # Development test
    # ---------------------------------------------------------

    RULES_PATH = (
        "data/processed/eligibility_rules.csv"
    )

    rules_df = pd.read_csv(
        RULES_PATH
    )

    # ---------------------------------------------------------
    # Temporary test citizens
    #
    # In production, these will come from the persistent
    # citizen/profile store.
    # ---------------------------------------------------------

    citizens = [

        {
            "citizen_id": "C001",
            "profile": {
                "age": 14,
                "gender": "female",
                "state": "Maharashtra",
                "district": "Pune",
                "social_category": "VJNT",
                "annual_family_income": 60000,
                "occupation": "Student",
                "school_class": 9,
                "student_status": True,
            },
        },

        {
            "citizen_id": "C002",
            "profile": {
                "age": 22,
                "gender": "male",
                "state": "Maharashtra",
                "district": "Pune",
                "social_category": "General",
                "annual_family_income": 60000,
                "occupation": "Student",
                "education_level": "Graduated",
                "student_status": True,
            },
        },
    ]

    results = run_daily_check(
        citizens=citizens,
        rules_df=rules_df,
    )

    print_daily_summary(
        daily_results=results,
    )

    for result in results:

        print(
            f"\nCitizen: {result['citizen_id']}"
        )

        print(
            "Eligible schemes:"
        )

        for scheme in result["eligible_schemes"]:
            print(
                f"  - {scheme['scheme_id']}"
            )

        print(
            "Missing information schemes:"
        )

        for scheme in result[
            "missing_information_schemes"
        ]:
            print(
                f"  - {scheme['scheme_id']}"
            )