"""
Generate CuraTera eligibility rules from the structured scheme dataset.

Pipeline:

curaterra_scheme_dataset_v2.xlsx
        |
        +--> Eligibility_Rules
        |
        +--> RAG_Documents
        |
        v
rule_generator.py
        |
        +--> eligibility_rules_preview.csv
        |
        +--> unsupported_rules.csv

The active eligibility_rules.csv is never overwritten automatically.

Important:
- The source workbook contains schemes S001-S025.
- S006 is the Savitribai Phule Scholarship.
- The current active CuraTera system uses S039 for that scheme.
- Therefore S006 -> S039 is the only currently verified ID mapping.
- Every other source scheme ID is kept unchanged unless explicitly mapped.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


# ============================================================================
# PATHS
# ============================================================================

DEFAULT_SOURCE_XLSX = "data/raw/curaterra_scheme_dataset_v2.xlsx"
DEFAULT_ACTIVE_CSV = "data/processed/eligibility_rules.csv"
DEFAULT_OUTPUT_CSV = "data/processed/eligibility_rules_preview.csv"
DEFAULT_UNSUPPORTED_CSV = "data/processed/unsupported_rules.csv"


# ============================================================================
# VERIFIED SCHEME ID MAPPINGS
# ============================================================================
#
# Source workbook:
#     S006 = Savitribai Phule Scholarship
#
# Active CuraTera system:
#     S039 = same Savitribai scheme
#
# Do NOT add mappings unless the schemes have been verified to be identical.
# ============================================================================

SCHEME_ID_MAP = {
    "S006": "S039",
}


# ============================================================================
# SOURCE SCHEMA
# ============================================================================

SOURCE_REQUIRED_COLUMNS = [
    "scheme_id",
    "rule_id",
    "attribute",
    "operator",
    "value",
    "rule_type",
]


ACTIVE_REQUIRED_COLUMNS = [
    "scheme_id",
    "rule_id",
    "section",
    "attribute",
    "operator",
    "normalized_value",
    "evidence_text",
]


# ============================================================================
# OPERATOR MAPPING
# ============================================================================

OPERATOR_MAP = {
    "equals": "==",
    "not_equals": "!=",
    "less_than": "<",
    "less_than_or_equal": "<=",
    "greater_than": ">",
    "greater_than_or_equal": ">=",
    "in": "IN",
    "between": "RANGE",
}


# ============================================================================
# ATTRIBUTE MAPPING
# ============================================================================
#
# Only map attributes when the meaning is sufficiently clear.
#
# Unknown attributes are retained instead of being silently renamed.
# This is safer than inventing a profile mapping.
# ============================================================================

ATTRIBUTE_MAP = {
    "state_residency": "state",
    "residency": "state",
    "family_income": "annual_family_income",
    "landholding": "land_holding",
    "disability": "disability_status",
    "farming_status": "farmer_status",
}


# ============================================================================
# SPECIAL ATTRIBUTE NORMALIZATION
# ============================================================================

ATTRIBUTE_VALUE_MAP = {
    "gender": {
        "female": "female",
        "male": "male",
        "transgender": "transgender",
        "any": "any",
        "all": "all",
    },
}


# ============================================================================
# EXCEPTIONS
# ============================================================================

class UnsupportedRuleError(ValueError):
    """Raised when a rule cannot be safely represented by the current engine."""


# ============================================================================
# BASIC HELPERS
# ============================================================================

def clean_text(value) -> str:
    """Return a clean string representation of a value."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_scheme_id(value) -> str:
    """Normalize scheme IDs such as S006 -> S006."""
    return clean_text(value).upper()


def map_scheme_id(source_scheme_id: str) -> str:
    """
    Convert a source scheme ID into the active CuraTera scheme ID.

    Only explicitly verified mappings are changed.
    """
    source_scheme_id = normalize_scheme_id(source_scheme_id)

    return SCHEME_ID_MAP.get(
        source_scheme_id,
        source_scheme_id,
    )


