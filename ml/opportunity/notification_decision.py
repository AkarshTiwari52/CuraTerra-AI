"""
CuraTera AI - Notification Decision Layer

Responsibility:
    Decide what action should be taken for opportunities detected
    by the Opportunity Builder.

This component does NOT:
    - decide eligibility
    - calculate scores
    - send notifications

It only decides the action.
"""

from typing import Any


def decide_notifications(
    opportunity_result: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Convert opportunity results into notification actions.

    Rules:

        NEW opportunity
            -> notify

        ALREADY SEEN
            -> do nothing

        MISSING INFORMATION
            -> follow_up

        NOT ELIGIBLE
            -> ignore
    """

    actions = []

    # -------------------------------------------------
    # New eligible opportunities
    # -------------------------------------------------

    for scheme_id in opportunity_result.get(
        "new_opportunities",
        []
    ):

        actions.append(
            {
                "scheme_id": scheme_id,
                "action": "notify",
                "reason": "new_opportunity",
            }
        )

    # -------------------------------------------------
    # Missing information
    # -------------------------------------------------

    for scheme_id in opportunity_result.get(
        "missing_information",
        []
    ):

        actions.append(
            {
                "scheme_id": scheme_id,
                "action": "follow_up",
                "reason": "missing_information",
            }
        )

    # -------------------------------------------------
    # Already seen
    #
    # No action is created.
    # -------------------------------------------------

    return actions