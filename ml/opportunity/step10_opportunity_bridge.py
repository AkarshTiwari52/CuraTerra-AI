"""
CuraTera AI - Step 10.6.11
Step 10 -> Step 9 Opportunity Bridge

Responsibility:
    Convert eligibility re-check results from Step 10 into
    proactive opportunities for Step 9.

This component:
    - accepts eligibility re-check results
    - creates opportunities only for newly eligible citizens
    - does not perform eligibility checking
    - does not modify citizen profiles
    - does not send notifications
"""

from __future__ import annotations

from typing import Any


def build_step10_opportunity(
    recheck_result: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Convert one Step 10 eligibility re-check result
    into an opportunity.

    Only newly eligible citizens create opportunities.
    """

    if recheck_result.get("impact") != "newly_eligible":
        return None

    citizen_id = recheck_result.get("citizen_id")
    scheme_id = recheck_result.get("scheme_id")

    if not citizen_id or not scheme_id:
        return None

    return {
        "citizen_id": citizen_id,
        "scheme_id": scheme_id,
        "opportunity_type": "policy_change",
        "reason": "Citizen became newly eligible after a government policy change.",
        "old_status": recheck_result.get("old_status"),
        "new_status": recheck_result.get("new_status"),
        "action": "create_opportunity",
        "source": "step10_policy_change",
    }


def bridge_recheck_results(
    recheck_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert Step 10 re-check results into Step 9 opportunities.
    """

    opportunities = []

    for result in recheck_results:
        opportunity = build_step10_opportunity(result)

        if opportunity is not None:
            opportunities.append(opportunity)

    return opportunities