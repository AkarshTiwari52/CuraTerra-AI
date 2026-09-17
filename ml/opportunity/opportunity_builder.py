from ml.opportunity.history_store import (
    opportunity_exists,
    add_opportunity,
    update_opportunity,
)


def build_opportunities(
    citizen_id: str,
    eligibility_results: list,
    checked_at: str
):
    """
    Compare current eligibility results with history.

    Returns:
        {
            "new_opportunities": [],
            "already_seen": [],
            "missing_information": []
        }
    """

    new_opportunities = []
    already_seen = []
    missing_information = []

    for result in eligibility_results:

        scheme_id = result.get("scheme_id")
        status = result.get("status")

        if not scheme_id:
            continue

        # -----------------------------------------
        # Eligible scheme
        # -----------------------------------------

        if status == "eligible":

            exists = opportunity_exists(
                citizen_id=citizen_id,
                scheme_id=scheme_id
            )

            if exists:

                update_opportunity(
                    citizen_id=citizen_id,
                    scheme_id=scheme_id,
                    status="eligible",
                    checked_at=checked_at
                )

                already_seen.append(
                    scheme_id
                )

            else:

                add_opportunity(
                    citizen_id=citizen_id,
                    scheme_id=scheme_id,
                    status="eligible",
                    detected_at=checked_at
                )

                new_opportunities.append(
                    scheme_id
                )

        # -----------------------------------------
        # Missing information
        # -----------------------------------------

        elif status == "missing_information":

            exists = opportunity_exists(
                citizen_id=citizen_id,
                scheme_id=scheme_id
            )

            if exists:

                update_opportunity(
                    citizen_id=citizen_id,
                    scheme_id=scheme_id,
                    status="missing_information",
                    checked_at=checked_at
                )

            else:

                add_opportunity(
                    citizen_id=citizen_id,
                    scheme_id=scheme_id,
                    status="missing_information",
                    detected_at=checked_at
                )

            missing_information.append(
                scheme_id
            )

        # -----------------------------------------
        # Not eligible
        # -----------------------------------------

        elif status == "not_eligible":

            # Nothing needs to be notified.
            continue

    return {
        "new_opportunities": new_opportunities,
        "already_seen": already_seen,
        "missing_information": missing_information,
    }