from copy import deepcopy


def detect_changes(old_policy, new_policy):
    """
    Compare two nested policy dictionaries.

    Returns a list containing every changed field.

    Example:

    old:
        {
            "eligibility": {
                "income_limit": 250000
            }
        }

    new:
        {
            "eligibility": {
                "income_limit": 300000
            }
        }

    Result:
        [
            {
                "field": "eligibility.income_limit",
                "old_value": 250000,
                "new_value": 300000
            }
        ]
    """

    changes = []

    def compare(old_value, new_value, path):
        # ---------------------------------------------------------
        # CASE 1: Both values are dictionaries
        # ---------------------------------------------------------
        if isinstance(old_value, dict) and isinstance(new_value, dict):

            all_keys = set(old_value.keys()) | set(new_value.keys())

            for key in sorted(all_keys):
                new_path = f"{path}.{key}" if path else key

                old_exists = key in old_value
                new_exists = key in new_value

                # Field was added
                if not old_exists:
                    changes.append({
                        "field": new_path,
                        "change_type": "added",
                        "old_value": None,
                        "new_value": deepcopy(new_value[key])
                    })

                # Field was removed
                elif not new_exists:
                    changes.append({
                        "field": new_path,
                        "change_type": "removed",
                        "old_value": deepcopy(old_value[key]),
                        "new_value": None
                    })

                # Field exists in both policies
                else:
                    compare(
                        old_value[key],
                        new_value[key],
                        new_path
                    )

            return

        # ---------------------------------------------------------
        # CASE 2: Values are different
        # ---------------------------------------------------------
        if old_value != new_value:
            changes.append({
                "field": path,
                "change_type": "modified",
                "old_value": deepcopy(old_value),
                "new_value": deepcopy(new_value)
            })

    compare(old_policy, new_policy, "")

    return changes


def has_changes(old_policy, new_policy):
    """
    Return True when at least one field changed.
    """
    return len(detect_changes(old_policy, new_policy)) > 0