def map_attribute(source_attribute: str) -> str:
    """
    Map a source attribute to the closest existing CitizenProfile attribute.
    """
    source_attribute = clean_text(source_attribute)

    return ATTRIBUTE_MAP.get(
        source_attribute,
        source_attribute,
    )


# ============================================================================
# VALUE NORMALIZATION
# ============================================================================

def normalize_in_value(value: str) -> str:
    """
    Convert semicolon-separated IN values into comma-separated values.

    Example:
        "VJNT; SBC"
        ->
        "VJNT,SBC"
    """

    parts = [
        part.strip()
        for part in str(value).split(";")
        if part.strip()
    ]

    return ",".join(parts)


def normalize_gender_value(value: str) -> str:
    """Normalize gender values."""
    value = clean_text(value).lower()

    return ATTRIBUTE_VALUE_MAP.get(
        "gender",
        {},
    ).get(
        value,
        value,
    )


def normalize_range_value(value: str) -> str:
    """
    Convert common ranges into a simple numeric range.

    Examples:
        18-60
        18 to 60
        Class 8-10
        Class 8 to 10

    Output:
        18-60
        8-10
    """

    value = clean_text(value)

    value = (
        value
        .replace("years", "")
        .replace("year", "")
        .strip()
    )

    match = re.search(
        r"(\d+)\s*(?:-|to)\s*(\d+)",
        value,
        flags=re.IGNORECASE,
    )

    if not match:
        raise UnsupportedRuleError(
            f"Could not safely parse RANGE value: {value!r}"
        )

    lower = match.group(1)
    upper = match.group(2)

    return f"{lower}-{upper}"


# ============================================================================
# EDUCATION / CLASS HANDLING
# ============================================================================

def detect_school_class_rule(
    source_attribute: str,
    source_value: str,
) -> tuple[str, str, str] | None:
    """
    Detect rules such as:

        education_level = Class 8-10
        education_level = Class 11-12
        education_level = Class VIII

    and map them to school_class where possible.
    """

    source_attribute = clean_text(source_attribute).lower()
    source_value = clean_text(source_value)

    if source_attribute != "education_level":
        return None

    # Example:
    # Class 8-10
    match = re.fullmatch(
        r"Class\s+(\d+)\s*(?:-|to)\s*(\d+)",
        source_value,
        flags=re.IGNORECASE,
    )

    if match:
        lower = match.group(1)
        upper = match.group(2)

        return (
            "school_class",
            "RANGE",
            f"{lower}-{upper}",
        )

    # Example:
    # Class VIII / Class 8
    single_match = re.fullmatch(
        r"Class\s+(\d+)",
        source_value,
        flags=re.IGNORECASE,
    )

    if single_match:
        number = single_match.group(1)

        return (
            "school_class",
            "==",
            number,
        )

    return None


# ============================================================================
# SOURCE LOADING
# ============================================================================

def load_source_rules(
    source_xlsx: str | Path,
) -> pd.DataFrame:
    """
    Load the complete Eligibility_Rules sheet.
    """

    source_xlsx = Path(source_xlsx)

    if not source_xlsx.exists():
        raise FileNotFoundError(
            f"Source workbook not found: {source_xlsx}"
        )

    df = pd.read_excel(
        source_xlsx,
        sheet_name="Eligibility_Rules",
        engine="openpyxl",
    )

    missing_columns = [
        column
        for column in SOURCE_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns in Eligibility_Rules sheet: "
            f"{missing_columns}"
        )

    df = df.copy()

    df["scheme_id"] = df["scheme_id"].apply(normalize_scheme_id)

    return df


# ============================================================================
# EVIDENCE LOADING
# ============================================================================

