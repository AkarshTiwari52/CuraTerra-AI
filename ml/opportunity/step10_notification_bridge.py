"""
CuraTera AI - Step 10.6.12
Step 10 -> Personalized Notification Bridge

Responsibility:
    Convert Step 10 policy-change opportunities into
    personalized notification payloads.

This component:
    - accepts Step 10 opportunity objects
    - creates notifications only for newly-created opportunities
    - does not perform eligibility checking
    - does not modify citizen profiles
    - does not decide eligibility
    - does not send notifications directly
"""

from __future__ import annotations

from typing import Any


def build_step10_notification(
    opportunity: dict[str, Any],
    language: str = "en",
) -> dict[str, Any] | None:
    """
    Build a personalized notification from a Step 10 opportunity.
    """

    if opportunity.get("opportunity_type") != "policy_change":
        return None

    if opportunity.get("new_status") != "eligible":
        return None

    citizen_id = opportunity.get("citizen_id")
    scheme_id = opportunity.get("scheme_id")

    if not citizen_id or not scheme_id:
        return None

    language = language.lower().strip()

    if language == "hi":
        message = (
            f"सरकारी योजना में बदलाव के बाद आप "
            f"{scheme_id} के लिए पात्र हो सकते हैं।"
        )

    elif language == "hinglish":
        message = (
            f"Government policy change ke baad aap "
            f"{scheme_id} ke liye eligible ho sakte hain."
        )

    else:
        message = (
            f"A government policy change may have made you "
            f"newly eligible for {scheme_id}."
        )

    return {
        "citizen_id": citizen_id,
        "scheme_id": scheme_id,
        "notification_type": "new_opportunity",
        "language": language,
        "priority": "high",
        "message": message,
        "old_status": opportunity.get("old_status"),
        "new_status": opportunity.get("new_status"),
        "source": opportunity.get(
            "source",
            "step10_policy_change",
        ),
    }


def build_notifications(
    opportunities: list[dict[str, Any]],
    language: str = "en",
) -> list[dict[str, Any]]:
    """
    Convert Step 10 opportunities into notification payloads.
    """

    notifications = []

    for opportunity in opportunities:
        notification = build_step10_notification(
            opportunity=opportunity,
            language=language,
        )

        if notification is not None:
            notifications.append(notification)

    return notifications