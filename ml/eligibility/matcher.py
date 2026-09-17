def normalize_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip().lower()

        # Boolean normalization
        if value == "true":
            return True

        if value == "false":
            return False

        # Common category normalization
        replacements = {
            "v.j.n.t.": "vjnt",
            "v.j.n.t": "vjnt",
            "v j n t": "vjnt",
            "s.b.c.": "sbc",
            "s.b.c": "sbc",
            "general category": "general",
        }

        value = replacements.get(value, value)

    return value


def compare_value(actual, operator, expected):

    actual = normalize_value(actual)
    expected = normalize_value(expected)

    if operator == "INFORMATION":
        return actual is not None

    if operator == "NO_LIMIT":
        return True

    if actual is None:
        return None

    if operator == "RANGE":

        range_text = (
            str(expected)
            .replace("years", "")
            .replace("year", "")
            .strip()
        )

        parts = range_text.split("-")

        if len(parts) != 2:
            raise ValueError(
                f"Invalid RANGE value: {expected}"
            )

        lower = float(parts[0].strip())
        upper = float(parts[1].strip())
        actual_number = float(actual)

        return lower <= actual_number <= upper

    if operator == "IN":

        if isinstance(expected, (list, tuple, set)):

            allowed_values = [
                normalize_value(item)
                for item in expected
            ]

        else:

            allowed_values = [
                normalize_value(item)
                for item in str(expected).split(",")
                if item.strip()
            ]

        return actual in allowed_values

    if operator == "==":
        return actual == expected

    if operator == "!=":
        return actual != expected

    # -----------------------------------------
    # Numeric comparisons
    # -----------------------------------------

    if operator in {">", ">=", "<", "<="}:

        try:
            actual_number = float(actual)
            expected_number = float(expected)
        except (TypeError, ValueError):
            raise ValueError(
                f"Cannot compare non-numeric values: "
                f"actual={actual!r}, expected={expected!r}, "
                f"operator={operator!r}"
            )

        if operator == ">":
            return actual_number > expected_number

        if operator == ">=":
            return actual_number >= expected_number

        if operator == "<":
            return actual_number < expected_number

        if operator == "<=":
            return actual_number <= expected_number

    raise ValueError(
        f"Unsupported operator: {operator}"
    )