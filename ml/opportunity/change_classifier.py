def classify_change(change):
    """
    Classify a detected policy change.

    Input example:
    {
        "field": "eligibility.income_limit",
        "change_type": "modified",
        "old_value": 250000,
        "new_value": 300000
    }

    Output:
    {
        "field": "eligibility.income_limit",
        "old_value": 250000,
        "new_value": 300000,
        "change_type": "eligibility_change",
        "severity": "high",
        "action": "recheck_eligibility"
    }
    """

    field = change.get("field", "").lower()

    # ---------------------------------------------------------
    # Eligibility-related changes
    # ---------------------------------------------------------
    eligibility_fields = (
        "eligibility.",
    )

    if field.startswith(eligibility_fields):

        return {
            "field": change.get("field"),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "change_type": "eligibility_change",
            "severity": "high",
            "action": "recheck_eligibility"
        }

    # ---------------------------------------------------------
    # Benefit-related changes
    # ---------------------------------------------------------
    if field.startswith("benefits."):

        return {
            "field": change.get("field"),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "change_type": "benefit_change",
            "severity": "medium",
            "action": "inform_citizens"
        }

    # ---------------------------------------------------------
    # Deadline-related changes
    # ---------------------------------------------------------
    if field.startswith("deadline."):

        return {
            "field": change.get("field"),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "change_type": "deadline_change",
            "severity": "high",
            "action": "inform_citizens"
        }

    # ---------------------------------------------------------
    # Document-related changes
    # ---------------------------------------------------------
    if field.startswith("documents."):

        return {
            "field": change.get("field"),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "change_type": "document_change",
            "severity": "medium",
            "action": "inform_citizens"
        }

    # ---------------------------------------------------------
    # Application-related changes
    # ---------------------------------------------------------
    if field.startswith("application."):

        return {
            "field": change.get("field"),
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
            "change_type": "application_change",
            "severity": "medium",
            "action": "inform_citizens"
        }

    # ---------------------------------------------------------
    # Unknown / informational changes
    # ---------------------------------------------------------
    return {
        "field": change.get("field"),
        "old_value": change.get("old_value"),
        "new_value": change.get("new_value"),
        "change_type": "informational_change",
        "severity": "low",
        "action": "no_action"
    }