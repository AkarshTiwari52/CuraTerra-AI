def build_features(profile: dict, scheme: dict) -> dict:

    features = {}

    # -----------------------------------
    # State match
    # -----------------------------------

    citizen_state = str(
        profile.get("state", "")
    ).strip().lower()

    scheme_state = str(
        scheme.get("state", "")
    ).strip().lower()

    features["state_match"] = int(
        citizen_state != ""
        and scheme_state != ""
        and citizen_state == scheme_state
    )

    # -----------------------------------
    # Gender match
    # -----------------------------------

    citizen_gender = str(
        profile.get("gender", "")
    ).strip().lower()

    scheme_gender = str(
        scheme.get("target_gender", "")
    ).strip().lower()

    features["gender_match"] = int(
        citizen_gender != ""
        and scheme_gender != ""
        and citizen_gender == scheme_gender
    )

    # -----------------------------------
    # Student match
    # -----------------------------------

    citizen_student = profile.get(
        "student_status"
    )

    scheme_student = scheme.get(
        "student_target"
    )

    features["student_match"] = int(
        citizen_student is True
        and scheme_student is True
    )

    # -----------------------------------
    # Social category match
    # -----------------------------------

    citizen_category = str(
        profile.get("social_category", "")
    ).strip().lower()

    scheme_category = str(
        scheme.get("target_category", "")
    ).strip().lower()

    features["category_match"] = int(
        citizen_category != ""
        and scheme_category != ""
        and citizen_category == scheme_category
    )

    # -----------------------------------
    # Farmer match
    # -----------------------------------

    citizen_farmer = profile.get(
        "farmer_status"
    )

    scheme_farmer = scheme.get(
        "farmer_target"
    )

    features["farmer_match"] = int(
        citizen_farmer is True
        and scheme_farmer is True
    )

    return features