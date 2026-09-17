from .features import build_features
from .scoring import calculate_score


def rank_schemes(
    profile: dict,
    eligible_schemes: list[dict],
    top_n: int = 5
) -> list[dict]:

    ranked = []

    for scheme in eligible_schemes:

        features = build_features(
            profile,
            scheme
        )

        score = calculate_score(
            features
        )

        ranked.append({
            "scheme_id": scheme["scheme_id"],
            "scheme_name": scheme.get("scheme_name"),
            "score": score,
            "features": features
        })

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked[:top_n]