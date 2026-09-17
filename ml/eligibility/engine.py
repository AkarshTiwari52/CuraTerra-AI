from .matcher import compare_value


def check_scheme(profile: dict, scheme_rules):

    passed_rules = []
    failed_rules = []
    missing_information = []

    for _, rule in scheme_rules.iterrows():

        attribute = rule["attribute"]
        operator = rule["operator"]
        expected = rule["normalized_value"]

        actual = profile.get(attribute)

        result = compare_value(
            actual,
            operator,
            expected
        )

        rule_result = {
    "rule_id": rule["rule_id"],
    "section": rule["section"],
    "attribute": rule["attribute"],
    "actual": actual,
    "operator": operator,
    "expected": expected,
    "evidence_text": rule["evidence_text"]
}

        if result is True:
            passed_rules.append(rule_result)

        elif result is False:
            failed_rules.append(rule_result)

        else:
            missing_information.append(attribute)

    if failed_rules:
        status = "not_eligible"

    elif missing_information:
        status = "missing_information"

    else:
        status = "eligible"

    return {
        "status": status,
        "passed_rules": passed_rules,
        "failed_rules": failed_rules,
        "missing_information": list(
            dict.fromkeys(missing_information)
        )
    }


def evaluate_all_schemes(profile: dict, rules_df):

    results = []

    for scheme_id, scheme_rules in rules_df.groupby("scheme_id"):

        result = check_scheme(
            profile,
            scheme_rules
        )

        result["scheme_id"] = scheme_id

        results.append(result)

    return results