def load_evidence(
    source_xlsx: str | Path,
) -> dict[str, str]:
    """
    Build:

        source_scheme_id -> eligibility evidence text
    """

    rag = pd.read_excel(
        source_xlsx,
        sheet_name="RAG_Documents",
        engine="openpyxl",
    )

    required_columns = {
        "scheme_id",
        "section",
        "text",
    }

    missing_columns = sorted(
        required_columns - set(rag.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing columns in RAG_Documents sheet: "
            f"{missing_columns}"
        )

    evidence_map: dict[str, str] = {}

    for scheme_id, group in rag.groupby("scheme_id"):

        scheme_id = normalize_scheme_id(scheme_id)

        eligibility_rows = group[
            group["section"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "eligibility"
        ]

        if eligibility_rows.empty:
            evidence_map[scheme_id] = ""
            continue

        texts = [
            clean_text(value)
            for value in eligibility_rows["text"]
        ]

        texts = [
            text
            for text in texts
            if text
        ]

        evidence_map[scheme_id] = "\n\n".join(texts)

    return evidence_map


# ============================================================================
# RULE TRANSFORMATION
# ============================================================================

def transform_rule(
    row: pd.Series,
    target_scheme_id: str,
    evidence_text: str,
    generated_index: int,
) -> dict:
    """
    Convert one source rule into the active eligibility schema.
    """

    source_rule_id = clean_text(row["rule_id"])
    source_attribute = clean_text(row["attribute"])
    source_operator = clean_text(row["operator"]).lower()
    source_value = clean_text(row["value"])
    rule_type = clean_text(row["rule_type"]).lower()

    # ------------------------------------------------------------------------
    # OR RULES
    # ------------------------------------------------------------------------
    #
    # The current matcher/engine works with one rule at a time and evaluates
    # all rules as AND conditions.
    #
    # Therefore:
    #
    #     A OR B
    #
    # cannot safely be converted into two normal rows because that would
    # become:
    #
    #     A AND B
    #
    # We therefore reject OR rules instead of changing policy meaning.
    # ------------------------------------------------------------------------

    if source_operator == "or":

        raise UnsupportedRuleError(
            f"Unsupported OR rule: "
            f"{source_rule_id} | "
            f"{source_attribute} | "
            f"{source_value}"
        )

    # ------------------------------------------------------------------------
    # ATTRIBUTE MAPPING
    # ------------------------------------------------------------------------

    target_attribute = map_attribute(
        source_attribute
    )

    # ------------------------------------------------------------------------
    # INFORMATIONAL RULE
    # ------------------------------------------------------------------------
    #
    # Example:
    #
    #     income_limit = No income limit
    #
    # This is not a citizen requirement.
    #
    # Existing matcher supports:
    #
    #     NO_LIMIT
    #
    # which always evaluates True.
    # ------------------------------------------------------------------------

    if rule_type == "info":

        operator = "NO_LIMIT"

        normalized_value = source_value

        return {
            "scheme_id": target_scheme_id,
            "rule_id": f"{target_scheme_id}-E{generated_index:03d}",
            "section": "Eligibility",
            "attribute": target_attribute,
            "operator": operator,
            "normalized_value": normalized_value,
            "evidence_text": evidence_text,
        }

    # ------------------------------------------------------------------------
    # HARD RULE OPERATOR
    # ------------------------------------------------------------------------

    if source_operator not in OPERATOR_MAP:

        raise UnsupportedRuleError(
            f"Unsupported operator "
            f"{source_operator!r} "
            f"in rule {source_rule_id}"
        )

    operator = OPERATOR_MAP[source_operator]

    normalized_value = source_value

    # ------------------------------------------------------------------------
    # EDUCATION CLASS RANGE
    # ------------------------------------------------------------------------

    class_rule = detect_school_class_rule(
        source_attribute=source_attribute,
        source_value=source_value,
    )

    if class_rule is not None:

        (
            target_attribute,
            operator,
            normalized_value,
        ) = class_rule

    # ------------------------------------------------------------------------
    # IN OPERATOR
    # ------------------------------------------------------------------------

    if operator == "IN":

        normalized_value = normalize_in_value(
            source_value
        )

    # ------------------------------------------------------------------------
    # RANGE OPERATOR
    # ------------------------------------------------------------------------

    if operator == "RANGE":

        normalized_value = normalize_range_value(
            source_value
        )

    # ------------------------------------------------------------------------
    # GENDER
    # ------------------------------------------------------------------------

    if target_attribute == "gender":

        normalized_value = normalize_gender_value(
            normalized_value
        )

    # ------------------------------------------------------------------------
    # RETURN ACTIVE SCHEMA
    # ------------------------------------------------------------------------

    return {
        "scheme_id": target_scheme_id,
        "rule_id": f"{target_scheme_id}-E{generated_index:03d}",
        "section": "Eligibility",
        "attribute": target_attribute,
        "operator": operator,
        "normalized_value": normalized_value,
        "evidence_text": evidence_text,
    }


# ============================================================================
# GENERATION
# ============================================================================

def generate_all_rules(
    source_xlsx: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate rules for every source scheme.

    Returns:

        generated_rules
        unsupported_rules
    """

    source_rules = load_source_rules(
        source_xlsx
    )

    evidence_map = load_evidence(
        source_xlsx
    )

    generated_rows: list[dict] = []
    unsupported_rows: list[dict] = []

    # ------------------------------------------------------------------------
    # Process EVERY source scheme
    # ------------------------------------------------------------------------

    for source_scheme_id, scheme_rules in source_rules.groupby(
        "scheme_id",
        sort=True,
    ):

        target_scheme_id = map_scheme_id(
            source_scheme_id
        )

        evidence_text = evidence_map.get(
            source_scheme_id,
            "",
        )

        # --------------------------------------------------------------------
        # Missing evidence
        # --------------------------------------------------------------------

        if not evidence_text:

            unsupported_rows.append(
                {
                    "scheme_id": target_scheme_id,
                    "source_scheme_id": source_scheme_id,
                    "rule_id": "",
                    "attribute": "",
                    "operator": "",
                    "value": "",
                    "reason": (
                        "No Eligibility evidence found "
                        "in RAG_Documents"
                    ),
                }
            )

        generated_index = 1

        # --------------------------------------------------------------------
        # Process rules inside this scheme
        # --------------------------------------------------------------------

        for _, row in scheme_rules.iterrows():

            try:

                transformed = transform_rule(
                    row=row,
                    target_scheme_id=target_scheme_id,
                    evidence_text=evidence_text,
                    generated_index=generated_index,
                )

                generated_rows.append(
                    transformed
                )

                generated_index += 1

            except UnsupportedRuleError as error:

                unsupported_rows.append(
                    {
                        "scheme_id": target_scheme_id,
                        "source_scheme_id": source_scheme_id,
                        "rule_id": clean_text(
                            row["rule_id"]
                        ),
                        "attribute": clean_text(
                            row["attribute"]
                        ),
                        "operator": clean_text(
                            row["operator"]
                        ),
                        "value": clean_text(
                            row["value"]
                        ),
                        "reason": str(error),
                    }
                )

    generated_df = pd.DataFrame(
        generated_rows,
        columns=ACTIVE_REQUIRED_COLUMNS,
    )

    unsupported_df = pd.DataFrame(
        unsupported_rows,
        columns=[
            "scheme_id",
            "source_scheme_id",
            "rule_id",
            "attribute",
            "operator",
            "value",
            "reason",
        ],
    )

    return generated_df, unsupported_df


# ============================================================================
# ACTIVE CSV MERGE
# ============================================================================

def update_active_csv_preview(
    existing_csv: str | Path,
    generated_rules: pd.DataFrame,
    output_csv: str | Path,
) -> None:
    """
    Create a preview by replacing generated scheme IDs in the existing CSV.

    The original active CSV is NEVER modified.
    """

    existing_csv = Path(existing_csv)
    output_csv = Path(output_csv)

    if not existing_csv.exists():

        # If an active file does not yet exist, simply write generated rules.
        generated_rules.to_csv(
            output_csv,
            index=False,
        )

        return

    existing = pd.read_csv(
        existing_csv
    )

    missing_columns = [
        column
        for column in ACTIVE_REQUIRED_COLUMNS
        if column not in existing.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing columns in active eligibility CSV: "
            f"{missing_columns}"
        )

    generated_scheme_ids = set(
        generated_rules["scheme_id"]
        .astype(str)
        .str.strip()
    )

    kept = existing[
        ~existing["scheme_id"]
        .astype(str)
        .str.strip()
        .isin(generated_scheme_ids)
    ].copy()

    updated = pd.concat(
        [
            kept,
            generated_rules,
        ],
        ignore_index=True,
    )

    output_csv.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    updated.to_csv(
        output_csv,
        index=False,
    )


# ============================================================================
# VALIDATION SUMMARY
# ============================================================================

def print_summary(
    generated_rules: pd.DataFrame,
    unsupported_rules: pd.DataFrame,
) -> None:

    print("\n" + "=" * 80)
    print("RULE GENERATION SUMMARY")
    print("=" * 80)

    if generated_rules.empty:

        print("Generated rules: 0")

    else:

        generated_scheme_ids = (
            generated_rules["scheme_id"]
            .dropna()
            .astype(str)
            .unique()
        )

        print(
            f"Generated rules: "
            f"{len(generated_rules)}"
        )

        print(
            f"Generated schemes: "
            f"{len(generated_scheme_ids)}"
        )

        print(
            "Scheme IDs:"
        )

        print(
            ", ".join(
                sorted(generated_scheme_ids)
            )
        )

    print()

    if unsupported_rules.empty:

        print(
            "Unsupported rules: 0"
        )

    else:

        print(
            f"Unsupported rules: "
            f"{len(unsupported_rules)}"
        )

        unsupported_scheme_ids = (
            unsupported_rules["scheme_id"]
            .dropna()
            .astype(str)
            .unique()
        )

        print(
            "Schemes containing unsupported rules:"
        )

        print(
            ", ".join(
                sorted(unsupported_scheme_ids)
            )
        )

        print(
            "\nThese rules were NOT silently converted."
        )

    print("=" * 80)


# ============================================================================
# ARGUMENTS
# ============================================================================

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Generate CuraTera eligibility rules "
            "for all supported schemes."
        )
    )

    parser.add_argument(
        "--source-xlsx",
        default=DEFAULT_SOURCE_XLSX,
        help="Path to the structured CuraTera Excel dataset.",
    )

    parser.add_argument(
        "--active-csv",
        default=DEFAULT_ACTIVE_CSV,
        help="Path to the current active eligibility CSV.",
    )

    parser.add_argument(
        "--output-csv",
        default=DEFAULT_OUTPUT_CSV,
        help="Path for the generated preview CSV.",
    )

    parser.add_argument(
        "--unsupported-csv",
        default=DEFAULT_UNSUPPORTED_CSV,
        help="Path for unsupported rule report.",
    )

    return parser.parse_args()


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:

    args = parse_args()

    source_xlsx = Path(
        args.source_xlsx
    )

    output_csv = Path(
        args.output_csv
    )

    unsupported_csv = Path(
        args.unsupported_csv
    )

    # ------------------------------------------------------------------------
    # Generate rules for ALL schemes
    # ------------------------------------------------------------------------

    generated_rules, unsupported_rules = generate_all_rules(
        source_xlsx=source_xlsx
    )

    # ------------------------------------------------------------------------
    # Display generated rules
    # ------------------------------------------------------------------------

    print("\nGenerated rules:\n")

    if generated_rules.empty:

        print(
            "No rules were generated."
        )

    else:

        print(
            generated_rules.to_string(
                index=False
            )
        )

    # ------------------------------------------------------------------------
    # Create preview
    # ------------------------------------------------------------------------

    update_active_csv_preview(
        existing_csv=args.active_csv,
        generated_rules=generated_rules,
        output_csv=output_csv,
    )

    # ------------------------------------------------------------------------
    # Save unsupported report
    # ------------------------------------------------------------------------

    unsupported_csv.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    unsupported_rules.to_csv(
        unsupported_csv,
        index=False,
    )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    print_summary(
        generated_rules=generated_rules,
        unsupported_rules=unsupported_rules,
    )

    print(
        f"\nPreview written to: "
        f"{output_csv}"
    )

    print(
        f"Unsupported-rule report written to: "
        f"{unsupported_csv}"
    )

    print(
        "\nActive eligibility_rules.csv "
        "was NOT overwritten."
    )


if __name__ == "__main__":
    main()