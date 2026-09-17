"""
CuraTera AI - Step 10 to Step 9 Opportunity Bridge

Step 10:
    Detects government changes and re-checks affected citizens.

Step 9:
    Handles citizen opportunities and normal notification flow.

Special rule:
    A newly_eligible result caused by a government change is treated
    as a new event even if the citizen has seen the scheme before.
"""

from __future__ import annotations

from typing import Any

from ml.opportunity.history_store import add_opportunity
from ml.opportunity.notification_builder import build_notification


def process_step10_recheck(
    recheck_results: list[dict[str, Any]],
    checked_at: str,
    language: str = "en",
) -> dict[str, Any]:

    newly_eligible = []
    no_longer_eligible = []
    unchanged = []

    notifications = []

    for result in recheck_results:

        citizen_id = result["citizen_id"]
        scheme_id = result["scheme_id"]
        impact = result.get("impact")

        # -------------------------------------------------
        # NEWLY ELIGIBLE DUE TO GOVERNMENT CHANGE
        # -------------------------------------------------

        if impact == "newly_eligible":

            opportunity = {
                "citizen_id": citizen_id,
                "scheme_id": scheme_id,
                "status": "eligible",
                "source": "government_change",
                "event_type": "government_change_newly_eligible",
                "old_status": result.get("old_status"),
                "new_status": result.get("new_status"),
            }

            newly_eligible.append(
                opportunity
            )

            # ---------------------------------------------
            # Store/update history
            # ---------------------------------------------

            try:
                add_opportunity(
                    citizen_id=citizen_id,
                    scheme_id=scheme_id,
                    status="eligible",
                    detected_at=checked_at,
                )
            except Exception:
                # If the history record already exists, the
                # important event is still allowed to continue.
                pass

            # ---------------------------------------------
            # Build special notification
            # ---------------------------------------------

            notification = build_notification(
                citizen_id=citizen_id,
                scheme_id=scheme_id,
                opportunity_type="government_change_newly_eligible",
                language=language,
            )

            # Add event information to the payload.
            notification["source"] = "government_change"
            notification["old_status"] = result.get(
                "old_status"
            )
            notification["new_status"] = result.get(
                "new_status"
            )

            notifications.append(
                notification
            )

        # -------------------------------------------------
        # NO LONGER ELIGIBLE
        # -------------------------------------------------

        elif impact == "no_longer_eligible":

            no_longer_eligible.append(
                {
                    "citizen_id": citizen_id,
                    "scheme_id": scheme_id,
                    "old_status": result.get(
                        "old_status"
                    ),
                    "new_status": result.get(
                        "new_status"
                    ),
                    "event_type": "government_change_no_longer_eligible",
                }
            )

        # -------------------------------------------------
        # EVERYTHING ELSE
        # -------------------------------------------------

        else:

            unchanged.append(
                result
            )

    return {
        "newly_eligible": newly_eligible,
        "no_longer_eligible": no_longer_eligible,
        "unchanged": unchanged,
        "notifications": notifications,
    }