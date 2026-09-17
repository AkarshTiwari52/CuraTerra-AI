from pathlib import Path
import json
from datetime import datetime
from copy import deepcopy


HISTORY_PATH = Path("data/processed/policy_history.json")


def _ensure_history_file():
    """
    Create the history directory and JSON file if they do not exist.
    """
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("{}", encoding="utf-8")


def _load_history():
    """
    Load the complete policy history from JSON.
    If the file is empty, treat it as an empty history.
    """
    _ensure_history_file()

    try:
        text = HISTORY_PATH.read_text(encoding="utf-8").strip()

        # Empty file means there is no policy history yet.
        if not text:
            return {}

        data = json.loads(text)

        if not isinstance(data, dict):
            raise ValueError("Policy history must be a JSON object.")

        return data

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {HISTORY_PATH}: {exc}"
        ) from exc

def _save_history(history):
    """
    Save the complete policy history to JSON.
    """
    _ensure_history_file()

    HISTORY_PATH.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def get_latest_policy(scheme_id):
    """
    Return the latest saved policy version for a scheme.

    Returns:
        dict | None
    """
    history = _load_history()

    scheme_history = history.get(scheme_id)

    if not scheme_history:
        return None

    return deepcopy(scheme_history.get("latest_version"))


def get_policy_versions(scheme_id):
    """
    Return all saved versions of a scheme.
    """
    history = _load_history()

    scheme_history = history.get(scheme_id)

    if not scheme_history:
        return []

    return deepcopy(scheme_history.get("versions", []))


def save_policy_version(
    scheme_id,
    policy,
    source_url=None,
    source_file=None
):
    """
    Save a new policy version.

    The first saved version becomes version 1.
    Every later saved version receives the next version number.
    """

    history = _load_history()

    if scheme_id not in history:
        history[scheme_id] = {
            "latest_version": None,
            "versions": []
        }

    scheme_history = history[scheme_id]

    versions = scheme_history.get("versions", [])

    next_version = len(versions) + 1

    version_record = {
        "version": next_version,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": source_url,
        "source_file": source_file,
        "policy": deepcopy(policy)
    }

    versions.append(version_record)

    scheme_history["versions"] = versions
    scheme_history["latest_version"] = version_record

    _save_history(history)

    return deepcopy(version_record)


def save_only_if_changed(
    scheme_id,
    policy,
    source_url=None,
    source_file=None
):
    """
    Save the policy only when it differs from the latest saved policy.

    Returns:
        {
            "changed": bool,
            "version": int | None,
            "previous_version": int | None,
            "policy": dict
        }
    """

    latest = get_latest_policy(scheme_id)

    if latest is None:
        new_version = save_policy_version(
            scheme_id=scheme_id,
            policy=policy,
            source_url=source_url,
            source_file=source_file
        )

        return {
            "changed": True,
            "version": new_version["version"],
            "previous_version": None,
            "policy": new_version["policy"]
        }

    old_policy = latest.get("policy")

    if old_policy == policy:
        return {
            "changed": False,
            "version": latest["version"],
            "previous_version": latest["version"],
            "policy": deepcopy(policy)
        }

    new_version = save_policy_version(
        scheme_id=scheme_id,
        policy=policy,
        source_url=source_url,
        source_file=source_file
    )

    return {
        "changed": True,
        "version": new_version["version"],
        "previous_version": latest["version"],
        "policy": new_version["policy"]
    }