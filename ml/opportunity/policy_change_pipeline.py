from pathlib import Path
from ml.opportunity.document_extractor import extract_pdf_text
from ml.opportunity.structured_policy_extractor import extract_structured_policy
from ml.opportunity.policy_history import (
    get_latest_policy,
    save_policy_version,
)
from ml.opportunity.change_detector import detect_changes


def extract_policy_from_pdf(pdf_path, scheme_id):
    """
    Extract structured policy information from a government PDF.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    # ---------------------------------------------------------
    # STEP 1: Extract raw text from PDF
    # ---------------------------------------------------------
    text = extract_pdf_text(str(pdf_path))

    if not text.strip():
        raise ValueError(
            f"No text extracted from PDF: {pdf_path}"
        )

    # ---------------------------------------------------------
    # STEP 2: Convert raw text into structured policy
    # ---------------------------------------------------------
    policy_result = extract_structured_policy(
        text=text,
        scheme_id=scheme_id
    )

    return policy_result


def process_policy_update(
    pdf_path,
    scheme_id,
    source_url=None
):
    """
    Process a government policy PDF.

    First PDF:
        Save as Version 1.

    Later PDF:
        Compare against latest version.
        Save as a new version only if policy changed.
    """

    pdf_path = Path(pdf_path)

    # ---------------------------------------------------------
    # Extract new policy
    # ---------------------------------------------------------
    new_policy_result = extract_policy_from_pdf(
        pdf_path=pdf_path,
        scheme_id=scheme_id
    )

    # Some extractors return the policy directly,
    # while others return a wrapper containing policy.
    if "policy" in new_policy_result:
        new_policy = new_policy_result["policy"]
    else:
        new_policy = new_policy_result

    # ---------------------------------------------------------
    # Get latest saved policy
    # ---------------------------------------------------------
    latest_version = get_latest_policy(scheme_id)

    # ---------------------------------------------------------
    # FIRST VERSION
    # ---------------------------------------------------------
    if latest_version is None:

        saved_version = save_policy_version(
            scheme_id=scheme_id,
            policy=new_policy,
            source_url=source_url,
            source_file=str(pdf_path)
        )

        return {
            "status": "initial_version",
            "changed": True,
            "version": saved_version["version"],
            "previous_version": None,
            "changes": [],
            "policy": new_policy
        }

    # ---------------------------------------------------------
    # EXISTING VERSION
    # ---------------------------------------------------------
    old_policy = latest_version["policy"]

    changes = detect_changes(
        old_policy,
        new_policy
    )

    # ---------------------------------------------------------
    # NO CHANGE
    # ---------------------------------------------------------
    if not changes:

        return {
            "status": "no_change",
            "changed": False,
            "version": latest_version["version"],
            "previous_version": latest_version["version"],
            "changes": [],
            "policy": new_policy
        }

    # ---------------------------------------------------------
    # POLICY CHANGED
    # ---------------------------------------------------------
    saved_version = save_policy_version(
        scheme_id=scheme_id,
        policy=new_policy,
        source_url=source_url,
        source_file=str(pdf_path)
    )

    return {
        "status": "policy_changed",
        "changed": True,
        "version": saved_version["version"],
        "previous_version": latest_version["version"],
        "changes": changes,
        "policy": new_policy
    }