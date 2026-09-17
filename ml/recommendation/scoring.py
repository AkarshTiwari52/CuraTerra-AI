def calculate_score(features: dict) -> float:

    score = 0.0

    score += features.get("state_match", 0) * 3
    score += features.get("gender_match", 0) * 2
    score += features.get("student_match", 0) * 3
    score += features.get("category_match", 0) * 3
    score += features.get("farmer_match", 0) * 3

    return score