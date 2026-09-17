
import pandas as pd


REQUIRED_COLUMNS = [
    "scheme_id",
    "rule_id",
    "section",
    "attribute",
    "operator",
    "normalized_value",
    "evidence_text",
]


def load_rules(csv_path: str) -> pd.DataFrame:
    """
    Load eligibility rules for all schemes.
    """

    df = pd.read_csv(csv_path)

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns in eligibility_rules.csv: "
            f"{missing_columns}"
        )

    # --------------------------------------------------------
    # Remove accidental duplicate header rows
    # --------------------------------------------------------

    df = df[
        df["scheme_id"]
        .astype(str)
        .str.strip()
        .str.lower()
        != "scheme_id"
    ].copy()

    # --------------------------------------------------------
    # Normalize important fields
    # --------------------------------------------------------

    df["scheme_id"] = (
        df["scheme_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["rule_id"] = (
        df["rule_id"]
        .astype(str)
        .str.strip()
    )

    df["section"] = (
        df["section"]
        .astype(str)
        .str.strip()
    )

    df["attribute"] = (
        df["attribute"]
        .astype(str)
        .str.strip()
    )

    df["operator"] = (
        df["operator"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df
